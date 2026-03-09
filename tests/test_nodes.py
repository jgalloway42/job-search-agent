"""Tests for daily agent pipeline nodes: fetch_jobs, deduplicate, score_filter, format_report.

Each node is tested in isolation using mocked state input and mocked
external dependencies (DB, HTTP, Gemini). No live API calls in CI.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from agent.state import AgentState
from database.db import init_db, insert_jobs


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
        failed_companies=[],
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
    def test_populates_raw_listings(self, base_state, sample_companies, sample_listings):
        """fetch_jobs returns a dict with 'raw_listings' key populated."""
        from agent.nodes.fetch_jobs import fetch_jobs

        state = {**base_state, "companies": sample_companies}

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.fetch_jobs.LeverFetcher") as MockLev:
            MockGH.return_value.fetch.return_value = [sample_listings[0]]
            MockLev.return_value.fetch.return_value = [sample_listings[1]]

            result = fetch_jobs(state)

        assert "raw_listings" in result
        assert len(result["raw_listings"]) == 2

    def test_errors_on_failed_company_are_nonfatal(self, base_state, sample_companies):
        """A fetcher exception appends to errors without stopping the pipeline."""
        from agent.nodes.fetch_jobs import fetch_jobs

        state = {**base_state, "companies": sample_companies}

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.fetch_jobs.LeverFetcher") as MockLev:
            MockGH.return_value.fetch.side_effect = RuntimeError("connection timeout")
            MockLev.return_value.fetch.return_value = []

            result = fetch_jobs(state)

        assert len(result["errors"]) == 1
        assert "Stripe" in result["errors"][0]
        assert "raw_listings" in result

    def test_routes_greenhouse_to_greenhouse_fetcher(self, base_state, sample_companies):
        """Companies with ats='greenhouse' use GreenhouseFetcher."""
        from agent.nodes.fetch_jobs import fetch_jobs

        greenhouse_only = [sample_companies[0]]
        state = {**base_state, "companies": greenhouse_only}

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.fetch_jobs.LeverFetcher") as MockLev, \
             patch("agent.nodes.fetch_jobs.HtmlScraper") as MockHTML:
            MockGH.return_value.fetch.return_value = []

            fetch_jobs(state)

        MockGH.return_value.fetch.assert_called_once()
        MockLev.return_value.fetch.assert_not_called()
        MockHTML.return_value.fetch.assert_not_called()

    def test_routes_lever_to_lever_fetcher(self, base_state, sample_companies):
        """Companies with ats='lever' use LeverFetcher."""
        from agent.nodes.fetch_jobs import fetch_jobs

        lever_only = [sample_companies[1]]
        state = {**base_state, "companies": lever_only}

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.fetch_jobs.LeverFetcher") as MockLev, \
             patch("agent.nodes.fetch_jobs.HtmlScraper") as MockHTML:
            MockLev.return_value.fetch.return_value = []

            fetch_jobs(state)

        MockLev.return_value.fetch.assert_called_once()
        MockGH.return_value.fetch.assert_not_called()
        MockHTML.return_value.fetch.assert_not_called()

    def test_routes_workday_to_html_scraper(self, base_state):
        """Companies with ats='workday' use HtmlScraper."""
        from agent.nodes.fetch_jobs import fetch_jobs

        workday_company = [{"name": "Workday Co", "tier": 3, "ats": "workday",
                            "careers_url": "https://example.com/careers"}]
        state = {**base_state, "companies": workday_company}

        with patch("agent.nodes.fetch_jobs.HtmlScraper") as MockHTML, \
             patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.fetch_jobs.LeverFetcher") as MockLev:
            MockHTML.return_value.fetch.return_value = []

            fetch_jobs(state)

        MockHTML.return_value.fetch.assert_called_once()
        MockGH.return_value.fetch.assert_not_called()
        MockLev.return_value.fetch.assert_not_called()


class TestDeduplicateNode:
    def test_filters_already_seen_job_ids(self, base_state, sample_listings, tmp_path, monkeypatch):
        """Jobs whose job_id is already in the DB are excluded from deduplicated."""
        from agent.nodes.deduplicate import deduplicate

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        insert_jobs(db_path, [sample_listings[0]])  # pre-insert first job
        monkeypatch.setattr("config.settings.DB_PATH", db_path)

        state = {**base_state, "raw_listings": sample_listings}
        result = deduplicate(state)

        assert len(result["deduplicated"]) == 1
        assert result["deduplicated"][0]["job_id"] == "lv-abc"

    def test_new_jobs_are_inserted_to_db(self, base_state, sample_listings, tmp_path, monkeypatch):
        """New jobs not in the DB are inserted and included in deduplicated."""
        from agent.nodes.deduplicate import deduplicate
        from database.db import is_seen

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        monkeypatch.setattr("config.settings.DB_PATH", db_path)

        state = {**base_state, "raw_listings": sample_listings}
        result = deduplicate(state)

        assert len(result["deduplicated"]) == 2
        assert is_seen(db_path, "gh-001")
        assert is_seen(db_path, "lv-abc")

    def test_empty_raw_listings_returns_empty_deduplicated(self, base_state, tmp_path, monkeypatch):
        """Empty raw_listings produces empty deduplicated without error."""
        from agent.nodes.deduplicate import deduplicate

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        monkeypatch.setattr("config.settings.DB_PATH", db_path)

        result = deduplicate(base_state)

        assert result["deduplicated"] == []
        assert result["errors"] == []


class TestScoreFilterNode:
    def _make_mock_llm(self, scores: list[dict]):
        """Return a mock ChatGoogleGenerativeAI class that returns the given scores."""
        mock_response = MagicMock()
        mock_response.content = json.dumps(scores)
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class = MagicMock(return_value=mock_llm_instance)
        return mock_llm_class, mock_llm_instance

    def test_calls_gemini_once_for_all_jobs(self, base_state, sample_listings, monkeypatch):
        """score_filter issues exactly one Gemini API call regardless of job count."""
        from agent.nodes.score_filter import score_filter

        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 1)
        scores = [
            {"job_id": "gh-001", "fit_score": 8, "reason": "Great match"},
            {"job_id": "lv-abc", "fit_score": 7, "reason": "Good match"},
        ]
        mock_llm_class, mock_llm_instance = self._make_mock_llm(scores)

        state = {**base_state, "deduplicated": sample_listings}
        with patch("agent.nodes.score_filter.ChatGoogleGenerativeAI", mock_llm_class):
            score_filter(state)

        mock_llm_instance.invoke.assert_called_once()

    def test_loads_prompt_from_file(self, base_state, sample_listings, monkeypatch):
        """score_filter reads the scoring prompt from config/scoring_prompt.txt."""
        from agent.nodes.score_filter import score_filter

        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 1)
        scores = [{"job_id": "gh-001", "fit_score": 8, "reason": "Good"}]
        mock_llm_class, mock_llm_instance = self._make_mock_llm(scores)

        state = {**base_state, "deduplicated": [sample_listings[0]]}
        with patch("agent.nodes.score_filter.ChatGoogleGenerativeAI", mock_llm_class):
            score_filter(state)

        # The HumanMessage content should include prompt file text
        call_args = mock_llm_instance.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert "fit_score" in call_args[0].content  # prompt file contains "fit_score"

    def test_filters_below_threshold(self, base_state, sample_listings, monkeypatch):
        """Jobs with fit_score < SCORE_THRESHOLD are excluded from scored_jobs."""
        from agent.nodes.score_filter import score_filter

        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 7)
        scores = [
            {"job_id": "gh-001", "fit_score": 8, "reason": "Above threshold"},
            {"job_id": "lv-abc", "fit_score": 4, "reason": "Below threshold"},
        ]
        mock_llm_class, _ = self._make_mock_llm(scores)

        state = {**base_state, "deduplicated": sample_listings}
        with patch("agent.nodes.score_filter.ChatGoogleGenerativeAI", mock_llm_class):
            result = score_filter(state)

        assert len(result["scored_jobs"]) == 1
        assert result["scored_jobs"][0]["job_id"] == "gh-001"

    def test_gemini_failure_is_nonfatal(self, base_state, sample_listings):
        """A Gemini API exception appends to errors and returns empty scored_jobs."""
        from agent.nodes.score_filter import score_filter

        mock_llm_class = MagicMock()
        mock_llm_class.return_value.invoke.side_effect = RuntimeError("API error")

        state = {**base_state, "deduplicated": sample_listings}
        with patch("agent.nodes.score_filter.ChatGoogleGenerativeAI", mock_llm_class):
            result = score_filter(state)

        assert result["scored_jobs"] == []
        assert len(result["errors"]) == 1
        assert "Gemini" in result["errors"][0]


class TestFormatReportNode:
    def test_returns_html_string(self, base_state, sample_listings):
        """format_report returns a dict with 'report' set to a non-empty HTML string."""
        from agent.nodes.format_report import format_report

        scored = [{**j, "fit_score": 8, "reason": "Good match"} for j in sample_listings]
        state = {**base_state, "scored_jobs": scored}
        result = format_report(state)

        assert "report" in result
        assert isinstance(result["report"], str)
        assert len(result["report"]) > 0
        assert "<html" in result["report"]

    def test_empty_scored_jobs_returns_no_matches_message(self, base_state):
        """Empty scored_jobs produces a 'no new matches' HTML body."""
        from agent.nodes.format_report import format_report

        result = format_report(base_state)

        assert "no new matching jobs" in result["report"].lower()

    def test_errors_appear_in_footer(self, base_state):
        """Errors in state['errors'] are rendered in the email footer section."""
        from agent.nodes.format_report import format_report

        state = {**base_state, "errors": ["Stripe: timeout", "Toast: 404"]}
        result = format_report(state)

        assert "Stripe: timeout" in result["report"]
        assert "Toast: 404" in result["report"]

    def test_jobs_grouped_by_tier(self, base_state, sample_listings):
        """Jobs in the HTML report are grouped and ordered by tier (1 first)."""
        from agent.nodes.format_report import format_report

        scored = [{**j, "fit_score": 8, "reason": "Match"} for j in sample_listings]
        state = {**base_state, "scored_jobs": scored}
        result = format_report(state)

        tier1_pos = result["report"].find("Tier 1")
        tier2_pos = result["report"].find("Tier 2")
        assert tier1_pos < tier2_pos
