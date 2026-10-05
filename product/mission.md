# Product Mission

> Part of the spec-driven development (SDD) setup: [mission](mission.md) · [tech stack](tech-stack.md) · [roadmap](roadmap.md).
> The detailed reference for every stage is [PROJECT_PLAN.md](../PROJECT_PLAN.md).

## Pitch

**EPC Project Intelligence Assistant** helps engineers, document controllers and project-controls
teams on Engineering, Procurement and Construction (EPC) projects **find answers in specifications,
process documents and drawings automatically, and get early warning of cost and schedule overruns**,
using AI/ML and Generative AI built and evaluated on **real public data**.

## Why this project exists

1. **Career goal:** a portfolio project that proves every skill in an AI/ML and GenAI engineer job
   in EPC: LLM apps, RAG, AI agents, intelligent document processing, drawing extraction, and
   project-controls automation.
2. **Business problem:** on lump-sum EPC projects, every hour lost searching documents and every
   late overrun warning comes straight out of the contractor's profit (PMI, *Delivering to Cost
   in an EPC World*).

## Users

| Persona | Role | Pain today | What they get |
|---|---|---|---|
| **Site / design engineer** | Builds or designs to spec | Hours spent searching 100-page specs; misses clauses | Ask a question, get a cited answer (Module A) |
| **Document controller** | Registers and routes documents | Thousands of documents classified and logged by hand; submittal registers built manually | Automatic classification and field extraction (Module B) |
| **Procurement / technical buyer** | Evaluates vendor bids | Manual compliance checks of bids against specs | Extracted requirements, deviation pre-check (Modules A, B) |
| **Process / I&C engineer** | Works with P&IDs | Old drawings only exist as scanned images | Equipment and instrument list plus connectivity extracted from drawings (Module C) |
| **Project controls engineer / PM** | Tracks cost and schedule | Monthly reports take days and arrive late; overruns found too late | Automatic EVM, overrun forecast, risk flags and a written report (Module D) |
| **Everyone** | Needs cross-system answers | Data scattered across systems | One AI agent that combines all modules (Module E) |

## Problems and solutions

| Problem | Solution | Module |
|---|---|---|
| Specs are long, and answers are hard to find and verify | RAG over real UFGS specs, with section and article citations and "not found" refusals | **A** |
| Document sorting, metadata entry and submittal registers are manual | ML and LLM classification plus schema-validated JSON extraction | **B** |
| P&IDs are images, not data | Symbol detection, tag OCR, connectivity graph | **C** |
| Reporting is slow and overruns are discovered late | EVM engine, ML forecast vs. EVM formulas, number-checked LLM report | **D** |
| Questions span several systems | A tool-using Claude agent over modules A–D | **E** |

## Differentiators

- **Real data, not toy data:** UFGS specifications, 133 real projects from the Ghent OR&S
  database, real P&IDs (PID2Graph). Synthetic data is used only where companies never publish
  (RFIs, NCRs, bids), and it's always labeled as synthetic.
- **Measured, not claimed:** every module has a golden set and published metrics (Recall@5,
  macro-F1, MAE, mAP, agent task success).
- **Trustworthy by design:** citations for every factual claim; the LLM never does arithmetic
  (Python computes, the LLM explains); a number guard on generated reports.
- **Domain-grounded:** built on documented EPC knowledge (`docs/01–03`), not generic AI.
- **Reproducible:** runs fully in Docker with locked dependencies (uv).

## Key features

**Core (minimum portfolio: A + D)**
- Spec Q&A with citations (Module A)
- EVM metrics, overrun forecast and automatic monthly report (Module D)

**Extended**
- Document classification and structured extraction (Module B)
- P&ID digitization (Module C)
- Synthetic EPC documents: RFIs, NCRs, daily reports, bids (Stage 7)
- Multi-tool AI agent (Module E)
- Streamlit UI, FastAPI, hosted demo

## Non-goals

- Not a replacement for engineering judgment or approval; it assists, it doesn't decide.
- Not a full EDMS, scheduling tool or ERP.
- No real client or confidential data.
- No training of large models from scratch; we use pretrained models, fine-tuning only for P&ID
  detection.

## Success criteria

| Area | Target |
|---|---|
| Module A | Recall@5 ≥ 0.85 · correctness ≥ 0.85 · citation accuracy ≥ 0.90 |
| Module B | Classification macro-F1 ≥ 0.90 · extraction F1 ≥ 0.85 |
| Module C | Reported mAP@0.5 and equipment-list F1 on real drawings |
| Module D | ML forecast compared with the EVM formula at 20/40/60% complete · 0 unverified numbers in reports |
| Module E | Task success ≥ 80% on 25 scenarios |
| Engineering | Tests in CI, coverage ≥ 70%, Docker-only, every step documented |
| Portfolio | Hosted demo, README with results, demo video |
