"""Node: build the HTML email digest from scored job listings.

Groups jobs by tier (1 → 4), formats each listing with title, company,
score, reason, and apply link, and appends any non-fatal errors to the footer.
"""

from collections import defaultdict

from agent.state import AgentState


def format_report(state: AgentState) -> dict:
    """Build the HTML email body from state['scored_jobs'].

    Groups jobs by their tier field (ascending). Each job card includes:
        - Job title (linked to url)
        - Company name and location
        - Fit score (e.g. 8/10)
        - One-sentence reason from Gemini
        - Direct apply link button

    If scored_jobs is empty, returns a brief "no new matches today" HTML body.
    Any messages in state['errors'] are rendered in the email footer.

    Args:
        state: Current agent state with 'scored_jobs' and 'errors' populated.

    Returns:
        Partial state dict with 'report' key set to the HTML string.
    """
    scored_jobs: list[dict] = state.get("scored_jobs", [])
    errors: list[str] = state.get("errors", [])

    if not scored_jobs:
        return {"report": _no_matches_html(errors)}

    by_tier: dict[int, list[dict]] = defaultdict(list)
    for job in scored_jobs:
        by_tier[job.get("tier", 99)].append(job)

    sections = [_render_tier(tier, by_tier[tier]) for tier in sorted(by_tier)]

    html = (
        '<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;'
        'max-width:700px;margin:auto;padding:20px;">'
        "<h1>Job Search Digest</h1>"
        + "".join(sections)
        + _errors_footer(errors)
        + "</body></html>"
    )
    return {"report": html}


def _render_tier(tier: int, jobs: list[dict]) -> str:
    cards = "".join(_render_card(job) for job in jobs)
    return f'<h2 style="color:#555;border-bottom:2px solid #eee;">Tier {tier}</h2>{cards}'


def _render_card(job: dict) -> str:
    url = job.get("url", "#")
    return (
        '<div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:16px;">'
        f'<h3 style="margin:0 0 4px;"><a href="{url}" style="color:#0066cc;">{job.get("title","")}</a></h3>'
        f'<p style="color:#666;margin:4px 0;">{job.get("company","")} — {job.get("location","")}</p>'
        f'<p style="margin:8px 0;"><strong>Score: {job.get("fit_score","?")}/10</strong>'
        f' — {job.get("reason","")}</p>'
        f'<a href="{url}" style="background:#0066cc;color:white;padding:8px 16px;'
        f'border-radius:4px;text-decoration:none;">Apply</a>'
        "</div>"
    )


def _no_matches_html(errors: list[str]) -> str:
    return (
        '<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;'
        'max-width:700px;margin:auto;padding:20px;">'
        "<h1>Job Search Digest</h1>"
        "<p>No new matching jobs today.</p>"
        + _errors_footer(errors)
        + "</body></html>"
    )


def _errors_footer(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{e}</li>" for e in errors)
    return (
        '<div style="margin-top:40px;border-top:1px solid #eee;padding-top:16px;'
        'color:#999;font-size:12px;">'
        f"<strong>Pipeline errors (non-fatal):</strong><ul>{items}</ul></div>"
    )
