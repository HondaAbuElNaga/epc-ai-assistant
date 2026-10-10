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
   - `issues`: one row per data problem found while loading (added after inspection, so that
     problems are listed, not silently dropped)
   Exact columns: see "Table columns" below (fixed 2026-10-10, after the inspection).
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

## Decisions (2026-10-10, after inspection; see format_notes.md §5.4)
1. **Three project groups**, by the tracking data in each project workbook:
   - **A, tracking ready (117):** `Tracking Overview` has at least one row (PV/EV/AC per period).
   - **B, raw progress only (41):** no `Tracking Overview` rows, but `TPn` sheets with per-activity
     actual cost and % complete. No PV/EV.
   - **C, plan only (73):** no tracking at all.
   The list is in `project_groups.csv` (versioned). The loader adds a `group` column to `projects`.
2. **Option 1 chosen by the owner:** `tracking` is loaded from `Tracking Overview` only (group A).
   Group B projects are listed, not loaded into `tracking`; computing their PV/EV belongs to the
   later EVM roadmap item.
3. **Group folders (owner request):** copies of each project's three files (Excel, Project Card,
   ProTrack) sorted into `data/processed/project_controls/ghent/groups/` →
   `A_tracking_ready/`, `B_raw_progress_only/`, `C_plan_only/`, one subfolder per project
   (git-ignored). The originals in `data/raw/` stay unchanged.
4. Acceptance criterion "every project has at least one tracking period" is expected to list the
   114 projects of groups B and C; they are kept in `projects` and `activities`.

## Table columns (task 4, 2026-10-10; sources in format_notes.md §4–5)

Missing values (`N/A`, `-`, empty, unparseable text) become `NaN`/`NaT`/`None`. Money is in
euro (the `Overview` sheet says BAC is in euro), stored as `float`. Every unparseable value
also adds a row to `issues`.

### `projects` (231 rows, from the `DSLIB` sheet rows 4–234 + the group check)

| Column | Type | Source | Note |
|---|---|---|---|
| `project_id` | str | A `Code` | Normalized `C2011-05` (§3) |
| `name` | str | B `Project name` | |
| `sector` | str | D `Sector` | Case unified (`Construction (civil)`) |
| `keywords` | str | E `Keywords` | |
| `submitted_by` | str | C `Submitted by` | |
| `group` | str | workbook check | `A` / `B` / `C` (spec Decisions) |
| `completeness_baseline` | str | F fill colour | `green` / `yellow` / `orange` / None; meaning not documented in the file |
| `completeness_risk` | str | G fill colour | same |
| `completeness_control` | str | H fill colour | same (`FFFF8001` counted as orange) |
| `n_activities` | int | K `# activities` | As reported by the source |
| `planned_duration_days` | float | L `PD (days)` | |
| `bac` | float | M `BAC` | Euro strings like `€743 676` parsed; `-` → NaN |
| `has_resources` | bool | N `Resources` | `Y`/`N`; other → None |
| `real_duration` | float | CE `Real Duration` | Unit not stated in `Overview`; checked in task 8 |
| `real_cost` | float | CF `Real Cost` | Euro strings parsed |
| `duration_deviation` | float | R `Early/late` | Fraction (0.12 = 12 % late) |
| `cost_deviation` | float | S `Under/over budget` | Fraction; sign as in source (positive = under budget per `Overview`) |
| `sp`, `ad`, `la`, `tf`, `ri` | float | T–X | Network topology indicators |
| `regularity` | str | Y | Lower-case `regular` / `irregular` |
| `excel_file` | str | file name | Per-project workbook name |

Not loaded now (available later if needed): authenticity (I–J), resource counts (O–Q),
sensitivity metrics (Z–BI), averaged performance metrics (BJ–CD; these can be recomputed from
`tracking`).

### `activities` (one row per row of `Baseline Schedule` below ID 0, all 231 projects)

| Column | Type | Source column | Note |
|---|---|---|---|
| `project_id` | str | file name | |
| `activity_id` | int | `ID` | Text IDs (`'2'`) converted |
| `name` | str | `Name` | |
| `wbs` | str | `WBS` | May be empty (12 projects have no WBS) |
| `is_summary` | bool | computed | True when another row's WBS starts with this WBS + `.` |
| `predecessors` | str | `Predecessors` | Raw text, e.g. `19FS;20FS` |
| `successors` | str | `Successors` (or `Sussessors`) | Raw text, e.g. `FS3;FS4` |
| `baseline_start` | datetime | `Baseline Start` | |
| `baseline_end` | datetime | `Baseline End` | Missing in newer files |
| `duration_raw` | str | `Duration` | As written: `3d`, `1d 2h`, `58 days` |
| `duration_days` | float | parsed | The days part (`1d 2h` → 1) |
| `duration_hours` | float | parsed | The hours part (`1d 2h` → 2). Not converted to days: that needs the `Agenda` calendar |
| `resource_demand` | str | `Resource Demand` | Raw text |
| `resource_cost` | float | `Resource Cost` | |
| `fixed_cost` | float | `Fixed Cost` | |
| `variable_cost` | float | `Variable Cost` | |
| `total_cost` | float | `Total Cost` | Missing in newer files |
| `calendar_days` | float | `Baseline duration (in calendar days)` | Only in 164 projects |

Required columns (missing → clear error, Requirement 5): `ID`, `Name`, `Baseline Start`,
`Duration`. All others are optional (NaN when the column is absent).

### `tracking` (group A only: one row per row of `Tracking Overview`)

| Column | Type | Source column | Note |
|---|---|---|---|
| `project_id` | str | file name | |
| `period` | int | row order | 1, 2, 3, … |
| `period_name` | str | `Name` | Free text, e.g. `24/05, 2011` |
| `is_final` | bool | `Name` | True when the name is `Actual Schedule` |
| `period_start` | datetime | `Start Tracking Period` | |
| `status_date` | datetime | `Status date` | |
| `pv`, `ev`, `ac` | float | `Planned Value (PV)`, `Earned Value (EV)`, `Actual Cost (AC)` | Euro |
| `es` | datetime | `Earned Schedule (ES)` | A date in the source |
| `sv`, `spi`, `cv`, `cpi` | float | `Schedule Variance (SV)`, `… (SPI)`, `Cost Variance (CV)`, `… (CPI)` | |
| `sv_t_raw` | str | `Schedule Variance (SV(t))` | Text like `-3d 5h` |
| `spi_t` | float | `Schedule Performance Index (SPI(t))` | |
| `p_factor` | float | first `p-factor` | |

Required: the first 14 columns of the header (format_notes §5.2). Forecast columns (EAC…) are
not loaded; forecasting is a later roadmap item.

### `issues`

| Column | Type | Note |
|---|---|---|
| `project_id` | str | |
| `table` | str | `projects` / `activities` / `tracking` |
| `problem` | str | e.g. `duplicate activity_id 12`, `BAC not a number: '-'`, `no ID 0 row` |
