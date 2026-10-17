# Spec: Profiling notebooks (one per dataset)

**Roadmap item:** Phase 2, "Profiling notebook per dataset"
**Status:** approved (2026-10-17) with the owner's answers below
**Branch:** `spec/2026-10-16-profiling-notebooks`
**Related:** PROJECT_PLAN Stage 2, process step 5: "a profiling notebook per dataset
(`notebooks/00_profile_<dataset>.ipynb`) covering counts, missing values, distributions and sample
records"; `data/DATA_CATALOG.md`

## Goal
Look at each dataset **as data**, not just as files: how much is there, what is missing, how the
values are spread, and what a typical record looks like. The results decide how Modules A–D will
use the data (e.g. chunk sizes for UFGS, which Ghent projects are usable for forecasting, tile
size for P&IDs), and they are a visible part of the portfolio on GitHub.

## What we already know (checked 2026-10-16)

- **Data on disk:** 4 datasets, 6,995 files, 15.49 GB (`data/checksums.json`, verify passed).
- **Notebooks:** the `notebooks/` folder does not exist yet. `ipykernel` is a dev dependency;
  JupyterLab runs with `uv run --with jupyterlab` (tech stack ✅). `jupyter-server` (part of
  JupyterLab) requires `nbconvert>=6.4.4` (PyPI metadata), so notebooks can be **run headless**
  with `jupyter nbconvert --execute`. No new tool for that.
- **Not installed:** `matplotlib`, `pymupdf`, `Pillow`, `networkx` (checked with
  `importlib.util.find_spec` in the container).
  - matplotlib 3.11.2, PSF-style license (PyPI); tech stack: 🔜 Stage 5.
  - PyMuPDF 1.28.2, "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License" (PyPI);
    tech stack: 🔜 Stage 3.
- **Existing code to reuse:** `src/datasets/ghent.py` `load_ghent()` returns `projects`,
  `activities`, `tracking`, `issues` tables. The P&ID format notes already describe how to read
  `.graphml` (`xml.etree`), image sizes (PNG/JPEG headers with `struct`) and `.npy` headers
  (`numpy.lib.format`) without decoding images or running pickle.
- **Memory:** heavy background jobs were stopped twice for low memory today. The PID2Graph images
  are about 7,168 × 4,561 px; decoding hundreds of them is not needed for profiling.
- **Licensing:** the repository has **no LICENSE file**. PID2Graph is CC BY-SA 4.0
  (share-alike); Ghent and Dataset-P&ID state no license. What the notebooks may show is Open
  question 3.

## Scope
- In:
  - `src/datasets/profiling.py`: small, tested functions that compute the profile tables (the
    project rule: "final code never lives in notebooks").
  - Four notebooks, `notebooks/00_profile_ufgs.ipynb`, `00_profile_ghent.ipynb`,
    `00_profile_pid2graph.ipynb`, `00_profile_dataset_pid.ipynb`. Each one: a short intro, then
    **counts → missing values → distributions → sample records → findings** (a short list of
    facts that matter for later modules, each one read from the output above it).
  - Notebooks are committed **with their outputs**, so GitHub shows the results.
  - `tests/test_profiling.py` on small fake data (CI has no real data).
- Out:
  - Cleaning or changing data (`data/raw` stays read-only; nothing is written to `data/processed`).
  - Loading the 4 pickled Dataset-P&ID array types (still a Phase 7 decision).
  - `tests/test_data_integrity.py` (next roadmap item).
  - OSHA / NYC (not downloaded).
  - Running notebooks in CI.

## What each notebook profiles

| Notebook | Counts | Missing values | Distributions | Sample records |
|---|---|---|---|---|
| UFGS | PDFs per division; pages; characters of text | PDFs/pages with **no text layer** (would need OCR); sections in the manifest that are not on disk | pages per PDF, text per page, publish year, file size | title + first lines of 2–3 sections |
| Ghent | projects per group (A/B/C) and sector; activities; tracking periods | missing cells per column of each table; loader `issues` by kind | activities per project, project duration, budget (BAC), periods per project, final CPI/SPI | one project's header row, a few activities, its tracking periods |
| PID2Graph | drawings per subset (real 12 vs synthetic 750); nodes, edges | drawings without nodes/edges; nodes without box or label | image sizes, nodes/edges per drawing, label counts, **box sizes in px** (real vs synthetic) | one drawing's node and edge list (no image, see Open question 3) |
| Dataset-P&ID | drawings, images, masks, `.npy` files | missing files per folder (manifest: 0) | image sizes; rows per drawing for all 7 array types **from the `.npy` headers** (shape only, no pickle); title-block fields; table rows | `KeyValue` and `Table` of one drawing (made-up text) |

## Requirements
1. Every number in a notebook is **computed by code in that notebook run**, never typed in. The
   "findings" cell only repeats numbers shown above it.
2. Notebooks run top to bottom without errors with
   `docker compose exec dev uv run --with jupyterlab jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb`.
3. **Memory-light:** no notebook decodes full drawing images or loads all PDFs at once. Image
   sizes come from file headers; PDFs are opened one at a time and closed; `.npy` shapes come from
   headers. Peak memory of one run stays below 2 GB (measured with `/usr/bin/time -v` or
   `docker stats`, reported in `tasks.md`).
4. **No pickle:** `.npy` files are opened with `allow_pickle=False` or by header only.
5. Each notebook starts with the dataset's source, license and citation (copied from
   `DATA_CATALOG.md`) and ends with the findings.
6. Notebooks are small enough for GitHub to show: each `.ipynb` under 1 MB (charts as PNG at
   modest size, long tables cut to the first rows).
7. `profiling.py` functions take a folder path, so tests can use a temporary fake dataset.
8. `ruff check` passes on the notebooks too (ruff checks `.ipynb` files).

## Inputs / outputs
- Input: `data/raw/**` (read only), the manifests, `load_ghent()`.
- Output (committed): `src/datasets/profiling.py`, `tests/test_profiling.py`, `notebooks/*.ipynb`
  (4), `pyproject.toml` + `uv.lock` (if new libraries are approved), `product/tech-stack.md`.

## Acceptance criteria
- [ ] 4 notebooks exist and each runs headless with exit code 0 (command of Requirement 2).
- [ ] Each notebook has the 5 parts: counts, missing values, distributions, sample records,
      findings; and the source/license header.
- [ ] Totals in the notebooks agree with `DATA_CATALOG.md` / `checksums.json` (UFGS 271 PDFs;
      Ghent 231 projects, groups 117/41/73; PID2Graph 512 + 250 drawings; Dataset-P&ID 500
      folders × 7 `.npy`, 500 images, 500 masks). Any difference is explained in the notebook.
- [ ] Peak memory per notebook run < 2 GB (measured, reported in `tasks.md`).
- [ ] Each `.ipynb` < 1 MB.
- [ ] `tests/test_profiling.py` passes offline; `ruff check` (incl. notebooks), `ruff format`,
      `pytest` clean; coverage ≥ 70 %.
- [ ] Tech stack updated for any library brought forward (status, reason, license).

## Technical approach
- **Profile functions** (in `src/datasets/profiling.py`, all returning pandas DataFrames):
  `ufgs_pdf_stats(folder)` (pages, text characters, empty pages per PDF), `image_size(path)`
  (PNG/JPEG header), `graphml_stats(path)` (nodes, edges, labels, box sizes),
  `npy_shape(path)` (header only), `missing_table(df)` (missing count and % per column).
  Ghent reuses `load_ghent()`.
- **Charts:** matplotlib histograms and bar charts (Open question 1).
- **UFGS text:** PyMuPDF `page.get_text()` per page (Open question 2).
- **Runtime:** the UFGS notebook opens 271 PDFs (37.6 MB) and the PID2Graph notebook parses 762
  `.graphml` files; both should take minutes, not hours. Heavy runs one at a time.
- **Risks:**
  - Bringing libraries forward early. Mitigation: both are already planned in the tech stack.
  - PyMuPDF is AGPL-3.0 (or a paid commercial license). AGPL puts conditions on sharing the
    source of software that uses it, including software offered over a network. PyMuPDF is
    already on the tech stack for Stage 3, but its license was not written there. This spec
    records it; what it means for the Stage 11 deployment is a question for then, not a legal
    conclusion now.
  - Notebook outputs make noisy git diffs. Mitigation: re-run a notebook only when its data or
    code changes.

## Owner's answers (2026-10-16)
1. Charts: **add matplotlib now**.
2. UFGS: **add PyMuPDF now** (page and text counts, pages without text).
3. Samples: **text only**, with the source named; no drawing images.
4. Notebooks committed **with their results**.

## Open questions (as asked)
1. **Charts:** bring **matplotlib** forward from Stage 5 now (`uv add matplotlib`)?
   **Recommended: yes.** "Distributions" without charts means long tables. The alternative is
   tables only (pandas `describe()`, value counts).
2. **UFGS:** bring **PyMuPDF** forward from Stage 3 now, to count pages and text and to find
   pages without text? **Recommended: yes**, Stage 3 needs it anyway, and "pages with no text"
   tells us early whether OCR is needed. The alternative is profiling only the manifest
   (file size, publish date, division), with no page or text numbers.
3. **What may the committed notebooks show?** Recommended: **text samples only**: a few rows of
   tables, short title/first lines of UFGS sections, Dataset-P&ID's made-up title block, with the
   citation; **no drawing images** in this step (CC BY-SA share-alike, and the repo has no license
   yet). The alternative is also showing a small, cropped P&ID image with attribution.
4. **Notebook outputs in git:** commit with outputs (GitHub shows results, good for the
   portfolio) — **recommended** — or strip outputs (smaller diffs, but readers see only code).
