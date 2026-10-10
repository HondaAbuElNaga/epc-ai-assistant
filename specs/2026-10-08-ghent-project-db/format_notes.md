# Format notes: Ghent DSLIB v3.4

Everything here was verified by opening or listing the files. Nothing is guessed.

## In simple words

- We have **231 real projects** (buildings, bridges, software, events, …).
- Each project has an **Excel file** with:
  - **the plan**: the list of activities with duration and cost (sheet `Baseline Schedule`);
  - sometimes **progress checks**: every few weeks someone measured the project
    (sheet `Tracking Overview`).
- A progress check has three numbers:
  - **PV** (Planned Value): the work we *planned* to finish by that date;
  - **EV** (Earned Value): the work we *really* finished;
  - **AC** (Actual Cost): the money we *really* spent.
  - EV < PV → the project is late. AC > EV → it is over budget.
- The projects fall into **three groups**:

  | Group | Projects | What it has | Folder |
  |---|---|---|---|
  | A | 117 | plan + progress checks (PV, EV, AC) ✅ | `groups/A_tracking_ready/` |
  | B | 41 | plan + raw notes only, no PV/EV ⚠️ | `groups/B_raw_progress_only/` |
  | C | 73 | plan only ❌ | `groups/C_plan_only/` |

  (Folders under `data/processed/project_controls/ghent/`; the list is in
  [project_groups.csv](project_groups.csv).)
- One big **summary file** (`DSLIB_Analysis_Sheet.xlsx`) has one row per project.
- The data is a bit messy (missing values written as `N/A` or `-`, money written as text,
  durations like `3d 2h`), so the loader cleans it.

The sections below are the technical details.

## 1. Download (task 2, 2026-10-10)

| Item | Value |
|---|---|
| Release | `DSLIB_v3.4` (published on GitHub 2026-05-26) |
| URL | https://github.com/MarioVanhoucke/DSLIB-Dynamic-Scheduling-Empirical-Project-Library/releases/download/DSLIB_v3.4/DSLIB3.4.zip |
| File | `DSLIB3.4.zip`, 137,394,368 bytes (same as the size GitHub reports) |
| SHA-256 | `19f87632c589f5d49f72b5f071992efc6379df2beb35f1efd3a60ac1381dc277` |
| Downloaded | 2026-10-10T13:56:13Z, inside the `dev` container with `src.common.http.PoliteClient` |
| Stored at | `data/raw/project_controls/ghent/` (git-ignored); details also in `download.json` there |

The zip has 1,400 entries (203.0 MB unpacked) and no unsafe paths (no absolute paths, no `..`).
It also contains a `__MACOSX/` folder of macOS metadata, which was **not** extracted. Only
`DSLIB 3.4/` was extracted: 696 files, 202.8 MB.

## 2. File layout

```
DSLIB 3.4/
├── DSLIB_Analysis_Sheet.xlsx   1,493,726 B   one sheet covering all projects
├── Readme.rtf                      7,275 B
├── .DS_Store                       (macOS metadata, ignored)
├── Excel/          231 × .xlsx   35.9 MB    one workbook per project
├── Project Card/   231 × .pdf   129.4 MB    one summary card per project
└── Protrack/       231 files     36.1 MB    116 × .p2x.zip, 115 × .p2x (ProTrack format)
```

The full list of files with sizes is in [file_list.csv](file_list.csv) (695 rows, `.DS_Store`
excluded).

## 3. Projects and IDs

- **231 projects.** This matches the source's figure (spec Open questions). PROJECT_PLAN's 133
  is out of date.
- Each file name starts with a project ID such as `C2011-01`, usually followed by the project
  name: `C2011-01 Nursing Home Noordhinder.xlsx`.
- The IDs are **not written consistently** across the folders. Project Card names use
  `C2016-9` (no zero padding), `C2016-31Apartment…` (no space), `C2019-11_procard.pdf` and
  `C2015-03.pdf`. One ProTrack file is `C2025-01.p2x` with no name.
- With the regex `^C(\d{4})-(\d+)` and the number zero-padded to 2 digits (`C2016-09`), all three
  folders give the **same 231 unique IDs**. The loader must use this normalized ID.
- Projects per ID year: 2011: 14, 2012: 17, 2013: 17, 2014: 8, 2015: 35, 2016: 43, 2017: 6,
  2018: 13, 2019: 28, 2020: 1, 2022: 2, 2023: 14, 2024: 5, 2025: 28.

## 4. `DSLIB_Analysis_Sheet.xlsx` (task 3, 2026-10-10)

Read with `openpyxl` (added to tech-stack for this). It has four sheets:

| Sheet | Size | Content |
|---|---|---|
| `Overview` | 110 × 13 | Data dictionary: the meaning of every DSLIB column, plus references |
| `DSLIB` | 286 × 88 | **One row per project**: the summary table |
| `Updates` | 198 × 7 | What changed in v3.4: 52 projects (34 progress-related, 15 resource-related, 1 precedence-related, 2 untyped) |
| `Known Problems` | 232 × 3 | One entry: `2011-06`, "Project cannot be rescheduled" |

`Overview` row 6 still says "203 projects", but the `DSLIB` sheet has 231 rows, which matches
the 231 files.

### 4.1 `DSLIB` sheet layout

- **Three header rows:** row 1 = group (`General`, `Tracking`, …), row 2 = metric (`CI`, `CPI`,
  …, only for columns Z onward), row 3 = column name (`Code`, `BAC`, `avg`, …). Column names
  repeat (`avg` appears 21 times), so a column's full name = group / metric / name.
- **Project rows: 4–234** (231 rows; all codes unique).
- **Rows 237–251: summary statistics** (sector counts, averages), which are *not* projects.

| Col | Group / name | Values found (231 projects) | Meaning (from `Overview`) |
|---|---|---|---|
| A | Code | 231 unique, e.g. `C2011-01` | Project ID; starts with the year of data collection |
| B | Project name | 216 distinct (some names repeat, e.g. `Apartment Building (1)`) | |
| C | Submitted by | 57 distinct | Who collected the data |
| D | Sector | e.g. `Construction (residential building)` (54) | Inconsistent case: `Construction (Civil)` 34 / `(civil)` 26; `Irregular`/`irregular` also in Y |
| E | Keywords | 223 filled, 8 empty | |
| F–H | Completeness: Baseline Schedule / Risk Analysis / Project Control | Mostly **empty cells; the information is the cell colour** (fill `FF00FF00` green, `FFFFFF00` yellow, `FFFF8000` orange, 5 cells `FFFF8001`). A few cells also hold `G`/`O`. | Colour code of Batselier & Vanhoucke (2015). The meaning of each colour is not written in the file. |
| I–J | Authenticity: Project / Tracking | Letters `G`/`Y`/`O`, colours, `N/A` (52 in J); 1 cell in I holds a leftover Dutch formula text `ANTAL.ALS(…)`; 2 cells in J hold `JA` | `N/A` in J = no tracking data |
| K | # activities | int 8–1,796 | |
| L | PD (days) | int 2–2,804 | Planned duration |
| M | BAC | 196 numbers (1,210–4,999,958,016); **30 `-`**, 1 `N/A`, and strings like `€743 676` | Budget at completion, euro |
| N | Resources | `N` 124, `Y` 102, `N/A` 4, one number `6` | Has resource data |
| O–P | Renewable / Consumable | counts, or `-` / `N/A` | Number of resources |
| Q | Resource Conflict in Schedule | `N/A` 124, `Resource Feasible` 74, `Resource Conflict` 33 | |
| R | Early/late | 155 numbers −0.9 to 1.8452; 76 `-` | Real vs planned duration. The values are **fractions** (0.12 = 12 %), though `Overview` calls them percentages. Positive = late |
| S | Under/over budget | 155 numbers −0.578 to 1.44; 76 `-` | Real vs planned cost, also fractions. `Overview` says positive = under budget |
| T–Y | Network topology: SP, AD, LA, TF, RI, Regularity | T–W: all numeric 0–1; X: 148 numbers + `-`/`N/A` | |
| Z–AQ | Time sensitivity: CI, SI, SSI, CRI-r/rho/tau × avg/std. dev./skew | mostly numeric | |
| AR–AZ | Cost sensitivity: CRI-r/rho/tau × avg/std/skew | ~199 numeric, rest `N/A` | |
| BA–BI | Resource sensitivity: same | 95 numeric, rest `N/A` | |
| BJ–CD | Performance metrics: CV, SV, SV(t), CPI, SPI, SPI(t), p-factor × avg/std. dev./final | ~140–148 numeric, ~85 `N/A`; 1 typo `0..05` in CC | Averages over all tracking periods + final value |
| CE–CF | Real Duration / Real Cost | 155 / 153 numeric; `N/A`; cost strings like `€ 464 186,97` | Known after the project ends |

**Missing-value markers used:** `N/A`, `-`, empty cell. **Money as text** sometimes uses the euro
sign, a space as thousands separator and a comma as decimal (`€ 464 186,97`).

## 5. Per-project workbooks (`Excel/*.xlsx`, 231 files)

The files were exported from ProTrack (README: "extracted from ProTrack files"). There are 60
different sheet combinations, but the same sheet types come back:

| Sheet | In how many files | Content |
|---|---|---|
| `Baseline Schedule` (2 files: `Baseline Schedule1`) | 231 | One row per activity |
| `Resources` | 230 | One row per resource |
| `Risk Analysis` | 229 | Duration distribution per activity (optimistic / most probable / pessimistic) |
| `Project Control - TP1`, `TP2`, … `TPn` | 158 have them (up to TP120) | One sheet per **tracking period** (TP), one row per activity |
| `Tracking Overview` | 189 have the sheet; **117 with rows** | One row per tracking period, project level |
| `Agenda` | most | Working hours and working days (calendar) |
| Charts: `Gantt chart`, `AC, EV, PV`, `CPI`, `SPI(t)`, … | many | Chart sheets, no data needed |

Sheet names are not always clean: trailing spaces (`Project Control - TP1 `, `AC, EV, PV `),
`AC,EV,PV`, and some files name the TP sheets just `TP1`, `TP2`, … The loader matches names
after `strip()` and with the pattern `(Project Control - )?TP\d+`.

### 5.1 `Baseline Schedule`

- Row 1 = groups (`General`, `Relations`, `Baseline`, `Resource Demand`, `Baseline Costs`),
  **row 2 = header**, then data.
- **First data row is ID 0 = the project itself** (name = project name, total duration, total
  cost). Activities follow.
- Header (164 files): `ID, Name, WBS, Predecessors, Successors, Baseline Start, Baseline End,
  Duration, Resource Demand, Resource Cost, Fixed Cost, Cost/Hour, Variable Cost, Total Cost,
  Baseline duration (in calendar days)`. 65 files lack the last column; 2 files (e.g.
  C2025-18) spell `Successors` as `Sussessors`.
- Example (C2011-05):
  `1 | order license | 1.1 | — | FS2 | 2011-05-18 08:00 | 2011-05-20 17:00 | 3d | project leader | 2400 | 0 | 0 | 0 | 2400 | 2.375`
- **Relations** are text: `Predecessors` = `1FS`, `19FS;20FS`; `Successors` = `FS3;FS4;FS6`.
- **Durations are text** with units: `3d` (20,458 cells), `4h` (1,680), `1d 2h` (1,003), plain
  `0`/numbers (1,316), `58 days` (190), plus variants with trailing spaces or `1d4h`; 1,194
  empty. Converting hours to days needs the working hours per day from the `Agenda` sheet.
- **WBS summary rows:** 144 projects have WBS parent rows (e.g. WBS `1.2` with children `1.2.1`,
  …). They are totals, not real activities. In every project that has a project-row total
  (189), the **sum of `Total Cost` over leaf activities = the ID 0 total** (0 mismatches).
- Leaf-activity count = DSLIB `# activities` in 154 of 231 projects; in the other 77 it differs
  by a few (e.g. C2011-10: 34 vs 32). The rule behind the summary count is not documented.
- In total: 25,622 rows below ID 0 (including WBS parents), 7–2,154 per project.
- **ID problems in 21 files** (mostly 2023–2025): IDs stored as text (`'2'`), no ID 0 row
  (C2025-07, C2025-08 start at 1), duplicate IDs (C2023-12).
- Newer files (e.g. C2023-01) have **no Baseline End and no Total Cost**, only `Fixed Cost`, and
  the ID 0 row has only a name. Activity names can be Dutch or Spanish.

### 5.2 `Tracking Overview` (project level, one row per period)

- Row 1 = groups, **row 2 = header**, rows 3+ = periods. The last row is often named
  `Actual Schedule` (the finished project).
- Header (122 files): `Name, Start Tracking Period, Status date, Planned Value (PV), Earned Value
  (EV), Actual Cost (AC), Earned Schedule (ES), Schedule Variance (SV), Schedule Performance
  Index (SPI), Cost Variance (CV), Cost Performance Index (CPI), Schedule Variance (SV(t)),
  Schedule Performance Index (SPI(t)), p-factor`, then 17 forecast columns
  (`EAC(t)-PV (PF=1)` … `EAC (PF=0.8*CPI+0.2*SPI(t))`, durations as dates and costs as euro), then
  chart helper columns. 57 files stop after the forecast columns. The first 14 columns are the
  same in every variant.
- Example (C2011-05, third period): `27/06, 2011 | 2011-06-20 17:00 | 2011-06-27 17:00 |
  PV 143,433.17 | EV 129,405.89 | AC 129,405.89 | ES 2011-06-22 11:00 | SV −14,027.28 | SPI 0.902 |
  CV 0.00008 | CPI 1.0 | SV(t) '-3d 5h' | SPI(t) 0.875 | p-factor 0.922`
- `Name` is free text (`24/05, 2011`, `9/12/2019 17:00`, `Actual Schedule`); `Status date` is a
  real datetime. **SV(t) is text with units** (`'0'`, `'-3d 5h'`, `'-10d'`); ES is a datetime.

### 5.3 `Project Control - TPn` (activity level, one sheet per period)

- Row 1: `TP Status Date` (datetime, cell C1) and `TP Name` (cell F1). Row 3 = groups,
  **row 4 = header**, then the ID 0 row and the activities.
- Header (102 files): baseline columns + `Actual Start, Actual Duration, PAC, PRC, Remaining
  Duration, PAC Dev, PRC Dev, Actual Cost, Remaining Cost, Percentage Completed, Tracking,
  Earned Value (EV), Planned Value (PV)`, + 6 relative columns (56 files lack those 6).
- **Check:** in projects with both sheets, the TP sheet's ID 0 row (PV, EV, AC, status date)
  equals the `Tracking Overview` row in **1,491 of 1,514 periods**. The 23 differences are all
  in C2019-11, whose ID 0 row has no PV/EV.

### 5.4 Which projects have tracking data

| Group | Projects | What is there |
|---|---|---|
| A. `Tracking Overview` with rows | **117** | Project-level PV/EV/AC/ES/SPI/CPI… per period, ready to use |
| B. TP sheets but no `Tracking Overview` | **41** (mostly C2023–C2025) | Raw progress only: per activity `Actual Start`, `Actual Duration`, `Actual Cost`, `Percentage Completed`. **No PV, no EV, no project totals** (ID 0 row is empty). PV/EV would have to be computed. |
| C. No tracking (empty overview, no TP sheets) | **73** | Baseline (and risk/resource) data only |

Group C: C2011-01…04, -06, -08, -09, -11, -14; C2012-01…12, -14, -16;
C2016-35…41, -43; C2017-01…05; C2018-01…07, -09, -11, -12; C2019-10, -12…28; C2020-01;
C2022-01, -02; C2023-02, -03, -10, -14; C2024-03, C2024-05. (Full list produced by the loader
check in task 8.)

DSLIB summary columns R/S and CE (Real duration) are numeric for 155 projects, close to but not
equal to 117 + 41 = 158. Not reconciled yet.

## 6. Consequences for the loader

1. Project ID: from the file name with `^C(\d{4})-(\d+)`, zero-padded (§3).
2. `projects` comes from the `DSLIB` sheet (rows 4–234 only), with `N/A`, `-` and empty → missing,
   euro strings → numbers, sector case unified. The completeness colours are kept as labels
   (`green`/`yellow`/`orange`) without guessing their meaning.
3. `activities` comes from `Baseline Schedule`: drop the ID 0 row, flag (not drop) WBS summary
   rows with an `is_summary` column, parse durations into working days + hours, keep the
   relations text.
4. `tracking` comes from `Tracking Overview` (group A). Group B needs a decision (see the spec).
5. The loader must tolerate: trailing spaces in sheet names, missing optional columns, IDs stored
   as text, and both header variants.
