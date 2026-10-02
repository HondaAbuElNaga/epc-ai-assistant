# EPC Project Intelligence Assistant

AI/ML and Generative AI toolkit for Engineering, Procurement & Construction (EPC) projects,
built on real public data.

## Modules

| Module | Folder | Data | Status |
|---|---|---|---|
| A. Spec RAG assistant | `src/spec_rag` | UFGS specifications (wbdg.org) | ⏳ Next |
| B. Document classification & extraction | `src/doc_extraction` | UFGS + public tenders | ⬜ |
| C. P&ID drawing extraction | `src/drawings` | PID2Graph, Dataset-P&ID | ⬜ |
| D. Project controls (EVM + forecasting + auto-reports) | `src/project_controls` | Ghent OR&S real project database | ⬜ |
| E. AI agent over all modules | `src/agent` | — | ⬜ |

## Structure

```
data/
  raw/            original downloads (not committed)
    ufgs/         UFGS spec PDFs
    project_controls/  Ghent project database, NYC capital projects
    pid/          P&ID drawing datasets
    osha/         OSHA severe injury reports
  processed/      cleaned / chunked / parsed outputs
  synthetic/      LLM-generated RFIs, bids, daily reports (clearly labeled synthetic)
docs/             EPC study notes, architecture
notebooks/        exploration
src/
  common/         config, LLM client, shared utils
  spec_rag/       Module A
  doc_extraction/ Module B
  drawings/       Module C
  project_controls/ Module D
  agent/          Module E
app/              Streamlit UI
tests/
```

## Setup

All work runs inside Docker. Dependencies are managed with [uv](https://docs.astral.sh/uv/)
(`pyproject.toml` + `uv.lock`). Nothing needs to be installed on the host except Docker.

```bash
copy .env.example .env                 # then add your ANTHROPIC_API_KEY
docker compose up -d --build           # build image + start the dev container
docker compose exec dev bash           # open a shell inside the container
```

Daily commands (run from the host):

| Task | Command |
|---|---|
| Run tests | `docker compose exec dev uv run pytest` |
| Run tests incl. real Claude call | `docker compose exec dev uv run pytest -m llm` |
| Add a library | `docker compose exec dev uv add <package>` |
| Add a dev-only library | `docker compose exec dev uv add --dev <package>` |
| Remove a library | `docker compose exec dev uv remove <package>` |
| Lint / format | `docker compose exec dev uv run ruff check .` / `uv run ruff format .` |
| Run a module | `docker compose exec dev uv run python -m src.<module>` |
| Stop | `docker compose down` |

`uv add` updates `pyproject.toml` and `uv.lock` (commit both). After pulling changes that touch
dependencies, run `docker compose up -d --build`.

## Roadmap

Full A–Z plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)

1. Week 1 – EPC fundamentals (`docs/`)
2. Weeks 2–3 – Module A
3. Week 4 – Module B
4. Weeks 5–6 – Module D
5. Weeks 7–8 – Module C
6. Week 9 – Module E (agent)
7. Week 10 – deploy, docs, demo

## Documentation

| File | Contents |
|---|---|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | All stages A–Z: process, technology, testing, checklists |
| [docs/DEVLOG.md](docs/DEVLOG.md) | Every step taken, how and why, with commands and results |
| [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md) | Study guide for every technology used in the project |
