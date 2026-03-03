"""SQLite database wrapper for the job search agent.

All database access in this project goes through this module. Nodes and
CLI commands import these functions directly — they never import sqlite3.
The DB path always comes from settings.DB_PATH (loaded from env), never
hardcoded.

Schema:
    jobs         — all seen job listings with scores
    applications — logged applications and outcome tracking
"""

import sqlite3
from typing import Any

from agent.state import JobListing


def init_db(db_path: str) -> None:
    """Create the database schema if it does not already exist.

    Creates the 'jobs' and 'applications' tables using IF NOT EXISTS,
    so it is safe to call on every startup.

    Schema:
        jobs(job_id PK, company, title, location, url, posted_date, tier,
             ats, fit_score, score_reason, first_seen_date)
        applications(id PK AUTOINCREMENT, job_id FK, applied_date, outcome,
                     outcome_date, notes)

    Args:
        db_path: Filesystem path to the SQLite database file. Will be
                 created if it does not exist.
    """
    pass


def is_seen(db_path: str, job_id: str) -> bool:
    """Check whether a job ID has already been recorded in the database.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID to look up.

    Returns:
        True if the job_id exists in the jobs table, False otherwise.
    """
    pass


def insert_jobs(db_path: str, jobs: list[JobListing]) -> None:
    """Insert new job listings into the database.

    Uses INSERT OR IGNORE to skip any job_id that already exists.
    Sets first_seen_date to the current UTC date (ISO format).

    Args:
        db_path: Path to the SQLite database file.
        jobs: List of JobListing dicts to insert. fit_score and
              score_reason are NULL at insert time; they are updated
              after LLM scoring if needed.
    """
    pass


def log_application(db_path: str, job_id: str) -> None:
    """Record that the user applied to a job.

    Inserts a row into the applications table with applied_date set to
    today's UTC date and outcome set to NULL.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID that was applied to. Must exist in the
                jobs table (foreign key).

    Raises:
        ValueError: If job_id does not exist in the jobs table.
    """
    pass


def update_outcome(db_path: str, job_id: str, outcome: str) -> None:
    """Update the outcome of a logged application.

    Valid outcome values: 'phone_screen', 'final_round', 'offer', 'rejected'.
    Sets outcome_date to today's UTC date.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID whose outcome is being updated.
        outcome: One of: 'phone_screen', 'final_round', 'offer', 'rejected'.

    Raises:
        ValueError: If outcome is not one of the valid values.
        ValueError: If no application exists for this job_id.
    """
    pass


def get_all_applications(db_path: str) -> list[dict]:
    """Return all application rows joined with job metadata.

    Joins applications with jobs on job_id to include title, company,
    tier, fit_score, and score_reason alongside outcome data.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of dicts, one per application row. Empty list if no applications.
    """
    pass


def get_stats(db_path: str) -> dict[str, Any]:
    """Return funnel summary statistics for the current database.

    Computes:
        - jobs_surfaced: total rows in jobs table
        - jobs_scored: rows with fit_score IS NOT NULL
        - jobs_qualified: rows with fit_score >= SCORE_THRESHOLD
        - applied: count of applications
        - phone_screens: count where outcome = 'phone_screen'
        - final_rounds: count where outcome = 'final_round'
        - offers: count where outcome = 'offer'

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Dict with the above keys and integer values.
    """
    pass
