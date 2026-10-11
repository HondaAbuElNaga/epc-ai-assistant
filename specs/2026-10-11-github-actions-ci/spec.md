# Spec: GitHub Actions CI

**Roadmap item:** Phase 9, "GitHub Actions CI, coverage ≥ 70%" (moved earlier, done in full
here)
**Status:** approved (2026-10-11), with the owner's decisions below
**Related:** PROJECT_PLAN "Testing strategy" (`.github/workflows/ci.yml`: install → ruff →
pytest) · `product/tech-stack.md` row "CI: GitHub Actions + `astral-sh/setup-uv`"

## In simple words

Today the checks (ruff + pytest) run **by hand** before each commit. CI is a robot on GitHub
that runs the same checks **automatically** on every pull request and every push to `main`, on
a clean computer, and shows ✅ or ❌ on the pull request page. A human can forget a check; the
robot can't. GitHub will also **refuse to merge** into `main` while the robot says ❌.

## Goal

Every change that goes into `main` is checked automatically: the code is clean (ruff), all
tests pass and cover enough of the code (pytest + coverage), and no secret (API key, password)
was committed. The result is visible on GitHub, which also shows reviewers and employers that
the project is tested.

## Decisions (owner, 2026-10-11)

1. **Protect `main`:** yes. A pull request can be merged only when CI is ✅.
2. **Extra checks (option b):** add a **secret scan** and a **coverage gate** now.

## Scope

- In:
  - One workflow file: `.github/workflows/ci.yml`, with two jobs:
    - **`tests`**: get the code → install uv and Python 3.12 → install the locked dependencies
      (`uv sync --locked`) → `ruff check` → `ruff format --check` → `pytest` (without
      real-API, network and evaluation tests) with coverage, **failing below 70 %**.
    - **`secrets`**: scan the whole git history for secrets with **gitleaks**.
  - Runs on: every **pull request** into `main`, and every **push to `main`** (after a merge).
  - Branch protection on `main`: both jobs must be ✅ before a merge.
  - A CI badge in `README.md`.
- Out:
  - Tests that call the real Claude API (`llm`), download from websites (`network`) or run
    evaluations (`eval`).
  - Type checking, dependency audit, Docker build, docs link check: possible later, each as a
    small spec.
  - Deployment, scheduled runs. Any secret in CI (no API key).

## Requirements

1. **Same tools as local work:** uv with the same version as the `Dockerfile` (`0.12.2`),
   Python 3.12, dependencies from `uv.lock` without changes (`uv sync --locked`). If the lock
   file does not match `pyproject.toml`, CI fails.
2. **Lint:** `uv run ruff check .` must pass.
3. **Format:** `uv run ruff format --check .` must pass. In CI it only **checks**; it never
   changes files.
4. **Tests + coverage gate:** `uv run pytest -m "not network and not llm and not eval"
   --cov=src --cov-report=term --cov-fail-under=70` must pass. The 70 % is the target in
   PROJECT_PLAN. Measured on 2026-10-11 with this exact command on the Ghent branch: **87 %**
   (97 passed, 3 deselected).
5. **Secret scan:** gitleaks scans the **full history** (not only the last commit), because a
   key that was committed and later deleted is still public in the history. Any finding = ❌.
   A false alarm is handled with a documented allow-list entry, never by turning the scan off.
6. **No secrets and least permission:** the workflow gets only `contents: read`; no API keys.
   Tests must not need `.env` or anything in `data/` (git-ignored, not on GitHub).
7. **Pinned versions:** each GitHub Action and gitleaks are pinned to an exact release
   (checked on GitHub when building, not guessed). Never `@main`.
8. **Fast:** one run takes under 5 minutes (uv cache enabled).
9. **One failure = red:** if any step fails, the run is ❌ and the later steps of that job are
   skipped.

## Inputs / outputs

- Input: the repository code (and history) at the pull request or push.
- Output: `.github/workflows/ci.yml`; a ✅/❌ check on each pull request and commit; branch
  protection on `main`; a CI badge in `README.md`.

## Acceptance criteria

- [ ] `ci.yml` exists and both jobs are ✅ on this spec's pull request.
- [ ] Proof that each check really works, on a throwaway branch (deleted afterwards, never
      merged): a failing test → ❌; a fake secret (a made-up, non-working key) → ❌.
- [ ] Coverage below 70 % fails the run (`--cov-fail-under=70` set).
- [ ] The run takes under 5 minutes (time from the GitHub run page, recorded in the DEVLOG).
- [ ] No secret is used; `permissions: contents: read` is set.
- [ ] `main` is protected: merging needs both jobs ✅.
- [ ] README shows the CI badge.
- [ ] Docs: DEVLOG step, LEARNING_GUIDE section on CI / GitHub Actions / secret scanning,
      roadmap, PROJECT_PLAN, tech-stack (gitleaks row, CI status ✅).

## Technical approach

- **Tools:** GitHub Actions + `astral-sh/setup-uv` are already in `product/tech-stack.md`.
  **gitleaks** is new: added to `tech-stack.md` before use. `pytest-cov` is already a dev
  dependency.
- **Runner:** `ubuntu-latest` with uv directly, **not** the Docker image. Reason: faster and
  simpler; uv + `uv.lock` give the same package versions as the container. Small risk: an
  OS-level difference between the runner and `python:3.12-slim`. Accepted for now.
- **gitleaks:** run the pinned gitleaks release directly (download + checksum check), with
  `fetch-depth: 0` so the full history is available. How exactly (official action or binary)
  is decided when building, after checking the current gitleaks docs and license terms.
- **Branch protection:** set with the `gh` CLI (GitHub API) after the first green run, because
  GitHub needs to have seen the job names first.
- **Order of the Ghent merge:** this branch starts from `main`, which does not have the Ghent
  loader yet. After the Ghent pull request is merged, its tests are checked by CI too. Once
  `main` is protected, the Ghent pull request also needs ✅ to be merged.
- **Risks:**
  - A test that silently depends on a local file (`data/`, `.env`) passes locally but fails in
    CI. That is a real bug to fix in the test, not to hide in CI.
  - gitleaks may find something already in the history. Then we check it: a real key must be
    **revoked** (made invalid at the provider) first; deleting it from git is not enough.
