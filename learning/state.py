"""LearningState TypedDict for the weekly learning pipeline."""

from typing import TypedDict


class LearningState(TypedDict):
    """Shared state passed between nodes in the weekly learning pipeline."""

    applications: list[dict]   # all logged applications + outcomes from DB
    analysis: str              # Gemini's pattern analysis text
    new_prompt: str            # rewritten scoring prompt text
    errors: list[str]          # non-fatal runtime errors
