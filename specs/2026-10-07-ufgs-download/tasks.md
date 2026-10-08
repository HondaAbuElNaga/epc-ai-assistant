# Tasks: UFGS download script

Spec: [spec.md](spec.md) · All commands inside the container (`docker compose exec dev ...`).

- [x] 1. `docs/stages/stage_02_data.md`: Stage 2 guide (datasets, order, checks, what to learn)
- [x] 2. Fixtures: tiny `documents.xml` sample and a minimal PDF in `tests/fixtures/`
- [x] 3. Write `tests/test_ufgs_download.py` (fails first): parsing, filtering, slug → name,
         403/503/non-PDF handling, resume/force, manifest, delay
- [x] 4. `src/common/http.py`: polite session (User-Agent, delay, retries with backoff)
- [x] 5. `src/datasets/ufgs.py`: section list, name mapping, download + validation + atomic write,
         manifest, summary, CLI (`--divisions`, `--limit`, `--dry-run`, `--force`)
- [x] 6. Register the `network` pytest marker; network test for `UFGS 01 33 00`
- [x] 7. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [x] 8. `--dry-run`, then `--limit 5`, then the full run for the 7 divisions; re-run to confirm
         resume (0 new downloads)
- [ ] 9. Docs: DEVLOG step with the real counts, LEARNING_GUIDE sections, roadmap tick,
         PROJECT_PLAN (script location), spec status → done

## v2 (spec section "v2 update")

- [x] 10. Commit v1 as a checkpoint (`f0d7d8b`)
- [ ] 11. Fixtures: API JSON samples (active with archived versions, retired, active without PDF,
          two current PDFs)
- [ ] 12. Tests first (fail): API parsing, PDF picking, new statuses, skip-after-API-check,
          retired-file cleanup, `--keep-retired`, network test for the API
- [ ] 13. Implement in `src/datasets/ufgs.py`; `DEFAULT_DIVISIONS` → 13 divisions
- [ ] 14. ruff check, ruff format, pytest
- [ ] 15. `--dry-run`, `--limit 5`, full run (13 divisions), re-run (0 new downloads)
- [ ] 16. Verify no non-ACTIVE PDF on disk; count files and size
- [ ] 17. Docs: DEVLOG step (real counts), LEARNING_GUIDE (web page vs API, JSON), Stage 2 guide,
          roadmap item text + tick, PROJECT_PLAN, spec status → done; commit and push
