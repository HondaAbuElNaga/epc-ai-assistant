# Spec: Ghent project database (download, inspect, loader)

**Roadmap item:** Phase 2, "Ghent project database: download, inspect format, loader"
**Status:** approved (2026-10-10)
**Branch:** `spec/2026-10-08-ghent-project-db`
**Related:** PROJECT_PLAN Stage 2 (download) and Stage 5 (Module D, project controls)

## Goal
Get the Ghent OR&S real project database onto disk and load it into clean pandas tables, so
Module D (EVM, overrun forecasting, monthly reports) can run on real projects instead of
invented numbers.

## Scope
- In:
  - Download the DSLIB release zip (see Open questions) into `data/raw/project_controls/ghent/`
    and unzip it there.
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
- [ ] Project count from the loader matches the count in the DSLIB analysis sheet (the sources
      say 231; PROJECT_PLAN's 133 gets corrected).
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

## Open questions (answered 2026-10-10, from the source pages)
Sources checked: https://www.projectmanagement.ugent.be/research/data,
https://www.projectmanagement.ugent.be/research/data/realdata, the DSLIB GitHub README, and the
GitHub API for the latest release.

1. **Form or account?** No. Neither UGent page mentions a form, registration or login. The
   data is a public GitHub release asset, so the download is a plain scripted HTTP download
   (Requirement 6 does not apply):
   - Release `DSLIB_v3.4`, published 2026-05-26
   - Asset `DSLIB3.4.zip`, 137,394,368 bytes (about 131 MiB)
   - URL: https://github.com/MarioVanhoucke/DSLIB-Dynamic-Scheduling-Empirical-Project-Library/releases/download/DSLIB_v3.4/DSLIB3.4.zip
   - The README says older releases are removed when a new one comes out, so the URL may change.
     The download step records the version actually fetched.
2. **Which dataset?** **DSLIB** (also called PSLIB, the "Dynamic Scheduling Library"). It is
   the only real-life (empirical) dataset on the page. All the others (RG30, PSPLIB, MMLIB, …)
   are artificial scheduling benchmarks. What the sources say about DSLIB:
   - Content: baseline scheduling, schedule risk analysis and project control (EVM/ES) data.
     The README says a project "may" have all three but not always completely, so tracking
     periods must be checked per project (see acceptance criteria).
   - Files (from the README): an Excel analysis sheet covering all projects, an `Excel` folder
     with one Excel file per project (extracted from ProTrack), a `ProTrack` folder, and a
     `Project Card` folder.
   - Sectors include construction (commercial, residential, civil, industrial, institutional),
     IT, events, engineering, education and mobility.
   - **Project count:** the sources give 231 projects for the current release (the realdata page
     table lists IDs 1–203). PROJECT_PLAN's figure of 133 is out of date. The real count comes
     from the inspection.
   - License: the repository has **no license file** and the pages show no terms of use. The
     README asks users to cite Batselier, J. & Vanhoucke, M. (2015), "Construction and
     evaluation framework for a real-life project database", *International Journal of Project
     Management*, 33(3), 697–710, https://doi.org/10.1016/j.ijproman.2014.09.004. For the
     extended dataset it also asks for Vanhoucke (2023) *The illusion of control* and
     Vanhoucke (2024) *A quest for projects with scarce resources*. Consequence: raw files stay
     out of git (Requirement 1), and the small test fixture is built from the real format with
     **made-up values**, not copied rows.
   - Format consequence: the data is Excel, so `openpyxl` will very likely be needed (task 4
     still confirms this after inspection, and Excel engines are added only then).
