"""Node: score job listings for fit using Gemini 2.0 Flash.

Batches all deduplicated jobs into a single LLM prompt (never one call per job).
The scoring prompt is loaded from config/scoring_prompt.txt at runtime.
Jobs below settings.SCORE_THRESHOLD are filtered out.
"""

from agent.state import AgentState


def score_filter(state: AgentState) -> dict:
    """Score all deduplicated jobs in a single Gemini API call and filter by threshold.

    Steps:
        1. Load the scoring prompt from config/scoring_prompt.txt.
        2. Build a JSON payload of all jobs in state['deduplicated'].
        3. Call Gemini via ChatGoogleGenerativeAI (one batch request).
        4. Parse the JSON response: list of {job_id, fit_score, reason}.
        5. Merge scores back into the job dicts.
        6. Filter to jobs where fit_score >= settings.SCORE_THRESHOLD.

    Non-fatal errors (e.g. JSON parse failure, partial response) are
    appended to state['errors'].

    Args:
        state: Current agent state with 'deduplicated' populated.

    Returns:
        Partial state dict with 'scored_jobs' and 'errors' keys updated.
    """
    ...
