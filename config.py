# ================================================================
# Config
# ================================================================
# Objective:
#       Central place for environment variable names, model settings,
#       and filesystem paths used across the agent, workflow, memory,
#       and observability modules.
# Inputs:
#       - Environment variables loaded from .env via python-dotenv
# Outputs:
#       - Module-level constants imported by other modules
# Notes:
#   - No secrets are hardcoded here; only env var names and defaults.
# ================================================================

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
import os

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_store"
LOGS_DIR = PROJECT_ROOT / "logs"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

AZURE_APPINSIGHTS_CONNECTION_STRING = os.environ.get(
    "AZURE_APPINSIGHTS_CONNECTION_STRING", ""
)

MAX_PITCH_REVISIONS = 2


def get_llm() -> ChatOpenAI:
    """Build the shared OpenAI chat model used by all three agents."""
    from langchain_openai import ChatOpenAI

    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)
