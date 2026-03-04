"""Node: load all application records and outcomes from the database."""

from learning.graph import LearningState


def load_feedback(state: LearningState) -> dict:
    """Query the database for all logged applications and their outcomes.

    Fetches all rows from the applications table joined with job metadata,
    including fields: job_id, title, company, tier, fit_score, applied_date,
    outcome, outcome_date, notes.

    Non-fatal errors (e.g. empty DB, query failure) are appended to
    state['errors'] and an empty list is returned for applications.

    Args:
        state: Current learning state (errors may already contain entries).

    Returns:
        Partial state dict with 'applications' key populated.
    """
    ...
