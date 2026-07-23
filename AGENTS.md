# Agent instructions

## Purpose

This repository is an automatically selected documentation snapshot from the
FreeCAD source repository. Use it as evidence when answering questions about
FreeCAD concepts, modules, architecture, or development.

## Interpretation rules

- This corpus is not the complete FreeCAD user manual or the complete source.
- Check `CORPUS_INFO.md` for the exact upstream repository, ref, and commit.
- Preserve the distinction between application-layer (`App`) objects and GUI
  or view-provider (`Gui`) objects.
- Treat files below `src/Mod/<Module>` as module-specific documentation.
- Do not infer an API, property, menu path, or behavior merely because it is
  absent from this filtered corpus.
- Doxygen commands such as `\\page`, `\\section`, and `\\ingroup` describe
  document structure and symbol relationships.
- Prefer version-matched evidence and mention version uncertainty when the
  user's FreeCAD version is unknown.
- Cite the original corpus path when a response depends on a specific file.
- Consult the full FreeCAD source or official user documentation when this
  corpus lacks implementation details or end-user instructions.

## Trust boundaries

Files under `corpus/freecad` are copied from the upstream commit recorded in
`CORPUS_INFO.md`. Files elsewhere in this repository are local tooling,
metadata, or project guidance rather than upstream FreeCAD documentation.
