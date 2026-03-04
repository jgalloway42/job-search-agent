"""Weekly LangGraph pipeline: load_feedback → analyze_patterns → update_prompt.

Runs on a weekly cron (Monday 8am UTC via GitHub Actions). Reads application
outcomes from the database, asks Gemini to find patterns in successful
applications, and rewrites config/scoring_prompt.txt with refined criteria.
The previous prompt is archived to config/prompt_history.json (max 5 entries)
before each overwrite.
"""

from langgraph.graph import END, StateGraph

from learning.nodes.analyze_patterns import analyze_patterns
from learning.nodes.load_feedback import load_feedback
from learning.nodes.update_prompt import update_prompt
from learning.state import LearningState

__all__ = ["LearningState", "build_graph", "run"]


def build_graph():
    """Build and compile the weekly learning LangGraph pipeline.

    Nodes are connected in sequence:
        load_feedback → analyze_patterns → update_prompt

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(LearningState)

    graph.add_node("load_feedback", load_feedback)
    graph.add_node("analyze_patterns", analyze_patterns)
    graph.add_node("update_prompt", update_prompt)

    graph.set_entry_point("load_feedback")
    graph.add_edge("load_feedback", "analyze_patterns")
    graph.add_edge("analyze_patterns", "update_prompt")
    graph.add_edge("update_prompt", END)

    return graph.compile()


def run() -> None:
    """Entry point: build the graph and invoke the weekly learning pipeline.

    Initialises LearningState, invokes the compiled graph, and logs
    completion. The update_prompt node handles writing the new prompt file.
    """
    initial_state = LearningState(
        applications=[],
        analysis="",
        new_prompt="",
        errors=[],
    )

    compiled = build_graph()
    final_state = compiled.invoke(initial_state)

    if final_state.get("errors"):
        print("Learning pipeline completed with errors:")
        for err in final_state["errors"]:
            print(f"  - {err}")
    else:
        print("Learning pipeline completed successfully.")

    if final_state.get("new_prompt"):
        print("Scoring prompt updated.")


if __name__ == "__main__":
    run()
