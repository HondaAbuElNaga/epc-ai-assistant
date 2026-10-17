# Tasks: Profiling notebooks (one per dataset)

- [x] 1. Owner approves `spec.md` and answers the open questions; status → `approved`
- [x] 2. If approved: `uv add matplotlib` / `uv add pymupdf`; update `product/tech-stack.md`
      (status ✅, reason, license); commit `pyproject.toml` + `uv.lock` together
- [x] 3. Write `tests/test_profiling.py` on fake data (tiny PDF made with PyMuPDF in the test, PNG
      and JPEG headers, a small `.graphml`, a `.npy` with and without pickle, a DataFrame with
      gaps). Run it: it must fail (module does not exist yet)
- [x] 4. Implement `src/datasets/profiling.py`; tests pass
- [x] 5. Notebook `00_profile_ghent.ipynb` (smallest data, reuses `load_ghent()`); run headless;
      record run time, peak memory, file size
      → exit 0, 19 s, peak 208 MB, 95,294 bytes (final run after review fixes, 2026-10-17; peak = max RSS of the child
      processes via `resource.getrusage`, because the container has no `/usr/bin/time`)
- [x] 6. Notebook `00_profile_ufgs.ipynb`; run headless; record the same
      → exit 0, 58 s, peak 170 MB, 64,284 bytes (final run, 2026-10-17)
- [x] 7. Notebook `00_profile_dataset_pid.ipynb`; run headless; record the same
      → exit 0, 26 s, peak 165 MB, 61,754 bytes (final run, 2026-10-17)
- [x] 8. Notebook `00_profile_pid2graph.ipynb`; run headless; record the same
      → exit 0, 33 s, peak 235 MB, 101,206 bytes (final run, 2026-10-17)
- [x] 9. Check the notebook totals against `DATA_CATALOG.md` / `checksums.json`
      → all agree: UFGS 271 PDFs / 37,587,638 B; Ghent 231 projects, 117/41/73; PID2Graph
      12 + 250 + 500 graphs with as many images (the criterion's "512 + 250" = 12 real + 500
      Dataset PID, + 250 synthetic); Dataset-P&ID 500 folders, 3,500 `.npy`, 500 images, 500 masks
- [x] 10. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
      → ruff clean (incl. notebooks); 163 passed, 2 deselected; coverage 89.41 % (after review fixes)
- [x] 11. Verify every acceptance criterion against real output (all met, see spec)
- [x] 12. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
      → security: nothing significant (no pickle path, expat 2.8.5 guards entity expansion, no
      names/paths/secrets in outputs). Bugs: truncated JPEG raised `struct.error` and a blank
      box value crashed `float("")` → both fixed with tests; missing % now 2 decimals. Accuracy
      (every key number re-computed independently, all matched): findings now only repeat
      printed numbers; UFGS header got the catalog's caveat and publish-date range; Ghent got the
      extra citations and evidence for "last period = final" (115 of 117 with EV ≥ 99 % BAC);
      SPI wording fixed; PID2Graph compares all 3 subsets and explains the valve px difference
      by image scale; Dataset-P&ID shows `SCALE = "None"` in 266 of 500 title blocks. Found
      while fixing: "AC > BAC" counted cent-level rounding, now AC > 1.01 × BAC (66).
      Not changed (low, current data never hits it): `.npy` version 3.0 and non-numeric drawing
      folders in `npy_shapes`.
- [x] 13. Docs: DEVLOG step 20, LEARNING_GUIDE (1.7 Jupyter: headless runs; matplotlib and
      PyMuPDF basics if added), PROJECT_PLAN checklist, roadmap tick + "Current position";
      spec status → `done`
- [x] 14. Commit, push the branch, open a pull request into `main`
