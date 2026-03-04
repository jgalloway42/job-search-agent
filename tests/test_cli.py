"""Tests for cli/log.py — CLI command handlers.

All DB interactions use tmp_path isolated databases. No live API calls.
"""

import argparse
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from agent.state import JobListing
from database.db import init_db, insert_jobs


# ── shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def seeded_job(db) -> dict:
    job = {
        "job_id": "gh-001",
        "company": "Stripe",
        "title": "Staff Data Scientist",
        "location": "Remote",
        "url": "https://example.com/1",
        "posted_date": "2026-03-01",
        "tier": 1,
        "ats": "greenhouse",
    }
    insert_jobs(db, [cast(JobListing, job)])
    return job


def _args(**kwargs) -> argparse.Namespace:
    """Build a minimal Namespace for testing command handlers."""
    return argparse.Namespace(**kwargs)


# ── cmd_apply ─────────────────────────────────────────────────────────────────

class TestCmdApply:
    def test_logs_application_and_prints(self, db, seeded_job, monkeypatch, capsys):
        from cli.log import cmd_apply

        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_apply(_args(job_id="gh-001"))

        out = capsys.readouterr().out
        assert "gh-001" in out

    def test_unknown_job_id_prints_error_and_exits(self, db, monkeypatch):
        from cli.log import cmd_apply

        monkeypatch.setattr("config.settings.DB_PATH", db)
        with pytest.raises(SystemExit):
            cmd_apply(_args(job_id="nonexistent"))

    def test_application_written_to_db(self, db, seeded_job, monkeypatch):
        from cli.log import cmd_apply
        from database.db import get_all_applications

        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_apply(_args(job_id="gh-001"))

        apps = get_all_applications(db)
        assert len(apps) == 1
        assert apps[0]["job_id"] == "gh-001"


# ── cmd_outcome ────────────────────────────────────────────────────────────────

class TestCmdOutcome:
    def _apply(self, db):
        from database.db import log_application
        log_application(db, "gh-001")

    def test_updates_outcome_and_prints(self, db, seeded_job, monkeypatch, capsys):
        from cli.log import cmd_outcome

        self._apply(db)
        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_outcome(_args(job_id="gh-001", outcome="phone_screen"))

        out = capsys.readouterr().out
        assert "phone_screen" in out

    def test_no_application_exits(self, db, seeded_job, monkeypatch):
        from cli.log import cmd_outcome

        monkeypatch.setattr("config.settings.DB_PATH", db)
        with pytest.raises(SystemExit):
            cmd_outcome(_args(job_id="gh-001", outcome="phone_screen"))

    def test_outcome_persisted_in_db(self, db, seeded_job, monkeypatch):
        from cli.log import cmd_outcome
        from database.db import get_all_applications

        self._apply(db)
        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_outcome(_args(job_id="gh-001", outcome="offer"))

        apps = get_all_applications(db)
        assert apps[0]["outcome"] == "offer"


# ── cmd_stats ──────────────────────────────────────────────────────────────────

class TestCmdStats:
    def test_prints_funnel_labels(self, db, monkeypatch, capsys):
        from cli.log import cmd_stats

        monkeypatch.setattr("config.settings.DB_PATH", db)
        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 6)
        cmd_stats(_args())

        out = capsys.readouterr().out
        assert "Jobs surfaced" in out
        assert "Applied" in out
        assert "Offers" in out

    def test_counts_match_db(self, db, seeded_job, monkeypatch, capsys):
        from cli.log import cmd_stats
        from database.db import log_application

        log_application(db, "gh-001")
        monkeypatch.setattr("config.settings.DB_PATH", db)
        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 6)
        cmd_stats(_args())

        out = capsys.readouterr().out
        assert "1" in out  # at least one count visible


# ── cmd_clean_today ────────────────────────────────────────────────────────────

class TestCmdCleanToday:
    def test_removes_todays_jobs_and_prints_count(self, db, seeded_job, monkeypatch, capsys):
        from cli.log import cmd_clean_today

        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_clean_today(_args())

        out = capsys.readouterr().out
        assert "1" in out  # 1 job removed

    def test_empty_db_prints_zero(self, db, monkeypatch, capsys):
        from cli.log import cmd_clean_today

        monkeypatch.setattr("config.settings.DB_PATH", db)
        cmd_clean_today(_args())

        out = capsys.readouterr().out
        assert "0" in out


# ── cmd_check_fetchers ────────────────────────────────────────────────────────

class TestCmdCheckFetchers:
    _fake_companies = [
        {"name": "Stripe", "tier": 1, "ats": "greenhouse", "ats_slug": "stripe"}
    ]

    def test_prints_pass_for_successful_fetcher(self, capsys):
        from cli.log import cmd_check_fetchers

        with patch("builtins.open", MagicMock()), \
             patch("yaml.safe_load", return_value=self._fake_companies), \
             patch("fetchers.greenhouse.GreenhouseFetcher") as MockGH:
            MockGH.return_value.fetch.return_value = [{"job_id": "1"}, {"job_id": "2"}]
            cmd_check_fetchers(_args())

        out = capsys.readouterr().out
        assert "PASS" in out
        assert "Stripe" in out

    def test_prints_fail_for_failing_fetcher(self, capsys):
        from cli.log import cmd_check_fetchers

        with patch("builtins.open", MagicMock()), \
             patch("yaml.safe_load", return_value=self._fake_companies), \
             patch("fetchers.greenhouse.GreenhouseFetcher") as MockGH:
            MockGH.return_value.fetch.side_effect = RuntimeError("timeout")
            cmd_check_fetchers(_args())

        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "Stripe" in out


# ── cmd_seed_demo ──────────────────────────────────────────────────────────────

class TestCmdSeedDemo:
    def test_delegates_to_seed_function(self):
        from cli.log import cmd_seed_demo

        with patch("scripts.seed_demo.seed") as mock_seed:
            cmd_seed_demo(_args())

        mock_seed.assert_called_once()


# ── main / argparse dispatch ──────────────────────────────────────────────────

class TestMain:
    def test_no_subcommand_prints_help(self, capsys):
        from cli.log import main

        with pytest.raises(SystemExit):
            main()  # argparse exits on --help or prints help on no command

    def test_apply_subcommand_dispatches(self, monkeypatch):
        from cli.log import main

        called = {}

        def fake_apply(args):
            called["job_id"] = args.job_id

        monkeypatch.setattr("cli.log.cmd_apply", fake_apply)
        import sys
        with patch.object(sys, "argv", ["cli.log", "apply", "--job-id", "test-123"]):
            main()

        assert called["job_id"] == "test-123"

    def test_outcome_subcommand_dispatches(self, monkeypatch):
        from cli.log import main

        called = {}

        def fake_outcome(args):
            called["outcome"] = args.outcome

        monkeypatch.setattr("cli.log.cmd_outcome", fake_outcome)
        import sys
        with patch.object(sys, "argv", ["cli.log", "outcome", "--job-id", "x", "--outcome", "offer"]):
            main()

        assert called["outcome"] == "offer"
