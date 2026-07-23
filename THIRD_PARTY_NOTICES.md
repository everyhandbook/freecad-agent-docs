# Third-party notices

This repository contains automatically selected text from two FreeCAD-operated upstream sources. The local synchronization and validation scripts do not replace the licensing of copied upstream content.

## FreeCAD source repository

Files under `corpus/freecad-source` originate from [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD) at the commit recorded in `CORPUS_INFO.md` and `manifest.json`.

FreeCAD is distributed under the GNU Lesser General Public License version 2.1 or later, with individual files potentially carrying additional compatible notices. The copied upstream `LICENSE` is retained at `corpus/freecad-source/LICENSE` and mirrored at the repository root. Source headers remain authoritative for individual files.

## FreeCAD Documentation Wiki

Files under `corpus/freecad-wiki/pages` originate from the live [FreeCAD Documentation Wiki](https://wiki.freecad.org). The Wiki API reports its content license as [Creative Commons Attribution 3.0](https://creativecommons.org/licenses/by/3.0/).

Attribution is provided through the original page title, page URL, page ID, revision ID, revision timestamp, and content hash recorded for every copied page in `manifest.json`. The files preserve the wikitext returned by the API; no authorship claim is made by this repository.

## Local project files

Repository guidance, selection configuration, reports, synchronization scripts, and GitHub workflows are local project material. They are not upstream FreeCAD documentation and are identified as such in `AGENTS.md`.