# FreeCAD Agent Documentation and CAD Workspace

This repository is an unofficial, agent-oriented FreeCAD knowledge corpus and a traceable workspace for future CAD projects. It combines versioned documentation embedded in the FreeCAD source tree with current English pages from the live FreeCAD Documentation wiki, then adds lightweight project and review conventions for agents.

## Included sources

- `corpus/freecad-source/`: documentation-like UTF-8 files copied byte-for-byte from a recorded commit of [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD).
- `corpus/freecad-wiki/`: raw MediaWiki source for English pages directly listed in the live wiki's `User Documentation` or `Developer Documentation` categories.

The Wiki selection excludes macro-library pages and sandbox pages, which consume substantial space without improving the core learning corpus. The generated corpus has a hard 9,500,000-byte limit so a complete Gitingest output remains below the requested 10 MB ceiling.

## Using with an agent

Ingest the whole repository for broad FreeCAD help and project context:

```text
https://github.com/everyhandbook/freecad-agent-docs
```

Use a narrower path when the agent only needs one evidence class:

```text
https://github.com/everyhandbook/freecad-agent-docs/tree/main/corpus/freecad-source/src/Doc
https://github.com/everyhandbook/freecad-agent-docs/tree/main/corpus/freecad-source/src/Mod/Sketcher
https://github.com/everyhandbook/freecad-agent-docs/tree/main/corpus/freecad-wiki
```

`AGENTS.md` defines operating, interpretation, and trust rules. `CORPUS_INFO.md` records the current source snapshot. Wiki files use a `--<pageid>.wiki` suffix and preserve MediaWiki templates, links, and translation markers. Exact page revision IDs, original URLs, Git blob IDs, sizes, and hashes are stored in `manifest.json`.

## CAD project workspace

Create real CAD work under `projects/<project-slug>/`, starting from `projects/_template/`. Each project records its goal, FreeCAD version, units, tolerances, constraints, source references, planned model tree, deliverables, and validation instead of leaving this context only in chat.

Repository-level continuity is intentionally small:

- `task.md` tracks the active phase and next actions.
- `docs/lessons.md` stores reusable decisions and pitfalls.
- `docs/session-logs/` preserves compact handoffs.
- `.agents/skills/` provides Codex workflows for project setup, checkpoints, implementation, handoff, and the PR review loop.

The imported workflow is a lean subset of [everyhandbook/3-agent-template](https://github.com/everyhandbook/3-agent-template). Product-specific mirrors, synchronization hooks, and unrelated optional packs are intentionally omitted.

## What this corpus can and cannot answer

The Wiki corpus covers normal use, workbenches, commands, tutorials, scripting, Python examples, compilation, and developer topics. Source-embedded documentation adds version-matched architecture and module context.

This still is not the complete FreeCAD implementation, generated C++ API reference, image library, forum history, addon source, or every Wiki namespace. Absence from this corpus is not evidence that an API or feature does not exist.

The actively maintained [FreeCAD Developers Handbook](https://github.com/FreeCAD/DevelopersHandbook) is a useful external reference. Its contents are not copied here because that repository currently does not expose an explicit redistribution license.

## Rebuilding and validation

Python 3.11 or newer is recommended. The scripts use only the Python standard library.

```console
python scripts/sync.py
python scripts/validate.py
```

Set `GITHUB_TOKEN` for authenticated GitHub API limits. `source-config.json` contains all reviewable source, selection, exclusion, per-file, and total-size rules. A sync is deterministic for the discovered Git commit and Wiki revision IDs.

GitHub Actions validates every push and checks the configured upstream sources weekly. When selected revisions change, the sync workflow commits the regenerated corpus, manifest, and reports.

## Attribution

This project is not affiliated with or endorsed by the FreeCAD project. FreeCAD source files retain their upstream licensing. FreeCAD Wiki content is provided under Creative Commons Attribution 3.0 according to the live Wiki API. See `LICENSE`, `THIRD_PARTY_NOTICES.md`, and source headers for details.
