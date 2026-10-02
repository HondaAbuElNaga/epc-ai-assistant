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

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then add your ANTHROPIC_API_KEY
```

## Roadmap

Full A–Z plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)

1. Week 1 – EPC fundamentals (`docs/`)
2. Weeks 2–3 – Module A
3. Week 4 – Module B
4. Weeks 5–6 – Module D
5. Weeks 7–8 – Module C
6. Week 9 – Module E (agent)
7. Week 10 – deploy, docs, demo
