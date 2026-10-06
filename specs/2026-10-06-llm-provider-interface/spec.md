# Spec: Provider-agnostic LLM interface + data classification guard

**Roadmap item:** Phase 0, "Provider-agnostic LLM interface + data classification guard"
**Status:** approved (2026-10-07, with review fixes 1–5 below)
**Related:** PROJECT_PLAN Stage 13.1 · product/mission.md ("Local-first ready")

## Goal

Every module calls the LLM through one interface that doesn't know which model or vendor is behind
it. This lets the project start with **Claude on public data** and later switch to **local models**
(Ollama on the RTX 4060, vLLM on a company server) by changing `.env` only. A guard makes it
impossible to send **confidential** data to an external provider.

## Scope

**In**
- A provider interface (Python `Protocol`) and a registry selected by `LLM_PROVIDER`.
- Adapters now: `anthropic` (Claude) and `fake` (deterministic, for tests and CI).
- Model **tiers** instead of model IDs in module code: `tier="main"` / `tier="fast"`, mapped to
  model IDs per provider in `config.py`.
- Data classification guard: `DATA_CLASSIFICATION=public|confidential`.
- Usage tracking per call (provider, model, input/output tokens), as today.
- Backward compatible: `llm.complete(prompt, system=..., model=..., max_tokens=...)` still works.

**Out (later phases)**
- `ollama` and `vllm` adapters → Phase 10 (the interface is designed so they plug in unchanged).
- `complete_json(prompt, schema)` structured output → Phase 5 (Module B); the interface reserves it.
- Tool use / agent loop → Phase 8.
- Streaming.

## Requirements

1. `src/common/llm.py` public API:
   - `complete(prompt, *, system=None, tier="main", model=None, max_tokens=1024) -> str`
   - An explicit `model=` wins over `tier=` (fix 4).
   - `usage`: cumulative calls and tokens; `last_call()`: provider and model of the last call.
   - `reset_usage()`: clears the counters; an autouse pytest fixture calls it so every test
     starts from zero (fix 5).
2. Provider selection by `LLM_PROVIDER` (default `anthropic`). An unknown name gives a clear error
   listing the valid providers.
3. Each provider declares `name` and `is_external: bool` (`anthropic` = True, `fake` = False;
   later `ollama`/`vllm` = False).
4. **Guard:** if `DATA_CLASSIFICATION=confidential` and the selected provider is external,
   `complete()` raises `DataClassificationError` **before** creating a client or opening any
   network connection.
5. Tier → model mapping in `config.py` per provider, overridable from `.env`
   (e.g. `ANTHROPIC_MODEL_MAIN`, `ANTHROPIC_MODEL_FAST`). `config.MODEL_MAIN` / `MODEL_FAST`
   stay available as aliases for the Anthropic tier models, so existing code keeps working
   (fix 2).
6. No file outside `src/common/providers/` imports `anthropic` (or any provider SDK), not even
   `llm.py`. Enforced by a test (fix 1).
7. `fake` provider returns deterministic text (configurable reply, default echoes a short marker)
   and counts usage, so unit tests never call a real API.
8. `DATA_CLASSIFICATION` defaults to `public` (current phases use public data only). Any value
   other than `public` / `confidential` raises a clear error instead of being ignored (fix 3).

## Inputs / outputs

- Input: `.env` → `LLM_PROVIDER`, `DATA_CLASSIFICATION`, `ANTHROPIC_API_KEY`, optional model
  overrides.
- Output files:
  - `src/common/llm.py` (public API, registry, guard)
  - `src/common/providers/__init__.py`, `base.py` (Protocol, errors), `anthropic_provider.py`,
    `fake_provider.py`
  - `src/common/config.py` (new settings)
  - `.env.example` (new variables, documented)
  - `tests/test_llm_interface.py`

## Acceptance criteria

- [ ] `LLM_PROVIDER=fake`: `llm.complete("hi")` returns the fake reply; `usage.calls == 1`.
- [ ] `LLM_PROVIDER=unknown`: raises a clear error listing the valid providers.
- [ ] `DATA_CLASSIFICATION=confidential` + `LLM_PROVIDER=anthropic`: raises
      `DataClassificationError`, and a test proves **no client was created** (the provider factory
      is never called).
- [ ] `DATA_CLASSIFICATION=confidential` + `LLM_PROVIDER=fake` (non-external): works.
- [ ] `tier="fast"` resolves to the configured fast model for the active provider.
- [ ] `model="x"` together with `tier="fast"` uses `x` (fix 4).
- [ ] `DATA_CLASSIFICATION` unset → `public`; an invalid value raises a clear error (fix 3).
- [ ] `config.MODEL_MAIN` / `MODEL_FAST` equal the Anthropic main/fast models (fix 2).
- [ ] Architecture test: no file under `src/` except `src/common/providers/` imports `anthropic`
      (fix 1).
- [ ] Existing `tests/test_setup.py` still passes (backward compatible), including `-m llm` once
      the API key is added.
- [ ] `ruff check` and `ruff format` clean; all tests pass in the container.
- [ ] DEVLOG step, LEARNING_GUIDE section (provider abstraction / adapter pattern), roadmap tick.

## Technical approach

- **Adapter pattern:** `LLMProvider` Protocol with `name`, `is_external`,
  `complete(request) -> LLMResponse`. A `LLMRequest` dataclass (prompt, system, model, max_tokens)
  and `LLMResponse` (text, input_tokens, output_tokens, model, provider).
- **Registry:** dict `name → factory`; providers are created lazily and cached. The guard runs in
  `complete()` before the factory is called.
- **Settings are read at call time** (not import time), so tests can switch provider with
  `monkeypatch.setenv`.
- No new libraries (only `anthropic`, already in the tech stack).

## Risks

| Risk | Mitigation |
|---|---|
| A local provider URL pointing at an external host would bypass the guard | Phase 11: network isolation (`internal: true`) + allow-list of internal hosts |
| Modules start passing vendor model IDs | Tiers in module code; architecture test |
| Over-engineering too early | Only 2 adapters now; no JSON, tools or streaming until needed |
