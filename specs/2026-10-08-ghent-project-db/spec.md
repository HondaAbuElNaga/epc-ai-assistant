# Spec: Ghent project database (download, inspect, loader)

**Roadmap item:** Phase 2, "Ghent project database: download, inspect format, loader"
**Status:** draft
**Branch:** `spec/2026-10-08-ghent-project-db`
**Related:** PROJECT_PLAN Stage 2 (download) and Stage 5 (Module D, project controls)

## Goal
Get the Ghent OR&S real project database onto disk and load it into clean pandas tables, so
Module D (EVM, overrun forecasting, monthly reports) can run on real projects instead of
invented numbers.

## Scope
- In:
  - Download the database from https://www.projectmanagement.ugent.be/research/data
    (manually if the site needs a form) into `data/raw/project_controls/ghent/`.
  - **Inspect the file format first** and write down what is really there (files, sheets,
    columns, units, number of projects) before writing the loader.
  - A loader that reads the raw files into three tables: `projects`, `activities`, `tracking`.
  - Record source, download date, license/citation and file list for `DATA_CATALOG.md`.
- Out:
  - pandera schemas (Phase 4, "Ghent data loader + pandera schema").
  - EVM calculations, forecasting, profiling notebook (later roadmap items).
  - NYC / OSHA data.

## Requirements
1. Raw files are stored unchanged in `data/raw/project_controls/ghent/` and are not committed
   to git (same as UFGS).
2. A format note, `specs/2026-10-08-ghent-project-db/format_notes.md` (versioned in git), lists
   every file, sheet and column actually found, with examples. Nothing in it is guessed.
3. `src/datasets/ghent.py` exposes `load_ghent(path) -> GhentData` with three DataFrames:
   - `projects`: one row per project (id, name, BAC, planned duration, …, as available)
   - `activities`: one row per activity (project id, activity id, duration, cost, …)
   - `tracking`: one row per project per tracking period (project id, period, PV, EV, AC, …)
   Exact columns are fixed **after** the inspection and written back into this spec.
4. Column names are `snake_case`; dates are parsed; money and durations are numeric.
5. The loader fails with a clear error naming the file and column when an expected column is
   missing.
6. If the site needs a form or login, the download step is manual and documented step by step;
   no scraping around the form.

## Inputs / outputs
- Input: the downloaded Ghent files (format unknown until inspected).
- Output:
  - `data/raw/project_controls/ghent/` (raw files, git-ignored)
  - `specs/2026-10-08-ghent-project-db/format_notes.md`
  - `src/datasets/ghent.py`
  - `tests/test_ghent_loader.py` + a tiny fixture in `tests/fixtures/` built from the real
    format (a few rows, no full dataset in git)

## Acceptance criteria
- [ ] Raw files are on disk; file list, sizes and download date are recorded.
- [ ] `format_notes.md` describes every file and column found, verified by opening them.
- [ ] `load_ghent()` returns `projects`, `activities`, `tracking` for the real data.
- [ ] Project count from the loader matches the count stated by the source (PROJECT_PLAN says
      133; to be verified, and corrected here if different).
- [ ] Every project has a baseline and at least one tracking period, and BAC > 0
      (projects that fail are listed, not silently dropped).
- [ ] Unit tests on the fixture pass; a test for the missing-column error passes.
- [ ] `ruff check`, `ruff format`, `pytest` are clean.

## Technical approach
- Libraries: `pandas` (in tech-stack). If the files are `.xlsx`, `openpyxl` is needed as the
  pandas Excel engine; it is **not** in `product/tech-stack.md` yet, so it gets added there
  first (and with `uv add`) only if the inspection shows Excel files.
- Order: download → inspect → write `format_notes.md` → update the column lists in this spec →
  tests on a small fixture → loader → run on the real data.
- Risks:
  - The format may be complex (PROJECT_PLAN risk table): start with the project summary data,
    then the detailed tracking data.
  - The download may need a form: then it is a manual step.
  - License: free for research, cite the authors (tech-stack). The exact citation is copied
    from the source site, not written from memory.

## Open questions (answer before approval)
1. Does the download page need a form or account? (check the site)
2. Which of the Ghent datasets do we take? The site may offer several; we want the one with
   real projects and tracking periods.
