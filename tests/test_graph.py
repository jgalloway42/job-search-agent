"""Integration-level tests for the full daily agent graph.

Tests that the graph compiles correctly and that nodes are wired in the
right sequence. All external calls (HTTP, DB, Gemini, SMTP) are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestBuildGraph:
    def test_graph_compiles_without_error(self):
        """build_graph() returns a compiled StateGraph without raising."""
        pass

    def test_graph_has_expected_nodes(self):
        """Compiled graph contains: fetch_jobs, deduplicate, score_filter, format_report."""
        pass


class TestGraphInvocation:
    def test_full_pipeline_runs_end_to_end(self):
        """Invoking the graph with mocked state produces a non-empty report."""
        pass

    def test_empty_deduplicated_skips_to_no_matches_report(self):
        """When deduplicated is empty after dedup, the report contains a no-matches message."""
        pass

    def test_errors_accumulate_across_nodes(self):
        """Errors from multiple nodes are merged into state['errors']."""
        pass
