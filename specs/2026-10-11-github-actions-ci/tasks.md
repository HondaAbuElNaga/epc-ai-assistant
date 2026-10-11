# Tasks: GitHub Actions CI

Spec: [spec.md](spec.md) · Local commands inside the container (`docker compose exec dev ...`).

- [x] 1. Owner approves the spec and answers the open questions (2026-10-11: protect `main`;
         add secret scan + coverage gate)
- [x] 2. Run the exact CI test command locally on this branch
         (`uv run pytest -m "not network and not llm and not eval" --cov=src --cov-report=term
         --cov-fail-under=70`) and fix any test that needs `data/` or `.env`
         → 2026-10-11, on a clean copy (git archive, no `data/`, no `.env`, no API key): 1 test
           failed because `data/raw/.gitkeep` was never committed; fixed (`ef1839b`). Re-run: ruff
           ✅, 97 passed, 3 deselected, coverage 86.98 %.
- [x] 3. Look up the current releases of `actions/checkout`, `astral-sh/setup-uv` and gitleaks
         (and the gitleaks license terms); add gitleaks to `product/tech-stack.md`
         → 2026-10-11 (`gh release list`): checkout v7.0.1, setup-uv v10.3.0, gitleaks 8.30.1
           (MIT). Both actions pinned by commit SHA. `gitleaks-action` v3.0.0 not used: its own
           EULA needs a license key for organisation accounts and forbids changes; the MIT binary
           is used instead (SHA-256 checked). Local full-history scan: 37 commits, no leaks.
- [x] 4. Write `.github/workflows/ci.yml`: triggers, `permissions: contents: read`;
         job `tests` (setup-uv with uv `0.12.2` + Python 3.12 + cache, `uv sync --locked`,
         ruff check, ruff format --check, pytest with the coverage gate);
         job `secrets` (gitleaks, full history)
- [x] 5. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`
         → 2026-10-11: ruff ✅, 97 passed, 3 deselected, coverage 86.98 %
- [ ] 6. Push, open the pull request, check both jobs are ✅ and note the duration
- [ ] 7. Proof of ❌ on a throwaway branch: a failing test, then a fake secret; delete the branch
- [ ] 8. Protect `main` with `gh`: both jobs required before merge
- [ ] 9. README CI badge
- [ ] 10. Docs: DEVLOG step, LEARNING_GUIDE (CI, GitHub Actions, secret scanning), roadmap
          (Phase 9 CI item ticked, "Current position"), PROJECT_PLAN, tech-stack status ✅,
          spec status → done
- [ ] 11. Merge the pull request into `main`
