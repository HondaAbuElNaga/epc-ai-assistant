"""Project-wide paths and settings.

LLM settings are functions that read the environment at call time, so tests can switch them
with monkeypatch.setenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

DATA_CLASSIFICATIONS = ("public", "confidential")
TIERS = ("main", "fast")

# Default model per provider and tier. Override with <PROVIDER>_MODEL_<TIER> in .env,
# e.g. ANTHROPIC_MODEL_FAST. Anthropic: Sonnet for reasoning/answers, Haiku for bulk extraction.
DEFAULT_MODELS = {
    "anthropic": {"main": "claude-sonnet-5-5", "fast": "claude-haiku-4-5"},
    "fake": {"main": "fake-main", "fast": "fake-fast"},
}


def llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").strip().lower()


def data_classification() -> str:
    value = os.getenv("DATA_CLASSIFICATION", "public").strip().lower()
    if value not in DATA_CLASSIFICATIONS:
        valid = ", ".join(DATA_CLASSIFICATIONS)
        raise ValueError(f"DATA_CLASSIFICATION={value!r} is invalid. Use one of: {valid}")
    return value


def model_for(provider: str, tier: str) -> str:
    if tier not in TIERS:
        raise ValueError(f"Unknown model tier {tier!r}. Use one of: {', '.join(TIERS)}")
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"No models configured for provider {provider!r}")
    override = os.getenv(f"{provider.upper()}_MODEL_{tier.upper()}")
    return override or DEFAULT_MODELS[provider][tier]


def anthropic_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")


# Kept for older code; new module code should use tiers via llm.complete(tier=...)
ANTHROPIC_API_KEY = anthropic_api_key()
MODEL_MAIN = model_for("anthropic", "main")
MODEL_FAST = model_for("anthropic", "fast")
