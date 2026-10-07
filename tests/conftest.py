"""Shared pytest fixtures."""

import pytest

from src.common import llm


@pytest.fixture(autouse=True)
def _fresh_llm_usage():
    """Every test starts with zero LLM usage and no cached provider clients."""
    llm.reset_usage()
    llm.clear_provider_cache()
    yield
