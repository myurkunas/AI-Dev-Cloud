"""Configuration, read from environment variables (with optional .env support).

Nothing secret is hard-coded. See .env.example for the available settings.
"""

import os

try:  # Load a local .env file if python-dotenv is installed. Optional.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is a convenience, not required.
    pass

# Project layout
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_PATH = os.getenv("CORPUS_PATH", os.path.join(BASE_DIR, "data", "corpus.json"))

# Model access (only used when the Claude backend is active)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

# Retrieval settings
TOP_K = int(os.getenv("TOP_K", "3"))
# Minimum retrieval score for an answer to count as "supported" by our sources.
SUPPORT_THRESHOLD = float(os.getenv("SUPPORT_THRESHOLD", "1.0"))
# A passage is only cited if its score is at least this fraction of the best
# passage's score — keeps loosely-related pages out of the citations.
SUPPORT_RATIO = float(os.getenv("SUPPORT_RATIO", "0.5"))

# Generation backend: "stub", "claude", or "auto".
# "auto" uses Claude when ANTHROPIC_API_KEY is set, otherwise the stub.
GENERATION_BACKEND = os.getenv("GENERATION_BACKEND", "auto")
