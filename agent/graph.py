"""Daily LangGraph pipeline: fetch → deduplicate → score_filter → format_report.

Entry point for the daily job search agent. Build and invoke the graph,
then trigger the email digest via notifications/email.py.
"""

from datetime import date

import yaml
from langgraph.graph import END, StateGraph

import config.settings as settings
import database.db as db
from agent.nodes.deduplicate import deduplicate
from agent.nodes.fetch_jobs import fetch_jobs
from agent.nodes.format_report import format_report
from agent.nodes.score_filter import score_filter
from agent.state import AgentState


def build_graph():
    """Build and compile the daily agent LangGraph pipeline.

    Nodes are connected in sequence:
        fetch_jobs → deduplicate → score_filter → format_report

    A conditional edge after deduplicate skips score_filter when there are
    no new deduplicated jobs, routing directly to format_report.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(AgentState)

    graph.add_node("fetch_jobs", fetch_jobs)
    graph.add_node("deduplicate", deduplicate)
    graph.add_node("score_filter", score_filter)
    graph.add_node("format_report", format_report)

    graph.set_entry_point("fetch_jobs")
    graph.add_edge("fetch_jobs", "deduplicate")

    graph.add_conditional_edges(
        "deduplicate",
        lambda state: "format_report" if not state.get("deduplicated") else "score_filter",
        {"score_filter": "score_filter", "format_report": "format_report"},
    )

    graph.add_edge("score_filter", "format_report")
    graph.add_edge("format_report", END)

    return graph.compile()


def run() -> None:
    """Entry point: load config, build the graph, invoke it, send the digest.

    Loads companies from config/companies.yaml, initialises AgentState,
    invokes the compiled graph, and calls the email sender with state["report"].
    """
    with open("config/companies.yaml") as f:
        companies = yaml.safe_load(f)["companies"]

    db.init_db(settings.DB_PATH)

    initial_state = AgentState(
        companies=companies,
        raw_listings=[],
        deduplicated=[],
        scored_jobs=[],
        report="",
        errors=[],
    )

    print(f"Starting daily agent — {len(companies)} companies, DB: {settings.DB_PATH}")
    compiled = build_graph()
    final_state = compiled.invoke(initial_state)

    from notifications.email import send_digest

    match_count = len(final_state.get("scored_jobs", []))
    errors = final_state.get("errors", [])
    subject = f"Job Digest {date.today().isoformat()} — {match_count} matches"
    print(f"Pipeline complete — {match_count} matches found, {len(errors)} errors")
    if errors:
        for err in errors:
            print(f"  [error] {err}")
    print("Sending digest email...")
    send_digest(subject, final_state["report"])
    print("Done.")


if __name__ == "__main__":
    run()
