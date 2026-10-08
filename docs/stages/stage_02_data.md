# Stage 2 Guide: Real Data

**Goal:** download every real dataset the project needs, record exactly where each one came from,
and check that the files are complete and usable **before** any module is built on them.

**Duration:** about 1 week (3–4 hours a day). Roadmap: Phase 2.

**Rule for this stage:** never write facts about a dataset (counts, formats, licenses) from
memory. Download it, inspect it, then write down what you saw.

---

## Datasets and order

| # | Dataset | Source | Goes to | Used by | Status |
|---|---|---|---|---|---|
| 1 | UFGS specifications (PDF), active sections of divisions 01, 03, 05, 22, 23, 26, 33, 40, 41, 42, 43, 44, 46 | https://www.wbdg.org/dod/ufgs | `data/raw/ufgs/` | A, B | done 2026-10-08: 271 PDFs, 37.6 MB ([spec](../../specs/2026-10-07-ufgs-download/spec.md)) |
| 2 | Ghent OR&S real project database (EVM data) | https://www.projectmanagement.ugent.be/research/data | `data/raw/project_controls/ghent/` | D | not started; may need a form, inspect the format first |
| 3 | PID2Graph (real P&IDs with annotations) | https://zenodo.org/records/14803338 | `data/raw/pid/pid2graph/` | C | not started |
| 4 | Dataset-P&ID (synthetic P&IDs) | link in arXiv paper 2109.03794 | `data/raw/pid/dataset_pid/` | C | not started |
| 5 | OSHA Severe Injury Reports, NYC capital projects (optional) | osha.gov, NYC Open Data | `data/raw/osha/`, `data/raw/project_controls/nyc/` | B, D (extra) | optional |

UFGS comes first: it feeds Module A, the first core module (Phase 3).

---

## UFGS: what we know (checked 2026-10-08)

- The WBDG UFGS page is a JavaScript app. The section list comes from the site's sitemap
  (`/api/sitemap/documents.xml`), which lists **current and retired** sections: 705 in our 13
  divisions.
- For each section, the downloader asks WBDG's API (`/api/documents/ufgs-<id>`, undocumented)
  for its status (`ACTIVE` or `RETIRED_SUPERSEDED`) and the exact link of its current PDF. Only
  ACTIVE sections are downloaded.
- Result on 2026-10-08:
  - **271 active** sections downloaded, **434 retired**, 0 errors, 37.6 MB;
  - division 42 (process heating/cooling) has no active section at all.
  - Full counts are in DEVLOG Step 14.
- `robots.txt` allows crawling; only `/auth/` is disallowed. We still wait 1 s between requests.

Run it (inside the container):
```bash
docker compose exec dev uv run python -m src.datasets.ufgs --dry-run     # list, no download
docker compose exec dev uv run python -m src.datasets.ufgs               # all 13 divisions
docker compose exec dev uv run python -m src.datasets.ufgs --divisions 03 --limit 5
```

---

## Checks for every dataset

1. **Provenance:** source URL, download date, license, version. These go in `data/DATA_CATALOG.md`.
2. **Completeness:** expected file count vs. actual; record what is missing and why.
3. **Integrity:** SHA-256 per file in `data/checksums.json`, so later changes are detected.
4. **Usability:** open a sample (PDF has text; tables load; annotations parse).
5. **Profile:** a notebook `notebooks/00_profile_<dataset>.ipynb` with counts, missing values,
   distributions, sample records.

Raw data is never edited by hand and never committed (`data/raw/**` is git-ignored). Cleaned
versions go to `data/processed/`.

---

## What to learn in this stage

| Topic | LEARNING_GUIDE |
|---|---|
| HTTP status codes, `requests` | 1.8 HTTP & requests |
| Sitemaps, robots.txt, polite downloading, retries with backoff | 1.9 Web data acquisition |
| Atomic writes, resumable downloads, checksums (SHA-256), provenance | 1.10 Data integrity |
| Web page vs API, JSON, undocumented APIs | 1.11 Web page vs API |
| DataFrame validation (`pandera`) | added with the Ghent loader |

---

## Done When

- [x] UFGS downloaded, manifest complete, counts recorded in the DEVLOG
- [ ] Ghent database downloaded, format inspected, loader written
- [ ] PID2Graph + Dataset-P&ID downloaded
- [ ] `data/DATA_CATALOG.md` + `data/checksums.json`
- [ ] Profiling notebook per dataset
- [ ] `tests/test_data_integrity.py` passes
