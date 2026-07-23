---
name: post-implement-check
description: Review completed implementation against the requested scope, plan, validation evidence, docs, and remaining risks. Use after implementation, before handoff/PR/merge, or when the user asks whether the work is actually ready.
---

# Post Implement Check

Perform an independent readiness check. Treat "files changed" and "work is ready" as different claims.

## Check

1. Scope: confirm the implementation matches the request or approved plan.
2. Behavior: inspect the relevant code/docs/workflows for missing pieces or regressions.
3. Validation: confirm tests/checks were run and interpret failures honestly.
4. Documentation: confirm task docs, README, session logs, or handoff notes match the actual state.
5. Risk: identify manual steps, unverified paths, external dependencies, and follow-up work.

## Verdict

Use one of these:

- `Ready`: core requirements are met and validation is sufficient.
- `Conditionally ready`: usable, but a named manual step or minor risk remains.
- `Needs changes`: core requirement, validation, or state alignment is missing.

## Output

Lead with findings before summary. Include file/line references when a concrete issue exists. Keep the final recommendation short and actionable.
