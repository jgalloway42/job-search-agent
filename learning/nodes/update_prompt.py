"""Node: rewrite config/scoring_prompt.txt based on Gemini's analysis."""

from learning.graph import LearningState

SCORING_PROMPT_PATH = "config/scoring_prompt.txt"


def update_prompt(state: LearningState) -> dict:
    """Ask Gemini to rewrite the scoring prompt using the pattern analysis.

    Sends a second Gemini call instructing it to produce an updated scoring
    prompt incorporating insights from state['analysis']. The new prompt
    must preserve the original output format (JSON array spec) and rubric
    structure. Overwrites config/scoring_prompt.txt atomically.

    Non-fatal errors (e.g. Gemini failure, file write error) are appended
    to state['errors']. On error, the existing prompt file is left intact.

    Args:
        state: Current learning state with 'analysis' populated.

    Returns:
        Partial state dict with 'new_prompt' key set to the written prompt text.
    """
    pass
