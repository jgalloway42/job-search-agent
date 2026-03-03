"""CLI for logging job applications and recording outcomes.

Provides subcommands for all developer-facing database interactions:
    apply         — log a new job application
    outcome       — record the result of an application
    stats         — print funnel summary to stdout
    clean-today   — remove today's seen job IDs (allows fresh re-run)
    check-fetchers — test each fetcher against live sources
    seed-demo     — regenerate data/demo.db with realistic fake data

Usage (via Makefile):
    make apply JOB_ID=xxx
    make outcome JOB_ID=xxx OUTCOME=phone_screen
    make stats
    make clean-today
    make check-fetchers
    make seed-demo
"""

import argparse


def cmd_apply(args: argparse.Namespace) -> None:
    """Log a new job application to the database.

    Writes a row to the applications table with applied_date = today
    and outcome = NULL.

    Args:
        args: Parsed CLI args. Must include args.job_id (str).
    """
    pass


def cmd_outcome(args: argparse.Namespace) -> None:
    """Record the outcome of a previously logged application.

    Valid outcomes: phone_screen, final_round, offer, rejected.

    Args:
        args: Parsed CLI args. Must include args.job_id (str) and
              args.outcome (str).
    """
    pass


def cmd_stats(args: argparse.Namespace) -> None:
    """Print the application funnel summary to stdout.

    Displays a formatted table showing: jobs surfaced, qualified,
    applied, phone screens, final rounds, offers.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    pass


def cmd_clean_today(args: argparse.Namespace) -> None:
    """Remove today's first_seen_date entries from the jobs table.

    Allows the daily pipeline to re-fetch and re-process today's
    listings without duplicates blocking the run.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    pass


def cmd_check_fetchers(args: argparse.Namespace) -> None:
    """Test each configured company fetcher and report pass/fail.

    Calls fetch() on each company in companies.yaml, reports success
    (job count returned) or failure (exception message) per company.
    Does not write to the database.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    pass


def cmd_seed_demo(args: argparse.Namespace) -> None:
    """Regenerate data/demo.db with a realistic set of fake data.

    Inserts ~200 fake job listings, ~18 applications, ~6 phone screens,
    ~2 final rounds, and ~1 offer into a fresh demo database at the
    hardcoded path data/demo.db (this command only — DB path is not
    taken from settings for seeding).

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    pass


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate subcommand handler."""
    pass


if __name__ == "__main__":
    main()
