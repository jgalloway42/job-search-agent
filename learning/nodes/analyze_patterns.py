"""Node: use Gemini to analyze patterns in application outcomes."""

import json

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import config.settings as settings
from learning.state import LearningState


def analyze_patterns(state: LearningState) -> dict:
    """Ask Gemini to identify what applied/responded jobs had in common.

    Builds a structured prompt from state['applications'] that includes:
        - Jobs applied to (with title, company, score, reason)
        - Which got responses (phone_screen, final_round, offer)
        - Which were rejected or silent

    Sends a single Gemini call via ChatGoogleGenerativeAI and stores the
    analysis text in state['analysis'].

    Non-fatal errors (e.g. API failure, empty applications list) are
    appended to state['errors'].

    Args:
        state: Current learning state with 'applications' populated.

    Returns:
        Partial state dict with 'analysis' key set to Gemini's response text.
    """
    errors: list[str] = list(state.get("errors", []))

    if not state.get("applications"):
        errors.append("analyze_patterns: no applications to analyze — skipping")
        return {"analysis": "", "errors": errors}

    try:
        responded = [
            a for a in state["applications"]
            if a.get("outcome") in {"phone_screen", "final_round", "offer"}
        ]
        rejected = [
            a for a in state["applications"]
            if a.get("outcome") == "rejected"
        ]
        silent = [
            a for a in state["applications"]
            if a.get("outcome") is None
        ]

        def fmt(apps: list[dict]) -> str:
            return json.dumps([
                {
                    "title": a.get("title"),
                    "company": a.get("company"),
                    "tier": a.get("tier"),
                    "fit_score": a.get("fit_score"),
                    "score_reason": a.get("score_reason"),
                }
                for a in apps
            ], indent=2)

        prompt = f"""You are analyzing job application outcomes to improve a scoring prompt.

## Jobs that received a response (phone_screen / final_round / offer):
{fmt(responded)}

## Jobs that were rejected:
{fmt(rejected)}

## Jobs with no response yet (silent):
{fmt(silent)}

Analyze the patterns above. Identify:
1. What traits do the jobs that received responses share (title keywords, company tier, domain, seniority)?
2. What traits are common among rejections or silent applications?
3. What specific criteria should be weighted more or less heavily in future job scoring?

Provide a concise analysis (3-5 bullet points per section). Be specific and actionable."""

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"analysis": str(response.content), "errors": errors}

    except Exception as e:
        errors.append(f"analyze_patterns Gemini error: {e}")
        return {"analysis": "", "errors": errors}
