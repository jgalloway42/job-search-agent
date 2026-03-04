"""Tests for the weekly learning pipeline: load_feedback, analyze_patterns, update_prompt, graph.

All external calls (DB, Gemini) are mocked. No live API calls in CI.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from learning.state import LearningState


# ── shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def base_state() -> LearningState:
    return LearningState(applications=[], analysis="", new_prompt="", errors=[])


@pytest.fixture
def sample_applications() -> list[dict]:
    return [
        {
            "job_id": "gh-001", "title": "Staff Data Scientist", "company": "Stripe",
            "tier": 1, "fit_score": 9, "score_reason": "Perfect title and domain match.",
            "applied_date": "2026-02-01", "outcome": "phone_screen",
            "outcome_date": "2026-02-10", "notes": None,
        },
        {
            "job_id": "lv-abc", "title": "Senior Data Scientist", "company": "Toast",
            "tier": 2, "fit_score": 7, "score_reason": "Good seniority, weak domain.",
            "applied_date": "2026-02-05", "outcome": None,
            "outcome_date": None, "notes": None,
        },
        {
            "job_id": "gh-002", "title": "ML Engineer", "company": "Datadog",
            "tier": 1, "fit_score": 6, "score_reason": "Adjacent role, some ML overlap.",
            "applied_date": "2026-02-08", "outcome": "rejected",
            "outcome_date": "2026-02-20", "notes": None,
        },
    ]


# ── TestLoadFeedback ───────────────────────────────────────────────────────────

class TestLoadFeedback:
    def test_returns_applications_from_db(self, base_state, sample_applications, monkeypatch):
        from learning.nodes.load_feedback import load_feedback

        monkeypatch.setattr("config.settings.DB_PATH", "fake.db")

        with patch("learning.nodes.load_feedback.db.get_all_applications", return_value=sample_applications):
            result = load_feedback(base_state)

        assert result["applications"] == sample_applications
        assert result["errors"] == []

    def test_db_error_is_nonfatal(self, base_state, monkeypatch):
        from learning.nodes.load_feedback import load_feedback

        monkeypatch.setattr("config.settings.DB_PATH", "fake.db")

        with patch("learning.nodes.load_feedback.db.get_all_applications", side_effect=Exception("db failure")):
            result = load_feedback(base_state)

        assert result["applications"] == []
        assert len(result["errors"]) == 1
        assert "db failure" in result["errors"][0]

    def test_preserves_existing_errors(self, sample_applications, monkeypatch):
        from learning.nodes.load_feedback import load_feedback

        monkeypatch.setattr("config.settings.DB_PATH", "fake.db")
        state = LearningState(applications=[], analysis="", new_prompt="", errors=["prior error"])

        with patch("learning.nodes.load_feedback.db.get_all_applications", return_value=sample_applications):
            result = load_feedback(state)

        assert "prior error" in result["errors"]


# ── TestAnalyzePatterns ────────────────────────────────────────────────────────

class TestAnalyzePatterns:
    def _mock_llm(self, content: str):
        mock_response = MagicMock()
        mock_response.content = content
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        return mock_llm

    def test_returns_analysis_from_gemini(self, sample_applications, monkeypatch):
        from learning.nodes.analyze_patterns import analyze_patterns

        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")
        state = LearningState(applications=sample_applications, analysis="", new_prompt="", errors=[])

        with patch("learning.nodes.analyze_patterns.ChatGoogleGenerativeAI", return_value=self._mock_llm("Great analysis.")):
            result = analyze_patterns(state)

        assert result["analysis"] == "Great analysis."
        assert result["errors"] == []

    def test_empty_applications_skips_and_errors(self, base_state, monkeypatch):
        from learning.nodes.analyze_patterns import analyze_patterns

        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")
        result = analyze_patterns(base_state)

        assert result["analysis"] == ""
        assert len(result["errors"]) == 1

    def test_gemini_error_is_nonfatal(self, sample_applications, monkeypatch):
        from learning.nodes.analyze_patterns import analyze_patterns

        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")
        state = LearningState(applications=sample_applications, analysis="", new_prompt="", errors=[])

        with patch("learning.nodes.analyze_patterns.ChatGoogleGenerativeAI", side_effect=Exception("api error")):
            result = analyze_patterns(state)

        assert result["analysis"] == ""
        assert len(result["errors"]) == 1
        assert "api error" in result["errors"][0]


# ── TestUpdatePrompt ───────────────────────────────────────────────────────────

class TestUpdatePrompt:
    def _mock_llm(self, content: str):
        mock_response = MagicMock()
        mock_response.content = content
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        return mock_llm

    @pytest.fixture
    def prompt_files(self, tmp_path):
        scoring = tmp_path / "scoring_prompt.txt"
        history = tmp_path / "prompt_history.json"
        scoring.write_text("original prompt content")
        history.write_text("[]")
        return scoring, history

    def test_overwrites_prompt_and_archives_history(self, prompt_files, monkeypatch):
        from learning.nodes import update_prompt as mod
        from learning.nodes.update_prompt import update_prompt

        scoring, history = prompt_files
        monkeypatch.setattr(mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(mod, "_HISTORY_PATH", history)
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")

        state = LearningState(applications=[], analysis="some analysis", new_prompt="", errors=[])

        with patch("learning.nodes.update_prompt.ChatGoogleGenerativeAI", return_value=self._mock_llm("new prompt content")):
            result = update_prompt(state)

        assert result["new_prompt"] == "new prompt content"
        assert scoring.read_text() == "new prompt content"

        archived = json.loads(history.read_text())
        assert len(archived) == 1
        assert archived[0]["prompt"] == "original prompt content"
        assert "updated_at" in archived[0]
        assert result["errors"] == []

    def test_history_trimmed_to_max(self, prompt_files, monkeypatch):
        from learning.nodes import update_prompt as mod
        from learning.nodes.update_prompt import update_prompt

        scoring, history = prompt_files
        monkeypatch.setattr(mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(mod, "_HISTORY_PATH", history)
        monkeypatch.setattr(mod, "_MAX_HISTORY", 3)
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")

        # Pre-populate with 3 entries (already at max)
        existing = [{"updated_at": f"2026-01-0{i}T00:00:00", "prompt": f"v{i}"} for i in range(1, 4)]
        history.write_text(json.dumps(existing))

        state = LearningState(applications=[], analysis="analysis", new_prompt="", errors=[])

        with patch("learning.nodes.update_prompt.ChatGoogleGenerativeAI", return_value=self._mock_llm("newest prompt")):
            update_prompt(state)

        archived = json.loads(history.read_text())
        assert len(archived) == 3
        assert archived[0]["prompt"] == "original prompt content"  # just-archived current prompt

    def test_empty_analysis_skips_update(self, prompt_files, monkeypatch):
        from learning.nodes import update_prompt as mod
        from learning.nodes.update_prompt import update_prompt

        scoring, history = prompt_files
        monkeypatch.setattr(mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(mod, "_HISTORY_PATH", history)
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")

        state = LearningState(applications=[], analysis="", new_prompt="", errors=[])
        result = update_prompt(state)

        assert result["new_prompt"] == ""
        assert len(result["errors"]) == 1
        assert scoring.read_text() == "original prompt content"  # unchanged

    def test_gemini_error_leaves_files_intact(self, prompt_files, monkeypatch):
        from learning.nodes import update_prompt as mod
        from learning.nodes.update_prompt import update_prompt

        scoring, history = prompt_files
        monkeypatch.setattr(mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(mod, "_HISTORY_PATH", history)
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")

        state = LearningState(applications=[], analysis="some analysis", new_prompt="", errors=[])

        with patch("learning.nodes.update_prompt.ChatGoogleGenerativeAI", side_effect=Exception("gemini down")):
            result = update_prompt(state)

        assert result["new_prompt"] == ""
        assert len(result["errors"]) == 1
        assert scoring.read_text() == "original prompt content"  # unchanged
        assert history.read_text() == "[]"  # unchanged

    def test_missing_history_file_handled_gracefully(self, tmp_path, monkeypatch):
        from learning.nodes import update_prompt as mod
        from learning.nodes.update_prompt import update_prompt

        scoring = tmp_path / "scoring_prompt.txt"
        history = tmp_path / "prompt_history.json"
        scoring.write_text("original prompt")
        # history file does NOT exist

        monkeypatch.setattr(mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(mod, "_HISTORY_PATH", history)
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")

        state = LearningState(applications=[], analysis="analysis", new_prompt="", errors=[])

        with patch("learning.nodes.update_prompt.ChatGoogleGenerativeAI", return_value=self._mock_llm("new prompt")):
            result = update_prompt(state)

        assert result["errors"] == []
        archived = json.loads(history.read_text())
        assert len(archived) == 1


# ── TestLearningGraph ──────────────────────────────────────────────────────────

class TestLearningGraph:
    def test_graph_runs_end_to_end(self, tmp_path, monkeypatch):
        """Full graph invocation with all external deps mocked."""
        from learning.graph import build_graph

        scoring = tmp_path / "scoring_prompt.txt"
        history = tmp_path / "prompt_history.json"
        scoring.write_text("original prompt")
        history.write_text("[]")

        sample_apps = [
            {
                "job_id": "gh-001", "title": "Staff DS", "company": "Stripe",
                "tier": 1, "fit_score": 9, "score_reason": "Great match.",
                "applied_date": "2026-02-01", "outcome": "phone_screen",
                "outcome_date": None, "notes": None,
            }
        ]

        mock_response = MagicMock()
        mock_response.content = "analysis text"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        import learning.nodes.update_prompt as up_mod

        monkeypatch.setattr("config.settings.DB_PATH", "fake.db")
        monkeypatch.setattr("config.settings.GEMINI_API_KEY", "fake-key")
        monkeypatch.setattr(up_mod, "_SCORING_PROMPT_PATH", scoring)
        monkeypatch.setattr(up_mod, "_HISTORY_PATH", history)

        with patch("learning.nodes.load_feedback.db.get_all_applications", return_value=sample_apps), \
             patch("learning.nodes.analyze_patterns.ChatGoogleGenerativeAI", return_value=mock_llm), \
             patch("learning.nodes.update_prompt.ChatGoogleGenerativeAI", return_value=mock_llm):

            compiled = build_graph()
            final_state = compiled.invoke(
                LearningState(applications=[], analysis="", new_prompt="", errors=[])
            )

        assert final_state["applications"] == sample_apps
        assert final_state["analysis"] == "analysis text"
        assert final_state["new_prompt"] == "analysis text"
        assert final_state["errors"] == []
