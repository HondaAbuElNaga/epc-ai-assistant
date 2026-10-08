# Project rules: EPC Project Intelligence Assistant

Portfolio project for an AI/ML + GenAI engineer role in EPC (engineering, procurement,
construction). Owner: HondaAbuElNaga, a beginner-to-intermediate learner. Explain simply, and
teach while building.

## Session start (no memory between sessions: the files are the memory)
1. Read `product/roadmap.md`, starting with "Current position", to know where the project is.
2. Read the last step in `docs/DEVLOG.md` to see what was done last.
3. Check `specs/` for a spec with status `draft` (awaiting approval) or `approved` (ready to build).
4. Run `git status --short` and `git log --oneline -5`.
5. Start the container if needed: `docker compose up -d`.
Then tell the user where the project is and what the next step is, before doing anything.

## Spec-driven development (SDD)
- Source of truth: `product/mission.md` (why, for whom), `product/tech-stack.md` (approved tools),
  `product/roadmap.md` (order and status). `PROJECT_PLAN.md` is the detailed reference.
- Before coding any roadmap feature: write `specs/<YYYY-MM-DD>-<feature>/spec.md` and `tasks.md`
  (templates in `specs/README.md`) and get them approved.
- Specs are **plain Markdown** only (no spec tooling or generators).
- Every new spec gets its **own git branch**, created from an up-to-date `main` and named after
  the spec folder: `spec/<YYYY-MM-DD>-<feature>`. The spec, its tasks, the code and the docs for
  that feature are all committed on that branch, then merged into `main` with a pull request
  when the feature is done.
- Only use technologies listed in `product/tech-stack.md`; update it first if a new one is needed.
- After a feature: tick it in `product/roadmap.md` and update "Current position".

## Environment
- All work runs inside the Docker `dev` container: `docker compose exec dev <cmd>`.
- Every Python library is managed with **uv** (`uv add`, `uv add --dev`, `uv remove`). Never pip,
  never requirements.txt. Commit `pyproject.toml` and `uv.lock` together.
- Run code and tests with `uv run` inside the container.

## Documentation (mandatory for every change)
1. **docs/DEVLOG.md**: add a new numbered step for every feature, fix or setup change, using the
   template at the bottom of that file (What / Why / How / Files / Verify / Problems & fixes /
   Learn), and add it to the index table.
2. **docs/LEARNING_GUIDE.md**: when a new technology, library or concept is introduced, add or
   extend its section (What / Why / Key concepts / Example / Where / Study).
3. **PROJECT_PLAN.md**: tick the checklist items that are completed; update the plan if the
   approach changes.
4. Each stage gets a detailed guide in `docs/stages/` when the stage starts.

## LLM usage & data security
- Strategy: build with Claude on **public data only**, then move to local models (Stages 13–14).
- All LLM calls go through `src/common/llm.py`; no module imports a provider SDK directly.
- Module code uses model tiers (`main` / `fast`), never vendor model IDs.
- Confidential data must never be sent to an external provider (data classification guard).

## Code
- Python 3.12, ruff (line length 100), tests in `tests/` with pytest.
- Mock the LLM in unit tests; real API tests use the `llm` marker, evaluations use `eval`.
- Before committing: `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`.

## Accuracy & honesty
- Never invent facts, numbers, dataset details or results. Verify (run the code, read the file,
  check the source) before writing them into docs. If something can't be verified, say so.
- Report test and evaluation results exactly as they come out, including failures.

## Git & GitHub
- Remote: https://github.com/HondaAbuElNaga/epc-ai-assistant (public, branch `main`).
- Stage **only files you changed**, by explicit path. Never `git add -A` or `git add .`; the user
  sometimes adds personal files (editor settings, tools). Ask about unknown files.
- Commit identity: `git -c user.email="mldevolpment.tech@gmail.com" -c user.name="HondaAbuElNaga"`.
- The `gh` CLI is at `C:\Program Files\GitHub CLI\gh.exe` (not on the Git Bash PATH).
- Commit and push after each completed feature or doc update.
