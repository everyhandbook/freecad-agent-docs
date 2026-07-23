# Lessons

## 2026-07-23

- Keep the generated evidence corpus and authored CAD projects separate: `corpus/` is reproducible source material; `projects/` is working state and deliverables.
- FreeCAD Wiki wikitext and commit-pinned source files have different version and trust boundaries. Route user workflows to the Wiki and architecture questions to the matching source snapshot.
- Measure the actual complete Gitingest artifact, not only raw corpus bytes; repository guidance and agent skills are part of the delivered context.
- A clean Codex review may appear as an issue comment, while actionable findings may appear in formal reviews or inline comments. Check both surfaces and require the reviewed commit to match the current PR head.
- Do not copy the FreeCAD Developers Handbook until redistribution terms are explicit; linking to it is safe and still useful.
- A small repository-local workflow is easier to maintain than mirroring every agent product, hook, and optional pack from the general template.
- On Windows, preserve UTF-8 bytes when importing non-ASCII skill files and run Python validators with UTF-8 mode; console pipelines can silently replace Korean text with question marks.
