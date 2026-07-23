#!/usr/bin/env python3
"""Validate corpus safety, encoding, source identity, hashes, and size budget."""
from __future__ import annotations
import hashlib, json
from pathlib import Path, PurePosixPath
from typing import Any
PROJECT_ROOT=Path(__file__).resolve().parents[1]
CONFIG_PATH=PROJECT_ROOT/"source-config.json"; MANIFEST_PATH=PROJECT_ROOT/"manifest.json"
def load_json(path:Path)->dict[str,Any]: return json.loads(path.read_text(encoding="utf-8"))
def fail(message:str)->None: raise RuntimeError(message)
def main()->int:
    config=load_json(CONFIG_PATH); manifest=load_json(MANIFEST_PATH)
    if config.get("schema_version")!=2 or manifest.get("schema_version")!=2: fail("Config and manifest must use schema version 2")
    corpus_root=(PROJECT_ROOT/config["destination"]).resolve(); corpus_root.relative_to(PROJECT_ROOT.resolve())
    sources={source["id"]:source for source in config["sources"]}; expected=set(); total_bytes=0
    for entry in manifest["files"]:
        relative=PurePosixPath(entry["output_path"]); path=(PROJECT_ROOT/relative).resolve()
        try: corpus_relative=path.relative_to(corpus_root)
        except ValueError: fail(f"Manifest output escapes the corpus root: {relative}")
        if not path.is_file(): fail(f"Manifest file is missing: {relative}")
        content=path.read_bytes(); content.decode("utf-8"); digest=hashlib.sha256(content).hexdigest()
        if digest!=entry["sha256"]: fail(f"SHA-256 mismatch: {relative}")
        if len(content)!=entry["size"]: fail(f"Size mismatch: {relative}")
        source_type=entry["source_type"]; source_id=entry["source_id"]
        if source_type=="github":
            if source_id not in sources or sources[source_id]["type"]!="github": fail(f"Unknown GitHub source: {source_id}")
            header=f"blob {len(content)}\0".encode("ascii"); blob_sha=hashlib.sha1(header+content,usedforsecurity=False).hexdigest()
            if blob_sha!=entry.get("git_blob_sha"): fail(f"Git blob SHA mismatch: {relative}")
            if len(content)>int(sources[source_id]["max_file_bytes"]): fail(f"GitHub file exceeds configured maximum: {relative}")
        elif source_type=="mediawiki":
            if source_id not in sources or sources[source_id]["type"]!="mediawiki": fail(f"Unknown MediaWiki source: {source_id}")
            if not str(entry.get("source_revision","")).isdigit(): fail(f"Missing MediaWiki revision ID: {relative}")
            if len(content)>int(sources[source_id]["max_page_bytes"]): fail(f"Wiki page exceeds configured maximum: {relative}")
        elif source_type!="generated": fail(f"Unsupported source type for {relative}: {source_type}")
        key=corpus_relative.as_posix()
        if key in expected: fail(f"Duplicate manifest output: {relative}")
        expected.add(key); total_bytes+=len(content)
    actual={path.relative_to(corpus_root).as_posix() for path in corpus_root.rglob("*") if path.is_file()}
    extra=sorted(actual-expected); missing=sorted(expected-actual)
    if extra: fail(f"Untracked files in corpus: {', '.join(extra)}")
    if missing: fail(f"Missing corpus files: {', '.join(missing)}")
    if total_bytes!=manifest.get("selected_bytes"): fail("Manifest selected_bytes does not match the corpus")
    limit=int(config["max_corpus_bytes"])
    if total_bytes>limit: fail(f"Corpus exceeds byte budget: {total_bytes:,} > {limit:,}")
    if manifest.get("max_corpus_bytes")!=limit: fail("Manifest byte budget does not match config")
    print(f"Validated {len(expected):,} files ({total_bytes:,} bytes) from {len(manifest['sources'])} sources."); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,json.JSONDecodeError,RuntimeError) as error:
        print(f"validation error: {error}"); raise SystemExit(1) from error