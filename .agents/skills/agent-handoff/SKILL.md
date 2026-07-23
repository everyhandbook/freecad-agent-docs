---
name: agent-handoff
description: Prepare a clean brief, review, handoff, or status note for another agent or a later session. Use when an agent needs to transfer context, ask another agent to review a plan or result, leave current progress, or summarize risks without forcing the next session to rediscover the work.
---

# Agent Handoff

Prepare a handoff document that lets another agent or a later session continue work without rebuilding context from scratch.

## Modes

- `brief`: context and goals before another agent plans or implements.
- `review`: plan/result review with findings, risks, and approval status.
- `handoff`: current state, changed files, remaining work, and resume prompt.
- `status`: compact progress snapshot for a user or future session.

If the user does not name a mode, choose the smallest mode that preserves the needed context.

## Include

1. Goal and current status.
2. Relevant files, branches, PRs, docs, or external IDs.
3. Decisions already made.
4. Remaining work and next recommended action.
5. Risks, blockers, and verification state.

## Preferred Location

- Record durable handoffs in `docs/session-logs/YYYY-MM-DD-[topic]-[mode].md`.
- Keep tiny transient handoffs in chat when no future session needs the file.
- Do not include secrets, private customer data, or machine-specific paths unless the target repo is explicitly private and the information is necessary.
