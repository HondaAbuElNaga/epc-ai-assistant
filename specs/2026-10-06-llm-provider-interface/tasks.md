# Tasks: Provider-agnostic LLM interface + data classification guard

Spec: [spec.md](spec.md) · All commands inside the container (`docker compose exec dev ...`).

- [ ] 1. Write `tests/test_llm_interface.py` covering every acceptance criterion (fails first)
- [ ] 2. `src/common/providers/base.py`: `LLMRequest`, `LLMResponse`, `LLMProvider` Protocol,
         `DataClassificationError`, `UnknownProviderError`
- [ ] 3. `src/common/providers/fake_provider.py`
- [ ] 4. `src/common/providers/anthropic_provider.py` (move the current client code here)
- [ ] 5. `src/common/config.py`: `llm_provider()`, `data_classification()`, tier → model mapping
         read at call time
- [ ] 6. `src/common/llm.py`: registry, guard, tiers, usage, `last_call()`; keep `complete()`
         signature compatible
- [ ] 7. `.env.example`: document `LLM_PROVIDER`, `DATA_CLASSIFICATION`, model overrides
- [ ] 8. Architecture test: no `anthropic` import outside `src/common/providers/`
- [ ] 9. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [ ] 10. Docs: DEVLOG step, LEARNING_GUIDE (adapter pattern, guard), roadmap tick, spec status → done
