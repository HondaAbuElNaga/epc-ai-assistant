# Spec: P&ID datasets (PID2Graph + Dataset-P&ID download)

**Roadmap item:** Phase 2, "PID2Graph + Dataset-P&ID download"
**Status:** draft (2026-10-14), waiting for the owner's approval
**Branch:** `spec/2026-10-14-pid-datasets`
**Related:** PROJECT_PLAN Stage 2 (download) and Stage 6 (Module C, P&ID reader)

## Goal
Get the two public P&ID datasets onto disk, checked and described, so that Module C (P&ID reader:
symbol detection, tag OCR, connectivity graph) can later train and test on them. This step only
covers download, integrity checks and a format inspection. No training and no conversion.

## What the sources say (checked 2026-10-14)

Everything below was read from the sources on 2026-10-14. Nothing here comes from memory.

### PID2Graph
Sources: the Zenodo API (`https://zenodo.org/api/records/14803338`), the paper on arXiv
(2411.13929), and a listing of the zip's contents read with HTTP Range requests (only the
table of contents was fetched, not the 9.3 GB file).
- **Record:** "PID2Graph", DOI `10.5281/zenodo.14803338`, published 2025-02-14, by Stürmer,
  Graumann, Koch (DLR). There is only one version of the record.
- **License:** CC BY-SA 4.0 for the record. The record also lists the license of each part:
  - Dataset PID: CC BY-SA 4.0.
  - Synthetic symbols: CC BY-SA 4.0.
  - OPEN100: "taken from open-100.com", with no license given. The open-100.com home page shows
    no license or terms either.
- **Citation (as given by the record):** Stürmer, J. M., Graumann, M., & Koch, T. (2025). *From
  Engineering Diagrams to Graphs: Digitizing P&IDs with Transformers*. 2025 IEEE 12th
  International Conference on Data Science and Advanced Analytics (DSAA).
  https://doi.org/10.1109/DSAA65442.2025.11248012
- **File:** one zip, `PID2Graph.zip`, **9,303,633,645 bytes** (8.66 GiB), with MD5
  `90f782220de97e7e249d2595c49ddc1c`. URL:
  `https://zenodo.org/api/records/14803338/files/PID2Graph.zip/content`. The server supports HTTP
  Range requests, so a stopped download can be resumed.
- **Contents (from the zip's table of contents):** 74,655 entries, **13.45 GB unzipped**.

  | Folder | Drawings | Images | Graphs | Size |
  |---|---|---|---|---|
  | `Complete/Dataset PID` | 500 | `.png` | `.graphml` | 3,273 MB |
  | `Complete/PID2Graph OPEN100` | **12 (real)** | `.png` | `.graphml` | 11 MB |
  | `Complete/PID2Graph Synthetic` | 250 | `.jpg` | `.graphml` | 199 MB |
  | `Patched/…` (same 3 sets, cut into tiles) | 35,799 tiles | `.png` | `.graphml` + 1 `.npy` per drawing | 9,966 MB |

- **Annotations:** each drawing is a graph. Nodes are symbols with a bounding box (xmin, ymin,
  xmax, ymax) and a label, plus helper nodes named "connector" (and "border" in the patches).
  Edges are lines with a label. The paper (Table I) lists **7 symbol classes**: general,
  pump/compressor, arrow, tank/vessel, instrumentation, inlet/outlet, valve. It also lists
  **2 line classes**: solid and non-solid.
- **Important for the portfolio story:** the only **real** drawings are the **12 OPEN100
  P&IDs**, which come from the OPEN100 nuclear reactor project. Everything else is synthetic.
  Dataset-P&ID is already included, but converted to the 7 classes. The mission text
  "real P&IDs (PID2Graph)" makes it sound bigger than it is (see Open question 3).

### Dataset-P&ID (Paliwal et al. 2021, "Digitize-PID", arXiv 2109.03794)
Sources: the paper's text and its embedded hyperlink, and the public Google Drive folder that
link points to.
- **Paper facts:** 500 synthetic P&ID sheets, with a 4:1 train/test ratio. The paper names
  **32 symbol types** (Fig. 3). It says the annotations cover symbols, lines and text, and that
  the dataset is "made publicly available".
- **Link (from the PDF's hyperlink):**
  `https://drive.google.com/drive/u/1/folders/1gMm_YKBZtXB3qUKUpI-LF1HE_MgzwfeR`. It still
  works and needs no login. The folder is named `DigitizePID_Dataset`.
- **Folder contents:**
  - 500 subfolders, `0` to `499`. Each has 7 annotation files (`<n>_symbols.npy`,
    `_lines.npy`, `_lines2.npy`, `_words.npy`, `_linker.npy`, `_KeyValue.npy`, `_Table.npy`).
    They are dated 2021-08-30/31.
  - `image_2.tar.gz`: **968,795,855 bytes** (about 924 MiB).
  - `mask.tar.gz`: **6,046,912 bytes**.
  - What the two archives contain is unknown until they are downloaded.
- **License:** the folder has no license file. The paper only says "publicly available". The
  PID2Graph record states CC BY-SA 4.0 for "Dataset PID".
- **Why download it when PID2Graph already includes it:** PID2Graph keeps only 7 classes and
  the graph. The original has the **32 classes, the text (`words`) and tables**, which are
  needed for tag OCR (PROJECT_PLAN 6.3) and for detecting finer symbols.

## Scope
- In:
  - Download `PID2Graph.zip` into `data/raw/pid/pid2graph/` (resumable, MD5-checked). Extract
    the parts chosen in Open question 1.
  - Download Dataset-P&ID (the parts chosen in Open question 2) into
    `data/raw/pid/dataset_pid/`.
  - A `manifest.json` per dataset (source, version/date, license, citation, files, sizes,
    checksums, download date).
  - **Inspect the real files** and write `format_notes.md` in this spec folder: real counts,
    image sizes, graphml attributes and label values, and the `.npy` shapes and dtypes.
- Out:
  - Conversion to YOLO format, tiling, train/test splits (Phase 7).
  - Any loader or model code (Phase 7).
  - `DATA_CATALOG.md`, `data/checksums.json`, profiling notebooks, `test_data_integrity.py`.
    These are later Phase 2 items, but this spec writes down the facts they will need.
  - NetworkX, OpenCV, Pillow: still 🔜 Stage 6. The inspection uses the standard library only.

## Requirements
1. Raw files are stored under `data/raw/pid/` and are **not committed** (`data/raw/**` is already
   git-ignored).
2. `src/datasets/pid.py`, run as `python -m src.datasets.pid [--only pid2graph|dataset-pid]`,
   does both downloads. It uses the existing `PoliteClient` (honest User-Agent, delay,
   retries).
3. **Resumable large download:** data is written to `<file>.part`. If the run is stopped, the
   next run continues with an HTTP `Range` header from the `.part` size. The file gets its final
   name only after the size and MD5 match the values from the Zenodo API. If they don't match,
   it fails with a clear error and no final file is written.
4. **Skip work already done:** a file that is already complete (correct size, and checksum when
   one is known) is not downloaded again.
5. **Safe extraction:**
   - zip: every member path is checked first. Absolute paths and `..` are rejected, so an
     archive cannot write outside its folder ("zip slip").
   - tar: `tarfile` with `filter="data"`, Python 3.12's safe mode.
6. **Dataset-P&ID listing:** the file list comes from the public Drive folder view. The script
   expects 500 folders × 7 files plus 2 archives. Anything missing or extra is **reported in the
   manifest**, not ignored.
7. **No pickle execution:** `.npy` files are only opened with `numpy.load(allow_pickle=False)`.
   If a file needs pickle (object arrays), it is inspected with `pickletools`, which reads
   without running any code. Loading it with pickle is decided with the owner later (Phase 7).
8. `manifest.json` per dataset lists every file with its size and SHA-256 (MD5 also for the
   Zenodo zip), the source URL, the license text found, the citation, and the UTC download date.
9. `format_notes.md` holds only facts that were checked by opening the files.

## Inputs / outputs
- Input: the two public sources above (no login, no form).
- Output:
  - `data/raw/pid/pid2graph/PID2Graph.zip` + the extracted folders + `manifest.json`
    (git-ignored)
  - `data/raw/pid/dataset_pid/<0…499>/*.npy`, the archives (+ extracted) + `manifest.json`
    (git-ignored)
  - `src/datasets/pid.py`
  - `tests/test_pid_download.py` + small fixtures in `tests/fixtures/`. The fixtures are a
    trimmed Drive folder-view page and a tiny zip/tar built in the test (one of them with a
    `../` member). There is **no real data** in git: CC BY-SA would make copied files
    share-alike.
  - `specs/2026-10-14-pid-datasets/format_notes.md`

## Acceptance criteria
- [ ] `PID2Graph.zip` is on disk: 9,303,633,645 bytes, MD5 `90f782220de97e7e249d2595c49ddc1c`.
- [ ] The extracted PID2Graph folders have the counts from the zip listing: 500 + 12 + 250
      complete drawings, each with an image and a `.graphml` (plus the patched counts, if
      Patched is extracted).
- [ ] Dataset-P&ID: 500 folders × 7 `.npy` files on disk (or each missing one listed in the
      manifest); the chosen archives are downloaded and extracted.
- [ ] A second run of `python -m src.datasets.pid` downloads nothing and finishes quickly.
- [ ] Unit tests pass offline: resume with `Range`, MD5 mismatch → error and no final file,
      zip-slip member rejected, skip existing, Drive folder-view parser, manifest contents.
- [ ] `format_notes.md` records the real image sizes, graphml node/edge attributes and label
      values, and `.npy` shapes/dtypes (or "needs pickle"). Each fact was checked on the files.
- [ ] `ruff check`, `ruff format`, `pytest` are clean, with coverage ≥ 70 % (CI gate).

## Technical approach
- **Libraries:** `requests`, `tqdm`, `numpy` (all ✅ in the tech stack), and the standard library
  (`hashlib`, `zipfile`, `tarfile`, `xml.etree`, `pickletools`, `re`, `struct` for PNG/JPEG
  headers). **No new dependency.** `gdown` (a Google Drive downloader) is not needed: the
  public `drive.usercontent.google.com/download?id=…&export=download&confirm=t` URL served the
  archives in the 2026-10-14 check.
- **Download flow:** Zenodo API → expected size and MD5 → streamed download to `.part` in
  chunks, with a tqdm progress bar → verify → rename → extract → manifest.
- **Drive flow:** the folder-view page gives the subfolder links → each subfolder page gives the
  file IDs → each file is downloaded with the polite delay. That is about 3,500 small files, so
  roughly 1 hour at a 1 s delay. It runs in the background and can be resumed because finished
  files are skipped.
- **Risks:**
  - **Google Drive can change its HTML or throttle.** The parser is tested on a saved page.
    Throttling (429) is retried by `PoliteClient`. If Drive blocks the bulk download, stop and
    ask the owner (it can be done by hand in the browser as a fallback). Don't work around the
    block.
  - **9.3 GB download time** depends on the connection. It is resumable, so an interrupted
    run loses no work.
  - **Disk:** zip 9.3 GB + extracted 3.5 GB (Complete only) or 13.45 GB (all), + about 1 GB for
    Dataset-P&ID. D: has 469 GB free.
  - **Licenses:** CC BY-SA 4.0 is share-alike. If we ever publish converted annotations, they
    must use the same license. OPEN100's own terms are unclear, so its drawings are used for
    research and evaluation only, with credit, and never republished.

## Open questions (owner decides; my recommendation first)
1. **Which parts of PID2Graph to extract?**
   - **Recommended: `Complete/` only (about 3.5 GB) and keep the zip.** Phase 7 plans its own
     tiling (1024 px with overlap), so the authors' patches (1500 px, about 10 GB) are not
     needed now. They can be extracted later from the same zip without downloading again.
   - Alternative: extract everything (13.45 GB).
2. **Which parts of the original Dataset-P&ID?**
   - **Recommended: the 500 annotation folders + `image_2.tar.gz` + `mask.tar.gz` (about 1 GB).**
     The PID2Graph copy of the images may be resized or changed, and the 32-class boxes must
     match the exact images they were drawn on.
   - Alternative: annotations only (a few MB), and reuse PID2Graph's PNGs (risk: the
     coordinates may not match).
   - Alternative: skip the original and use only PID2Graph's 7-class version (no text/OCR
     labels).
3. **Fix the "real P&IDs" wording now?**
   - **Recommended: yes.** `product/mission.md` says "real P&IDs (PID2Graph)", and PROJECT_PLAN
     and `docs/stages/stage_02_data.md` say "PID2Graph (real P&IDs with annotations)".
     That would become "12 real P&IDs (PID2Graph OPEN100) + 750 synthetic", so no reader is
     misled.
   - PROJECT_PLAN Stage 6 also plans "equipment list F1 on 10 held-out real drawings", which
     leaves only 2 real drawings for training. That is only **noted** here. It gets decided in
     the Phase 7 spec.
