# Agent instructions

## Purpose

This repository is an automatically selected, multi-source documentation snapshot for answering questions about FreeCAD concepts, workflows, modules, architecture, scripting, and development.

## Evidence routing

- Check `CORPUS_INFO.md` for current source revisions and corpus size.
- Use `corpus/freecad-wiki` first for end-user workflows, commands, workbenches, tutorials, and scripting examples.
- Use `corpus/freecad-source` for version-matched architecture, Doxygen relationships, coding conventions, and module-specific developer context.
- Use `manifest.json` when an exact original URL, Git commit, Git blob, Wiki page ID, Wiki revision ID, or content hash is required.
- Cite the original page title or source path when an answer depends on a specific file.

## Interpretation rules

- This corpus is not the complete FreeCAD implementation, generated API reference, image collection, addon ecosystem, forum archive, or every Wiki namespace.
- Preserve the distinction between application-layer (`App`) objects and GUI or view-provider (`Gui`) objects.
- Treat files below `src/Mod/<Module>` as module-specific documentation.
- Doxygen commands such as `\page`, `\section`, and `\ingroup` describe document structure and symbol relationships.
- `.wiki` files contain raw MediaWiki source. Templates, `<translate>` blocks, translation comments, and `[[Page|label]]` links are markup rather than literal UI text.
- Wiki pages and the FreeCAD source commit advance independently. Prefer evidence that matches the user's FreeCAD version and mention uncertainty when the version is unknown.
- Do not infer that an API, property, menu path, workbench, or behavior does not exist merely because it is absent here.
- Consult the full FreeCAD source, live Wiki, generated source documentation, or relevant addon repository when implementation detail is missing.

## Trust boundaries

- Files under `corpus/freecad-source` are byte-for-byte Git blobs from the FreeCAD commit recorded in `CORPUS_INFO.md` and `manifest.json`.
- Files below `corpus/freecad-wiki/pages` are UTF-8 wikitext returned by the live FreeCAD MediaWiki API for the revision recorded in `manifest.json`.
- `corpus/freecad-wiki/README.md`, repository root files, scripts, reports, and workflows are local generated tooling or project guidance rather than upstream FreeCAD documentation.