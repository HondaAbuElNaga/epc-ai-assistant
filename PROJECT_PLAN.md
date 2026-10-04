# EPC Project Intelligence Assistant: Full Project Plan (A to Z)

This is the master plan for the whole project. It covers every stage, the process inside each
stage, the technology, the data, how each part is tested, and what "done" means.
Tick the checkboxes as you go.

---

## Table of Contents

0. [Project Overview](#0-project-overview)
1. [System Architecture](#1-system-architecture)
2. [Technology Stack](#2-technology-stack)
3. [Timeline](#3-timeline)
4. [Stage 0: Environment Setup](#stage-0-environment-setup)
5. [Stage 1: EPC Domain Fundamentals](#stage-1-epc-domain-fundamentals)
6. [Stage 2: Data Acquisition](#stage-2-data-acquisition)
7. [Stage 3: Module A, Spec RAG Assistant](#stage-3-module-a-spec-rag-assistant)
8. [Stage 4: Module B, Document Classification and Extraction](#stage-4-module-b-document-classification-and-extraction)
9. [Stage 5: Module D, Project Controls](#stage-5-module-d-project-controls)
10. [Stage 6: Module C, P&ID Drawing Extraction](#stage-6-module-c-pid-drawing-extraction)
11. [Stage 7: Synthetic EPC Documents](#stage-7-synthetic-epc-documents)
12. [Stage 8: Module E, AI Agent](#stage-8-module-e-ai-agent)
13. [Stage 9: User Interface and API](#stage-9-user-interface-and-api)
14. [Stage 10: Testing Strategy (All Stages)](#stage-10-testing-strategy-all-stages)
15. [Stage 11: Deployment](#stage-11-deployment)
16. [Stage 12: Documentation and Portfolio](#stage-12-documentation-and-portfolio)
17. [Risks and Mitigations](#risks-and-mitigations)
18. [Job Description Mapping](#job-description-mapping)
19. [Master Checklist](#master-checklist)

---

## 0. Project Overview

**Goal:** build a portfolio-grade AI system that solves real EPC problems using real public data:

| Problem in EPC companies | What this project builds |
|---|---|
| Engineers spend hours searching long specifications | **Module A:** a RAG assistant that answers questions from specs, with citations |
| Thousands of documents need sorting and data entry | **Module B:** a document classifier and a structured-data extractor |
| Old drawings exist only as images or PDFs | **Module C:** a P&ID reader that produces an equipment list and a connection graph |
| Project controls reporting is manual and late | **Module D:** earned value calculation, overrun prediction, and automatic monthly reports |
| Information is scattered across systems | **Module E:** an AI agent that uses all of the modules as tools |

**Success criteria for the whole project:**
- Each module runs end to end on real data.
- Each module has measured accuracy (numbers in the README, not claims).
- One UI demonstrates everything.
- The code is tested and the repository is clean and documented.
- There is a 3–5 minute demo video.

---

## 1. System Architecture

```
                         ┌───────────────────────────┐
                         │   Streamlit UI / FastAPI   │  (Stage 9)
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │   Module E: AI Agent      │  (Stage 8)
                         │   Claude + tool use       │
                         └──┬────────┬────────┬────┬─┘
             ┌──────────────┘        │        │    └───────────────┐
             ▼                       ▼        ▼                    ▼
   ┌──────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
   │ A: Spec RAG      │ │ B: Doc classify│ │ C: P&ID reader │ │ D: Project       │
   │ parse→chunk→embed│ │   & extract    │ │ detect→OCR→    │ │   controls       │
   │ →retrieve→answer │ │ ML + LLM JSON  │ │   graph        │ │ EVM→ML→report    │
   └────────┬─────────┘ └───────┬────────┘ └───────┬────────┘ └────────┬─────────┘
            ▼                   ▼                  ▼                   ▼
     ChromaDB (vectors)   processed JSON     detections/graphs    pandas / parquet
            ▲                   ▲                  ▲                   ▲
            └───────────────────┴──────┬───────────┴───────────────────┘
                                       │
                          data/raw  (UFGS, PID2Graph, Ghent DB, OSHA)
                          data/synthetic (generated RFIs, bids, daily reports)
```

**Design rules:**
1. Each module is a plain Python package with a small public API (for example `spec_rag.ask(question)`). The UI and the agent call these functions and never reach into a module's internals.
2. **The LLM never does arithmetic.** Python computes the numbers and the LLM only explains them.
3. Every LLM answer that states facts must cite a source (a spec section, a document ID, or a project ID).
4. Raw data is never modified. Processing scripts read from `raw/` and write to `processed/`, so they can be re-run at any time.

---

## 2. Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.12 (inside the container) | Most libraries support it |
| Environment | **Docker** + Docker Compose: all work runs inside the `dev` container | Same environment on every machine; nothing installed on Windows except Docker |
| Dependencies | **uv** (`pyproject.toml` + `uv.lock`). Every library is added with `uv add`; no pip, no requirements.txt | Fast, locked, reproducible |
| LLM | Claude API (`anthropic` SDK): `claude-sonnet-5-5` for reasoning and answers, `claude-haiku-4-5` for cheap bulk extraction | Strong document understanding and tool use |
| PDF parsing | PyMuPDF (`fitz`); Docling as an optional upgrade for tables | Fast and accurate on text PDFs |
| Embeddings | `sentence-transformers` (`BAAI/bge-small-en-v1.5` to start) | Free and runs locally |
| Vector DB | ChromaDB (local, persistent) | No server needed |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Improves retrieval precision |
| Classical ML | scikit-learn, XGBoost | Baselines and forecasting |
| Validation | Pydantic (LLM output schemas), pandera (dataframes) | Catches bad data early |
| Computer vision | Ultralytics YOLO, OpenCV | Symbol detection and line detection |
| OCR | PaddleOCR or EasyOCR | Reading tag numbers on drawings |
| Graphs | NetworkX | P&ID connectivity |
| UI | Streamlit | Fast demo UI |
| API | FastAPI | Clean service layer (optional) |
| Testing | pytest, pytest-cov | Unit and integration tests |
| Code quality | ruff (lint and format), mypy (optional) | Clean code |
| CI | GitHub Actions | Runs tests on every push |
| Deployment | Production Docker image, Streamlit Community Cloud or Hugging Face Spaces | Free hosting |
| GPU (Module C) | Google Colab or Kaggle (the only work done outside the container; install there with `uv pip install`) | Free GPU for YOLO training |

---

## 3. Timeline

Assumes 3–4 hours a day.

| Week | Stage | Main output |
|---|---|---|
| 1 | Stage 0 + 1 + 2 | Environment ready, EPC notes, all data downloaded |
| 2–3 | Stage 3 (Module A) | Spec RAG with an evaluation report |
| 4 | Stage 4 (Module B) | Classifier and extractor with metrics |
| 5–6 | Stage 5 (Module D) | EVM engine, forecast model, auto-report |
| 7–8 | Stage 6 (Module C) | P&ID detection, OCR and graph |
| 8 | Stage 7 | Synthetic EPC documents (done in parallel) |
| 9 | Stage 8 (Module E) | Agent with evaluation scenarios |
| 10 | Stage 9 + 11 + 12 | UI, deployment, README, demo video |
| 11–12 | Buffer | Fixes, improvements, interview preparation |

**Fast track (5–6 weeks):** Stages 0–3, then Stage 5, then a light Stage 9.

---

## Stage 0: Environment Setup

**Goal:** a clean, reproducible development environment.

**Process:**
**Rule: all work runs inside the Docker `dev` container, and every library is managed with uv.**

1. Start Docker Desktop.
2. Create an API key at console.anthropic.com, then `copy .env.example .env` and paste the key.
3. Build and start the container:
   ```
   cd D:\claude\EPC\epc-ai-assistant
   docker compose up -d --build
   docker compose exec dev bash
   ```
4. Project files:
   - `pyproject.toml`: dependencies (main + `dev` group), pytest and ruff settings
   - `uv.lock`: exact locked versions (always commit it)
   - `Dockerfile`: python:3.12-slim + uv; installs dependencies into `/opt/venv` with `uv sync --frozen`
   - `docker-compose.yml`: the `dev` service mounts the project at `/app`, keeps a uv cache volume, and exposes ports 8501 (Streamlit), 8888 (Jupyter) and 8000 (FastAPI)
5. Add libraries only with `docker compose exec dev uv add <package>` (`--dev` for test and lint tools). Never use pip.
6. Create `src/common/config.py` (paths and model names) and `src/common/llm.py` (one wrapper around the Claude client that adds retries, logging and token tracking).
7. VS Code: install the **Dev Containers** extension to edit and run code directly inside the container.
8. Create a GitHub repository and push.

**Testing:**
- `tests/test_setup.py` checks that Python is 3.12, all packages import, the data folders exist, and (with `-m llm`) that one tiny Claude call returns text.
- Run: `docker compose exec dev uv run pytest`, then `docker compose exec dev uv run pytest -m llm`.

**Done when:**
- [ ] `docker compose exec dev uv run pytest` passes
- [ ] The repository is on GitHub with no `.env` committed

---

## Stage 1: EPC Domain Fundamentals

**Goal:** understand the business well enough to explain *why* each module matters in an interview.

**Topics to study and write up in `docs/01_epc_fundamentals.md`:**

| Topic | Key points |
|---|---|
| EPC delivery model | One contractor handles engineering, procurement and construction; compare with EPCM, design-bid-build and design-build |
| Contract types | Lump-sum turnkey (LSTK) vs. reimbursable vs. unit-rate; who carries the risk in each |
| Project lifecycle | Feasibility, FEED (front-end engineering design), detailed engineering, procurement, construction, commissioning, handover |
| Engineering documents | P&IDs, PFDs (process flow diagrams), GA (general arrangement) drawings, isometrics, datasheets, specifications, equipment and line lists |
| Specification structure | MasterFormat divisions (03 = concrete, 05 = metals, 26 = electrical…); each section has PART 1 GENERAL, PART 2 PRODUCTS, PART 3 EXECUTION |
| Procurement documents | Material requisitions, RFQs (requests for quotation), technical bid evaluation, purchase orders, vendor document register, expediting |
| Construction documents | RFIs (requests for information), NCRs (non-conformance reports), daily reports, punch lists, ITPs (inspection and test plans), permits |
| Document control | Revisions (A, B, 0, 1…), transmittals, document numbering, EDMS systems (Aconex, SharePoint) |
| Project controls | WBS, CBS, baseline, earned value (PV, EV, AC, CPI, SPI, EAC, ETC, VAC, TCPI), earned schedule, S-curves, change orders |
| Risk | Risk register, Monte Carlo simulation, contingency |
| The PMI paper | Delivering to cost: early deviation detection, change control, integrated cost and schedule control |

**Deliverables:**
- `docs/01_epc_fundamentals.md`
- `docs/02_glossary.md` (about 120 terms)
- `docs/03_evm_formulas.md` (each formula with a worked numeric example)

**Testing (self-check):**
- [ ] You can explain CPI = 0.85 in plain words ("we get 85 cents of work for every dollar spent")
- [ ] You can name 10 EPC document types and who produces each one
- [ ] You can explain why lump-sum contracts make cost control critical for the contractor

---

## Stage 2: Data Acquisition

**Goal:** all real datasets downloaded, catalogued and checked.

| Dataset | Source | Where it goes | Used by |
|---|---|---|---|
| UFGS specifications (PDF) | https://www.wbdg.org/dod/ufgs | `data/raw/ufgs/` | A, B |
| Ghent OR&S real project database (133 projects, EVM data) | https://www.projectmanagement.ugent.be/research/data | `data/raw/project_controls/ghent/` | D |
| NYC capital projects | NYC Open Data (search "Capital Projects") | `data/raw/project_controls/nyc/` | D (extra) |
| PID2Graph (real P&IDs with annotations) | https://zenodo.org/records/14803338 | `data/raw/pid/pid2graph/` | C |
| Dataset-P&ID (500 synthetic P&IDs) | Link in arXiv paper 2109.03794 | `data/raw/pid/dataset_pid/` | C |
| OSHA Severe Injury Reports | osha.gov, Severe Injury Reports | `data/raw/osha/` | B (bonus) |

**Process:**
1. Write `scripts/download_ufgs.py`: fetch the section list, download the PDFs (start with divisions 01, 03, 05, 22, 23, 26, 33), use polite request delays, and skip files that already exist.
2. Download the Ghent database manually (it may require a form) and unzip it. Then **inspect the file format before writing any code**.
3. Download PID2Graph from Zenodo.
4. Write `data/DATA_CATALOG.md`: for each dataset record the source URL, download date, license, file count, size and known issues.
5. Write a profiling notebook per dataset (`notebooks/00_profile_<dataset>.ipynb`) covering counts, missing values, distributions and sample records.

**Testing:**
- `tests/test_data_integrity.py`:
  - expected folders exist and are not empty
  - every PDF opens without error and has more than 0 pages with text
  - the Ghent data loads, each project has a baseline plus at least one tracking period, and BAC (budget at completion) is greater than 0
  - checksums are stored in `data/checksums.json` and match

**Done when:**
- [ ] All datasets are downloaded and listed in `DATA_CATALOG.md`
- [ ] A profiling notebook exists for each dataset
- [ ] Integrity tests pass

---

## Stage 3: Module A, Spec RAG Assistant

**Goal:** ask a question in plain English and get a correct answer with exact spec section citations.

### Process

**3.1 Parsing** (`src/spec_rag/parse.py`)
- Extract text page by page with PyMuPDF.
- Remove repeated headers and footers, page numbers, and the "UFGS-xx xx xx" banners.
- Detect structure with regular expressions: section number (`03 30 00`), title, PART 1/2/3, article numbers (`1.1`, `2.3.1`).
- Output one JSON file per section: `{section_id, title, division, parts:[{part, articles:[{num, title, text}]}]}`.

**3.2 Chunking** (`src/spec_rag/chunk.py`)
- Chunk by **structure** first (one article = one chunk). Split long articles into pieces of about 400–800 tokens with about 15% overlap.
- Attach metadata to each chunk: section_id, title, division, part, article, page.
- Put a context header at the top of each chunk: `"03 30 00 Cast-in-Place Concrete > PART 3 EXECUTION > 3.9 Curing"`.

**3.3 Embedding and indexing** (`src/spec_rag/index.py`)
- Embed with `bge-small-en-v1.5`, store in a persistent ChromaDB collection, and make indexing re-runnable.

**3.4 Retrieval** (`src/spec_rag/retrieve.py`)
- Hybrid retrieval: vector search plus BM25 keyword search (spec language is very keyword-heavy, e.g. "ASTM C94"). Combine with reciprocal rank fusion.
- Rerank the top 20 with the cross-encoder and keep the top 5.
- Support metadata filters (for example only Division 03).

**3.5 Generation** (`src/spec_rag/answer.py`)
- The prompt tells the model to answer *only* from the context, cite `[section § article]` for each claim, and say "not found in the provided specifications" when the answer isn't there.
- Return `{answer, citations[], retrieved_chunks[]}`.

**3.6 Iteration:** compare chunk sizes, embedding models (bge-small vs. bge-base), hybrid vs. vector-only retrieval, and with vs. without the reranker. Record the results in a table.

### Testing and evaluation

| Test type | What |
|---|---|
| Unit tests | Parser finds the correct section_id, PARTs and articles on 3 known PDFs; the chunker never exceeds the max token count; metadata is complete |
| Golden evaluation set | `tests/golden/spec_qa.jsonl`: **50+ hand-written questions** with the correct answer and the correct section/article. Mix: 30 factual, 10 multi-section, 10 unanswerable |
| Retrieval metrics | Recall@5, MRR (does the right article appear in the top results?) |
| Answer metrics | Correctness (LLM judge plus manual spot check), citation accuracy (is the cited article actually the source?), faithfulness (no claim outside the context), refusal rate on unanswerable questions |
| Regression test | `pytest -m eval` runs the golden set; it fails if Recall@5 or correctness drops below the last saved baseline |

**Target metrics:** Recall@5 ≥ 0.85, correctness ≥ 0.85, citation accuracy ≥ 0.90, ≥ 0.80 correct refusals.

**Done when:**
- [ ] `python -m src.spec_rag.cli "What is the minimum curing period for concrete?"` returns a cited answer
- [ ] Evaluation report saved to `docs/eval_module_a.md` with the experiments table
- [ ] Unit tests and evaluation tests pass

---

## Stage 4: Module B, Document Classification and Extraction

**Goal:** (1) automatically classify a document by discipline or division; (2) extract key fields into validated JSON.

### Process

**4.1 Classification dataset**
- Labels come from UFGS: the division number in the section ID (03, 05, 26…) is the class. No manual labeling is needed.
- Unit = one section, or one page for a harder task.
- Split train/validation/test **by section** (all pages of one section go to the same split) to avoid leakage.

**4.2 Models (simple to advanced, compare all three)**
1. Baseline: TF-IDF + Logistic Regression
2. Embeddings (bge) + Logistic Regression
3. Zero-shot or few-shot Claude classification

**4.3 Extraction** (`src/doc_extraction/extract.py`)
- Define a Pydantic schema, e.g. `SpecSummary{section_id, title, referenced_standards[list], materials[list{name, grade, standard}], tests_required[list], submittals_required[list], key_tolerances[list{parameter, value, unit}]}`.
- Use Claude tool use / structured output so the response matches the schema, then validate it with Pydantic. If validation fails, retry once with the error message.
- Run in batches with Haiku to keep costs down, and cache results to `data/processed/extractions/`.

**4.4 Bonus: OSHA classification.** Classify incident narratives into event type and body part. The dataset already has labels.

### Testing and evaluation

| Test | What |
|---|---|
| Unit tests | Schema validation rejects bad JSON; the label parser maps section IDs to divisions correctly |
| Classification metrics | Accuracy, **macro-F1**, confusion matrix, per-class report on the held-out test set |
| Extraction golden set | **30 sections labeled by hand** → field-level precision, recall and F1 (e.g. did it find every ASTM standard?) |
| Robustness | Scanned or noisy pages, very short sections, mixed-division documents |
| Cost and latency | Tokens and seconds per document for each model |

**Target:** classification macro-F1 ≥ 0.90; extraction F1 ≥ 0.85 on referenced standards.

**Done when:**
- [ ] Comparison table of the 3 classifiers (accuracy, F1, cost, speed)
- [ ] Extraction JSON for every downloaded spec
- [ ] `docs/eval_module_b.md`

---

## Stage 5: Module D, Project Controls

**Goal:** turn raw project tracking data into earned value metrics, forecasts, risk flags and a written monthly report.

### Process

**5.1 Data loading** (`src/project_controls/load.py`)
- Parse the Ghent project files (baseline schedule, activities, tracking periods) into clean tables:
  `projects`, `activities`, `tracking(project_id, period, PV, EV, AC, ...)`.
- Validate them with a pandera schema.

**5.2 EVM engine** (`src/project_controls/evm.py`), implemented as pure Python functions:

| Metric | Formula |
|---|---|
| CV / SV | EV − AC / EV − PV |
| CPI / SPI | EV / AC / EV / PV |
| EAC (typical) | BAC / CPI |
| EAC (combined) | AC + (BAC − EV) / (CPI × SPI) |
| ETC, VAC | EAC − AC, BAC − EAC |
| TCPI | (BAC − EV) / (BAC − AC) |
| Earned schedule ES, SPI(t) | time at which PV = EV; SPI(t) = ES / AT |

**5.3 Forecasting with ML** (`src/project_controls/forecast.py`)
- Task: from the data available at X% complete (20/40/60%), predict the **final cost overrun %** and the **final schedule overrun %**.
- Features: CPI, SPI, SPI(t), their trends (slopes), project size, duration, number of activities, sector, network complexity.
- Models: the EVM formula EAC (baseline to beat), linear regression, random forest, XGBoost.
- With only 133 projects, use **leave-one-out or grouped k-fold cross-validation**, keep models small, and report confidence intervals.
- The key result: *does ML beat the standard EVM formula, and at what stage of the project?*

**5.4 Risk flags:** a rules engine (CPI < 0.9, SPI < 0.9, three falling periods in a row, TCPI > 1.1) plus the model's predicted overrun.

**5.5 Automatic monthly report** (`src/project_controls/report.py`)
- Python computes every number and builds a facts JSON.
- Claude writes the narrative: executive summary, cost status, schedule status, top risks, recommendations.
- **Number guard:** after generation, extract every number in the text and check it exists in the facts JSON. If any doesn't, regenerate.
- Output: Markdown or PDF with an S-curve chart (PV/EV/AC over time) and a CPI/SPI trend chart.

### Testing and evaluation

| Test | What |
|---|---|
| EVM unit tests | Hand-calculated textbook examples (e.g. PV = 100, EV = 90, AC = 120 gives CPI = 0.75, SPI = 0.90); edge cases AC = 0, EV = 0, final period |
| Data tests | pandera schema checks; EV ≤ BAC; periods are in order; no negative costs |
| Forecast metrics | MAE and MAPE of predicted vs. actual final cost, per completion stage; compared against the EVM formula baseline |
| Leakage check | Features at X% complete use only data available at that point |
| Report tests | The number guard has zero unknown numbers; all required sections are present; human review of 5 reports |

**Done when:**
- [ ] EVM metrics computed for all 133 projects
- [ ] Forecast comparison table (ML vs. EVM formula at 20/40/60%)
- [ ] One-command report: `python -m src.project_controls.report --project C2013-05`
- [ ] `docs/eval_module_d.md`

---

## Stage 6: Module C, P&ID Drawing Extraction

**Goal:** P&ID image in, structured equipment and instrument list plus a connectivity graph out.

### Process

**6.1 Data preparation**
- Convert PID2Graph and Dataset-P&ID annotations to YOLO format (one class per symbol type).
- Images are very large, so cut them into **tiles** (e.g. 1024×1024 with overlap) for training and merge the detections back afterwards.
- Split train/validation/test by drawing, not by tile.

**6.2 Symbol detection** (`src/drawings/detect.py`)
- Fine-tune a YOLO model (small size) on Colab.
- Train on synthetic data, then fine-tune and test on real PID2Graph drawings.

**6.3 Text and tag reading** (`src/drawings/ocr.py`)
- OCR on the full drawing; filter tags with regular expressions such as `^[A-Z]{1,4}-?\d{2,4}[A-Z]?$` (P-101, FIC-2001, V-12A).
- Link each tag to the nearest detected symbol.

**6.4 Line detection and graph** (`src/drawings/graph.py`)
- Remove the symbols and text, then detect lines (Hough transform or skeletonization).
- Connect line endpoints to symbols and build a NetworkX graph: nodes are equipment or instruments, edges are pipes or signals.

**6.5 Output:** `equipment_list.csv` (tag, type, location) and `graph.json`, plus an optional Claude vision pass to check ambiguous tags.

### Testing and evaluation

| Test | What |
|---|---|
| Unit tests | Annotation converter round-trip; tiling and merging coordinates are correct; the tag regex accepts and rejects the right strings |
| Detection metrics | mAP@0.5, mAP@0.5:0.95, per-class precision and recall (real vs. synthetic test sets reported separately) |
| OCR metrics | Tag-level exact-match accuracy |
| Graph metrics | Edge precision and recall against PID2Graph ground-truth graphs |
| End-to-end | Equipment list F1 on 10 held-out real drawings |

**Note:** Ultralytics YOLO is AGPL-licensed. That is fine for a portfolio project; mention it in the README.

**Done when:**
- [ ] Detection model trained, with metrics
- [ ] `python -m src.drawings.run path/to/pid.png` outputs a CSV and a graph
- [ ] `docs/eval_module_c.md` with example images of good and bad cases

---

## Stage 7: Synthetic EPC Documents

**Goal:** cover the document types that companies never publish (RFIs, vendor bids, daily reports, NCRs), **clearly labeled as synthetic**.

**Process:**
1. Write templates per document type with realistic fields (based on Stage 1 research).
2. Generate the content with Claude, grounded in real UFGS sections (an RFI about a real spec clause, for example).
3. Build in labels on purpose (type, discipline, urgency, related spec section) so they can be used for supervised evaluation.
4. Vary the style: formal and informal, typos, short and long.
5. Save to `data/synthetic/` with a `README.md` explaining how they were generated.

**Testing:**
- Validate every document against its schema.
- Check diversity: no near-duplicates (embedding similarity < 0.95).
- Read 20 random documents by hand for realism.
- Make sure the spec references point to real sections in the index.

**Use:** extend Module B (classify RFI / NCR / daily report, extract fields) and Module E (the agent links RFIs to spec clauses).

---

## Stage 8: Module E, AI Agent

**Goal:** one assistant that answers multi-step EPC questions by calling the module tools.

### Process

**8.1 Tools** (`src/agent/tools.py`): each one is a thin wrapper around a module's public API:

| Tool | Calls |
|---|---|
| `search_specs(query, division?)` | Module A |
| `classify_document(text)` / `extract_fields(text)` | Module B |
| `read_pid(image_path)` | Module C |
| `get_project_status(project_id)` / `forecast_project(project_id)` / `generate_report(project_id)` | Module D |
| `list_projects(filter)` | Module D |

**8.2 Agent loop** (`src/agent/agent.py`)
- Claude tool use with a system prompt describing the EPC role, the rules (cite sources, never invent numbers) and when to use each tool.
- Limit tool calls (e.g. at most 8 per question) and catch errors so a failed tool returns a message instead of crashing.
- Log every step (tool, input, output, tokens) for debugging and for the demo.

**8.3 Example tasks**
- "Which projects have CPI below 0.9, and what is their forecast overrun?"
- "This RFI asks about concrete slump. What does the spec say, and is the contractor's proposal compliant?"
- "Summarize project C2014-03's status and list the top 3 risks."

### Testing and evaluation

| Test | What |
|---|---|
| Tool unit tests | Each tool returns the documented schema; errors are handled |
| Scenario evaluation | `tests/golden/agent_tasks.jsonl`: **25 tasks**, each with the expected tools and expected facts in the answer |
| Metrics | Task success rate, correct tool selection, average number of tool calls, cost per task, hallucinated-number rate (number guard) |
| Safety | The agent refuses or says "unknown" for out-of-scope questions; tools are read-only |

**Target:** task success ≥ 80%.

---

## Stage 9: User Interface and API

**Streamlit app** (`app/`), with one page per module:
1. **Spec Assistant:** question box, answer, expandable citations showing the source text
2. **Document Analyzer:** upload a PDF or text file, see its class and the extracted JSON
3. **P&ID Reader:** upload an image, see the detections drawn on it and the equipment table
4. **Project Controls:** pick a project, see the S-curve, CPI/SPI trend, forecast and a report download button
5. **Agent Chat:** chat, with the agent's steps visible in an expander

**FastAPI (optional)** (`src/api/main.py`): endpoints `/ask`, `/classify`, `/extract`, `/pid`, `/projects/{id}/status`, `/agent`.

**Testing:**
- API tests with FastAPI's `TestClient`
- A Streamlit smoke test (the app starts and each page renders without errors)
- A manual UI checklist: empty input, a very large file, wrong file type, a slow API response showing a spinner

---

## Stage 10: Testing Strategy (All Stages)

### Test pyramid

| Level | Tool | Runs | Examples |
|---|---|---|---|
| Unit | pytest | Every commit (CI) | Parsers, EVM formulas, regexes, schemas |
| Data | pandera, custom checks | When data changes | Schemas, ranges, duplicates |
| Integration | pytest | Every commit (with mocked LLM) | Parse → chunk → index → retrieve pipeline |
| LLM evaluation | pytest `-m eval` plus golden sets | Manually or nightly (costs money) | RAG accuracy, extraction F1, agent task success |
| End-to-end / UI | Smoke tests plus a manual checklist | Before release | Full user flows |

### Rules
- **Mock the LLM in unit and integration tests** (fixed fake responses) so CI is fast and free.
- **Golden sets are versioned** in `tests/golden/`. Never edit them to make a test pass.
- **Save evaluation results** to `docs/eval_results/<module>_<date>.json` to track progress over time.
- **Coverage target:** ≥ 70% on `src/` (`pytest --cov=src`).
- **CI** (`.github/workflows/ci.yml`): install → ruff → pytest (without evaluation tests).

### Folder layout
```
tests/
  unit/            test_parse.py, test_chunk.py, test_evm.py, test_schemas.py, test_tag_regex.py ...
  integration/     test_rag_pipeline.py, test_report_pipeline.py ...
  eval/            test_eval_rag.py, test_eval_extraction.py, test_eval_agent.py
  golden/          spec_qa.jsonl, extraction_labels.jsonl, agent_tasks.jsonl
  fixtures/        small sample PDFs, images, project files
```

---

## Stage 11: Deployment

**Process:**
1. Add a `prod` stage to the `Dockerfile`: `uv sync --frozen --no-dev`, copy `src` and `app`, run Streamlit as a non-root user.
2. Use a small **demo dataset** (about 30 specs, 10 projects, 5 P&IDs) for the hosted version.
3. Deploy to Hugging Face Spaces or Streamlit Community Cloud, with the API key stored as a platform secret.
4. Add basic usage limits so strangers can't burn through your API credit (password or request cap).
5. Show a cost and token counter in the sidebar.

**Testing:**
- [ ] `docker build` and `docker run` work locally
- [ ] The hosted app passes the smoke checklist
- [ ] There is no API key in the image or the repository

---

## Stage 12: Documentation and Portfolio

**Deliverables:**
1. **README.md:** problem, architecture diagram, demo GIF, results table (all metrics), how to run, datasets and licenses, limitations.
2. **docs/:** EPC notes, one evaluation report per module, a design decisions log (`docs/decisions.md`: what you tried, what worked, why).
3. **Demo video** (3–5 minutes): the problem, then the walkthrough of each module, then the agent.
4. **LinkedIn post or blog article:** "Building an AI assistant for EPC projects with real data."
5. **Interview notes:** for each module, the problem, approach, metrics, what went wrong and what you would do next.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| A library doesn't support the Python version | The container pins Python 3.12, independent of the Windows Python |
| Large images (torch pulls CUDA wheels) | Use the PyTorch CPU index in `[tool.uv.sources]` for the container; GPU training stays on Colab |
| The Ghent data format is complex | Inspect it first; start with the summary data, then the detailed tracking data |
| Small dataset (133 projects) leads to overfitting | Simple models, leave-one-out cross-validation, always compare against the EVM formula baseline |
| UFGS PDF formatting varies | Fallback parser; log sections that failed to parse |
| P&ID detection is weak on real drawings | Train on synthetic data and fine-tune on real; report honestly |
| LLM cost grows | Use Haiku for bulk work, cache every LLM response, use small evaluation subsets during development |
| LLM hallucination | Citations, number guard, refusal tests |
| Scope creep / burnout | Finish A + D first (minimum viable portfolio), then add the rest |

---

## Job Description Mapping

| Job requirement | Where this project shows it |
|---|---|
| Design, develop and deploy AI/ML and GenAI solutions for EPC | Whole project, with deployment in Stage 11 |
| AI-powered automation for engineering and construction workflows | Modules B, C and D (auto-report) |
| LLM applications, RAG, AI agents, intelligent document processing | Module A (RAG), Module E (agent), Module B (IDP) |
| Extract, analyze and classify information from documents, drawings, specs and records | Modules B and C |
| Automate project controls, reporting and document management | Module D, plus classification and routing in Module B |
| Identify opportunities where AI improves productivity | Stage 1 analysis plus the README "business impact" section |

---

## Master Checklist

**Stage 0: Setup**
- [x] Docker `dev` container builds and runs; dependencies managed with uv (`pyproject.toml` + `uv.lock`)
- [ ] `.env` with API key; Claude test call works
- [x] `src/common/config.py`, `src/common/llm.py`
- [x] GitHub repository pushed

**Stage 1: EPC fundamentals**
- [x] `docs/01_epc_fundamentals.md`
- [x] `docs/02_glossary.md`
- [x] `docs/03_evm_formulas.md`

**Stage 2: Data**
- [ ] UFGS downloaded
- [ ] Ghent database downloaded and inspected
- [ ] PID2Graph and Dataset-P&ID downloaded
- [ ] OSHA data downloaded
- [ ] `DATA_CATALOG.md` and profiling notebooks
- [ ] Data integrity tests

**Stage 3: Module A (Spec RAG)**
- [ ] Parser, chunker, indexer
- [ ] Hybrid retrieval and reranker
- [ ] Answer generation with citations
- [ ] Golden set of 50+ questions
- [ ] Evaluation report and experiments table

**Stage 4: Module B (Classification and extraction)**
- [ ] 3 classifiers compared
- [ ] Pydantic extraction schema and pipeline
- [ ] 30 hand-labeled extractions and F1
- [ ] Evaluation report

**Stage 5: Module D (Project controls)**
- [ ] Data loader and pandera schema
- [ ] EVM engine with unit tests
- [ ] Forecast models vs. EVM baseline
- [ ] Risk flags
- [ ] Auto-report with number guard and charts
- [ ] Evaluation report

**Stage 6: Module C (P&ID)**
- [ ] YOLO dataset conversion and tiling
- [ ] Detector trained
- [ ] OCR and tag linking
- [ ] Line detection and graph
- [ ] Evaluation report

**Stage 7: Synthetic documents**
- [ ] RFIs, NCRs, daily reports, bids generated and validated

**Stage 8: Module E (Agent)**
- [ ] Tools wrapped
- [ ] Agent loop with logging
- [ ] 25-task evaluation, ≥ 80% success

**Stage 9: UI and API**
- [ ] Streamlit pages for all modules
- [ ] FastAPI (optional)

**Stage 10: Testing**
- [ ] Unit, integration and evaluation suites
- [ ] Coverage ≥ 70%
- [ ] GitHub Actions CI green

**Stage 11: Deployment**
- [ ] Docker image
- [ ] Hosted demo with usage limits

**Stage 12: Portfolio**
- [ ] Final README with results
- [ ] Demo video
- [ ] LinkedIn or blog post
- [ ] Interview notes
