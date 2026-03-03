"""Tests for daily agent pipeline nodes: fetch_jobs, deduplicate, score_filter, format_report.

Each node is tested in isolation using mocked state input and mocked
external dependencies (DB, HTTP, Gemini). No live API calls in CI.
"""

import pytest
from unittest.mock import MagicMock, patch

from agent.state import AgentState


@pytest.fixture
def base_state() -> AgentState:
    """Minimal valid AgentState with empty collections."""
    return AgentState(
        companies=[],
        raw_listings=[],
        deduplicated=[],
        scored_jobs=[],
        report="",
        errors=[],
    )


@pytest.fixture
def sample_companies() -> list[dict]:
    """Two sample company configs: one Greenhouse, one Lever."""
    return [
        {"name": "Stripe", "tier": 1, "ats": "greenhouse", "ats_slug": "stripe",
         "target_roles": ["Staff Data Scientist"]},
        {"name": "Toast", "tier": 2, "ats": "lever", "ats_slug": "toast",
         "target_roles": ["Senior Data Scientist"]},
    ]


@pytest.fixture
def sample_listings() -> list[dict]:
    """Two minimal JobListing dicts for use in deduplication/scoring tests."""
    return [
        {"job_id": "gh-001", "company": "Stripe", "title": "Staff Data Scientist",
         "location": "Remote", "url": "https://example.com/1", "posted_date": "2026-03-01",
         "description": "We need a staff DS...", "tier": 1, "ats": "greenhouse"},
        {"job_id": "lv-abc", "company": "Toast", "title": "Senior Data Scientist",
         "location": "Boston, MA", "url": "https://example.com/2", "posted_date": "2026-03-01",
         "description": "Join our data team...", "tier": 2, "ats": "lever"},
    ]


class TestFetchJobsNode:
    def test_populates_raw_listings(self, base_state, sample_companies):
        """fetch_jobs returns a dict with 'raw_listings' key populated."""
        pass

    def test_errors_on_failed_company_are_nonfatal(self, base_state, sample_companies):
        """A fetcher exception appends to errors without stopping the pipeline."""
        pass

    def test_routes_greenhouse_to_greenhouse_fetcher(self, base_state, sample_companies):
        """Companies with ats='greenhouse' use GreenhouseFetcher."""
        pass

    def test_routes_lever_to_lever_fetcher(self, base_state, sample_companies):
        """Companies with ats='lever' use LeverFetcher."""
        pass

    def test_routes_workday_to_html_scraper(self, base_state):
        """Companies with ats='workday' use HtmlScraper."""
        pass


class TestDeduplicateNode:
    def test_filters_already_seen_job_ids(self, base_state, sample_listings):
        """Jobs whose job_id is already in the DB are excluded from deduplicated."""
        pass

    def test_new_jobs_are_inserted_to_db(self, base_state, sample_listings):
        """New jobs not in the DB are inserted and included in deduplicated."""
        pass

    def test_empty_raw_listings_returns_empty_deduplicated(self, base_state):
        """Empty raw_listings produces empty deduplicated without error."""
        pass


class TestScoreFilterNode:
    def test_calls_gemini_once_for_all_jobs(self, base_state, sample_listings):
        """score_filter issues exactly one Gemini API call regardless of job count."""
        pass

    def test_loads_prompt_from_file(self, base_state, sample_listings):
        """score_filter reads the scoring prompt from config/scoring_prompt.txt."""
        pass

    def test_filters_below_threshold(self, base_state, sample_listings):
        """Jobs with fit_score < SCORE_THRESHOLD are excluded from scored_jobs."""
        pass

    def test_gemini_failure_is_nonfatal(self, base_state, sample_listings):
        """A Gemini API exception appends to errors and returns empty scored_jobs."""
        pass


class TestFormatReportNode:
    def test_returns_html_string(self, base_state):
        """format_report returns a dict with 'report' set to a non-empty HTML string."""
        pass

    def test_empty_scored_jobs_returns_no_matches_message(self, base_state):
        """Empty scored_jobs produces a 'no new matches' HTML body."""
        pass

    def test_errors_appear_in_footer(self, base_state):
        """Errors in state['errors'] are rendered in the email footer section."""
        pass

    def test_jobs_grouped_by_tier(self, base_state, sample_listings):
        """Jobs in the HTML report are grouped and ordered by tier (1 first)."""
        pass
