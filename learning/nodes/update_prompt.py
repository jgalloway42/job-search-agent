"""Node: rewrite config/scoring_prompt.txt based on Gemini's analysis."""

import json
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import config.settings as settings
from learning.state import LearningState

_SCORING_PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "scoring_prompt.txt"
_HISTORY_PATH = Path(__file__).parent.parent.parent / "config" / "prompt_history.json"
_MAX_HISTORY = 5


def update_prompt(state: LearningState) -> dict:
    """Ask Gemini to rewrite the scoring prompt using the pattern analysis.

    Sends a second Gemini call instructing it to produce an updated scoring
    prompt incorporating insights from state['analysis']. The new prompt
    must preserve the original output format (JSON array spec) and rubric
    structure. Archives the current prompt to config/prompt_history.json
    (max 5 entries, newest first) before overwriting scoring_prompt.txt.

    Non-fatal errors (e.g. Gemini failure, file write error) are appended
    to state['errors']. On error, the existing prompt file is left intact.

    Args:
        state: Current learning state with 'analysis' populated.

    Returns:
        Partial state dict with 'new_prompt' key set to the written prompt text.
    """
    errors: list[str] = list(state.get("errors", []))

    if not state.get("analysis"):
        errors.append("update_prompt: no analysis available — skipping prompt update")
        return {"new_prompt": "", "errors": errors}

    try:
        current_prompt = _SCORING_PROMPT_PATH.read_text()

        rewrite_prompt = f"""You are updating a job-fit scoring prompt based on observed application outcomes.

## Current scoring prompt:
{current_prompt}

## Pattern analysis from recent applications:
{state["analysis"]}

Rewrite the scoring prompt to incorporate the insights above. Requirements:
- Preserve the exact output format specification (JSON array with job_id, fit_score, reason fields)
- Preserve the scoring rubric structure (1-10 scale with the same tier definitions)
- Update the candidate profile and/or scoring criteria based on the analysis
- Keep the same overall length and structure
- Return ONLY the full updated prompt text, nothing else"""

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
        )
        response = llm.invoke([HumanMessage(content=rewrite_prompt)])
        new_prompt_text = str(response.content)

        # Load existing history (default to empty list if missing or corrupt)
        history: list[dict] = []
        if _HISTORY_PATH.exists():
            try:
                history = json.loads(_HISTORY_PATH.read_text())
            except (json.JSONDecodeError, OSError):
                history = []

        # Prepend current prompt as newest history entry, then trim
        history.insert(0, {
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "prompt": current_prompt,
        })
        history = history[:_MAX_HISTORY]

        _HISTORY_PATH.write_text(json.dumps(history, indent=2))
        _SCORING_PROMPT_PATH.write_text(new_prompt_text)

        return {"new_prompt": new_prompt_text, "errors": errors}

    except Exception as e:
        errors.append(f"update_prompt error: {e}")
        return {"new_prompt": "", "errors": errors}
