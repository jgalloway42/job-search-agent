"""Daily LangGraph pipeline: fetch → deduplicate → score_filter → format_report.

Entry point for the daily job search agent. Build and invoke the graph,
then trigger the email digest via notifications/email.py.
"""

from langgraph.graph import StateGraph



def build_graph() -> StateGraph:
    """Build and compile the daily agent LangGraph pipeline.

    Nodes are connected in sequence:
        fetch_jobs → deduplicate → score_filter → format_report

    A conditional edge after score_filter routes to format_report with a
    "no new matches" message when scored_jobs is empty, skipping re-scoring.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    pass


def run() -> None:
    """Entry point: load config, build the graph, invoke it, send the digest.

    Loads companies from config/companies.yaml, initialises AgentState,
    invokes the compiled graph, and calls the email sender with state["report"].
    """
    pass


if __name__ == "__main__":
    run()
