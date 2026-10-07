# Tasks: Provider-agnostic LLM interface + data classification guard

Spec: [spec.md](spec.md) · All commands inside the container (`docker compose exec dev ...`).

- [x] 1. Write `tests/test_llm_interface.py` covering every acceptance criterion (fails first)
- [x] 2. `src/common/providers/base.py`: `LLMRequest`, `LLMResponse`, `LLMProvider` Protocol,
         `DataClassificationError`, `UnknownProviderError`
- [x] 3. `src/common/providers/fake_provider.py`
- [x] 4. `src/common/providers/anthropic_provider.py` (move the current client code here)
- [x] 5. `src/common/config.py`: `llm_provider()`, `data_classification()`, tier → model mapping
         read at call time
- [x] 6. `src/common/llm.py`: registry, guard, tiers, usage, `last_call()`; keep `complete()`
         signature compatible
- [x] 7. `.env.example`: document `LLM_PROVIDER`, `DATA_CLASSIFICATION`, model overrides
- [x] 8. Architecture test: no `anthropic` import outside `src/common/providers/`
- [x] 9. `uv run ruff check . && uv run ruff format . && uv run pytest`
- [x] 10. Docs: DEVLOG step, LEARNING_GUIDE (adapter pattern, guard), roadmap tick, spec status → done
