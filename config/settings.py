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
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return val


# --- Secrets ---

GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GMAIL_ADDRESS: str = _require("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD: str = _require("GMAIL_APP_PASSWORD")
DIGEST_EMAIL: str = _require("DIGEST_EMAIL")

# --- Tuning ---

SCORE_THRESHOLD: int = int(os.getenv("SCORE_THRESHOLD", "6"))

# --- Paths ---

DB_PATH: str = _require("DB_PATH")
