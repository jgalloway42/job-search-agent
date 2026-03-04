"""Weekly LangGraph pipeline: load_feedback → analyze_patterns → update_prompt.

Runs on a weekly cron (Monday 8am UTC via GitHub Actions). Reads application
outcomes from the database, asks Gemini to find patterns in successful
applications, and rewrites config/scoring_prompt.txt with refined criteria.
"""

from langgraph.graph import StateGraph
from typing import TypedDict


class LearningState(TypedDict):
    """Shared state passed between nodes in the weekly learning pipeline."""

    applications: list[dict]   # all logged applications + outcomes from DB
    analysis: str              # Gemini's pattern analysis text
    new_prompt: str            # rewritten scoring prompt text
    errors: list[str]          # non-fatal runtime errors


def build_graph() -> StateGraph:
    """Build and compile the weekly learning LangGraph pipeline.

    Nodes are connected in sequence:
        load_feedback → analyze_patterns → update_prompt

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    ...


def run() -> None:
    """Entry point: build the graph and invoke the weekly learning pipeline.

    Initialises LearningState, invokes the compiled graph, and logs
    completion. The update_prompt node handles writing the new prompt file.
    """
    pass


if __name__ == "__main__":
    run()
