"""Tests for database/db.py — all 7 functions.

Uses pytest's tmp_path fixture for full isolation: each test gets a fresh
SQLite file in a temp directory. No mocking required — SQLite runs locally.

Run a single class while implementing:
    pytest tests/test_db.py::TestInitDb -v

Run all DB tests:
    pytest tests/test_db.py -v
"""

import sqlite3
from datetime import date

import pytest

from database.db import (
    get_all_applications,
    get_stats,
    init_db,
    insert_jobs,
    is_seen,
    log_application,
    update_outcome,
)


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path):
    """Initialised DB path — fresh for every test."""
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def sample_job():
    return dict(
        job_id="stripe-001",
        company="Stripe",
        title="Staff Data Scientist",
        location="Remote",
        url="https://example.com/jobs/1",
        posted_date="2026-03-04",
        description="Great role focused on causal inference.",
        tier=1,
        ats="greenhouse",
    )


@pytest.fixture
def db_with_job(db, sample_job):
    """DB that already contains one job."""
    insert_jobs(db, [sample_job])
    return db


@pytest.fixture
def db_with_application(db_with_job):
    """DB with one job and one logged application."""
    log_application(db_with_job, "stripe-001")
    return db_with_job


# ── TestInitDb ────────────────────────────────────────────────────────────────


class TestInitDb:
    def test_creates_jobs_table(self, tmp_path):
        path = str(tmp_path / "test.db")
        init_db(path)
        conn = sqlite3.connect(path)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "jobs" in tables

    def test_creates_applications_table(self, tmp_path):
        path = str(tmp_path / "test.db")
        init_db(path)
        conn = sqlite3.connect(path)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "applications" in tables

    def test_idempotent(self, tmp_path):
        """Calling init_db twice does not raise."""
        path = str(tmp_path / "test.db")
        init_db(path)
        init_db(path)  # should not raise or wipe existing data


# ── TestIsSeen ────────────────────────────────────────────────────────────────


class TestIsSeen:
    def test_returns_false_for_unknown_id(self, db):
        assert is_seen(db, "unknown-id") is False

    def test_returns_true_after_insert(self, db, sample_job):
        insert_jobs(db, [sample_job])
        assert is_seen(db, "stripe-001") is True

    def test_does_not_confuse_different_ids(self, db, sample_job):
        insert_jobs(db, [sample_job])
        assert is_seen(db, "stripe-002") is False


# ── TestInsertJobs ────────────────────────────────────────────────────────────


class TestInsertJobs:
    def test_inserts_new_job(self, db, sample_job):
        insert_jobs(db, [sample_job])
        assert is_seen(db, "stripe-001") is True

    def test_ignores_duplicate_job_id(self, db, sample_job):
        insert_jobs(db, [sample_job])
        insert_jobs(db, [sample_job])  # should not raise or duplicate
        count = sqlite3.connect(db).execute(
            "SELECT COUNT(*) FROM jobs WHERE job_id='stripe-001'"
        ).fetchone()[0]
        assert count == 1

    def test_sets_first_seen_date(self, db, sample_job):
        insert_jobs(db, [sample_job])
        row = sqlite3.connect(db).execute(
            "SELECT first_seen_date FROM jobs WHERE job_id='stripe-001'"
        ).fetchone()
        assert row[0] == date.today().isoformat()

    def test_inserts_multiple_jobs(self, db, sample_job):
        job2 = {**sample_job, "job_id": "stripe-002", "title": "ML Engineer"}
        insert_jobs(db, [sample_job, job2])
        assert is_seen(db, "stripe-001") is True
        assert is_seen(db, "stripe-002") is True


# ── TestLogApplication ────────────────────────────────────────────────────────


class TestLogApplication:
    def test_logs_application(self, db_with_job):
        log_application(db_with_job, "stripe-001")
        count = sqlite3.connect(db_with_job).execute(
            "SELECT COUNT(*) FROM applications WHERE job_id='stripe-001'"
        ).fetchone()[0]
        assert count == 1

    def test_raises_for_unknown_job(self, db):
        with pytest.raises(ValueError):
            log_application(db, "does-not-exist")

    def test_outcome_is_null_on_creation(self, db_with_job):
        log_application(db_with_job, "stripe-001")
        row = sqlite3.connect(db_with_job).execute(
            "SELECT outcome FROM applications WHERE job_id='stripe-001'"
        ).fetchone()
        assert row[0] is None

    def test_sets_applied_date(self, db_with_job):
        log_application(db_with_job, "stripe-001")
        row = sqlite3.connect(db_with_job).execute(
            "SELECT applied_date FROM applications WHERE job_id='stripe-001'"
        ).fetchone()
        assert row[0] == date.today().isoformat()


# ── TestUpdateOutcome ─────────────────────────────────────────────────────────


class TestUpdateOutcome:
    def test_updates_outcome(self, db_with_application):
        update_outcome(db_with_application, "stripe-001", "phone_screen")
        row = sqlite3.connect(db_with_application).execute(
            "SELECT outcome FROM applications WHERE job_id='stripe-001'"
        ).fetchone()
        assert row[0] == "phone_screen"

    def test_sets_outcome_date(self, db_with_application):
        update_outcome(db_with_application, "stripe-001", "offer")
        row = sqlite3.connect(db_with_application).execute(
            "SELECT outcome_date FROM applications WHERE job_id='stripe-001'"
        ).fetchone()
        assert row[0] == date.today().isoformat()

    def test_raises_for_invalid_outcome(self, db_with_application):
        with pytest.raises(ValueError):
            update_outcome(db_with_application, "stripe-001", "ghosted")

    def test_raises_for_no_application(self, db_with_job):
        with pytest.raises(ValueError):
            update_outcome(db_with_job, "stripe-001", "phone_screen")

    @pytest.mark.parametrize("outcome", ["phone_screen", "final_round", "offer", "rejected"])
    def test_all_valid_outcomes_accepted(self, db_with_application, outcome):
        update_outcome(db_with_application, "stripe-001", outcome)  # should not raise


# ── TestGetAllApplications ────────────────────────────────────────────────────


class TestGetAllApplications:
    def test_returns_empty_list_with_no_applications(self, db):
        assert get_all_applications(db) == []

    def test_returns_one_row_per_application(self, db_with_application):
        rows = get_all_applications(db_with_application)
        assert len(rows) == 1

    def test_row_includes_job_fields(self, db_with_application):
        rows = get_all_applications(db_with_application)
        assert rows[0]["job_id"] == "stripe-001"
        assert rows[0]["company"] == "Stripe"
        assert rows[0]["title"] == "Staff Data Scientist"

    def test_row_includes_application_fields(self, db_with_application):
        rows = get_all_applications(db_with_application)
        assert rows[0]["applied_date"] == date.today().isoformat()
        assert rows[0]["outcome"] is None


# ── TestGetStats ──────────────────────────────────────────────────────────────


class TestGetStats:
    def test_empty_db_returns_zeros(self, db):
        stats = get_stats(db)
        assert stats["jobs_surfaced"] == 0
        assert stats["applied"] == 0
        assert stats["phone_screens"] == 0

    def test_counts_jobs_surfaced(self, db_with_job):
        assert get_stats(db_with_job)["jobs_surfaced"] == 1

    def test_counts_applications(self, db_with_application):
        assert get_stats(db_with_application)["applied"] == 1

    def test_counts_phone_screens(self, db_with_application):
        update_outcome(db_with_application, "stripe-001", "phone_screen")
        assert get_stats(db_with_application)["phone_screens"] == 1

    def test_counts_offers(self, db_with_application):
        update_outcome(db_with_application, "stripe-001", "offer")
        assert get_stats(db_with_application)["offers"] == 1

    def test_returns_expected_keys(self, db):
        stats = get_stats(db)
        expected = {"jobs_surfaced", "jobs_scored", "jobs_qualified", "applied",
                    "phone_screens", "final_rounds", "offers"}
        assert expected.issubset(stats.keys())
