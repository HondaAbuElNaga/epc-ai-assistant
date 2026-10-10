# Format notes: Ghent DSLIB v3.4

Everything here was verified by opening or listing the files. Nothing is guessed.

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

## 4. Workbook contents

To do (task 3): the sheets, columns, units and example rows of `DSLIB_Analysis_Sheet.xlsx`
and the per-project Excel files.
