"""Shared pytest fixtures and environment setup.

Sets required env vars at module level so config.settings imports cleanly
in all test files — must appear before any node/graph imports.
"""

import os

# Set required env vars before any production module is imported.
# Tests that need different values override via monkeypatch.
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GMAIL_ADDRESS", "test@example.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "testpassword1234")
os.environ.setdefault("DIGEST_EMAIL", "recipient@example.com")
os.environ.setdefault("DB_PATH", "/tmp/test-job-agent.db")
