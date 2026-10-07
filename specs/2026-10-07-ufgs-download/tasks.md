# Tasks: UFGS download script

Spec: [spec.md](spec.md) · All commands inside the container (`docker compose exec dev ...`).

- [ ] 1. `docs/stages/stage_02_data.md`: Stage 2 guide (datasets, order, checks, what to learn)
- [ ] 2. Fixtures: tiny `documents.xml` sample and a minimal PDF in `tests/fixtures/`
- [ ] 3. Write `tests/test_ufgs_download.py` (fails first): parsing, filtering, slug → name,
         403/503/non-PDF handling, resume/force, manifest, delay
- [ ] 4. `src/common/http.py`: polite session (User-Agent, delay, retries with backoff)
- [ ] 5. `src/datasets/ufgs.py`: section list, name mapping, download + validation + atomic write,
         manifest, summary, CLI (`--divisions`, `--limit`, `--dry-run`, `--force`)
- [ ] 6. Register the `network` pytest marker; network test for `UFGS 01 33 00`
- [ ] 7. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [ ] 8. `--dry-run`, then `--limit 5`, then the full run for the 7 divisions; re-run to confirm
         resume (0 new downloads)
- [ ] 9. Docs: DEVLOG step with the real counts, LEARNING_GUIDE sections, roadmap tick,
         PROJECT_PLAN (script location), spec status → done
