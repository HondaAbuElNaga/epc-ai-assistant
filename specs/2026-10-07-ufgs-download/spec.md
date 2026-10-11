# Spec: UFGS download script

**Roadmap item:** Phase 2, "UFGS download script (divisions 01, 03, 05, 22, 23, 26, 33)"
**Status:** done (2026-10-08). v2 update approved 2026-10-08. v1 was approved 2026-10-07 and built (commit `f0d7d8b`).
**Related:** PROJECT_PLAN Stage 2 · used by Module A (spec RAG) and Module B (classification)

## Goal

Download the current UFGS (Unified Facilities Guide Specifications) PDFs for seven divisions
into `data/raw/ufgs/`, politely and repeatably, with a manifest that records exactly what was
downloaded, from where, when, and what was missing. These real specifications are the corpus for
Module A and the labeled data for Module B.

## v2 update (2026-10-08): why and what changes

**What v1 measured** (full run, 7 divisions, 599 sections): 257 downloaded, 3 skipped,
**339 not_found**, 0 errors, 260 PDFs, 38.1 MB.

**Why so many misses (verified):** the sitemap lists current *and* retired sections. A sample
of 30 `not_found` sections were all `RETIRED_SUPERSEDED` with no files. Some PDFs v1
downloaded are also retired sections: their old PDF is still in the bucket.

**The WBDG API (verified 2026-10-08, undocumented):**
`GET https://www.wbdg.org/api/documents/ufgs-<section_id>` returns
`{success, data: {title, status, publishDate, mediaFiles: [...], ...}}`.

- `status` is `ACTIVE` or `RETIRED_SUPERSEDED`.
- Each `mediaFiles` item has `fileName`, `fileUrl`, `isCurrent`, `isArchived` and
  `versionNumber`.
- Examples:
  - `03-30-00` (ACTIVE) has a current `UFGS 03 30 00.pdf` and `.zip` under
    `/FFC/DOD/UFGS/`, plus older archived versions under `UFGS_ARCHIVES/` and `documents/`.
  - `40-05-13` (ACTIVE) has the same structure.
  - `33-32-13-13` (RETIRED) has `mediaFiles: []`.

**Decisions (approved by the owner 2026-10-08):**
1. **Scope (option B):** the 7 divisions plus the process divisions:
   - 40 Process Interconnections;
   - 41 Material Processing and Handling Equipment;
   - 42 Process Heating, Cooling, and Drying Equipment;
   - 43 Process Gas and Liquid Handling, Purification, and Storage Equipment;
   - 44 Pollution and Waste Control Equipment;
   - 46 Water and Wastewater Equipment.

   That's 106 more sitemap entries (current + retired), **705 in total**. Correction: in chat I
   said "+112". That number also counted division 48 (Electrical Power Generation, 6 entries),
   which isn't in option B.
2. **Active only:** a section is downloaded only if the API says `ACTIVE`.
3. **Delete the retired PDFs** that v1 put on disk.
4. **v1 committed first** as a checkpoint (done: `f0d7d8b`).

**v2 requirements (replacing 2, 5 and 7 below where they differ):**
- V1. For every sitemap section in scope, call the API through the same `PoliteClient`
  (1 s delay, retries).
- V2. **Picking the PDF:**
  - Choose the `mediaFiles` item where `isCurrent` is true, `isArchived` is false and
    `fileName` ends in `.pdf`. Download its exact `fileUrl`; the URL is no longer built from
    the name rule.
  - If there isn't exactly one such item, record `error` with the reason. Never guess.
- V3. **New statuses:**
  - `retired`: the API status isn't `ACTIVE`; nothing is downloaded.
  - `no_pdf`: the section is ACTIVE but has no current PDF.
  - `not_found`: the API returns 404 or `success: false`.

  The full set is `downloaded | skipped | retired | no_pdf | not_found | error`.
- V4. **The manifest** gains `title`, `api_status`, `publish_date` and `api_url`. `pdf_url` is
  now the URL from the API.
- V5. **Resume:** an existing valid PDF is still `skipped`, but only after the API confirms the
  section is ACTIVE. That one API call per section is how retired files are detected.
- V6. **Cleanup:**
  - At the end of a run, if a PDF exists on disk for a section now marked `retired`, delete it
    and log it. The manifest entry gets `"removed": true`.
  - `--keep-retired` turns this off.
  - Deletion only touches files at our own `local_path` for that section, never anything else.
- V7. `DEFAULT_DIVISIONS` becomes the 13 divisions above.
- V8. The name rule (`pdf_name`) stays only for the local file name, and the network test still
  uses it.

**v2 acceptance criteria (added to those below):**
- [x] Offline tests:
  - an ACTIVE section downloads the API's `fileUrl`, not a built URL;
  - a RETIRED section becomes `retired` and makes no PDF request;
  - ACTIVE with no current PDF becomes `no_pdf`;
  - two current PDFs becomes `error`;
  - API 404 becomes `not_found`;
  - a retired file on disk is deleted, and `--keep-retired` keeps it;
  - an existing ACTIVE PDF is `skipped`.
- [x] Real run for 13 divisions: every in-scope sitemap section is in the manifest; 0 `error`
      after a re-run; a second run downloads nothing.
- [x] No PDF on disk belongs to a section whose status isn't ACTIVE.
- [x] Real counts are reported in the DEVLOG exactly as they come out.

**Estimate:** 705 API calls plus about one PDF request per active section at at least 1 s
each, so roughly 15–25 minutes. This is an estimate; the real time goes in the DEVLOG.

**Risk:** the API is undocumented and may change. Mitigations:
- one function parses it;
- the network test calls it for `03-30-00`;
- if `success` or `mediaFiles` is missing, the section becomes `error` rather than a guess.

---

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
- ~~Reverse-engineering WBDG's internal API~~: now in scope (v2 above).
- Archived/retired sections and divisions outside the 13 (02, 07–14, 21, 25, 27, 28, 31, 32, 34, 35, 48, 00).

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

- [x] Unit tests with **no network**, using a fake session:
  - sitemap parsing and division filtering;
  - slug → name for the 4 verified patterns;
  - a 403 is recorded as `not_found` without retrying;
  - a 503 is retried, then succeeds;
  - a non-PDF body is rejected and no file is left behind;
  - existing files are skipped, and `--force` re-downloads them;
  - the manifest contains every section;
  - the delay is applied between requests.
- [x] Network test (marker `network`, not run by default): downloads `UFGS 01 33 00`, which was
      verified above, and checks the `%PDF` header and SHA-256 in the manifest.
- [x] Real run for the 7 divisions finishes. Every section in today's sitemap for those divisions
      appears in the manifest as `downloaded` or `not_found`, with **0 `error`** after a re-run.
- [x] Re-running immediately downloads nothing (every file is `skipped`).
- [x] The real counts (downloaded / not_found per division, total size) are reported exactly in
      the DEVLOG.
- [x] `ruff check`, `ruff format` and `pytest` all clean in the container.
- [x] Docs: DEVLOG step, LEARNING_GUIDE (sitemaps, polite scraping, retries/backoff, atomic
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
