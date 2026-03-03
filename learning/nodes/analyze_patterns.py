"""Node: use Gemini to analyze patterns in application outcomes."""

from learning.graph import LearningState


def analyze_patterns(state: LearningState) -> dict:
    """Ask Gemini to identify what applied/responded jobs had in common.

    Builds a structured prompt from state['applications'] that includes:
        - Jobs applied to (with title, company, score, reason)
        - Which got responses (phone_screen, final_round, offer)
        - Which were rejected or silent

    Sends a single Gemini call via ChatGoogleGenerativeAI and stores the
    analysis text in state['analysis'].

    Non-fatal errors (e.g. API failure, empty applications list) are
    appended to state['errors'].

    Args:
        state: Current learning state with 'applications' populated.

    Returns:
        Partial state dict with 'analysis' key set to Gemini's response text.
    """
    pass
