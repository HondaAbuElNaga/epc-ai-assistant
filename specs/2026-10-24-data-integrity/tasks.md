# Tasks: Data integrity tests

- [x] 1. Owner approves `spec.md` and answers the open questions; status → `approved` (2026-10-28: all recommended answers)
- [x] 2. `pyproject.toml`: add the `data` marker, change `addopts` to
      `-m 'not network and not data'`; CI command gets `and not data`. Run `uv run pytest`:
      same passed count as `main`
- [x] 3. Write `tests/test_data_integrity.py`: folders + file counts (Req. 2–3), checksums per
      dataset (Req. 4), UFGS PDFs (Req. 5), Ghent with a module-scoped fixture (Req. 6–7),
      `EPC_RAW_DIR` / `EPC_CHECKSUMS` overrides
- [x] 4. Run `uv run pytest -m data` alone (no other heavy job); record result and run time
- [x] 5. Fault checks 1–3 from the spec; paste the failing output; undo every edit
      (`git diff` shows only the intended changes)
- [x] 6. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
- [x] 7. Verify every acceptance criterion against real output
- [x] 8. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
- [x] 9. Docs: DEVLOG step 21, LEARNING_GUIDE (pytest markers / data tests, if missing),
      PROJECT_PLAN Stage 2 ticks ("Integrity tests pass"), roadmap tick + "Current position";
      spec status → `done`
- [x] 10. Commit, push the branch, open a pull request into `main`; CI green (PR #8; CI tests + secrets passed 2026-10-28)

## Results (2026-10-28, in the container)

**Task 2.** Before (CI command, `main` state): 162 passed, 3 deselected, coverage 89 %.
After: 162 passed, 16 deselected (3 + the 13 data tests), coverage 88.84 %. Same passed count.

**Task 4.** `uv run pytest -m data`: **13 passed**.
- First version: 4 min 43 s. Each `checksums.verify` walks all of `data/raw/` (~7,000 files,
  20-35 s through the Windows -> container file share) and the tests called it 8 times.
- Fix: one module-scoped `verify(quick=True)` for all datasets, split per dataset with
  `dataset_of`. Then: 2 min 43 s, and 1 min 29 s on a second run (pytest's own time; disk cache
  makes the times vary). Slowest parts: UFGS PDFs 39-76 s, the shared verify 39-72 s, Ghent
  load 10-15 s.
- On that second run the wall-clock time was over 10 minutes while pytest reported 1 min 29 s;
  the extra time was outside pytest (`docker compose exec`, PC with ~2.6 GB of 16 GB RAM free).
  Cause not verified.

**Task 5. Fault checks** (all edits undone; `git status` showed only the intended files):
1. `checksums.json` copied to `/tmp/checksums_fault.json` in the container, size of
   `ufgs/01/UFGS_01_11_00.pdf` + 1, `EPC_CHECKSUMS` pointed at it:
   `AssertionError: ufgs: size changed: ['ufgs/01/UFGS_01_11_00.pdf']` (1 failed, 3 passed).
2. `GHENT_PROJECTS = 232`: `assert 231 == 232` (1 failed). Edit reverted to 231.
3. `EPC_RAW_DIR=/tmp/no_such_data`: 9 failed, 4 errors (Ghent fixture `FileNotFoundError`),
   **0 skipped**; all 4 `test_folder_has_recorded_file_count[...]` failed.

**Task 6.** `ruff check .` all checks passed; `ruff format .` 35 files unchanged; coverage gate
passed (88.84 %).

**Task 7.** Acceptance criteria: all met except "CI green", checked in task 10. Requirement 8
(under 3 minutes): met on both runs of the final version (2:43, 1:29 pytest time).

**Task 8. Review (3 subagents).** Security: nothing above Info (the CI `-m` repeats `addopts`;
a future opt-in marker must go in both). Bugs: empty `EPC_RAW_DIR`/`EPC_CHECKSUMS` became the
current folder → fixed with `or`; count test can't see a rename → comment added (the size test
catches it); BAC missing in group B would pass → kept, it follows answer 3 / Requirement 6.
Accuracy: all numbers match the catalog; "~30 s" comment → measured "39-72 s". After the fixes:
`pytest -m data` 13 passed in 1 min 26 s; ruff clean.
