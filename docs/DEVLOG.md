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

**Decision:** the roadmap builds **Module D before Module B**, so the minimum portfolio
(A + D) is ready around week 5 instead of week 6.

**Verify:** all links resolve; the roadmap status matches the DEVLOG (Phase 0 done except the API
key, Phase 1 material written).

**Learn:** LEARNING_GUIDE section 8.7 (Spec-driven development).

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
