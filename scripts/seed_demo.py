"""Seed data/demo.db with realistic fake job search data for portfolio demos.

Generates and inserts:
    - ~200 job listings across the configured companies (all tiers)
    - 18 logged applications with varying applied_dates
    - 6 phone screens, 2 final rounds, 1 offer, 4 rejections

Run via:
    make seed-demo
    python scripts/seed_demo.py

Always writes to data/demo.db (hardcoded for this script only — not settings.DB_PATH).
Drops and recreates all tables before inserting, so re-running is idempotent.
"""

DEMO_DB_PATH = "data/demo.db"


def generate_jobs() -> list[dict]:
    """Generate ~200 realistic fake job listings spread across all companies.

    Each listing has a stable fake job_id, realistic title drawn from
    target_roles in companies.yaml, plausible location, and a pre-assigned
    fit_score so the digest email renders without needing a real Gemini call.

    Returns:
        List of dicts matching the jobs table schema.
    """
    pass


def generate_applications(jobs: list[dict]) -> list[dict]:
    """Select 18 jobs from the generated set and produce application records.

    Assigns outcomes to simulate a realistic funnel:
        18 applied → 6 phone_screen → 2 final_round → 1 offer, 4 rejected

    Spreads applied_dates over the past 90 days.

    Args:
        jobs: The full list of generated job dicts (must include job_id).

    Returns:
        List of dicts matching the applications table schema.
    """
    pass


def seed() -> None:
    """Drop all tables, recreate schema, and insert generated fake data.

    Always targets DEMO_DB_PATH (data/demo.db), never settings.DB_PATH.
    Prints a summary on completion.
    """
    pass


if __name__ == "__main__":
    seed()
