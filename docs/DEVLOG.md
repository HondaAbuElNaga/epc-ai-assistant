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
