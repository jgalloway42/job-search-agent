"""Application settings loaded from environment variables via python-dotenv.

All configuration lives here. No other module should import os.environ or
read .env directly. Never hardcode secrets, paths, or magic strings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """Return the value of a required environment variable.

    Args:
        name: Name of the environment variable.

    Returns:
        The string value of the variable.

    Raises:
        EnvironmentError: If the variable is not set or is empty.
    """
    pass


# --- Secrets ---

GEMINI_API_KEY: str
GMAIL_ADDRESS: str
GMAIL_APP_PASSWORD: str
DIGEST_EMAIL: str

# --- Tuning ---

SCORE_THRESHOLD: int  # minimum fit score (1-10) to include in digest, default 6

# --- Paths ---

DB_PATH: str  # resolved from DB_PATH env var — never hardcoded
