# Tasks: Ghent project database (download, inspect, loader)

Spec: [spec.md](spec.md) · Branch: `spec/2026-10-08-ghent-project-db` · All commands inside the
container (`docker compose exec dev ...`).

- [x] 1. Open the download page; answer the open questions in the spec (form? which dataset?)
         Done 2026-10-10: no form; dataset = DSLIB v3.4 (GitHub release zip)
- [x] 2. Download into `data/raw/project_controls/ghent/`; record file list, sizes, date
         Done 2026-10-10: DSLIB3.4.zip, 231 projects; see format_notes.md §1–3, file_list.csv
- [x] 3. Inspect every file; write `format_notes.md` (files, sheets, columns, units, examples)
         Done 2026-10-10; openpyxl added (tech-stack + uv) to read the .xlsx files
- [x] 3b. Owner decision: option 1 (tracking from group A only); projects sorted into group
          folders A/B/C (copies) + `project_groups.csv` (spec "Decisions")
- [x] 4. Update the spec: exact columns of `projects`, `activities`, `tracking`; add `openpyxl`
         to `product/tech-stack.md` + `uv add` only if the files are Excel
- [x] 5. Build a tiny fixture in `tests/fixtures/` from the real format
- [x] 6. Write `tests/test_ghent_loader.py` (tables, snake_case, types, missing-column error),
         see it fail
- [ ] 7. Implement `src/datasets/ghent.py` (`load_ghent()`, `GhentData`)
- [ ] 8. Run on the real data: project count, baseline + tracking per project, BAC > 0;
         list any projects that fail
- [ ] 9. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [ ] 10. Docs: DEVLOG step, LEARNING_GUIDE (new tech only), roadmap tick + "Current position",
          stage_02 checklist, PROJECT_PLAN checklist, spec status → done
- [ ] 11. Push the branch, open a pull request, merge into `main`
