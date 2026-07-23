#!/usr/bin/env python3
"""Validate corpus safety, completeness, encoding, and manifest hashes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "source-config.json"
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    config = load_json(CONFIG_PATH)
    manifest = load_json(MANIFEST_PATH)
    corpus_root = (PROJECT_ROOT / config["destination"]).resolve()
    project_root = PROJECT_ROOT.resolve()
    corpus_root.relative_to(project_root)

    expected: set[str] = set()
    total_bytes = 0
    for entry in manifest["files"]:
        relative = PurePosixPath(entry["output_path"])
        path = (PROJECT_ROOT / relative).resolve()
        try:
            path.relative_to(corpus_root)
        except ValueError:
            fail(f"Manifest output escapes the corpus root: {relative}")
        if not path.is_file():
            fail(f"Manifest file is missing: {relative}")

        content = path.read_bytes()
        content.decode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        if digest != entry["sha256"]:
            fail(f"SHA-256 mismatch: {relative}")
        git_header = f"blob {len(content)}\0".encode("ascii")
        git_blob_sha = hashlib.sha1(git_header + content, usedforsecurity=False).hexdigest()
        if git_blob_sha != entry["git_blob_sha"]:
            fail(f"Git blob SHA mismatch: {relative}")
        if len(content) != entry["size"]:
            fail(f"Size mismatch: {relative}")
        if len(content) > int(config["max_file_bytes"]):
            fail(f"File exceeds configured maximum size: {relative}")

        expected.add(path.relative_to(corpus_root).as_posix())
        total_bytes += len(content)

    actual = {
        path.relative_to(corpus_root).as_posix()
        for path in corpus_root.rglob("*")
        if path.is_file()
    }
    extra = sorted(actual - expected)
    missing = sorted(expected - actual)
    if extra:
        fail(f"Untracked files in corpus: {', '.join(extra)}")
    if missing:
        fail(f"Missing corpus files: {', '.join(missing)}")

    print(
        f"Validated {len(expected)} files ({total_bytes:,} bytes) from "
        f"{manifest['source_repository']}@{manifest['source_commit'][:12]}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RuntimeError) as error:
        print(f"validation error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
