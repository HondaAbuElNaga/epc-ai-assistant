# Spec: GitHub Actions CI

**Roadmap item:** Phase 9, "GitHub Actions CI, coverage ≥ 70%" (the CI part, moved earlier;
the coverage gate stays in Phase 9)
**Status:** draft (2026-10-11)
**Related:** PROJECT_PLAN "Testing strategy" (`.github/workflows/ci.yml`: install → ruff →
pytest) · `product/tech-stack.md` row "CI: GitHub Actions + `astral-sh/setup-uv`"

## In simple words

Today the checks (ruff + pytest) run **by hand** before each commit. CI is a robot on GitHub
that runs the same checks **automatically** on every pull request and every push to `main`, on
a clean computer, and shows ✅ or ❌ on the pull request page. A human can forget a check; the
robot can't.

## Goal

Every change that goes into `main` is checked automatically: the code is clean (ruff) and all
tests pass (pytest). The result is visible on GitHub, which also shows reviewers and employers
that the project is tested.

## Scope

- In:
  - One workflow file: `.github/workflows/ci.yml`.
  - Runs on: every **pull request** into `main`, and every **push to `main`** (after a merge).
  - Steps: get the code → install uv and Python 3.12 → install the locked dependencies (`uv sync --locked`) →
    `ruff check` → `ruff format --check` → `pytest` (without real-API, network and evaluation
    tests) with a coverage report.
  - A CI badge in `README.md`.
- Out:
  - Coverage **gate** (fail below 70 %): stays in Phase 9; this spec only **prints** coverage.
  - Tests that call the real Claude API (`llm`), download from websites (`network`) or run
    evaluations (`eval`).
  - Building the Docker image in CI, deployment, scheduled runs.
  - Any secret (no API key in CI).

## Requirements

1. **Same tools as local work:** uv with the same version as the `Dockerfile` (`0.12.2`),
   Python 3.12, dependencies from `uv.lock` without changes (`uv sync --locked`). If the lock
   file does not match `pyproject.toml`, CI fails.
2. **Lint:** `uv run ruff check .` must pass.
3. **Format:** `uv run ruff format --check .` must pass. In CI it only **checks**; it never
   changes files.
4. **Tests:** `uv run pytest -m "not network and not llm and not eval" --cov=src
   --cov-report=term` must pass. Coverage is printed, not enforced.
5. **No secrets and least permission:** the workflow gets only `contents: read`; no API keys.
   Tests must not need `.env` or anything in `data/` (git-ignored, not on GitHub).
6. **Pinned versions:** each GitHub Action is pinned to an exact release (checked on GitHub
   when building, not guessed). Never `@main`.
7. **Fast:** one run takes under 5 minutes (uv cache enabled).
8. **One failure = red:** if any step fails, the whole run is ❌ and the later steps are
   skipped.

## Inputs / outputs

- Input: the repository code at the pull request or push.
- Output: `.github/workflows/ci.yml`; a ✅/❌ check on each pull request and commit; a CI badge
  in `README.md`.

## Acceptance criteria

- [ ] `ci.yml` exists and the run on this spec's pull request is ✅.
- [ ] A deliberately broken change shows ❌ (proof the robot really checks). Done on a throwaway
      branch that is deleted afterwards, never merged.
- [ ] The run takes under 5 minutes (time from the GitHub run page, recorded in the DEVLOG).
- [ ] No secret is used; `permissions: contents: read` is set.
- [ ] README shows the CI badge.
- [ ] Docs: DEVLOG step, LEARNING_GUIDE section on CI / GitHub Actions, roadmap, PROJECT_PLAN,
      tech-stack status ✅.

## Technical approach

- **Tools:** GitHub Actions + `astral-sh/setup-uv` are already in `product/tech-stack.md`
  (status 🔜 → ✅ when done). `pytest-cov` is already a dev dependency.
- **Runner:** `ubuntu-latest` with uv directly, **not** the Docker image. Reason: faster and
  simpler; uv + `uv.lock` give the same package versions as the container. Small risk: an
  OS-level difference between the runner and `python:3.12-slim`. Accepted for now.
- **Order of the Ghent merge:** this branch starts from `main`, which does not have the Ghent
  loader yet. CI runs whatever tests are in the branch, so after the Ghent pull request is
  merged, its 45 tests are checked by CI too.
- **Risk:** a test that silently depends on a local file (`data/`, `.env`) passes locally but
  fails in CI. That is a real bug to fix in the test, not to hide in CI.

## Open questions (owner decision)

1. **Branch protection:** should GitHub **block** a merge into `main` while CI is ❌? This is a
   repository setting, not code. Recommended: yes, after the first green run.
2. **Extra checks:** add any other validation step now (see the list in the chat), or keep this
   first version minimal and add them later as small specs?
