# Tasks: Data integrity tests

- [x] 1. Owner approves `spec.md` and answers the open questions; status → `approved` (2026-10-28: all recommended answers)
- [ ] 2. `pyproject.toml`: add the `data` marker, change `addopts` to
      `-m 'not network and not data'`; CI command gets `and not data`. Run `uv run pytest`:
      same passed count as `main`
- [ ] 3. Write `tests/test_data_integrity.py`: folders + file counts (Req. 2–3), checksums per
      dataset (Req. 4), UFGS PDFs (Req. 5), Ghent with a module-scoped fixture (Req. 6–7),
      `EPC_RAW_DIR` / `EPC_CHECKSUMS` overrides
- [ ] 4. Run `uv run pytest -m data` alone (no other heavy job); record result and run time
- [ ] 5. Fault checks 1–3 from the spec; paste the failing output; undo every edit
      (`git diff` shows only the intended changes)
- [ ] 6. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
- [ ] 7. Verify every acceptance criterion against real output
- [ ] 8. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
- [ ] 9. Docs: DEVLOG step 21, LEARNING_GUIDE (pytest markers / data tests, if missing),
      PROJECT_PLAN Stage 2 ticks ("Integrity tests pass"), roadmap tick + "Current position";
      spec status → `done`
- [ ] 10. Commit, push the branch, open a pull request into `main`; CI green
