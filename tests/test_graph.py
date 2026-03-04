"""Integration-level tests for the full daily agent graph.

Tests that the graph compiles correctly and that nodes are wired in the
right sequence. All external calls (HTTP, DB, Gemini, SMTP) are mocked.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from agent.state import AgentState
from database.db import init_db, insert_jobs


@pytest.fixture
def sample_listings() -> list[dict]:
    return [
        {"job_id": "gh-001", "company": "Stripe", "title": "Staff Data Scientist",
         "location": "Remote", "url": "https://example.com/1", "posted_date": "2026-03-01",
         "description": "We need a staff DS...", "tier": 1, "ats": "greenhouse"},
    ]


@pytest.fixture
def stripe_company() -> list[dict]:
    return [{"name": "Stripe", "tier": 1, "ats": "greenhouse", "ats_slug": "stripe",
             "target_roles": ["Staff Data Scientist"]}]


class TestBuildGraph:
    def test_graph_compiles_without_error(self):
        """build_graph() returns a compiled StateGraph without raising."""
        from agent.graph import build_graph

        graph = build_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """Compiled graph contains: fetch_jobs, deduplicate, score_filter, format_report."""
        from agent.graph import build_graph

        graph = build_graph()
        node_ids = set(graph.get_graph().nodes.keys())

        assert "fetch_jobs" in node_ids
        assert "deduplicate" in node_ids
        assert "score_filter" in node_ids
        assert "format_report" in node_ids


class TestGraphInvocation:
    def test_full_pipeline_runs_end_to_end(self, tmp_path, monkeypatch, sample_listings, stripe_company):
        """Invoking the graph with mocked state produces a non-empty report."""
        from agent.graph import build_graph

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        monkeypatch.setattr("config.settings.DB_PATH", db_path)
        monkeypatch.setattr("config.settings.SCORE_THRESHOLD", 1)

        mock_response = MagicMock()
        mock_response.content = json.dumps([
            {"job_id": "gh-001", "fit_score": 8, "reason": "Great match"},
        ])
        mock_llm = MagicMock()
        mock_llm.return_value.invoke.return_value = mock_response

        initial_state = AgentState(
            companies=stripe_company,
            raw_listings=[],
            deduplicated=[],
            scored_jobs=[],
            report="",
            errors=[],
        )

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.score_filter.ChatGoogleGenerativeAI", mock_llm):
            MockGH.return_value.fetch.return_value = sample_listings

            graph = build_graph()
            result = graph.invoke(initial_state)

        assert result["report"]
        assert "<html" in result["report"]

    def test_empty_deduplicated_skips_to_no_matches_report(self, tmp_path, monkeypatch, sample_listings, stripe_company):
        """When deduplicated is empty after dedup, the report contains a no-matches message."""
        from agent.graph import build_graph

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        insert_jobs(db_path, sample_listings)  # pre-insert so job is already seen
        monkeypatch.setattr("config.settings.DB_PATH", db_path)

        initial_state = AgentState(
            companies=stripe_company,
            raw_listings=[],
            deduplicated=[],
            scored_jobs=[],
            report="",
            errors=[],
        )

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH, \
             patch("agent.nodes.score_filter.ChatGoogleGenerativeAI") as MockLLM:
            MockGH.return_value.fetch.return_value = sample_listings

            graph = build_graph()
            result = graph.invoke(initial_state)

        MockLLM.return_value.invoke.assert_not_called()
        assert "no new matching jobs" in result["report"].lower()

    def test_errors_accumulate_across_nodes(self, tmp_path, monkeypatch, stripe_company):
        """Errors from multiple nodes are merged into state['errors']."""
        from agent.graph import build_graph

        db_path = str(tmp_path / "test.db")
        init_db(db_path)
        monkeypatch.setattr("config.settings.DB_PATH", db_path)

        initial_state = AgentState(
            companies=stripe_company,
            raw_listings=[],
            deduplicated=[],
            scored_jobs=[],
            report="",
            errors=[],
        )

        with patch("agent.nodes.fetch_jobs.GreenhouseFetcher") as MockGH:
            MockGH.return_value.fetch.side_effect = RuntimeError("fetch failed")

            graph = build_graph()
            result = graph.invoke(initial_state)

        assert len(result["errors"]) >= 1
        assert any("Stripe" in e for e in result["errors"])
