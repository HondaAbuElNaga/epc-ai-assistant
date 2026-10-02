"""Stage 0: the environment is ready."""

import importlib
import sys

import pytest

from src.common import config


def test_python_version():
    assert sys.version_info[:2] == (3, 12)


@pytest.mark.parametrize(
    "module", ["anthropic", "numpy", "pandas", "pydantic", "dotenv", "requests", "tqdm"]
)
def test_dependencies_import(module):
    importlib.import_module(module)


def test_project_paths_exist():
    for path in (config.RAW_DIR, config.PROCESSED_DIR, config.SYNTHETIC_DIR):
        assert path.is_dir(), path


@pytest.mark.llm
def test_claude_call():
    if not config.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")
    from src.common import llm

    reply = llm.complete("Reply with exactly the word: OK", model=config.MODEL_FAST, max_tokens=10)
    assert "OK" in reply
    assert llm.usage.calls == 1
