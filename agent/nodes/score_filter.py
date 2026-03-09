"""Node: score job listings for fit using Gemini 2.0 Flash.

Batches all deduplicated jobs into a single LLM prompt (never one call per job).
The scoring prompt is loaded from config/scoring_prompt.txt at runtime.
Jobs below settings.SCORE_THRESHOLD are filtered out.
"""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import config.settings as settings
from agent.state import AgentState

_PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "scoring_prompt.txt"


def score_filter(state: AgentState) -> dict:
    """Score all deduplicated jobs in a single Gemini API call and filter by threshold.

    Steps:
        1. Load the scoring prompt from config/scoring_prompt.txt.
        2. Build a JSON payload of all jobs in state['deduplicated'].
        3. Call Gemini via ChatGoogleGenerativeAI (one batch request).
        4. Parse the JSON response: list of {job_id, fit_score, reason}.
        5. Merge scores back into the job dicts.
        6. Filter to jobs where fit_score >= settings.SCORE_THRESHOLD.

    Non-fatal errors (e.g. JSON parse failure, partial response) are
    appended to state['errors'].

    Args:
        state: Current agent state with 'deduplicated' populated.

    Returns:
        Partial state dict with 'scored_jobs' and 'errors' keys updated.
    """
    errors: list[str] = list(state.get("errors", []))

    if not state["deduplicated"]:
        return {"scored_jobs": [], "errors": errors}

    try:
        prompt_text = _PROMPT_PATH.read_text()

        jobs_payload = [
            {
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "description": job.get("description", "")[:800],
            }
            for job in state["deduplicated"]
        ]

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
        )
        message = HumanMessage(content=f"{prompt_text}\n\n{json.dumps(jobs_payload)}")
        response = llm.invoke([message])

        raw = str(response.content).strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(raw)
        score_map = {item["job_id"]: item for item in scores}

        scored_jobs = []
        for job in state["deduplicated"]:
            score_data = score_map.get(job["job_id"])
            if score_data:
                job_with_score = {
                    **job,
                    "fit_score": score_data["fit_score"],
                    "reason": score_data["reason"],
                }
                if job_with_score["fit_score"] >= settings.SCORE_THRESHOLD:
                    scored_jobs.append(job_with_score)

        return {"scored_jobs": scored_jobs, "errors": errors}

    except Exception as e:
        errors.append(f"Gemini scoring error: {e}")
        return {"scored_jobs": [], "errors": errors}
