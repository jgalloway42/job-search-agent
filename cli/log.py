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

import config.settings as settings
import database.db as db


def cmd_apply(args: argparse.Namespace) -> None:
    """Log a new job application to the database.

    Writes a row to the applications table with applied_date = today
    and outcome = NULL.

    Args:
        args: Parsed CLI args. Must include args.job_id (str).
    """
    try:
        db.log_application(settings.DB_PATH, args.job_id)
        print(f"Logged application: {args.job_id}")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_outcome(args: argparse.Namespace) -> None:
    """Record the outcome of a previously logged application.

    Valid outcomes: phone_screen, final_round, offer, rejected.

    Args:
        args: Parsed CLI args. Must include args.job_id (str) and
              args.outcome (str).
    """
    try:
        db.update_outcome(settings.DB_PATH, args.job_id, args.outcome)
        print(f"Updated outcome: {args.job_id} → {args.outcome}")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_stats(args: argparse.Namespace) -> None:
    """Print the application funnel summary to stdout.

    Displays a formatted table showing: jobs surfaced, qualified,
    applied, phone screens, final rounds, offers.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    s = db.get_stats(settings.DB_PATH)
    print("── Job Search Funnel ─────────────────")
    print(f"  Jobs surfaced  : {s['jobs_surfaced']}")
    print(f"  Jobs scored    : {s['jobs_scored']}")
    print(f"  Jobs qualified : {s['jobs_qualified']}")
    print(f"  Applied        : {s['applied']}")
    print(f"  Phone screens  : {s['phone_screens']}")
    print(f"  Final rounds   : {s['final_rounds']}")
    print(f"  Offers         : {s['offers']}")


def cmd_clean_today(args: argparse.Namespace) -> None:
    """Remove today's first_seen_date entries from the jobs table.

    Allows the daily pipeline to re-fetch and re-process today's
    listings without duplicates blocking the run.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    deleted = db.clean_today(settings.DB_PATH)
    print(f"Removed {deleted} job(s) first seen today. Run `make run` to re-fetch.")


def cmd_check_fetchers(args: argparse.Namespace) -> None:
    """Test each configured company fetcher and report pass/fail.

    Calls fetch() on each company in companies.yaml, reports success
    (job count returned) or failure (exception message) per company.
    Does not write to the database.

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    import yaml

    from fetchers.base import BaseFetcher
    from fetchers.greenhouse import GreenhouseFetcher
    from fetchers.html_scraper import HtmlScraper
    from fetchers.lever import LeverFetcher

    with open("config/companies.yaml") as f:
        companies = yaml.safe_load(f)

    passed = 0
    failed = 0
    for company in companies:
        name = company["name"]
        ats = company.get("ats")
        try:
            fetcher: BaseFetcher
            if ats == "greenhouse":
                fetcher = GreenhouseFetcher()
            elif ats == "lever":
                fetcher = LeverFetcher()
            else:
                fetcher = HtmlScraper()
            jobs = fetcher.fetch(company)
            print(f"  PASS  {name}: {len(jobs)} job(s)")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")


def cmd_seed_demo(args: argparse.Namespace) -> None:
    """Regenerate data/demo.db with a realistic set of fake data.

    Inserts ~200 fake job listings, ~18 applications, ~6 phone screens,
    ~2 final rounds, and ~1 offer into a fresh demo database at the
    hardcoded path data/demo.db (this command only — DB path is not
    taken from settings for seeding).

    Args:
        args: Parsed CLI args (no additional fields required).
    """
    from scripts.seed_demo import seed

    seed()


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate subcommand handler."""
    parser = argparse.ArgumentParser(
        prog="python -m cli.log",
        description="Job search agent CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # apply
    p_apply = sub.add_parser("apply", help="Log a job application")
    p_apply.add_argument("--job-id", required=True, help="ATS job ID")
    p_apply.set_defaults(func=cmd_apply)

    # outcome
    p_outcome = sub.add_parser("outcome", help="Record application outcome")
    p_outcome.add_argument("--job-id", required=True, help="ATS job ID")
    p_outcome.add_argument(
        "--outcome",
        required=True,
        choices=["phone_screen", "final_round", "offer", "rejected"],
    )
    p_outcome.set_defaults(func=cmd_outcome)

    # stats
    p_stats = sub.add_parser("stats", help="Print funnel summary")
    p_stats.set_defaults(func=cmd_stats)

    # clean-today
    p_clean = sub.add_parser("clean-today", help="Remove today's seen job IDs")
    p_clean.set_defaults(func=cmd_clean_today)

    # check-fetchers
    p_check = sub.add_parser("check-fetchers", help="Test all fetchers live")
    p_check.set_defaults(func=cmd_check_fetchers)

    # seed-demo
    p_seed = sub.add_parser("seed-demo", help="Regenerate data/demo.db")
    p_seed.set_defaults(func=cmd_seed_demo)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
