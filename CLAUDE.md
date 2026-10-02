# Project rules: EPC Project Intelligence Assistant

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

## Code
- Python 3.12, ruff (line length 100), tests in `tests/` with pytest.
- Mock the LLM in unit tests; real API tests use the `llm` marker, evaluations use `eval`.
- Before committing: `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`.
