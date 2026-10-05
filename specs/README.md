# Feature Specs (Spec-Driven Development)

Every roadmap feature gets a spec here **before** any code is written.

## Workflow

```
product/roadmap.md item
        │
        ▼
1. specs/<YYYY-MM-DD>-<feature>/spec.md    ← WHAT and WHY (requirements, acceptance criteria)
2. specs/<YYYY-MM-DD>-<feature>/tasks.md   ← HOW (small ordered tasks, tests first)
        │   review and approve
        ▼
3. Implement task by task (in Docker, deps via uv)
4. Verify against the acceptance criteria (tests and metrics)
5. Update: roadmap [x] · DEVLOG step · LEARNING_GUIDE (new tech) · PROJECT_PLAN checklist
```

Example folder: `specs/2026-10-06-ufgs-download/`

## spec.md template

```markdown
# Spec: <feature name>

**Roadmap item:** Phase N, <item>   **Status:** draft | approved | done

## Goal
One or two sentences: what and why (link to the mission user/problem).

## Scope
- In: ...
- Out: ...

## Requirements
1. ...

## Inputs / outputs
- Input: ...
- Output: files, functions, schemas

## Acceptance criteria
- [ ] Measurable check 1 (test or metric)
- [ ] ...

## Technical approach
Libraries (must be in product/tech-stack.md), design, risks.
```

## tasks.md template

```markdown
# Tasks: <feature name>

- [ ] 1. Write tests for ...
- [ ] 2. Implement ...
- [ ] 3. Run `docker compose exec dev uv run pytest` and ruff
- [ ] 4. Update docs (roadmap, DEVLOG, LEARNING_GUIDE)
```
