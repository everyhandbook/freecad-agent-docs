# FreeCAD corpus and agent workspace — 2026-07-23

## Status

PR #1 contains the initial public FreeCAD agent corpus. This follow-up adds a lean repository-local workflow and a reusable CAD project structure on the same branch.

## Decisions

- Keep the 10 MB complete Gitingest ceiling.
- Import only Codex-relevant workflow skills from `everyhandbook/3-agent-template`.
- Use the optional pack's actual skill name, `pr-review-loop`, for current-head Codex review handling.
- Store future CAD work in `projects/<slug>/`, separate from generated evidence.
- Require written units, tolerances, assumptions, deliverables, and validation for each CAD project.

## Validation

- `python scripts/validate.py`: passed for 1,808 corpus files and 9,038,135 source bytes.
- Skill validator: all eight repository-local skills passed.
- Complete local Gitingest: 1,832 files, 7,734,344 output bytes, approximately 1.9M tokens.
- GitHub checks remain to be confirmed after pushing the new PR head.

## Handoff

Wait for Codex review on the latest PR head. Classify findings before editing, apply only actionable current-head fixes, revalidate, push, and request review again. Do not merge without explicit user approval.
