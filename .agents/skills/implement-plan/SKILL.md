---
name: implement-plan
description: Implement an approved plan end-to-end. Use when the user approves a plan, asks to implement a plan file, says to proceed according to the plan, or provides a plan path that should drive code/docs changes, validation, and handoff.
---

# Implement Plan

Use the approved plan as the execution baseline. Do not silently replace it with a new direction.

## Start

1. Find the plan path from the user request or latest approved plan.
2. Summarize the goal, scope, files/areas, constraints, and validation plan.
3. Note any approval boundaries before changing external systems, pushing, merging, deploying, deleting, or handling secrets.

If no plan can be found, ask for the plan path or restate the recently approved plan before editing.

## Execute

- Follow the plan in order unless repo reality requires a small adjustment.
- Keep changes scoped to the plan and existing repo patterns.
- Preserve unrelated dirty changes.
- Update related docs or task tracking when behavior, operating state, or follow-up work changes.
- If the plan becomes wrong, stop and explain the smallest correction needed.

## Verify

- Run the validation named in the plan when available.
- If no validation is named, run the narrowest meaningful checks for the changed files.
- If a check cannot run, record the reason and any residual risk.

## Finish

Report:

- What was implemented.
- What was verified.
- Files or docs changed.
- Remaining risks or follow-up.
- PR/branch/commit state when repository state changed.
