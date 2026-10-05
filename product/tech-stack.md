# Tech Stack

> SDD source of truth for technology choices. Change this file **before** adopting a new tool.
> Learning material for each item: [docs/LEARNING_GUIDE.md](../docs/LEARNING_GUIDE.md).
> Status: ✅ in use · 🔜 planned (stage).

## Environment & tooling

| Area | Choice | Version / detail | Status | Why |
|---|---|---|---|---|
| Runtime | Docker + Docker Compose | `dev` service, image `epc-ai-assistant:dev` | ✅ | One identical environment everywhere; no host Python |
| Base image | `python:3.12-slim` | Python 3.12 | ✅ | Wide ML library support |
| Package manager | **uv** | 0.12.2 (copied from `ghcr.io/astral-sh/uv`) | ✅ | Fast, locked (`uv.lock`); **the only way to add libraries** |
| Project file | `pyproject.toml` (`package = false`) | main deps + `dev` group | ✅ | Single config for deps, pytest, ruff |
| Virtualenv | `/opt/venv` inside the container | `UV_PROJECT_ENVIRONMENT` | ✅ | Not hidden by the `/app` bind mount |
| Version control | Git + GitHub (`gh` CLI) | github.com/HondaAbuElNaga/epc-ai-assistant | ✅ | History, portfolio, CI |
| Editor | VS Code + Dev Containers extension | — | ✅ | Edit and run inside the container |
| GPU training | Google Colab / Kaggle | only exception to Docker-only | 🔜 Stage 6 | Free GPU for YOLO |

## Core libraries

| Area | Choice | Status | Notes |
|---|---|---|---|
| LLM SDK | `anthropic` | ✅ | Wrapped in `src/common/llm.py` (retries, token usage) |
| Main model | `claude-sonnet-5-5` | ✅ | Answers, reasoning, agent, reports |
| Fast model | `claude-haiku-4-5` | ✅ | Bulk extraction, classification, cheap evaluation |
| Config | `python-dotenv` | ✅ | `.env` → `src/common/config.py` |
| Data | `pandas`, `numpy` | ✅ | Tables, EVM |
| Validation | `pydantic` | ✅ | LLM output schemas, API models |
| HTTP | `requests`, `tqdm` | ✅ | Dataset downloads |
| Data validation | `pandera` | 🔜 Stage 2 | DataFrame schemas |

## Module-specific

| Module | Choice | Status |
|---|---|---|
| A: PDF parsing | PyMuPDF (`pymupdf`); Docling as an optional upgrade | 🔜 Stage 3 |
| A: Embeddings | `sentence-transformers` + `BAAI/bge-small-en-v1.5` (PyTorch **CPU** build via a uv index) | 🔜 Stage 3 |
| A: Vector DB | ChromaDB (persistent, local) | 🔜 Stage 3 |
| A: Keyword search | `rank-bm25`; hybrid with RRF | 🔜 Stage 3 |
| A: Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | 🔜 Stage 3 |
| B: Classical ML | scikit-learn (TF-IDF + Logistic Regression) | 🔜 Stage 4 |
| B: Extraction | Claude tool use / structured output + Pydantic | 🔜 Stage 4 |
| D: Forecasting | scikit-learn, XGBoost | 🔜 Stage 5 |
| D: Charts | matplotlib / plotly | 🔜 Stage 5 |
| C: Detection | Ultralytics YOLO (AGPL-3.0) | 🔜 Stage 6 |
| C: Image processing | OpenCV | 🔜 Stage 6 |
| C: OCR | PaddleOCR or EasyOCR | 🔜 Stage 6 |
| C: Graph | NetworkX | 🔜 Stage 6 |
| E: Agent | Claude tool use (custom loop, no framework) | 🔜 Stage 8 |

## Application

| Area | Choice | Status |
|---|---|---|
| UI | Streamlit (port 8501) | 🔜 Stage 9 |
| API | FastAPI + Uvicorn (port 8000) | 🔜 Stage 9 (optional) |
| Notebooks | JupyterLab via `uv run --with jupyterlab` (port 8888) | ✅ available |

## Quality & delivery

| Area | Choice | Status |
|---|---|---|
| Tests | pytest, pytest-cov; markers `llm` (real API) and `eval` (golden sets) | ✅ |
| Lint / format | ruff (line length 100; rules E, F, I, B, UP) | ✅ |
| Type check | mypy | 🔜 optional |
| CI | GitHub Actions + `astral-sh/setup-uv` | 🔜 Stage 10 |
| Deploy | Multi-stage Dockerfile (`prod`, `--no-dev`, non-root) → Hugging Face Spaces or Streamlit Community Cloud | 🔜 Stage 11 |

## Data sources

| Dataset | Use | License | Status |
|---|---|---|---|
| UFGS (wbdg.org) | A, B | Public domain (U.S. government) | 🔜 Stage 2 |
| Ghent OR&S real project database | D | Free for research; cite the authors | 🔜 Stage 2 |
| NYC Open Data capital projects | D (extra) | Open data | 🔜 Stage 2 |
| PID2Graph (Zenodo) | C | Check the Zenodo record | 🔜 Stage 2 |
| Dataset-P&ID (Paliwal et al.) | C | Research use | 🔜 Stage 2 |
| OSHA Severe Injury Reports | B (bonus) | Public | 🔜 Stage 2 |

## Conventions

- All commands run as `docker compose exec dev uv run …`. Never use pip, requirements.txt or a
  host venv.
- Add a dependency: `docker compose exec dev uv add <pkg>` (`--dev` for tooling), then commit
  `pyproject.toml` and `uv.lock`.
- Code: `src/<module>/` packages with a small public API; tests in `tests/`; final code never
  lives in notebooks.
- The LLM never computes numbers; every factual answer is cited.
- Secrets only in `.env` (git-ignored) or platform secrets.
- Raw data is never modified (`data/raw` → scripts → `data/processed`).
