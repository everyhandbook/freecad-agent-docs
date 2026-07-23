# FreeCAD Agent Documentation Corpus

This repository is an unofficial, automatically selected snapshot of text
documentation from [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD).
It is designed to be ingested by AI agents with tools such as
[Gitingest](https://github.com/coderamp-labs/gitingest), while remaining
browsable by people.

## Scope

The initial corpus intentionally includes only documentation-like files from
the FreeCAD source repository:

- the root FreeCAD README;
- Sphinx, Doxygen, and text documentation under `src/Doc`;
- module and workbench README, Markdown, reStructuredText, and Doxygen files
  under `src/Mod`;

It intentionally excludes application source code, tests, third-party code,
images, large diagram source files, generated HTML, UI resources, translations,
roadmaps, and the FreeCAD Wiki.
This corpus is therefore not a replacement for the complete FreeCAD user
manual or source tree.

## Ingesting the corpus

Ingest the whole repository, or target a module-sized subdirectory when only
one workbench is relevant:

```text
https://github.com/OWNER/REPOSITORY
https://github.com/OWNER/REPOSITORY/tree/main/corpus/freecad/src/Doc
https://github.com/OWNER/REPOSITORY/tree/main/corpus/freecad/src/Mod/Sketcher
https://github.com/OWNER/REPOSITORY/tree/main/corpus/freecad/src/Mod/PartDesign
```

The exact upstream commit is recorded in `CORPUS_INFO.md`; detailed file hashes
are recorded in `manifest.json`. `AGENTS.md` explains how to interpret the corpus.

## Rebuilding

Python 3.11 or newer is recommended. The scripts use only the Python standard
library.

```console
python scripts/sync.py
python scripts/validate.py
```

Set `GITHUB_TOKEN` when running repeatedly or from CI to receive authenticated
GitHub API rate limits. Selection rules live in `source-config.json`. A sync
does not rewrite or summarize upstream documents; selected blobs are preserved
byte-for-byte.

## Generated and maintained files

- `corpus/freecad/`: selected upstream files with their original paths.
- `manifest.json`: upstream commit, blob IDs, sizes, and SHA-256 checksums.
- `CORPUS_INFO.md`: compact snapshot metadata included in Agent ingests.
- `reports/inventory.md`: human-readable size and selection report.
- `source-config.json`: reviewable selection rules.
- `scripts/`: deterministic synchronization and validation tools.

## Status and attribution

This project is not affiliated with or endorsed by the FreeCAD project. The
copied corpus originates from FreeCAD and remains subject to the applicable
upstream licensing and notices. See `LICENSE`, `THIRD_PARTY_NOTICES.md`, and
the source headers where present.
