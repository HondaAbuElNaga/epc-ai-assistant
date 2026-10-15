# Tasks: Data catalog + checksums

- [ ] 1. Owner approves `spec.md` and answers the open questions; status → `approved`
- [ ] 2. Write `tests/test_checksums.py` (temporary folders, no real data): write + verify ok,
      changed byte, missing file, new file (warning, exit 0), skipped files, `/` paths,
      identical output on a second write, `--quick` size-only check, `--dataset` filter.
      Run it: it must fail (module does not exist yet)
- [ ] 3. Implement `src/datasets/checksums.py` (`scan`, `write`, `verify`, CLI); tests pass
- [ ] 4. Run `--write` on the real data (in the background); record the run time and counts
- [ ] 5. Cross-check: SHA-256 of `DSLIB3.4.zip`, `PID2Graph.zip` and the UFGS PDFs in
      `checksums.json` equal the values in the existing download records; paste the result here
- [ ] 6. Run `--write` again → `git diff data/checksums.json` is empty; run `--verify` → 0
      missing, 0 changed
- [ ] 7. Check the UFGS distribution statement (WBDG site + first pages of a PDF) and write down
      exactly what it says and where
- [ ] 8. Write `data/DATA_CATALOG.md` (summary table + one section per dataset + OSHA/NYC rows),
      numbers copied from `checksums.json` and the manifests
- [ ] 9. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
- [ ] 10. Verify every acceptance criterion against real output
- [ ] 11. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
- [ ] 12. Docs: DEVLOG step 19, LEARNING_GUIDE (checksums / SHA-256 section if missing),
      PROJECT_PLAN checklist, roadmap tick + "Current position"; spec status → `done`
- [ ] 13. Commit, push the branch, open a pull request into `main`
