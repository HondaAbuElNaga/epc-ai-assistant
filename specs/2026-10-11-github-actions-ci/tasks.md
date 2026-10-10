# Tasks: GitHub Actions CI

Spec: [spec.md](spec.md) · Local commands inside the container (`docker compose exec dev ...`).

- [ ] 1. Owner approves the spec and answers the open questions
- [ ] 2. Run the exact CI test command locally in the container
         (`uv run pytest -m "not network and not llm and not eval" --cov=src --cov-report=term`)
         and fix any test that needs `data/` or `.env`
- [ ] 3. Look up the current releases of `actions/checkout` and `astral-sh/setup-uv` on GitHub
- [ ] 4. Write `.github/workflows/ci.yml` (triggers, `permissions: contents: read`, setup-uv
         with uv `0.12.2` + Python 3.12 + cache, `uv sync --frozen`, ruff check,
         ruff format --check, pytest)
- [ ] 5. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`
- [ ] 6. Push, open the pull request, check the first run is ✅ and note its duration
- [ ] 7. Proof of ❌: throwaway branch with a failing test, see the red run, delete the branch
- [ ] 8. README CI badge
- [ ] 9. Docs: DEVLOG step, LEARNING_GUIDE (CI / GitHub Actions), roadmap (CI ticked, coverage
         gate left in Phase 9), PROJECT_PLAN, tech-stack status ✅, spec status → done
- [ ] 10. Branch protection on `main` if the owner said yes (GitHub setting)
- [ ] 11. Merge the pull request into `main`
