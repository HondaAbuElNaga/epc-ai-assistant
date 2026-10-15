# Spec: Data catalog + checksums

**Roadmap item:** Phase 2, "`data/DATA_CATALOG.md` + checksums"
**Status:** approved (2026-10-16) with the owner's decisions below
**Branch:** `spec/2026-10-16-data-catalog`
**Related:** PROJECT_PLAN Stage 2, process step 4 and the testing bullet "checksums are stored in
`data/checksums.json` and match"

## Goal
Write one page that lists every dataset the project uses: where it came from, when it was
downloaded, its license, how many files it has, how big it is and its known issues. Add a
checksum file so we can **prove** later that the local data is still exactly what was downloaded.
This is the basis for the portfolio's data story ("which data, from where, may I use it?") and for
the later `tests/test_data_integrity.py` item.

## What is on disk today (checked 2026-10-16)

Counted with `find -type f | wc -l` and `du -sh` on the host. The catalog will hold the exact
numbers produced by the script, not these rounded ones.

| Dataset | Folder | Files | Size | Existing record |
|---|---|---|---|---|
| UFGS | `data/raw/ufgs/` | 273 | 37 MB | `manifest.json` (705 sections; per-PDF SHA-256) |
| Ghent DSLIB v3.4 | `data/raw/project_controls/ghent/` | 698 | 327 MB | `download.json` (zip SHA-256 only) |
| PID2Graph | `data/raw/pid/pid2graph/` | 1,526 | 12 GB | `manifest.json` (zip MD5 + SHA-256, counts) |
| Dataset-P&ID | `data/raw/pid/dataset_pid/` | 4,504 | 2.2 GB | `manifest.json` (per-file SHA-256 of downloads) |
| OSHA, NYC | `data/raw/osha/`, — | 0 | — | not downloaded (optional roadmap item) |

What the existing records do **not** cover:
- Files that were **extracted** from archives (Ghent `DSLIB 3.4/`, PID2Graph `Complete/`,
  Dataset-P&ID `image_2/`, `mask/`) have no checksum anywhere.
- The four records use four different layouts, so nothing can check them all in one go.
- License facts are spread over three spec files. The UFGS distribution statement was never
  checked (`specs/2026-10-07-ufgs-download/spec.md` says so and points to this item).

## Scope
- In:
  - `data/DATA_CATALOG.md`, hand-written: one section per dataset (see Requirement 1).
  - `data/checksums.json`: SHA-256 and size of **every file** under `data/raw/` (see Open
    question 1), written by a script.
  - `src/datasets/checksums.py`, run as `python -m src.datasets.checksums` with two modes:
    `--write` (create/update the file) and `--verify` (check the disk against it).
  - Unit tests on small temporary folders (CI has no real data).
  - Check the UFGS distribution statement on the WBDG site and in a downloaded PDF.
- Out:
  - `tests/test_data_integrity.py` (next roadmap item; it will call `--verify` logic).
  - Profiling notebooks (separate roadmap item).
  - OSHA and NYC downloads: listed in the catalog as "not downloaded (optional)".
  - Changing the existing download scripts or their manifests.
  - `data/processed/` (made by our own code; can be rebuilt, so no checksum).

## Requirements
1. `DATA_CATALOG.md` has a summary table at the top (dataset, module, files, size, license,
   downloaded) and one section per dataset with: source URL, version/release, download date
   (UTC, from the existing records), license and citation **exactly as the source states it**
   (or "no license stated" when there is none), folder layout, file count, size, how to
   re-download (`python -m src.datasets.<name>`), which modules use it, and known issues.
2. Every number in the catalog comes from `checksums.json` or the existing manifests. Every
   license line names where it was read. Nothing from memory.
3. Known issues that must be in the catalog (already found in earlier specs): only 12 PID2Graph
   drawings are real; 4 of 7 Dataset-P&ID `.npy` types need pickle; Ghent repo has no license
   file; UFGS: 434 retired sections not downloaded; PID2Graph `Patched/` not extracted.
4. `checksums.json` layout: one entry per file, keyed by path relative to `data/raw/` with
   forward slashes (same on Windows and Linux), value `{"bytes": int, "sha256": str}`, plus a
   header with `updated_at` (UTC) and per-dataset totals. Keys are sorted, and the file is only
   rewritten when an entry changed, so a re-run with unchanged data gives an identical file
   (clean `git diff`; a new timestamp alone would make a diff).
5. Skipped files: `.gitkeep`, unfinished downloads (`*.part`), and the download records
   themselves (`manifest.json`, `download.json`, and the cached Drive listing
   `drive_listing.json`), which change on every re-run.
6. `--verify` reports four lists: **missing** (in the file, not on disk), **changed** (size or
   hash differs), **new** (on disk, not in the file) and **ok** count. Exit code 0 only when
   missing and changed are empty; new files are a warning.
7. Speed: files are hashed in 1 MiB chunks (no full file in memory). A `--quick` option only
   compares sizes, for a fast check. Progress is shown with `tqdm` (14+ GB takes minutes).
8. `--dataset ufgs|ghent|pid2graph|dataset_pid` limits write/verify to one folder.

## Inputs / outputs
- Input: `data/raw/**` (git-ignored), the existing manifests.
- Output (committed): `data/DATA_CATALOG.md`, `data/checksums.json`, `src/datasets/checksums.py`,
  `tests/test_checksums.py`.

## Acceptance criteria
- [ ] `checksums.json` lists every file under `data/raw/` except the skipped ones (Req. 5);
      its per-dataset counts match `find -type f` minus skipped files.
- [ ] The SHA-256 values in `checksums.json` for `DSLIB3.4.zip`, `PID2Graph.zip` and the UFGS
      PDFs equal the ones already in the download records (cross-check, done by a test or a
      one-off script whose output is pasted in `tasks.md`).
- [ ] `python -m src.datasets.checksums --verify` on the real data: 0 missing, 0 changed.
- [ ] Running `--write` twice without data changes gives a byte-identical file.
- [ ] Unit tests pass offline: write + verify ok; a changed byte → `changed`; a deleted file →
      `missing`; an added file → `new` (exit 0); skipped files ignored; paths use `/`.
- [ ] `DATA_CATALOG.md` has all 4 datasets + OSHA/NYC rows, every field of Requirement 1, and
      every issue of Requirement 3; its counts and sizes match `checksums.json`.
- [ ] UFGS license/distribution line is filled from a checked source, or says clearly
      "not stated" with the place that was checked.
- [ ] `ruff check`, `ruff format`, `pytest` clean, coverage ≥ 70 % (CI gate).

## Technical approach
- **Libraries:** standard library only (`hashlib`, `json`, `pathlib`, `argparse`) + `tqdm`
  (✅ in the tech stack). No new dependency.
- **Design:** three small functions: `scan(root) -> dict[path, {bytes, sha256}]`,
  `write(root, out)`, `verify(root, checksums) -> Report`. The CLI wraps them. Same style as
  `src/datasets/ufgs.py` (`_sha256` already exists there; move it to a shared helper or reuse it).
- **Where the file lives:** `data/checksums.json`, as PROJECT_PLAN says. `data/raw/**` is
  ignored, but `data/checksums.json` and `data/DATA_CATALOG.md` are not, so they get committed.
- **Risks:**
  - File size: about 7,000 entries × ~130 bytes ≈ 1 MB of JSON in git. Acceptable; see Open
    question 1 for the smaller choice.
  - Hashing 14.5 GB on a Windows bind mount is slow (a plain `du` took over 2 minutes). Run
    `--write` in the background once; `--quick` covers everyday checks.
  - Line endings are not a risk: `zipfile`/`tarfile` write the bytes exactly as stored, so the
    hashes are the same on Windows and Linux.

## Owner's decisions (2026-10-16)
1. Checksums: **(a) every file** under `data/raw/`.
2. Catalog: written **by hand**, numbers copied from the script output.
3. OSHA/NYC: listed as "not downloaded (optional)".

## Open questions (as asked)
1. **What gets a checksum?**
   (a) every file under `data/raw/`, about 7,000 entries, ~1 MB JSON. Catches a damaged
   extracted file. **Recommended.**
   (b) only the downloaded files (archives + UFGS PDFs + Dataset-P&ID `.npy`), about 3,800
   entries; extracted files are trusted because the archive is checked.
2. **Catalog by hand or generated?** Recommended: **by hand** (it needs judgement: licenses,
   issues), with the numbers copied from the script output. A generator would only save a few
   minutes for 4 datasets.
3. **OSHA/NYC:** list them as "not downloaded (optional)" now, and fill them in if that item is
   done later. Recommended: yes.
