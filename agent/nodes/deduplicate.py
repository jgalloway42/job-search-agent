"""Node: filter out job listings already seen in previous pipeline runs.

Uses the ATS job_id as the deduplication key. Never uses title or URL,
as both can change without the underlying job changing.
"""

from agent.state import AgentState


def deduplicate(state: AgentState) -> dict:
    """Filter raw_listings to only jobs not yet recorded in the database.

    Queries the database for all seen job IDs, removes any listings whose
    job_id already exists, then inserts the remaining new jobs into the DB
    to mark them as seen for future runs.

    Non-fatal errors (e.g. DB failures per job) are appended to state['errors'].

    Args:
        state: Current agent state with 'raw_listings' populated.

    Returns:
        Partial state dict with 'deduplicated' and 'errors' keys updated.
    """
    ...
