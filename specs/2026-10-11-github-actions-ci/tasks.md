# Tasks: GitHub Actions CI

Spec: [spec.md](spec.md) · Local commands inside the container (`docker compose exec dev ...`).

- [x] 1. Owner approves the spec and answers the open questions (2026-10-11: protect `main`;
         add secret scan + coverage gate)
- [ ] 2. Run the exact CI test command locally on this branch
         (`uv run pytest -m "not network and not llm and not eval" --cov=src --cov-report=term
         --cov-fail-under=70`) and fix any test that needs `data/` or `.env`
- [ ] 3. Look up the current releases of `actions/checkout`, `astral-sh/setup-uv` and gitleaks
         (and the gitleaks license terms); add gitleaks to `product/tech-stack.md`
- [ ] 4. Write `.github/workflows/ci.yml`: triggers, `permissions: contents: read`;
         job `tests` (setup-uv with uv `0.12.2` + Python 3.12 + cache, `uv sync --locked`,
         ruff check, ruff format --check, pytest with the coverage gate);
         job `secrets` (gitleaks, full history)
- [ ] 5. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`
- [ ] 6. Push, open the pull request, check both jobs are ✅ and note the duration
- [ ] 7. Proof of ❌ on a throwaway branch: a failing test, then a fake secret; delete the branch
- [ ] 8. Protect `main` with `gh`: both jobs required before merge
- [ ] 9. README CI badge
- [ ] 10. Docs: DEVLOG step, LEARNING_GUIDE (CI, GitHub Actions, secret scanning), roadmap
          (Phase 9 CI item ticked, "Current position"), PROJECT_PLAN, tech-stack status ✅,
          spec status → done
- [ ] 11. Merge the pull request into `main`
