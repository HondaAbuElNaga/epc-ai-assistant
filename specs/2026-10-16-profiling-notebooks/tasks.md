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
      → exit 0, 21 s, peak 209 MB, 93,620 bytes (2026-10-17; peak = max RSS of the child
      processes via `resource.getrusage`, because the container has no `/usr/bin/time`)
- [x] 6. Notebook `00_profile_ufgs.ipynb`; run headless; record the same
      → exit 0, 43 s, peak 171 MB, 63,002 bytes (2026-10-17)
- [x] 7. Notebook `00_profile_dataset_pid.ipynb`; run headless; record the same
      → exit 0, 32 s, peak 168 MB, 60,729 bytes (2026-10-17)
- [x] 8. Notebook `00_profile_pid2graph.ipynb`; run headless; record the same
      → exit 0, 34 s, peak 228 MB, 100,158 bytes (2026-10-17)
- [x] 9. Check the notebook totals against `DATA_CATALOG.md` / `checksums.json`
      → all agree: UFGS 271 PDFs / 37,587,638 B; Ghent 231 projects, 117/41/73; PID2Graph
      12 + 250 + 500 graphs with as many images (the criterion's "512 + 250" = 12 real + 500
      Dataset PID, + 250 synthetic); Dataset-P&ID 500 folders, 3,500 `.npy`, 500 images, 500 masks
- [ ] 10. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
- [ ] 11. Verify every acceptance criterion against real output
- [ ] 12. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
- [ ] 13. Docs: DEVLOG step 20, LEARNING_GUIDE (1.7 Jupyter: headless runs; matplotlib and
      PyMuPDF basics if added), PROJECT_PLAN checklist, roadmap tick + "Current position";
      spec status → `done`
- [ ] 14. Commit, push the branch, open a pull request into `main`
