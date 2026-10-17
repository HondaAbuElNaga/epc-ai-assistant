# Tasks: Profiling notebooks (one per dataset)

- [x] 1. Owner approves `spec.md` and answers the open questions; status → `approved`
- [ ] 2. If approved: `uv add matplotlib` / `uv add pymupdf`; update `product/tech-stack.md`
      (status ✅, reason, license); commit `pyproject.toml` + `uv.lock` together
- [ ] 3. Write `tests/test_profiling.py` on fake data (tiny PDF made with PyMuPDF in the test, PNG
      and JPEG headers, a small `.graphml`, a `.npy` with and without pickle, a DataFrame with
      gaps). Run it: it must fail (module does not exist yet)
- [ ] 4. Implement `src/datasets/profiling.py`; tests pass
- [ ] 5. Notebook `00_profile_ghent.ipynb` (smallest data, reuses `load_ghent()`); run headless;
      record run time, peak memory, file size
- [ ] 6. Notebook `00_profile_ufgs.ipynb`; run headless; record the same
- [ ] 7. Notebook `00_profile_dataset_pid.ipynb`; run headless; record the same
- [ ] 8. Notebook `00_profile_pid2graph.ipynb`; run headless; record the same
- [ ] 9. Check the notebook totals against `DATA_CATALOG.md` / `checksums.json`
- [ ] 10. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
- [ ] 11. Verify every acceptance criterion against real output
- [ ] 12. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
- [ ] 13. Docs: DEVLOG step 20, LEARNING_GUIDE (1.7 Jupyter: headless runs; matplotlib and
      PyMuPDF basics if added), PROJECT_PLAN checklist, roadmap tick + "Current position";
      spec status → `done`
- [ ] 14. Commit, push the branch, open a pull request into `main`
