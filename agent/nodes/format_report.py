"""Node: build the HTML email digest from scored job listings.

Groups jobs by tier (1 → 4), formats each listing with title, company,
score, reason, and apply link, and appends any non-fatal errors to the footer.
"""

from agent.state import AgentState


def format_report(state: AgentState) -> dict:
    """Build the HTML email body from state['scored_jobs'].

    Groups jobs by their tier field (ascending). Each job card includes:
        - Job title (linked to url)
        - Company name and location
        - Fit score (e.g. 8/10)
        - One-sentence reason from Gemini
        - Direct apply link button

    If scored_jobs is empty, returns a brief "no new matches today" HTML body.
    Any messages in state['errors'] are rendered in the email footer.

    Args:
        state: Current agent state with 'scored_jobs' and 'errors' populated.

    Returns:
        Partial state dict with 'report' key set to the HTML string.
    """
    ...
