# Tasks: Data catalog + checksums

- [x] 1. Owner approves `spec.md` and answers the open questions; status → `approved`
      → approved 2026-10-16: every file, catalog by hand, OSHA/NYC listed as not downloaded
- [x] 2. Write `tests/test_checksums.py` (temporary folders, no real data): write + verify ok,
      changed byte, missing file, new file (warning, exit 0), skipped files, `/` paths,
      identical output on a second write, `--quick` size-only check, `--dataset` filter.
      Run it: it must fail (module does not exist yet)
      → 18 tests; failed at import (`cannot import name 'checksums'`) before the module existed
- [x] 3. Implement `src/datasets/checksums.py` (`scan`, `write`, `verify`, CLI); tests pass
      → 18 passed; ruff clean
- [x] 4. Run `--write` on the real data (in the background); record the run time and counts
      → 7 min 1 s, 6,995 entries, `checksums.json` 1,086,225 bytes:
        ufgs 271 files / 37,587,638 B · ghent 697 / 340,223,260 B ·
        pid2graph 1,525 / 12,786,840,026 B · dataset_pid 4,502 / 2,328,204,243 B.
        Counts = `find -type f` minus skipped files (273−2, 698−1, 1,526−1, 4,504−2).
        (A first attempt was stopped by Claude Code because the PC ran low on memory while
        other jobs ran in parallel; re-run alone, it finished.)
- [x] 5. Cross-check: SHA-256 of `DSLIB3.4.zip`, `PID2Graph.zip` and the UFGS PDFs in
      `checksums.json` equal the values in the existing download records; paste the result here
      → ghent zip: True · PID2Graph.zip: sha256 True, bytes True · UFGS PDFs: 271/271 match ·
        Dataset-P&ID downloads: 3502/3502 match
- [x] 6. Run `--write` again → `git diff data/checksums.json` is empty; run `--verify` → 0
      missing, 0 changed
      → second `--write`: `cmp` with the first file → IDENTICAL. `--verify` (full SHA-256,
        3 min 17 s): ok 6,995 · missing 0 · changed 0 · new 0 · PASSED
- [x] 7. Check the UFGS distribution statement (WBDG site + first pages of a PDF) and write down
      exactly what it says and where
      → none found. Text of all 271 PDFs searched ("distribution statement", "public release",
        "distribution unlimited", "copyright", "public domain", "approved for public"): only
        spec content and an embedded Adobe font notice. WBDG API record: no license field.
        WBDG pages need JavaScript (not readable). Background quoted from 17 U.S.C. §105(a) and
        §101 (law.cornell.edu), marked "not a legal conclusion" in the catalog
- [x] 8. Write `data/DATA_CATALOG.md` (summary table + one section per dataset + OSHA/NYC rows),
      numbers copied from `checksums.json` and the manifests
      → written; two sentences re-checked against the files (P&ID overlap → format_notes §6;
        ASTM → 219/271 PDFs)
- [x] 9. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` (coverage ≥ 70 %)
      → ruff clean, 28 files formatted; 142 passed, 2 deselected; coverage 89 % (checksums.py 98 %)
- [x] 10. Verify every acceptance criterion against real output
      → all 8 criteria met (evidence in tasks 4–9)
- [x] 11. Review with 3 subagents (bugs, security, accuracy); fix confirmed findings
      → skipped at the owner's request (2026-10-16)
- [x] 12. Docs: DEVLOG step 19, LEARNING_GUIDE (checksums / SHA-256 section if missing),
      PROJECT_PLAN checklist, roadmap tick + "Current position"; spec status → `done`
- [x] 13. Commit, push the branch, open a pull request into `main`
