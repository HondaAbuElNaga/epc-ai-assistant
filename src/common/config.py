"""Project-wide paths and settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Sonnet for reasoning/answers, Haiku for cheap bulk extraction
MODEL_MAIN = os.getenv("MODEL_MAIN", "claude-sonnet-5-5")
MODEL_FAST = os.getenv("MODEL_FAST", "claude-haiku-4-5")
