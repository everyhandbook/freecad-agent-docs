#!/usr/bin/env python3
"""Build a deterministic, text-only documentation snapshot from FreeCAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "source-config.json"
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
CORPUS_INFO_PATH = PROJECT_ROOT / "CORPUS_INFO.md"
REPORT_JSON_PATH = PROJECT_ROOT / "reports" / "inventory.json"
REPORT_MD_PATH = PROJECT_ROOT / "reports" / "inventory.md"
USER_AGENT = "freecad-agent-docs-sync/1.0"


class SyncError(RuntimeError):
    """Raised when a safe, reproducible sync cannot be completed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download and rebuild even if the selected upstream blobs are unchanged.",
    )
    parser.add_argument(
        "--ref",
        help="Override the configured upstream ref for this run.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"Cannot read valid JSON from {path}: {exc}") from exc


def compile_glob(pattern: str) -> re.Pattern[str]:
    """Translate a small, path-aware glob subset to a regular expression."""
    pattern = pattern.lstrip("/")
    index = 0
    output = ["^"]
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    output.append("(?:.*/)?")
                    index += 1
                else:
                    output.append(".*")
                continue
            output.append("[^/]*")
        elif char == "?":
            output.append("[^/]")
        else:
            output.append(re.escape(char))
        index += 1
    output.append("$")
    return re.compile("".join(output))


def matches(path: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.fullmatch(path) for pattern in patterns)


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SyncError(f"GitHub request failed for {url}: {exc}") from exc


def fetch_blob(repository: str, commit_sha: str, path: str) -> bytes:
    encoded_path = urllib.parse.quote(path, safe="/")
    url = f"https://raw.githubusercontent.com/{repository}/{commit_sha}/{encoded_path}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SyncError(f"Cannot download upstream file {path}: {exc}") from exc


def resolve_commit(repository: str, ref: str) -> tuple[str, str]:
    encoded_ref = urllib.parse.quote(ref, safe="")
    commit_url = f"https://api.github.com/repos/{repository}/commits/{encoded_ref}"
    commit = fetch_json(commit_url)
    try:
        return commit["sha"], commit["commit"]["tree"]["sha"]
    except (KeyError, TypeError) as exc:
        raise SyncError("GitHub commit response did not contain the expected SHAs") from exc


def fetch_tree(repository: str, tree_sha: str) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{repository}/git/trees/{tree_sha}?recursive=1"
    payload = fetch_json(url)
    if payload.get("truncated"):
        raise SyncError("GitHub returned a truncated recursive tree; refusing a partial sync")
    tree = payload.get("tree")
    if not isinstance(tree, list):
        raise SyncError("GitHub tree response did not contain a file list")
    return tree


def fetch_tree_with_git(repository: str, ref: str) -> tuple[str, str, list[dict[str, Any]]]:
    """Fallback for unauthenticated GitHub API rate limits."""
    temp_parent = PROJECT_ROOT / ".sync-tmp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=temp_parent) as temporary:
            checkout = Path(temporary) / "metadata"
            clone = [
                "git",
                "clone",
                "--quiet",
                "--depth",
                "1",
                "--filter=blob:none",
                "--no-checkout",
                "--branch",
                ref,
                f"https://github.com/{repository}.git",
                str(checkout),
            ]
            subprocess.run(clone, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            commit_sha = subprocess.check_output(
                ["git", "-C", str(checkout), "rev-parse", "HEAD^{commit}"], text=True
            ).strip()
            tree_sha = subprocess.check_output(
                ["git", "-C", str(checkout), "rev-parse", "HEAD^{tree}"], text=True
            ).strip()
            raw_tree = subprocess.check_output(
                ["git", "-C", str(checkout), "ls-tree", "-r", "-z", "HEAD"]
            )
            entries: list[dict[str, Any]] = []
            for record in raw_tree.split(b"\0"):
                if not record:
                    continue
                header, raw_path = record.split(b"\t", 1)
                _mode, object_type, object_sha = header.decode("ascii").split()
                entries.append(
                    {
                        "path": raw_path.decode("utf-8"),
                        "type": object_type,
                        "sha": object_sha,
                        "size": None,
                    }
                )
            return commit_sha, tree_sha, entries
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError, UnicodeDecodeError) as exc:
        raise SyncError(f"Git metadata fallback failed for {repository}@{ref}: {exc}") from exc
    finally:
        try:
            temp_parent.rmdir()
        except OSError:
            pass


def document_extension(path: str, extensions: list[str]) -> str | None:
    lowered = path.lower()
    for extension in sorted(extensions, key=len, reverse=True):
        if lowered.endswith(extension.lower()):
            return extension.lower()
    if PurePosixPath(path).name.lower().startswith("readme"):
        return "README"
    return None


def safe_destination(root: Path, relative_path: str) -> Path:
    destination = (root / PurePosixPath(relative_path)).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError as exc:
        raise SyncError(f"Unsafe output path from upstream: {relative_path}") from exc
    return destination


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def selection_fingerprint(entries: list[dict[str, Any]]) -> str:
    lines = [f"{entry['path']}\0{entry['sha']}" for entry in entries]
    return sha256("\n".join(lines).encode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_inventory_markdown(report: dict[str, Any]) -> None:
    included = report["included"]
    skipped = report["skipped"]
    candidate_stats = report["candidate_extension_stats"]
    lines = [
        "# FreeCAD documentation inventory",
        "",
        f"- Upstream: `{report['source_repository']}`",
        f"- Ref: `{report['source_ref']}`",
        f"- Commit: `{report['source_commit']}`",
        f"- Total upstream blobs: {report['total_upstream_blobs']:,}",
        f"- Selected text files: {len(included):,}",
        f"- Selected bytes: {report['selected_bytes']:,}",
        f"- Rough token estimate: {report['estimated_tokens']:,}",
        f"- Skipped after selection: {len(skipped):,}",
        "",
        "## Document-like files in upstream",
        "",
        "| Extension | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for extension, values in sorted(candidate_stats.items()):
        size_label = f"{values['bytes']:,}" if values["bytes"] is not None else "unknown"
        lines.append(f"| `{extension}` | {values['files']:,} | {size_label} |")

    lines.extend(["", "## Selected files", ""])
    for entry in included:
        lines.append(f"- `{entry['source_path']}` ({entry['size']:,} bytes)")

    lines.extend(["", "## Skipped selected files", ""])
    if skipped:
        for entry in skipped:
            lines.append(f"- `{entry['path']}`: {entry['reason']}")
    else:
        lines.append("None.")

    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def ensure_replaceable_directory(path: Path) -> None:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    try:
        relative = resolved.relative_to(project)
    except ValueError as exc:
        raise SyncError(f"Refusing to replace a directory outside the project: {resolved}") from exc
    if len(relative.parts) < 2 or relative.parts[0] != "corpus":
        raise SyncError(f"Refusing to replace unexpected generated directory: {resolved}")


def main() -> int:
    args = parse_args()
    config = load_json(CONFIG_PATH)
    repository = config["source"]["repository"]
    ref = args.ref or config["source"]["ref"]
    destination = (PROJECT_ROOT / config["destination"]).resolve()
    ensure_replaceable_directory(destination)

    include_patterns = [compile_glob(value) for value in config["include_patterns"]]
    exclude_patterns = [compile_glob(value) for value in config["exclude_patterns"]]
    max_file_bytes = int(config["max_file_bytes"])
    inventory_extensions = list(config["inventory_extensions"])

    try:
        commit_sha, tree_sha = resolve_commit(repository, ref)
        tree = fetch_tree(repository, tree_sha)
    except SyncError as api_error:
        print(f"GitHub API metadata lookup failed; trying a filtered git clone: {api_error}", file=sys.stderr)
        commit_sha, tree_sha, tree = fetch_tree_with_git(repository, ref)
    blobs = [entry for entry in tree if entry.get("type") == "blob"]

    candidate_stats: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    unknown_sizes: Counter[str] = Counter()
    for entry in blobs:
        extension = document_extension(entry["path"], inventory_extensions)
        if extension:
            counts[extension] += 1
            if entry.get("size") is None:
                unknown_sizes[extension] += 1
            else:
                sizes[extension] += int(entry["size"])
    for extension in sorted(counts):
        candidate_stats[extension] = {
            "files": counts[extension],
            "bytes": None if unknown_sizes[extension] else sizes[extension],
        }

    selected_tree_entries: list[dict[str, Any]] = []
    pre_download_skips: list[dict[str, str]] = []
    for entry in blobs:
        path = entry["path"]
        if not matches(path, include_patterns):
            continue
        if matches(path, exclude_patterns):
            pre_download_skips.append({"path": path, "reason": "matched an exclude pattern"})
            continue
        size = int(entry.get("size") or 0)
        if size > max_file_bytes:
            pre_download_skips.append(
                {"path": path, "reason": f"larger than {max_file_bytes} bytes"}
            )
            continue
        selected_tree_entries.append(entry)

    selected_tree_entries.sort(key=lambda entry: entry["path"])
    fingerprint = selection_fingerprint(selected_tree_entries)
    if MANIFEST_PATH.exists() and not args.force:
        existing = load_json(MANIFEST_PATH)
        if (
            existing.get("selection_fingerprint") == fingerprint
            and CORPUS_INFO_PATH.exists()
            and REPORT_JSON_PATH.exists()
            and REPORT_MD_PATH.exists()
        ):
            print(
                f"No selected documentation changes: {repository}@{commit_sha[:12]} "
                f"matches the existing corpus fingerprint."
            )
            return 0

    temp_parent = PROJECT_ROOT / ".sync-tmp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    downloaded: list[dict[str, Any]] = []
    skipped = list(pre_download_skips)

    with tempfile.TemporaryDirectory(dir=temp_parent) as temporary:
        staging = Path(temporary) / "freecad"
        staging.mkdir(parents=True)

        for index, entry in enumerate(selected_tree_entries, start=1):
            path = entry["path"]
            print(f"[{index}/{len(selected_tree_entries)}] {path}")
            content = fetch_blob(repository, commit_sha, path)
            if len(content) > max_file_bytes:
                skipped.append({"path": path, "reason": f"larger than {max_file_bytes} bytes"})
                continue

            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                skipped.append({"path": path, "reason": "not valid UTF-8 text"})
                continue

            output = safe_destination(staging, path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
            downloaded.append(
                {
                    "source_path": path,
                    "output_path": str(
                        PurePosixPath(config["destination"]) / PurePosixPath(path)
                    ),
                    "git_blob_sha": entry["sha"],
                    "sha256": sha256(content),
                    "size": len(content),
                }
            )

        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging), str(destination))

    try:
        temp_parent.rmdir()
    except OSError:
        pass

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "schema_version": 1,
        "generated_at": generated_at,
        "source_repository": repository,
        "source_ref": ref,
        "source_commit": commit_sha,
        "source_tree": tree_sha,
        "selection_fingerprint": fingerprint,
        "files": downloaded,
    }
    selected_bytes = sum(entry["size"] for entry in downloaded)
    report = {
        "generated_at": generated_at,
        "source_repository": repository,
        "source_ref": ref,
        "source_commit": commit_sha,
        "total_upstream_blobs": len(blobs),
        "candidate_extension_stats": candidate_stats,
        "selected_bytes": selected_bytes,
        "estimated_tokens": round(selected_bytes / 4),
        "included": downloaded,
        "skipped": sorted(skipped, key=lambda entry: entry["path"]),
    }
    write_json(MANIFEST_PATH, manifest)
    write_json(REPORT_JSON_PATH, report)
    write_inventory_markdown(report)
    corpus_info = (
        "# Corpus snapshot\n\n"
        f"- Source repository: `{repository}`\n"
        f"- Source ref: `{ref}`\n"
        f"- Source commit: `{commit_sha}`\n"
        f"- Generated at: `{generated_at}`\n"
        f"- Selected UTF-8 files: {len(downloaded):,}\n"
        f"- Selected source bytes: {selected_bytes:,}\n\n"
        "The detailed path and checksum inventory is stored in `manifest.json`.\n"
    )
    CORPUS_INFO_PATH.write_text(corpus_info, encoding="utf-8", newline="\n")

    upstream_license = destination / "LICENSE"
    if upstream_license.exists():
        shutil.copyfile(upstream_license, PROJECT_ROOT / "LICENSE")

    print(
        f"Synced {len(downloaded)} UTF-8 text files ({selected_bytes:,} bytes) "
        f"from {repository}@{commit_sha[:12]}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as error:
        print(f"sync error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
