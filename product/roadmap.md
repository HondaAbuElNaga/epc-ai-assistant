# Product Roadmap

> SDD roadmap: **what** gets built, in **which order**, and when it counts as **done**.
> Each feature gets a spec in [`specs/`](../specs/README.md) before coding. The detailed process
> for each stage is in [PROJECT_PLAN.md](../PROJECT_PLAN.md).
>
> Effort: **XS** < 1 day · **S** 1–2 days · **M** 3–4 days · **L** ~1 week · **XL** 2+ weeks
> Status: `[x]` done · `[~]` in progress · `[ ]` not started

**Current position:** Phase 0 almost done (API key pending) · Phase 1 material written, study in
progress · **next: Phase 2 (data)**.

---

## Phase 0: Foundation (Stage 0)

**Goal:** a reproducible dev environment and project skeleton.
**Done when:** `docker compose exec dev uv run pytest -m llm` passes.

- [x] Project structure, README, PROJECT_PLAN `XS`
- [x] GitHub repository `XS`
- [x] Docker + uv environment (`Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `uv.lock`) `S`
- [x] `src/common/config.py`, `src/common/llm.py` `XS`
- [x] Setup tests + ruff `XS`
- [x] Documentation system: DEVLOG, LEARNING_GUIDE, CLAUDE.md `S`
- [x] SDD product docs: mission, tech stack, roadmap `XS`
- [ ] `.env` with API key; real Claude test call passes `XS`

## Phase 1: Domain Knowledge (Stage 1)

**Goal:** understand EPC well enough to explain every module's business value.
**Done when:** the stage guide checklist is complete.

- [x] `docs/01_epc_fundamentals.md`, `02_glossary.md`, `03_evm_formulas.md`, stage guide `M`
- [ ] Study the material (5-day plan), open one real UFGS spec, solve the EVM exercises `L`

## Phase 2: Real Data (Stage 2)

**Goal:** all datasets downloaded, catalogued, profiled and integrity-tested.
**Done when:** `DATA_CATALOG.md` is complete and the data tests pass.

- [ ] UFGS download script (divisions 01, 03, 05, 22, 23, 26, 33) `S`
- [ ] Ghent project database: download, inspect format, loader `S`
- [ ] PID2Graph + Dataset-P&ID download `XS`
- [ ] OSHA + NYC capital projects (optional) `XS`
- [ ] `data/DATA_CATALOG.md` + checksums `XS`
- [ ] Profiling notebook per dataset `S`
- [ ] `tests/test_data_integrity.py` `XS`

## Phase 3: Module A, Spec RAG (Stage 3), core

**Goal:** ask a question, get a correct, cited answer from real specs.
**Done when:** Recall@5 ≥ 0.85, correctness ≥ 0.85, citation accuracy ≥ 0.90.

- [ ] Spec parser (sections, PART 1/2/3, articles) `M`
- [ ] Structure-aware chunker with metadata `S`
- [ ] Embedding + ChromaDB index `S`
- [ ] Hybrid retrieval (vector + BM25 + RRF) + reranker `M`
- [ ] Cited answer generation with refusal `S`
- [ ] CLI: `python -m src.spec_rag.cli "..."` `XS`
- [ ] Golden set (50+ questions) + evaluation report `M`

## Phase 4: Module D, Project Controls (Stage 5), core

**Goal:** EVM, overrun forecast and automatic report on 133 real projects.
**Done when:** forecast comparison table published; reports pass the number guard.

- [ ] Ghent data loader + pandera schema `S`
- [ ] EVM engine (incl. earned schedule) + unit tests from `docs/03_evm_formulas.md` `S`
- [ ] Forecast models vs. EVM baseline (LOOCV, 20/40/60%) `L`
- [ ] Risk flags `XS`
- [ ] Monthly report: facts JSON → LLM narrative → number guard → charts `M`

> **Milestone: Minimum Portfolio (A + D).** Light Streamlit page + README results. Shareable.

## Phase 5: Module B, Document Intelligence (Stage 4)

**Goal:** classify documents and extract structured fields.
**Done when:** macro-F1 ≥ 0.90; extraction F1 ≥ 0.85.

- [ ] Labeled dataset from UFGS divisions (grouped split) `S`
- [ ] 3 classifiers compared (TF-IDF+LR, embeddings+LR, Claude) `M`
- [ ] Pydantic extraction schema + pipeline (standards, materials, submittals SD-01…SD-11) `M`
- [ ] 30 hand-labeled extractions + evaluation report `S`

## Phase 6: Synthetic EPC Documents (Stage 7)

**Goal:** realistic, labeled RFIs, NCRs, daily reports and bids grounded in real specs.

- [ ] Templates + generator + schema validation `M`
- [ ] Diversity and realism checks `S`

## Phase 7: Module C, P&ID Reader (Stage 6)

**Goal:** P&ID image → equipment list + connectivity graph.
**Done when:** mAP and equipment-list F1 reported on real drawings.

- [ ] Annotation conversion + tiling `M`
- [ ] YOLO training on Colab `L`
- [ ] Tag OCR + linking to symbols `M`
- [ ] Line detection + NetworkX graph `L`

## Phase 8: Module E, AI Agent (Stage 8)

**Goal:** one agent answers multi-step EPC questions using modules A–D.
**Done when:** ≥ 80% success on 25 scenario tasks.

- [ ] Tool wrappers `S`
- [ ] Agent loop with logging and limits `M`
- [ ] 25-task evaluation `M`

## Phase 9: Product & Delivery (Stages 9–12)

**Goal:** a usable, deployed, documented product.

- [ ] Streamlit app (5 pages) `L`
- [ ] FastAPI (optional) `M`
- [ ] GitHub Actions CI, coverage ≥ 70% `S`
- [ ] Production Docker image + hosted demo with usage limits `M`
- [ ] Final README with results, demo video, LinkedIn post, interview notes `M`

---

## Timeline (3–4 hours a day)

| Weeks | Phases |
|---|---|
| 1 | 0, 1, 2 |
| 2–3 | 3 (Module A) |
| 4–5 | 4 (Module D) → **Minimum Portfolio** |
| 6 | 5 (Module B) |
| 7 | 6 (synthetic) |
| 7–8 | 7 (Module C) |
| 9 | 8 (agent) |
| 10 | 9 (product) |
| 11–12 | Buffer |

> Order change vs. PROJECT_PLAN: Module D comes **before** Module B so the minimum portfolio
> (A + D) is reached sooner.
