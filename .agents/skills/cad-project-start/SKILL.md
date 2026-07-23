---
name: cad-project-start
description: Initialize or structure a traceable CAD project in this repository. Use when starting a new FreeCAD/CAD model, converting a request into model requirements, preparing a project directory, or defining deliverables and validation before implementation.
---

# CAD Project Start

Create a project workspace that preserves requirements, assumptions, evidence, outputs, and validation alongside the CAD files.

## Workflow

1. Read `AGENTS.md`, `task.md`, `docs/lessons.md`, and any relevant recent session log.
2. Create `projects/<project-slug>/` from `projects/_template/`. Do not modify `_template` for project-specific work.
3. Complete `project.md` before modeling:
   - goal and success criteria;
   - CAD tool and exact FreeCAD version when known;
   - unit system, coordinate/origin convention, dimensions, tolerances, and material;
   - manufacturing, assembly, licensing, compatibility, or export constraints;
   - source references and which facts are assumptions;
   - expected `.FCStd`, drawings, meshes, STEP files, screenshots, or other deliverables.
4. Record the intended model tree and major modeling decisions. Preserve the distinction between FreeCAD `App` objects and GUI/view-provider behavior.
5. Use version-matched repository evidence:
   - `corpus/freecad-wiki` for user workflows, commands, workbenches, and examples;
   - `corpus/freecad-source` for architecture and developer context;
   - full upstream sources when this filtered corpus is insufficient.
6. Complete `validation.md` as work proceeds. Check dimensions, constraints, recompute errors, geometry health, export behavior, and project-specific acceptance criteria.
7. Update `task.md` and a session log when project state changes materially.

## Guardrails

- Do not invent missing dimensions, tolerances, materials, or manufacturing requirements. Mark them as open questions or explicit assumptions.
- Do not silently overwrite user-authored `.FCStd` or exported artifacts.
- Keep generated project files under `projects/<project-slug>/`; keep `corpus/` generated and evidence-only.
- Treat screenshots as supporting evidence, not a substitute for dimensional and model validation.
- Mention FreeCAD version uncertainty when behavior may differ by release.
