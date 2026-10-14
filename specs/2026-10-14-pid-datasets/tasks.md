# Tasks: P&ID datasets (PID2Graph + Dataset-P&ID download)

Spec: [spec.md](spec.md) · Branch: `spec/2026-10-14-pid-datasets` · All commands inside the
container (`docker compose exec dev ...`).

Size note: the roadmap says `XS`. With a 9.3 GB download and about 3,500 Drive files it is
closer to `S`, though most of that time is waiting on downloads.

- [x] 1. Owner approves the spec and answers Open questions 1–3; record the answers in the spec
         Done 2026-10-14: Complete/ only; annotations + images; wording fixed (spec "Decisions")
- [ ] 2. Save the test fixtures: a trimmed Drive folder-view page (2 subfolders + 1 archive) in
         `tests/fixtures/`
- [ ] 3. Write `tests/test_pid_download.py` (offline, fake session) and see it fail:
         resume with `Range` from `.part`, MD5 mismatch → error and no final file, skip existing,
         zip-slip member rejected, Complete-only extraction, tar `filter="data"`, Drive page
         parser (folders, file IDs, names), manifest fields
- [ ] 4. Implement `src/datasets/pid.py` (`python -m src.datasets.pid [--only ...]`) on
         `PoliteClient`
- [ ] 5. `ruff check`, `ruff format`, `pytest` (coverage ≥ 70 %) green before any real download
- [ ] 6. Real run, PID2Graph (in the background): size + MD5 verified, extract, manifest; check
         the counts against the zip listing in the spec
- [ ] 7. Real run, Dataset-P&ID: 500 × 7 `.npy` + archives; list anything missing; extract the
         archives (safe tar)
- [ ] 8. Second run downloads nothing (skip check)
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
