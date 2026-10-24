# Spec: Data integrity tests

**Roadmap item:** Phase 2, "`tests/test_data_integrity.py`"
**Status:** draft
**Branch:** `spec/2026-10-24-data-integrity`
**Related:** PROJECT_PLAN Stage 2, "Testing" (4 checks listed there); `data/DATA_CATALOG.md`;
`data/checksums.json`; specs `2026-10-16-data-catalog` and `2026-10-16-profiling-notebooks`

## Goal
One test command that says "the data on this machine is the data the project was built on":
all folders there, every file the right size, every UFGS PDF readable with text, and the Ghent
loader giving the numbers recorded in the catalog. Modules A–D (and their evaluation scores)
depend on this data, so a broken, missing or silently changed file must fail a test, not show up
later as a strange result. This closes Phase 2 ("the data tests pass").

## What we already know (checked 2026-10-24, in the container)

- **No data in CI.** `data/raw/**` is in `.gitignore`, so GitHub Actions has no data. The CI
  job runs `pytest -m "not network and not llm and not eval"`; `pyproject.toml` `addopts` is
  `-m 'not network'`. Data tests have to stay out of CI and out of the default local run.
- **Checksums:** `src/datasets/checksums.py` already has `verify(root, out, dataset, quick)`
  returning a `Report` (`ok`, `missing`, `changed`, `new`, `passed`). `data/checksums.json`
  holds 6,995 files: ufgs 271 · ghent 697 · pid2graph 1,525 · dataset_pid 4,502. A full SHA-256
  verify took **3 min 17 s** (DEVLOG step 19); `quick=True` compares sizes only (seconds).
- **UFGS PDFs:** `src/datasets/profiling.py` `ufgs_pdf_stats(folder)` → one row per PDF with
  `pages`, `text_chars`, `empty_pages`. Real run today: **271 PDFs in 74 s**, min pages 5,
  min text 10,393 characters, **0 pages without text**. Folders: 12 divisions (01, 03, 05, 22,
  23, 26, 33, 40, 41, 43, 44, 46); division 42 has no active section (catalog line 66).
- **Ghent:** `load_ghent()` takes **23 s** and returns:
  - 231 projects; groups A 117 · B 41 · C 73.
  - all 231 projects have activities (the baseline schedule).
  - **tracking only for group A**: 117 projects, each with **≥ 2** periods; B and C have none.
    So the PROJECT_PLAN line "each project has a baseline plus at least one tracking period"
    is not true for the data; the test checks it for group A only.
  - `bac` > 0 for every project that has one; `bac` missing for **31 projects, all group C**
    (loader issue "BAC missing"). Group A: 0 missing.
- **P&ID datasets** have no loader; the profiling notebook reads them. Here they are covered by
  the folder and checksum checks only.

## Scope
- In:
  - `tests/test_data_integrity.py` with the 4 PROJECT_PLAN checks, adjusted to the real data
    (above).
  - a new pytest marker `data` in `pyproject.toml`, left out of the default run and of CI.
  - docs: DEVLOG step, LEARNING_GUIDE (markers / data tests, if not already covered),
    PROJECT_PLAN ticks, roadmap tick + "Current position" (Phase 2 done, apart from the optional
    OSHA/NYC item).
- Out:
  - new code in `src/` (the tests use `checksums.verify`, `ufgs_pdf_stats`, `load_ghent` as they
    are). If a small helper turns out to be needed, it goes in `src/` with a unit test.
  - running data tests in CI (no data there; uploading 15 GB is not an option).
  - checks on the P&ID drawings' content (graph/label pairs etc.): later, with Module C.
  - OSHA / NYC (optional roadmap item, not downloaded).

## Requirements
1. Tests are marked `data` and do **not** run in `uv run pytest` or in CI. They run with
   `uv run pytest -m data`.
2. When run with `-m data` and a dataset folder is missing or empty, the test **fails** (it does
   not skip): a missing folder is exactly what the test is for.
3. **Folders:** `data/raw/ufgs`, `project_controls/ghent`, `pid/pid2graph`, `pid/dataset_pid`
   exist and each holds the file count recorded in `checksums.json` `datasets`.
4. **Checksums:** `checksums.verify(...)` reports 0 missing and 0 changed files, for each of the
   4 datasets (one test per dataset, so a failure names the dataset). Depth: see open question 1.
5. **UFGS PDFs:** all 271 open with PyMuPDF; each has ≥ 1 page, and no page is without text
   (today: 0 empty pages). A failing test lists the bad files.
6. **Ghent:** `load_ghent()` loads without error, and:
   - 231 projects, groups A 117 / B 41 / C 73;
   - every project has ≥ 1 activity;
   - every group A project has ≥ 1 tracking period;
   - `bac` > 0 wherever it is present, and present for every group A project.
   The data is loaded once per test module (module-scoped fixture), not once per test.
7. Expected numbers come from `checksums.json` where it has them (file counts); the Ghent
   numbers are written in the test as constants with a comment pointing to `DATA_CATALOG.md`.
   Depth: see open question 2.
8. The whole `-m data` run takes **under 3 minutes** in the container (estimate today: ~74 s
   PDFs + ~23 s Ghent + checksum time).

## Inputs / outputs
- Input: `data/raw/**`, `data/checksums.json`.
- Output: `tests/test_data_integrity.py`; `pyproject.toml` (marker + addopts); docs.

## Acceptance criteria
- [ ] `uv run pytest -m data` → all data tests pass on the real data; run time recorded.
- [ ] `uv run pytest` (default) → the data tests are deselected; the count of passed tests is
      unchanged from `main` apart from deselections; coverage still ≥ 70 %.
- [ ] Fault check 1: with `checksums.json` copied to a temporary file and one size changed (test
      run pointed at the copy, the real file untouched), the checksum test fails and names the file.
- [ ] Fault check 2: with the expected Ghent project count changed by 1 in a local edit, the
      Ghent test fails; the edit is undone.
- [ ] Fault check 3: with `-m data` and a data root that does not exist (temporary path), the
      folder test fails (does not skip).
- [ ] CI on the pull request is green (it never sees the data tests).
- [ ] `ruff check .` and `ruff format --check .` clean.

The fault checks show the tests can fail. They run once by hand and are recorded in `tasks.md`.
They are not committed as tests.

## Technical approach
- pytest only (tech stack ✅); PyMuPDF and pandas are already there through the reused
  functions. **No new tools.**
- `pytestmark = pytest.mark.data` at the top of the file; `addopts = "-m 'not network and not
  data'"`; marker description "data: tests that check the real files in data/raw/ (local only)".
  The CI command already selects with `-m`, which replaces `addopts`' `-m`; CI's expression gets
  `and not data` added so it can't pick them up by accident.
- The data root can be overridden with an environment variable `EPC_RAW_DIR` (default
  `config.RAW_DIR`), so fault check 3 can point at an empty path without touching the real data.
  The checksum file the same way (`EPC_CHECKSUMS`) for fault check 1.
- `pytest.mark.parametrize` over the 4 dataset names for the folder and checksum tests.
- Risks: the PDF and checksum tests are heavy on disk; DEVLOG step 19 records the PC running out
  of memory when heavy jobs ran in parallel. Rule: run `-m data` alone, not next to another
  heavy job.

## Open questions (owner decides)
1. **Checksum depth in the tests.**
   - a) sizes only (`quick=True`, seconds); the full SHA-256 stays the existing command
     `python -m src.datasets.checksums --verify` (3 min 17 s), run after a re-download.
     **Recommended:** keeps `-m data` fast enough to run often, and a changed file almost always
     changes its size... but not always.
   - b) full SHA-256 in the test (`-m data` becomes ~5 min).
2. **Exact numbers or rules only?**
   - a) exact numbers (231 / 117 / 41 / 73, 271 PDFs, file counts) **recommended**: a silent
     change in the data (a new DSLIB release, a re-download) fails a test, and the docs quoting
     these numbers must then be updated too.
   - b) rules only (> 0 projects, BAC > 0, ...): survives a data update, but misses one.
3. **Ghent BAC rule.** Require BAC for group A only, and allow the 31 known missing in group C
   (**recommended**, it's the real data), or also pin "exactly 31 missing, all group C"?
