# Development Log

Every step of the project, in order. For each step: **what** was done, **why**, **how**
(exact commands), **files** created or changed, **how to verify** it, and **what to learn** from it.

New steps are added at the bottom. Technologies mentioned here are explained in
[LEARNING_GUIDE.md](LEARNING_GUIDE.md).

---

## Index

| Step | Date | Stage | Title |
|---|---|---|---|
| 1 | 2026-09-29 | Research | Understand the topic: PMI paper and job description |
| 2 | 2026-10-03 | Stage 0 | Create the project folder structure |
| 3 | 2026-10-03 | Planning | Write the A–Z project plan |
| 4 | 2026-10-03 | Stage 0 | Create the GitHub repository |
| 5 | 2026-10-03 | Stage 0 | Docker + uv development environment |
| 6 | 2026-10-03 | Stage 0 | Shared config and Claude client |
| 7 | 2026-10-03 | Stage 0 | Setup tests and code quality checks |
| 8 | 2026-10-03 | Docs | Development log, learning guide and project rules |
| 9 | 2026-10-05 | Stage 1 | EPC domain fundamentals study notes |
| 10 | 2026-10-05 | Process | Spec-driven development: mission, tech stack, roadmap, specs |
| 11 | 2026-10-06 | Strategy | Claude first, then local models + security for confidential data |
| 12 | 2026-10-07 | Stage 0 | Provider-agnostic LLM interface + data classification guard |
| 13 | 2026-10-07 | Stage 0 | API key and first real Claude call (Phase 0 done) |
| 14 | 2026-10-08 | Stage 2 | UFGS downloader: 271 active specification PDFs (13 divisions) |

---

## Step 1: Understand the topic (PMI paper and job description)

**What:** read the PMI paper *Delivering to Cost in an EPC World* (CH2M Hill, 2007) and matched
the job description to EPC business problems.

**Why:** an AI engineer in EPC must understand the business first. Every module in this project
answers a real pain point in EPC companies.

**Key takeaways:**
- EPC = one contractor does Engineering, Procurement and Construction, often at a **fixed price**,
  so cost overruns hit the contractor's profit directly.
- Cost problems start early (in engineering and procurement), so **early warning** is the most
  valuable thing a control system can give.
- Every job bullet maps to a module (see the "Job Description Mapping" section of
  [PROJECT_PLAN.md](../PROJECT_PLAN.md)).

**Data check:** all main datasets were confirmed as public and free: UFGS specs, the Ghent
project database (133 real projects), PID2Graph, Dataset-P&ID, and OSHA reports.

---

## Step 2: Create the project folder structure

**What:** created `D:\claude\EPC\epc-ai-assistant` with a standard layout.

**Why:** a clean structure from day one makes the project easy to navigate and easy for an
interviewer to read. Each module gets its own folder, and raw data is separated from processed
data.

**How:**
```bash
mkdir -p data/raw/{ufgs,project_controls,pid,osha} data/processed data/synthetic
mkdir -p docs notebooks app tests
mkdir -p src/{common,spec_rag,doc_extraction,drawings,project_controls,agent}
touch src/__init__.py src/*/__init__.py tests/__init__.py
```

**Files:**
| File / folder | Purpose |
|---|---|
| `src/<module>/` | One Python package per module |
| `src/*/__init__.py` | Empty file that makes a folder a Python package (so `import src.common` works) |
| `data/raw/` | Original downloads, never modified |
| `data/processed/` | Outputs of our scripts, can be regenerated at any time |
| `data/**/.gitkeep` | Empty placeholder file. Git doesn't save empty folders, so this keeps the folder in the repo. |
| `.gitignore` | Tells git which files to never upload (`.env`, data, caches) |
| `.env.example` | Template for secrets; the real `.env` is never committed |
| `README.md` | Project front page on GitHub |

**Learn:** the raw vs. processed data rule; why secrets go in `.env`; what `.gitignore` does.

---

## Step 3: Write the A–Z project plan

**What:** wrote [PROJECT_PLAN.md](../PROJECT_PLAN.md) with 13 stages (0–12). Each stage has a
goal, process, technology, tests and "done when" criteria.

**Why:** a plan prevents scope creep, gives a clear order of work, and defines measurable
success before any code is written.

**Learn:** read the plan fully once. Every technology in it is explained in
[LEARNING_GUIDE.md](LEARNING_GUIDE.md).

---

## Step 4: Create the GitHub repository

**What:** created the public repository https://github.com/HondaAbuElNaga/epc-ai-assistant and
pushed the code.

**Why:** GitHub is your portfolio. It gives you version history, a backup, and a link to share
with employers.

**How:**
```bash
git init                                   # start version control in the folder
git add -A                                 # stage all files
git commit -m "Initial project structure"  # save a snapshot

winget install --id GitHub.cli -e          # install the GitHub CLI (gh)
gh auth login --web --git-protocol https   # log in with a one-time device code
git branch -M main                         # rename the branch master → main
gh repo create HondaAbuElNaga/epc-ai-assistant --public --source . --remote origin --push
```

**How login works:** `gh auth login --web` shows a one-time code (e.g. `ABCD-1234`). You open
`github.com/login/device`, enter the code and authorize. The token is then stored in the Windows
credential manager (keyring). Always check the address is really `github.com` before entering a
code.

**Verify:** `gh auth status` shows "Logged in as HondaAbuElNaga"; the repo page shows the files.

**Learn:** git basics (init, add, commit, push, branch, remote); what a GitHub token is.

---

## Step 5: Docker + uv development environment

**What:** all work now runs inside a Docker container, and every Python library is managed by uv.

**Why:**
- **Docker:** the same environment on every computer (yours, a server, an interviewer's laptop).
  Windows had Python 3.14, which is too new for some ML libraries. The container uses its own
  Python 3.12, so the Windows version doesn't matter.
- **uv:** a very fast Python package manager. `uv.lock` records the exact version of every
  library, so builds are identical every time.

**Files:**

`pyproject.toml`: the project definition.
```toml
[project]
requires-python = ">=3.12,<3.13"   # Python version allowed
dependencies = ["anthropic", ...]  # libraries the app needs

[dependency-groups]
dev = ["pytest", "ruff", ...]      # libraries only for development (tests, lint)

[tool.uv]
package = false                    # this is an application, not a library to publish
```

`uv.lock`: generated by `uv lock`. Never edit it by hand, and always commit it.

`Dockerfile`: the recipe for the image.
```dockerfile
FROM python:3.12-slim                              # small Linux image with Python 3.12
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/   # copy the uv binary in
ENV UV_PROJECT_ENVIRONMENT=/opt/venv ...           # put the virtualenv OUTSIDE /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen                               # install the exact locked versions
COPY . .
```
- `/opt/venv` is outside `/app`, so the folder mounted from Windows never hides the installed
  libraries.
- `--frozen` means "install exactly what `uv.lock` says, and fail if the lock is out of date".
- Dependencies are copied and installed **before** the code. Docker caches this layer, so
  changing code doesn't reinstall libraries.

`docker-compose.yml`: how to run the container.
- `volumes: .:/app` shares the project folder live: edit on Windows, run in Linux.
- `uv-cache` volume keeps downloaded packages so reinstalls are fast.
- `ports` opens 8501 (Streamlit), 8888 (Jupyter) and 8000 (FastAPI) to your browser.
- `command: uv sync --frozen && sleep infinity` syncs libraries on every start, then keeps the
  container running so you can `exec` into it.
- `env_file: .env` loads your API key into the container.

`.dockerignore`: keeps `.git`, `.env` and the data out of the image (smaller and safer).

**How:**
```bash
uv lock                          # create uv.lock (run once on the host, or inside the container)
docker compose up -d --build     # build the image and start the container
docker compose exec dev bash     # open a shell inside
```

**Daily rule:** add libraries **only** with `docker compose exec dev uv add <package>`.
Never use pip.

**Verify:** `docker compose ps` shows `epc-dev` running.

**Learn:** images vs. containers, layers and caching, volumes, ports, uv vs. pip.

---

## Step 6: Shared config and Claude client

**What:** created `src/common/config.py` and `src/common/llm.py`.

**Why:** every module needs paths and the Claude API. Keeping them in one place means one place
to change models, add retries or count costs.

`config.py`
- Finds the project root with `Path(__file__).resolve().parents[2]`.
- Loads `.env` with `python-dotenv`.
- Defines `RAW_DIR`, `PROCESSED_DIR`, `SYNTHETIC_DIR` and the model names: `MODEL_MAIN`
  (`claude-sonnet-5-5`, for reasoning) and `MODEL_FAST` (`claude-haiku-4-5`, cheap bulk work).
  Both can be overridden from `.env`.

`llm.py`
- `client()` creates the Anthropic client once (a lazy singleton) with `max_retries=3`, and gives
  a clear error if the API key is missing.
- `complete(prompt, system=, model=, max_tokens=)` sends one message and returns the text.
- The `usage` object counts calls and input/output tokens, which we use later to show cost.

**Usage:**
```python
from src.common import llm
answer = llm.complete("Explain CPI in one sentence")
print(answer, llm.usage)
```

**Learn:** environment variables, the Messages API (model, max_tokens, messages, system),
tokens and cost, the singleton pattern.

---

## Step 7: Setup tests and code quality checks

**What:** created `tests/test_setup.py` and configured pytest and ruff in `pyproject.toml`.

**Tests:**
| Test | Checks |
|---|---|
| `test_python_version` | The container runs Python 3.12 |
| `test_dependencies_import` | Every main library imports (one test per library using `parametrize`) |
| `test_project_paths_exist` | The data folders exist |
| `test_claude_call` (marker `llm`) | A real Claude call returns "OK". Skipped when there is no API key. |

**Markers:** `llm` = calls the real API (costs money); `eval` = slow evaluation tests. Run them
only when needed: `uv run pytest -m llm`.

**How:**
```bash
docker compose exec dev uv run pytest -v       # run tests
docker compose exec dev uv run ruff check .    # find code problems
docker compose exec dev uv run ruff format .   # auto-format code
```

**Result:** 9 passed, 1 skipped (no API key yet). Ruff first found 2 lines longer than 100
characters in `llm.py`; `ruff format` fixed them.

**Learn:** pytest basics (test functions, `assert`, `parametrize`, `skip`, markers),
linting vs. formatting.

---

## Step 8: Development log, learning guide and project rules

**What:** created this file (`docs/DEVLOG.md`), [LEARNING_GUIDE.md](LEARNING_GUIDE.md) and
`CLAUDE.md` (project rules).

**Why:** the project should explain itself: what was built, why, and how, plus a study guide
for every technology. `CLAUDE.md` makes these rules permanent for every future step (Docker + uv
only, and log every step here).

---

## Step 9: EPC domain fundamentals study notes (Stage 1)

**What:** wrote the Stage 1 study material: a stage guide, the EPC fundamentals notes, a
glossary and the EVM formulas with worked examples.

**Why:** an AI engineer in EPC must understand the business: which documents exist, who uses
them, how cost and schedule are controlled, and where projects go wrong. Every later module
solves one of the pain points described here.

**Files:**
| File | Contents |
|---|---|
| `docs/stages/stage_01_epc_fundamentals.md` | 5-day study plan, how to study, resources, done criteria |
| `docs/01_epc_fundamentals.md` | 14 sections: EPC, delivery models, contracts, lifecycle, engineering documents, specs (MasterFormat, UFGS, SD codes), procurement, construction, document control, project controls, risk, the PMI paper, AI opportunities, self-check questions |
| `docs/02_glossary.md` | About 120 terms A–Z, tagged by area (GEN/ENG/PRO/CON/DOC/PC/QA) |
| `docs/03_evm_formulas.md` | All EVM formulas, a worked example, earned schedule, rules of credit, interpretation, common mistakes, exercises with answers |

**How:** the EVM example numbers were computed and checked inside the container before writing:
```bash
docker compose up -d
docker compose exec -T dev uv run python - < check.py   # script shown in 03_evm_formulas.md §9
```
Results: CPI 0.8261, SPI 0.7600, EAC 1,210,526, TCPI 1.1481, ES 4.2, SPI(t) 0.84,
IEAC(t) 11.90 months.

**Verify:** every number in `03_evm_formulas.md` matches the Python output; all links between
the docs work.

**Problems & fixes:**
- The PMI paper's full text is members-only (HTTP 403). Section 12 states this clearly and
  summarizes from the abstract only.
- The first `docker compose exec` failed with `service "dev" is not running` (the container had
  stopped). Fixed with `docker compose up -d`.

**Learn:** do the 5-day plan in the stage guide; solve the exercises in `03_evm_formulas.md`;
answer the self-check questions in `01_epc_fundamentals.md` §14.

---

## Step 10: Spec-driven development (SDD) setup

**What:** added three product files (`product/mission.md`, `product/tech-stack.md`,
`product/roadmap.md`) and a feature-spec workflow (`specs/README.md`), built from the README and
PROJECT_PLAN.

**Why:** PROJECT_PLAN is long (660+ lines). SDD gives short, always-current answers to:
*why are we building this* (mission), *with what* (tech stack), *what's next* (roadmap). It also
forces a written spec with acceptance criteria before any code, so features stay small,
testable and documented.

**Files:**
| File | Contents |
|---|---|
| `product/mission.md` | Pitch, users (6 personas), problems → solutions, differentiators, features, non-goals, success criteria |
| `product/tech-stack.md` | Every technology with version, status (in use / planned stage), reason; data sources and licenses; conventions |
| `product/roadmap.md` | 10 phases (0–9) with goals, done criteria, features with effort sizes and status; current position; timeline |
| `specs/README.md` | SDD workflow + `spec.md` and `tasks.md` templates |
| `CLAUDE.md` | New SDD rules: spec before code, only approved tech, tick the roadmap |

**Decision (manual SDD):** GitHub Spec Kit skills had been added to `.claude/skills/`, but
without the `.specify/` folder they need, so they couldn't run. The choice was a simple manual SDD
workflow (`product/` + `specs/<date>-<feature>/spec.md` + `tasks.md`), and the Spec Kit skills
were removed.

**Decision:** the roadmap builds **Module D before Module B**, so the minimum portfolio
(A + D) is ready around week 5 instead of week 6.

**Verify:** all links resolve; the roadmap status matches the DEVLOG (Phase 0 done except the API
key, Phase 1 material written).

**Learn:** LEARNING_GUIDE section 8.7 (Spec-driven development).

---

## Step 11: Strategy: Claude first, then local models and security

**What:** adopted the strategy *build with Claude on public data → move to local models → harden
for confidential data*. Updated the product docs and plan, and wrote the first spec (the
provider-agnostic LLM interface).

**Why:** the system will later be used on confidential company documents that must **never leave
the company**. Research (Oct 2026) showed:
- Only the LLM depends on an external API; embeddings, reranker, parsing, YOLO and OCR are
  already local.
- On an RTX 4060 (8 GB VRAM), 7–9B models at 4-bit (e.g. Qwen3.5-9B) fit fully in the GPU: close to
  Claude for classification and extraction, slightly lower for RAG, clearly weaker for multi-step
  agents. Larger open models on company servers close most of the gap.
- Security is a property of the whole system (isolation, access control, audit), not of the model.

**Files:**
| File | Change |
|---|---|
| `PROJECT_PLAN.md` | Model strategy in the overview; new **Stage 13** (local models, gates per module) and **Stage 14** (10 security layers, each with a test); timeline, risks, job mapping, checklist |
| `product/mission.md` | Confidential-data goal, local-first differentiator, enterprise track, non-goals, success criteria |
| `product/tech-stack.md` | Provider-agnostic interface, data guard, Ollama/vLLM, local models, constrained decoding, HHEM, security tooling |
| `product/roadmap.md` | Phase 0 item (LLM interface), new **Phase 10** (local models) and **Phase 11** (security), timeline |
| `specs/2026-10-06-llm-provider-interface/` | spec.md + tasks.md (status: draft, awaiting approval) |
| `docs/LEARNING_GUIDE.md` | New **Part 10** (13 sections): adapter pattern, data guard, quantization/VRAM, Ollama, vLLM, constrained decoding, HHEM, evaluation gates, network isolation, supply chain, permission-aware retrieval, prompt injection, audit/encryption/auth |
| `CLAUDE.md` | LLM usage & data security rules |

**Verify:** the roadmap, plan and tech stack agree on the phase order: 0–9 with Claude, 10 local,
11 security.

**Learn:** LEARNING_GUIDE Part 10 (start with 10.1 and 10.2, needed for the next feature).

---

## Step 12: Provider-agnostic LLM interface + data classification guard

**What:** rebuilt `src/common/llm.py` so every module calls the LLM through one interface that
does not know which vendor is behind it. Added two providers (`anthropic`, `fake`), model tiers
(`main` / `fast`), and a guard that refuses to send confidential data to an external provider.
Spec: [`specs/2026-10-06-llm-provider-interface/`](../specs/2026-10-06-llm-provider-interface/spec.md)
(approved 2026-10-07 with 5 review fixes).

**Why:** this is what lets the project start with Claude on public data and later switch to local
models (Phase 10) by changing `.env` only. The guard turns the rule "confidential data never
leaves the company" into code that is tested.

**How:**
1. Wrote `tests/test_llm_interface.py` first; it failed (`No module named 'src.common.providers'`).
2. Built `src/common/providers/` (contract, fake, anthropic), then `config.py` and `llm.py`.
3. `complete()` order: read `LLM_PROVIDER` → look up the provider class (unknown name → error
   listing the valid ones) → guard (checks the class's `is_external`, before any client exists)
   → resolve model (`model=` wins, else tier) → create/reuse the provider → call → count usage.
```bash
docker compose exec dev uv run ruff format .
docker compose exec dev uv run ruff check .
docker compose exec dev uv run pytest -v
```

**Files:**
| File | Change |
|---|---|
| `src/common/providers/base.py` | `LLMRequest`, `LLMResponse`, `LLMProvider` Protocol, `DataClassificationError`, `UnknownProviderError` |
| `src/common/providers/anthropic_provider.py` | Claude adapter (the old client code moved here); `is_external = True` |
| `src/common/providers/fake_provider.py` | Offline adapter for tests; reply from `FAKE_LLM_REPLY` or a fixed marker |
| `src/common/providers/__init__.py` | Re-exports the contract and errors |
| `src/common/llm.py` | Registry, guard, tiers, `usage`, `reset_usage()`, `last_call()`; no SDK import |
| `src/common/config.py` | `llm_provider()`, `data_classification()`, `model_for()`, `anthropic_api_key()`; `MODEL_MAIN`/`MODEL_FAST` kept as aliases |
| `.env.example` | Documents `LLM_PROVIDER`, `DATA_CLASSIFICATION`, model overrides |
| `tests/test_llm_interface.py` | 13 tests covering every acceptance criterion, incl. the architecture test |
| `tests/conftest.py` | Autouse fixture: zero usage and no cached providers before each test |
| `pyproject.toml` | ruff `extend-exclude = ["*.md"]` (see Problems & fixes) |

**Verify:** in the container, `ruff check` → `All checks passed!`, `ruff format` → `17 files left
unchanged`, `pytest` → **22 passed, 1 skipped**. The skip is `test_claude_call` (no
`ANTHROPIC_API_KEY` yet); the real-API check is still open.

**Problems & fixes:**
- `ruff format .` (ruff 0.16.10) also reformatted Python code blocks inside Markdown, breaking the
  aligned comments in `docs/03_evm_formulas.md`. Restored the three affected docs with
  `git checkout` and added `extend-exclude = ["*.md"]` to `[tool.ruff]`.
- One line in `config.py` was 102 characters (E501); split it.

**Learn:** LEARNING_GUIDE 10.1 (adapter pattern, now with how it is built here) and 10.2 (data
guard, design choices), 8.4 (ruff Markdown note), 8.2 (mocking with `monkeypatch`).

---

## Step 13: API key and first real Claude call (Phase 0 done)

**What:** added `ANTHROPIC_API_KEY` to `.env` (git-ignored) and ran the real API test through the
new provider interface. This closes Phase 0.

**Why:** Phase 0 is "done when `pytest -m llm` passes": it proves the whole path works,
`llm.complete()` → registry → guard → Anthropic adapter → Claude API.

**How:**
```bash
docker compose up -d --force-recreate   # reload .env into the container
docker compose exec dev uv run pytest -m llm -v
docker compose exec dev uv run pytest
```

**Files:**
| File | Change |
|---|---|
| `.env` | API key (local only, never committed; checked with `git ls-files` and `git log --all -- .env`) |
| `product/roadmap.md` | Phase 0 key item ticked; current position → Phase 2 next |
| `PROJECT_PLAN.md` | Stage 0 "done when" items and checklist ticked |
| `specs/2026-10-06-llm-provider-interface/spec.md` | Last acceptance criterion (`-m llm`) ticked |
| `docs/LEARNING_GUIDE.md` | 1.4 Docker Compose: `env_file` gotcha |

**Verify:** `pytest -m llm` → `1 passed, 22 deselected`; full `pytest` → **23 passed**.

**Problems & fixes:**
1. First run: `400 invalid_request_error`, "Your credit balance is too low to access the
   Anthropic API". The key was accepted, but the account had no API credit (API billing is separate
   from a claude.ai subscription). Fix: add credit in console.anthropic.com → Plans & Billing.
2. Second run: `401 authentication_error`, "API key is invalid". The container still had the
   **old** key: Compose loads `env_file` only when the container is created, and `load_dotenv()`
   does not override an existing variable. Compared the two values (without printing them): not
   equal. Fix: `docker compose up -d --force-recreate`; the values then matched and the test passed.

**Learn:** LEARNING_GUIDE 1.4 Docker Compose (`env_file` gotcha), 9.3 secrets management.

---

## Step 14: UFGS downloader: 271 active specification PDFs (13 divisions)

**What:** a downloader for UFGS (Unified Facilities Guide Specifications) from WBDG. It finds
every section in the sitemap, asks WBDG's API whether each one is still active and where its
current PDF is, downloads only active sections, and writes a manifest. It was built in two
versions:
- **v1** (commit `f0d7d8b`): built each PDF link from the section number.
- **v2:** asks the API first and keeps active sections only.

**Why:** UFGS is the real-specification corpus for Module A (spec RAG) and the labeled data for
Module B (the division is the class). The scope is the 7 building divisions plus the process
divisions 40–46, chosen by the owner on 2026-10-08 because EPC work is mostly industrial and
process plants.

**How:**
```bash
docker compose exec dev uv run python -m src.datasets.ufgs --dry-run     # 705 sections listed
docker compose exec dev uv run python -m src.datasets.ufgs --limit 5 --out /tmp/ufgs_trial
docker compose exec dev uv run python -m src.datasets.ufgs               # full run, 15 min 38 s
docker compose exec dev uv run python -m src.datasets.ufgs               # re-run: nothing new
```
For each section:
1. `GET /api/documents/ufgs-<id>` →
2. if `status` is `ACTIVE`, take the one media file with `isCurrent: true`, `isArchived: false`,
   `.pdf` →
3. stream it to `.part`, check `%PDF`, compute SHA-256, rename →
4. write a manifest entry.

At the end, PDFs of retired sections left over from v1 are deleted.

**Files:**
| File | Change |
|---|---|
| `src/common/http.py` | `PoliteClient`: honest User-Agent, 1 s delay, retries with backoff on 429/5xx, `Retry-After` |
| `src/datasets/ufgs.py` | Sitemap → API check → download → manifest → retired cleanup; CLI |
| `tests/test_ufgs_download.py` | 30 offline tests (fake session) + 2 `network` tests (real API shape, real download) |
| `tests/fixtures/ufgs_sitemap_sample.xml`, `ufgs_api_03-30-00.json` | Sitemap sample; real API answer (trimmed) |
| `pyproject.toml` | `network` marker, not run by default (`addopts = "-m 'not network'"`) |
| `specs/2026-10-07-ufgs-download/` | v1 spec + v2 update (approved), tasks |
| `docs/stages/stage_02_data.md` | Stage 2 guide (new) |
| `docs/LEARNING_GUIDE.md` | 1.9 Web data acquisition, 1.10 Data integrity, 1.11 Web page vs API |
| `PROJECT_PLAN.md`, `product/roadmap.md` | Script location, 13 divisions, item ticked |
| `data/raw/ufgs/<DD>/*.pdf`, `manifest.json` | Data, local only (git-ignored) |

**Verify (real results, 2026-10-08):**

| Div | Name | Sitemap | Active (on disk) | Retired |
|---|---|---|---|---|
| 01 | General Requirements | 83 | 33 | 50 |
| 03 | Concrete | 63 | 23 | 40 |
| 05 | Metals | 39 | 17 | 22 |
| 22 | Plumbing | 42 | 11 | 31 |
| 23 | HVAC | 150 | 52 | 98 |
| 26 | Electrical | 102 | 45 | 57 |
| 33 | Utilities | 120 | 59 | 61 |
| 40 | Process Interconnections | 11 | 4 | 7 |
| 41 | Material Processing and Handling Equipment | 24 | 8 | 16 |
| 42 | Process Heating, Cooling, and Drying Equipment | 7 | **0** | 7 |
| 43 | Process Gas and Liquid Handling, Purification, and Storage | 17 | 2 | 15 |
| 44 | Pollution and Waste Control Equipment | 25 | 2 | 23 |
| 46 | Water and Wastewater Equipment | 22 | 15 | 7 |
| | **Total** | **705** | **271** | **434** |

- Full run: downloaded 32, skipped 239 (already on disk from v1), retired 434, no_pdf 0,
  not_found 0, **error 0**, in 15 min 38 s.
- 21 retired PDFs from v1 were removed. Check: v1 had 260 files, 239 + 21 = 260.
- On disk: **271 PDFs, 37.6 MB**.
  - Every file belongs to an ACTIVE section; every active section has its file.
  - No `.part`/`.tmp` left.
  - All 271 PDF links come from `/FFC/DOD/UFGS/`, none from the archive.
- Publish years of the active sections range from 2006 to 2026; 86 of them are from 2025–2026.
- Re-run: RERUN_RESULT
- `pytest`: 53 passed, 2 deselected. `pytest -m network`: 2 passed. `ruff check` and
  `ruff format`: clean.

**Problems & fixes:**
1. **v1: 339 of 599 sections `not_found` (S3 403).**
   - A sample of 30 showed they were all `RETIRED_SUPERSEDED` with no files: the sitemap lists
     retired sections too.
   - Some PDFs v1 *did* download were retired sections whose old file is still in the bucket.
   - Fix (v2): ask the API for the status and the exact current file; never build or guess a
     link.
2. **The API lists every version of a file** (current, `UFGS_ARCHIVES/`, `documents/…`), plus a
   `.zip` with the editable source. Fix: keep only `isCurrent && !isArchived && .pdf`. If that
   isn't exactly one file, record `error`.
3. **In chat I first said option B adds 112 sections.** That was wrong. It's 106; the 112
   wrongly included division 48. Corrected in the spec before approval.
4. **The background run was reported as "killed" (exit code -1)**, both in v1 and v2. The
   process inside the container kept running and finished; the log ends with the summary. Check
   the log, not the exit code of the wrapper.

**Learn:**
- LEARNING_GUIDE 1.9 Web data acquisition;
- 1.10 Data integrity;
- 1.11 Web page vs API (JSON);
- 8.1 pytest (fakes instead of mocks, markers).

---

## Template for new steps

```markdown
## Step N: <title>

**What:** ...
**Why:** ...
**How:** (exact commands / code)
**Files:** (table of created/changed files and their purpose)
**Verify:** (how to check it works; test results)
**Problems & fixes:** (errors met and how they were solved)
**Learn:** (concepts to study; link to LEARNING_GUIDE sections)
```
