# Tasks: Ghent project database (download, inspect, loader)

Spec: [spec.md](spec.md) · Branch: `spec/2026-10-08-ghent-project-db` · All commands inside the
container (`docker compose exec dev ...`).

- [ ] 1. Open the download page; answer the open questions in the spec (form? which dataset?)
- [ ] 2. Download into `data/raw/project_controls/ghent/`; record file list, sizes, date
- [ ] 3. Inspect every file; write `format_notes.md` (files, sheets, columns, units, examples)
- [ ] 4. Update the spec: exact columns of `projects`, `activities`, `tracking`; add `openpyxl`
         to `product/tech-stack.md` + `uv add` only if the files are Excel
- [ ] 5. Build a tiny fixture in `tests/fixtures/` from the real format
- [ ] 6. Write `tests/test_ghent_loader.py` (tables, snake_case, types, missing-column error),
         see it fail
- [ ] 7. Implement `src/datasets/ghent.py` (`load_ghent()`, `GhentData`)
- [ ] 8. Run on the real data: project count, baseline + tracking per project, BAC > 0;
         list any projects that fail
- [ ] 9. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [ ] 10. Docs: DEVLOG step, LEARNING_GUIDE (new tech only), roadmap tick + "Current position",
          stage_02 checklist, PROJECT_PLAN checklist, spec status → done
- [ ] 11. Push the branch, open a pull request, merge into `main`
