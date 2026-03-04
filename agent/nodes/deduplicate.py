"""Node: filter out job listings already seen in previous pipeline runs.

Uses the ATS job_id as the deduplication key. Never uses title or URL,
as both can change without the underlying job changing.
"""

import config.settings as settings
import database.db as db
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
    errors: list[str] = list(state.get("errors", []))
    new_jobs: list[dict] = []

    for job in state["raw_listings"]:
        try:
            if not db.is_seen(settings.DB_PATH, job["job_id"]):
                new_jobs.append(job)
        except Exception as e:
            errors.append(f"Dedup error for {job.get('job_id', 'unknown')}: {e}")

    if new_jobs:
        try:
            db.insert_jobs(settings.DB_PATH, new_jobs)
        except Exception as e:
            errors.append(f"DB insert error: {e}")

    return {"deduplicated": new_jobs, "errors": errors}
