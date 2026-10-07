# Spec: UFGS download script

**Roadmap item:** Phase 2, "UFGS download script (divisions 01, 03, 05, 22, 23, 26, 33)"
**Status:** approved (2026-10-07)
**Related:** PROJECT_PLAN Stage 2 · used by Module A (spec RAG) and Module B (classification)

## Goal

Download the current UFGS (Unified Facilities Guide Specifications) PDFs for seven divisions
into `data/raw/ufgs/`, politely and repeatably, with a manifest that records exactly what was
downloaded, from where, when, and what was missing. These real specifications are the corpus for
Module A and the labeled data for Module B.

## Source facts (verified 2026-10-07)

- `https://www.wbdg.org/dod/ufgs` is a JavaScript app: the HTML has no section or PDF links.
- `https://www.wbdg.org/robots.txt`: `Allow: /`, `Disallow: /auth/`, no `Crawl-delay`, and a
  sitemap at `/api/sitemap.xml`.
- `https://www.wbdg.org/api/sitemap/documents.xml` lists 1,440 current section pages, each with a
  URL like `/dod/ufgs/ufgs-03-30-00`. It also lists archive and division pages, which we ignore.
- Sections in our divisions: 01 → 83, 03 → 63, 05 → 39, 22 → 42, 23 → 150, 26 → 102,
  33 → 120, **599 total**. These counts are from today's sitemap and may change.
- PDF URL pattern: `https://www.wbdg.org/FFC/DOD/UFGS/<name>.pdf`, which redirects to WBDG's S3
  bucket. File names tested:

  | Sitemap slug | PDF name | Result |
  |---|---|---|
  | `ufgs-03-30-00` | `UFGS 03 30 00` | 200, PDF |
  | `ufgs-01-33-00` | `UFGS 01 33 00` | 200, PDF |
  | `ufgs-32-13-15-20` | `UFGS 32 13 15.20` | 200, PDF |
  | `ufgs-01-45-00-15-10` | `UFGS 01 45 00.15 10` | 200, PDF |
  | `ufgs-01-11-00-00-40` | `UFGS 01 11 00.00 40` | **403** |
  | `ufgs-33-32-13-13` | `UFGS 33 32 13.13` | **403** |

  So the rule `AA-BB-CC[-DD[-EE]]` → `UFGS AA BB CC[.DD[ EE]]` works for many sections but not
  all. The exact link is only available through the site's internal API, which isn't
  documented. **We don't guess further:** misses are recorded as `not_found`, and the real miss
  rate is measured on the first full run.
- Not yet verified: the license/distribution statement and the master update date. Both get
  checked on the downloaded PDFs and recorded in `DATA_CATALOG.md` (a separate roadmap item).

## Scope

**In**
- Section list from the sitemap, filtered to the requested divisions.
- Download with polite behaviour, retries, validation and resume (skip files already present).
- `manifest.json` with one entry per section, plus a summary printed at the end.
- CLI: `python -m src.datasets.ufgs --divisions 01 03 05 22 23 26 33 [--limit N] [--dry-run] [--force]`.
- Stage 2 guide `docs/stages/stage_02_data.md` (CLAUDE.md: each stage gets a guide when it starts).

**Out (other roadmap items)**
- Ghent, PID2Graph, OSHA and NYC downloads.
- `DATA_CATALOG.md`, `data/checksums.json`, profiling notebook, `tests/test_data_integrity.py`
  (opening every PDF needs PyMuPDF, which arrives in Stage 3).
- Reverse-engineering WBDG's internal API to recover `not_found` sections. If the miss rate turns
  out to be high, we decide on that in a follow-up spec.
- Archived sections and other divisions.

## Requirements

1. **Section list:** read `documents.xml`, keep URLs matching `/dod/ufgs/ufgs-DD(-DD)+`, and keep
   only the requested divisions (the first number group). Order is stable (sorted by section ID).
2. **Name mapping:** convert the slug to the PDF name with the rule above, and URL-encode the
   spaces.
3. **Polite HTTP:**
   - one shared `requests.Session`;
   - a User-Agent naming the project and its GitHub URL;
   - at least 1 s between requests (configurable);
   - a 60 s timeout;
   - up to 3 retries with exponential backoff on 429, 5xx and connection errors;
   - no retries on 403/404.
4. **Validation:** a file counts as downloaded only if the response is 200 and the body starts
   with `%PDF`. It's written to `<file>.part` and then renamed, so a crash never leaves a broken
   PDF behind.
5. **Resume:** if the target file exists and starts with `%PDF`, skip it (status `skipped`).
   `--force` downloads it again.
6. **Storage:** `data/raw/ufgs/<division>/UFGS_<section>.pdf`, for example
   `data/raw/ufgs/03/UFGS_03_30_00.pdf` (no spaces in local file names). `data/raw/` is
   git-ignored, so PDFs are never committed.
7. **Manifest:** `data/raw/ufgs/manifest.json` has one entry per section with:
   - `section_id`, `division`, `page_url`, `pdf_url`, `local_path`;
   - `status`: `downloaded` | `skipped` | `not_found` | `error`;
   - `http_status`, `bytes`, `sha256`, `downloaded_at` (UTC ISO);
   - `error` (message, if any).

   It also stores run metadata: start and end time, divisions, and counts per status. It's
   rewritten after every section, so an interrupted run keeps its progress.
8. **Summary:** at the end, print the counts per status and per division, plus the `not_found`
   section IDs.
9. **`--dry-run`** lists the sections and URLs without downloading anything. **`--limit N`**
   handles only the first N sections (for quick checks).
10. Logging goes through `logging`, with a `tqdm` progress bar.

## Inputs / outputs

- Input: WBDG sitemap and PDFs (public, HTTPS). No API keys, no LLM.
- Output files:
  - `src/datasets/__init__.py`, `src/datasets/ufgs.py` (logic + CLI via `python -m`)
  - `src/common/http.py` (polite session: User-Agent, delay, retries; reused by later
    downloaders)
  - `tests/test_ufgs_download.py`, plus small sitemap and PDF fixtures in `tests/fixtures/`
  - `docs/stages/stage_02_data.md`
  - Data (local only): `data/raw/ufgs/<DD>/*.pdf`, `data/raw/ufgs/manifest.json`

## Acceptance criteria

- [ ] Unit tests with **no network**, using a fake session:
  - sitemap parsing and division filtering;
  - slug → name for the 4 verified patterns;
  - a 403 is recorded as `not_found` without retrying;
  - a 503 is retried, then succeeds;
  - a non-PDF body is rejected and no file is left behind;
  - existing files are skipped, and `--force` re-downloads them;
  - the manifest contains every section;
  - the delay is applied between requests.
- [ ] Network test (marker `network`, not run by default): downloads `UFGS 01 33 00`, which was
      verified above, and checks the `%PDF` header and SHA-256 in the manifest.
- [ ] Real run for the 7 divisions finishes. Every section in today's sitemap for those divisions
      appears in the manifest as `downloaded` or `not_found`, with **0 `error`** after a re-run.
- [ ] Re-running immediately downloads nothing (every file is `skipped`).
- [ ] The real counts (downloaded / not_found per division, total size) are reported exactly in
      the DEVLOG.
- [ ] `ruff check`, `ruff format` and `pytest` all clean in the container.
- [ ] Docs: DEVLOG step, LEARNING_GUIDE (sitemaps, polite scraping, retries/backoff, atomic
      writes, SHA-256), Stage 2 guide, roadmap tick, PROJECT_PLAN updated (the script is now
      `src/datasets/ufgs.py`, not `scripts/download_ufgs.py`).

## Technical approach

- Libraries: `requests`, `tqdm` (in the tech stack, already installed), and the standard library
  (`xml.etree`, `hashlib`, `json`, `argparse`). **No new dependencies.**
- Why `src/datasets/` instead of `scripts/`: the code is importable by tests (the pytest
  `pythonpath` is `.`), and it follows the project's `python -m src.<module>` CLI style.
- Testability: the downloader takes a `session` and a `sleep` function as parameters. Tests pass
  fakes, so there are no new mocking libraries.
- Estimated run time: 599 sections × at least 1 s ≈ 10+ minutes. Total size is unknown until the
  first run (the 2 PDFs sampled were 1.49 MB and 0.10 MB).

## Risks

| Risk | Mitigation |
|---|---|
| Name rule misses some sections (403) | Recorded as `not_found` and measured; follow-up spec only if the miss rate matters |
| WBDG changes the site, sitemap or S3 layout | Sitemap and URL pattern live in one place; the network test catches breakage |
| Rate limiting or blocking | 1 s delay, backoff on 429, honest User-Agent, resume on re-run |
| Sitemap counts change over time | Manifest records what was actually downloaded and when |
