# Data catalog

Every dataset this project uses: where it comes from, when it was downloaded, whether we may use
it, what is on disk, and what is wrong with it. The raw files live in `data/raw/` and are **not in
git** (too big, and some licenses don't allow copying). Anyone can download them again with the
commands below.

- **Numbers** (files, bytes) come from `data/checksums.json` (updated 2026-10-16). Download
  dates come from each dataset's own download record (`manifest.json` / `download.json`).
- **Licenses** are quoted from the source. Where the source says nothing, this page says so.
- **Check the data:** `docker compose exec dev uv run python -m src.datasets.checksums --verify`
  (full SHA-256 check, about 3–7 minutes) or add `--quick` (sizes only, seconds). Last full
  check: 2026-10-16, 6,995 ok, 0 missing, 0 changed.

## Summary

| Dataset | Module | Files | Size | License | Downloaded (UTC) |
|---|---|---|---|---|---|
| [UFGS specifications](#ufgs-unified-facilities-guide-specifications) | A, B | 271 | 37.6 MB | None stated (US government work, see below) | 2026-10-07 / 08 |
| [Ghent DSLIB v3.4](#ghent-dslib-v34-real-project-database) | D | 697 | 340.2 MB | None stated; cite the authors | 2026-10-10 |
| [PID2Graph](#pid2graph) | C | 1,525 | 12.79 GB | CC BY-SA 4.0 (OPEN100 part: none stated) | 2026-10-14 |
| [Dataset-P&ID](#dataset-pid-digitize-pid) | C | 4,502 | 2.33 GB | None in the folder; CC BY-SA 4.0 per PID2Graph | 2026-10-14 / 15 |
| [OSHA Severe Injury Reports](#not-downloaded-optional) | B (bonus) | — | — | — | not downloaded (optional) |
| [NYC capital projects](#not-downloaded-optional) | D (extra) | — | — | — | not downloaded (optional) |
| **Total** | | **6,995** | **15.49 GB** | | |

Sizes are decimal (1 GB = 10⁹ bytes). Modules: A = Spec RAG, B = document classification and
extraction, C = P&ID reader, D = project controls.

---

## UFGS (Unified Facilities Guide Specifications)

| | |
|---|---|
| **What** | US military construction specifications (USACE / NAVFAC / AFCEC), one PDF per section |
| **Source** | https://www.wbdg.org/dod/ufgs (section list: https://www.wbdg.org/api/sitemap/documents.xml) |
| **Version** | Current version of each **active** section on the download day. Publish dates in the files: 2006-04-01 to 2026-08-01 |
| **Downloaded** | 2026-10-07 15:46 to 2026-10-08 18:12 UTC; last check run 2026-10-08 (`manifest.json`) |
| **Folder** | `data/raw/ufgs/<division>/UFGS_<section>.pdf` |
| **Files / size** | 271 PDFs, 37,587,638 bytes |
| **Re-download** | `docker compose exec dev uv run python -m src.datasets.ufgs` |
| **Spec** | [`specs/2026-10-07-ufgs-download/`](../specs/2026-10-07-ufgs-download/spec.md) |

**PDFs per division:** 01: 33 · 03: 23 · 05: 17 · 22: 11 · 23: 52 · 26: 45 · 33: 59 · 40: 4 ·
41: 8 · 42: 0 · 43: 2 · 44: 2 · 46: 15.

**License (checked 2026-10-16):** no license, copyright or distribution statement was found.
- The text of all 271 PDFs was searched for "distribution statement", "public release",
  "distribution unlimited", "copyright" and "public domain". The only hits were ordinary
  specification text (e.g. section "1.7.2 Public Release of Information", "water distribution")
  and the copyright notice of an embedded Adobe font.
- The WBDG document API record (e.g. `https://www.wbdg.org/api/documents/ufgs-01-11-00`) has no
  license field. The WBDG web pages load their text with JavaScript, so they could not be read
  automatically.
- Background, not a legal conclusion: page 1 of each PDF names USACE / NAVFAC / AFCEC (US
  government agencies). US law, 17 U.S.C. § 105(a): "Copyright protection under this title is not
  available for any work of the United States Government". A "work of the United States
  Government" is one "prepared by an officer or employee of the United States Government as part
  of that person's official duties" (17 U.S.C. § 101). Whether every section was written that
  way is not stated in the files. 219 of the 271 PDFs mention ASTM standards; the text of those
  standards is **not** included.

**Known issues**
- 434 sections in the 13 chosen divisions are **retired**; they are recorded in the manifest but
  not downloaded. Division 42 has no active section, so it has no PDF.
- The PDF link is found through WBDG's undocumented API; if WBDG changes it, the download script
  reports `not_found` instead of guessing.
- Sections contain editor notes and `[_____]` blanks to fill in; they are templates, not the text
  of one real contract.

---

## Ghent DSLIB v3.4 (real project database)

| | |
|---|---|
| **What** | 231 real projects (construction and other sectors) with baseline schedules, costs and, for many, tracking periods with earned-value data. Collected by the OR&S group, Ghent University |
| **Source** | https://github.com/MarioVanhoucke/DSLIB-Dynamic-Scheduling-Empirical-Project-Library (release `DSLIB_v3.4`, published 2026-05-26). Listed on https://www.projectmanagement.ugent.be/research/data |
| **Downloaded** | 2026-10-10 13:56 UTC (`download.json`) |
| **Folder** | `data/raw/project_controls/ghent/DSLIB3.4.zip` + extracted `DSLIB 3.4/` (`Excel/`, `Project Card/`, `Protrack/`, `DSLIB_Analysis_Sheet.xlsx`, `Readme.rtf`) |
| **Files / size** | 697 files, 340,223,260 bytes (zip: 137,394,368 bytes; extracted: 696 files) |
| **Re-download** | `docker compose exec dev uv run python -m src.datasets.ghent` |
| **Spec** | [`specs/2026-10-08-ghent-project-db/`](../specs/2026-10-08-ghent-project-db/spec.md) (with `format_notes.md`) |

**Groups** (from our loader): A = tracking ready (117 projects) · B = raw progress only (41) ·
C = plan only (73).

**License:** the repository has **no license file** and the pages show no terms of use. The
README asks users to cite:
- Batselier, J. & Vanhoucke, M. (2015). Construction and evaluation framework for a real-life
  project database. *International Journal of Project Management*, 33(3), 697–710.
  https://doi.org/10.1016/j.ijproman.2014.09.004
- For the extended dataset also Vanhoucke (2023) *The illusion of control* and Vanhoucke (2024)
  *A quest for projects with scarce resources*.

Because no license is given, raw files stay out of git and our test fixtures are built by hand.

**Known issues** (details in `format_notes.md` §5)
- **ID problems in 21 workbooks** (mostly 2023–2025): IDs stored as text, no ID 0 row (C2025-07,
  C2025-08), duplicate IDs (C2023-12).
- Newer workbooks (e.g. C2023-01) have no Baseline End and no Total Cost, only Fixed Cost.
- Durations are text with mixed units (`3d`, `4h`, `1d 2h`, `58 days`, ...).
- WBS summary rows are totals, not activities (144 projects).
- Leaf-activity count differs from the DSLIB summary count in 77 of 231 projects.
- Activity names can be Dutch or Spanish.
- The zip contains one macOS `.DS_Store` file (harmless).

---

## PID2Graph

| | |
|---|---|
| **What** | P&ID drawings as images + graphs (symbols = nodes with box and label, lines = edges) |
| **Source** | https://zenodo.org/records/14803338, DOI `10.5281/zenodo.14803338`, published 2025-02-14 (one version) |
| **Downloaded** | 2026-10-14 23:21 UTC (`manifest.json`); MD5 `90f782220de97e7e249d2595c49ddc1c` checked |
| **Folder** | `data/raw/pid/pid2graph/PID2Graph.zip` + extracted `PID2Graph/Complete/` |
| **Files / size** | 1,525 files, 12,786,840,026 bytes (zip: 9,303,633,645 bytes) |
| **Re-download** | `docker compose exec dev uv run python -m src.datasets.pid --only pid2graph` |
| **Spec** | [`specs/2026-10-14-pid-datasets/`](../specs/2026-10-14-pid-datasets/spec.md) (with `format_notes.md`) |

**Extracted (`Complete/`):** Dataset PID 500 `.png` + 500 `.graphml` · **PID2Graph OPEN100 12
`.png` + 12 `.graphml` (the only real drawings)** · PID2Graph Synthetic 250 `.jpg` + 250
`.graphml`.

**License:** the Zenodo record says **CC BY-SA 4.0**. Per part: Dataset PID CC BY-SA 4.0;
synthetic symbols CC BY-SA 4.0; OPEN100 "taken from open-100.com" with **no license given** (the
open-100.com home page shows none either). CC BY-SA means: credit the authors, and anything made
from the data must be shared under the same license.

**Citation (as given by the record):** Stürmer, J. M., Graumann, M., & Koch, T. (2025). *From
Engineering Diagrams to Graphs: Digitizing P&IDs with Transformers*. 2025 IEEE 12th International
Conference on Data Science and Advanced Analytics (DSAA).
https://doi.org/10.1109/DSAA65442.2025.11248012

**Known issues**
- **Only 12 drawings are real** (OPEN100, a nuclear reactor project); 750 are synthetic. Any
  result on real drawings rests on 12 sheets.
- Only 7 symbol classes and 2 line classes (the original Dataset-P&ID has 32 symbol classes).
- Symbols in the real drawings are much smaller (a valve is about 20 px) than in the synthetic
  ones; this matters for tiling.
- `Patched/` (35,799 tiles, about 10 GB) was **not extracted** (owner decision); it is still in
  the zip.

---

## Dataset-P&ID (Digitize-PID)

| | |
|---|---|
| **What** | 500 synthetic P&ID sheets with annotations for 32 symbol types, text, lines and tables |
| **Source** | Google Drive folder `DigitizePID_Dataset`: https://drive.google.com/drive/folders/1gMm_YKBZtXB3qUKUpI-LF1HE_MgzwfeR (linked from the paper, arXiv 2109.03794) |
| **Downloaded** | 2026-10-14 19:44 to 2026-10-15 11:19 UTC (`manifest.json`); 0 missing, 0 extra |
| **Folder** | `data/raw/pid/dataset_pid/<0…499>/` (7 `.npy` each), `image_2.tar.gz`, `mask.tar.gz` + extracted `image_2/`, `mask/` |
| **Files / size** | 4,502 files, 2,328,204,243 bytes (3,500 `.npy` + 2 archives + 500 images + 500 masks) |
| **Re-download** | `docker compose exec dev uv run python -m src.datasets.pid --only dataset-pid` |
| **Spec** | [`specs/2026-10-14-pid-datasets/`](../specs/2026-10-14-pid-datasets/spec.md) (with `format_notes.md`) |

**License:** the Drive folder has **no license file**; the paper only says the data is "made
publicly available". The PID2Graph Zenodo record lists "Dataset PID" (its converted copy) as
CC BY-SA 4.0.

**Citation:** Paliwal, S., Jain, A., Sharma, M., & Vig, L. (2021). Digitize-PID: Automatic
Digitization of Piping and Instrumentation Diagrams. arXiv:2109.03794.
https://doi.org/10.1007/978-3-030-75015-2_17

**Known issues**
- **4 of the 7 `.npy` types** in every folder (2,000 files) are object arrays that need
  **pickle** to load, and pickle can run code. They were only inspected without loading
  (`pickletools`); loading them is a Phase 7 decision.
- All 500 drawings are synthetic.
- PID2Graph's "Dataset PID" folder is a converted copy of this dataset (7 classes, no text or
  tables). It is **not confirmed** that drawing N is the same drawing in both (`format_notes.md`
  §6), so never combine one dataset's boxes with the other's images, and don't put the two
  copies into different train/test splits.

---

## Not downloaded (optional)

| Dataset | Planned use | Source (from PROJECT_PLAN) | Status |
|---|---|---|---|
| OSHA Severe Injury Reports | Module B (bonus) | osha.gov, Severe Injury Reports | not downloaded (optional roadmap item) |
| NYC capital projects | Module D (extra) | NYC Open Data, search "Capital Projects" | not downloaded (optional roadmap item) |

They get a full section here if that roadmap item is done.
