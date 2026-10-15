# Tasks: P&ID datasets (PID2Graph + Dataset-P&ID download)

Spec: [spec.md](spec.md) · Branch: `spec/2026-10-14-pid-datasets` · All commands inside the
container (`docker compose exec dev ...`).

Size note: the roadmap says `XS`. With a 9.3 GB download and about 3,500 Drive files it is
closer to `S`, though most of that time is waiting on downloads.

- [x] 1. Owner approves the spec and answers Open questions 1–3; record the answers in the spec
         Done 2026-10-14: Complete/ only; annotations + images; wording fixed (spec "Decisions")
- [x] 2. Save the test fixtures: a trimmed Drive folder-view page (2 subfolders + 1 archive) in
         `tests/fixtures/`
         Done 2026-10-14: `drive_folder_root.html` (folders 0, 1 + image_2.tar.gz) and
         `drive_folder_0.html` (7 .npy); the full real root page had 502 entries (500 + 2)
- [x] 3. Write `tests/test_pid_download.py` (offline, fake session) and see it fail:
         resume with `Range` from `.part`, MD5 mismatch → error and no final file, skip existing,
         zip-slip member rejected, Complete-only extraction, tar `filter="data"`, Drive page
         parser (folders, file IDs, names), manifest fields
         Done: 24 tests; first run failed at import (`cannot import name 'pid'`), as expected
- [x] 4. Implement `src/datasets/pid.py` (`python -m src.datasets.pid [--only ...]`) on
         `PoliteClient`
         Done: 24/24 pass. Added `--refresh-listing` (Drive listing cached in `drive_listing.json`)
- [x] 5. `ruff check`, `ruff format`, `pytest` (coverage ≥ 70 %) green before any real download
         Done 2026-10-14: ruff clean (1 file reformatted); 122 passed, 2 deselected; coverage 88 %
         total, `pid.py` 88 %
- [x] 6. Real run, PID2Graph (in the background): size + MD5 verified, extract, manifest; check
         the counts against the zip listing in the spec
         Done 2026-10-15: 9,303,633,645 bytes, MD5 90f78222…c1c OK. First run broke at 283 MB
         (IncompleteRead) → auto-resume added (commit ae89c3b); then 180 kB/s–1.1 MB/s. Complete/:
         500 + 12 + 250 drawings, each image + .graphml = the zip listing. Extraction (1,524 files)
         took ~11 h, cause not verified (Docker → Windows folder writes, or the closed log pipe)
- [x] 7. Real run, Dataset-P&ID: 500 × 7 `.npy` + archives; list anything missing; extract the
         archives (safe tar)
         Done 2026-10-15: 3,500 .npy (28.8 MB incl. mask), missing 0, extra 0. image_2.tar.gz broke at
         884 MB on the first run, finished by a second run (968,795,855 bytes). image_2 = 500 .jpg,
         mask = 500 .png (`<n>_mask.png`)
- [x] 8. Second run downloads nothing (skip check)
         Done 2026-10-15: full run (both datasets) in 33 s; 0 downloads, 0 files extracted
- [ ] 9. Inspect the files and write `format_notes.md`: image sizes, graphml attributes + label
         values, `.npy` shapes/dtypes (`allow_pickle=False`; `pickletools` if pickle is needed),
         what `image_2` and `mask` contain
- [ ] 10. Docs: `product/tech-stack.md` data-source rows (real licenses), mission/PROJECT_PLAN/
          stage_02 wording (if Q3 = yes), DEVLOG step, LEARNING_GUIDE (Range requests/resumable
          downloads, zip slip + safe tar, graphml, `.npy` + pickle risk), roadmap tick +
          "Current position", PROJECT_PLAN checklist, spec status → done
- [ ] 11. Review: 3 subagents (bugs, security, accuracy) on `git diff main...HEAD`; fix
          confirmed findings
- [ ] 12. Push the branch, open a pull request (CI green), merge into `main`
