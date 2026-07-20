# ================================================================
# Pitch Coach
# ================================================================
# Objective:
#       Synthesize Research Agent and Funding Advisor findings into a
#       pitch deck outline, and decide whether the workflow should end
#       or loop back to an earlier agent for more detail. This is the
#       only agent that drives the feedback-loop decision.
# Inputs:
#       - WorkflowState (reads: domain, research_findings, funding_findings,
#         revision_count)
# Outputs:
#       - Partial state update: pitch_outline, next_step ("end",
#         "research_agent", or "funding_advisor"), feedback_notes,
#         revision_count
# Notes:
#   - The model is asked to append one verdict line so the routing
#     decision stays a simple, explicit string check rather than a
#     second model call or hidden heuristic.
#   - revision_count is capped by config.MAX_PITCH_REVISIONS so the
#     feedback loop always terminates.
# ================================================================

from typing import Any

from config import MAX_PITCH_REVISIONS, get_llm
from workflow.state import WorkflowState

PITCH_PROMPT = """You are the Pitch Coach for a startup accelerator.

Startup domain: {domain}

Research Agent findings:
{research_findings}

Funding Advisor findings:
{funding_findings}

Write a pitch deck outline with these sections: Problem, Solution, Market,
Business Model, Funding Ask, Team, Traction. Base every section on the
findings above -- do not invent details that contradict them.

After the outline, on its own final line, write exactly one of:
COMPLETE
NEEDS_MORE_RESEARCH: <one sentence describing the specific gap>
NEEDS_MORE_FUNDING: <one sentence describing the specific gap>"""

VERDICT_TOKENS = ("COMPLETE", "NEEDS_MORE_RESEARCH", "NEEDS_MORE_FUNDING")


def run(state: WorkflowState) -> dict[str, Any]:
    """Call the configured OpenAI model to synthesize a pitch outline and decide on the feedback route."""
    prompt = PITCH_PROMPT.format(
        domain=state["domain"],
        research_findings=state["research_findings"],
        funding_findings=state["funding_findings"],
    )
    response = get_llm().invoke(prompt)
    text = response.content.strip()

    lines = text.splitlines()
    verdict_line = lines[-1].strip() if lines else "COMPLETE"
    has_verdict = any(verdict_line.startswith(token) for token in VERDICT_TOKENS)
    outline = "\n".join(lines[:-1]).strip() if has_verdict else text

    revision_count = state.get("revision_count", 0)

    if revision_count >= MAX_PITCH_REVISIONS or not has_verdict or verdict_line.startswith("COMPLETE"):
        return {
            "pitch_outline": outline,
            "next_step": "end",
            "feedback_notes": "",
        }

    reason = verdict_line.split(":", 1)[1].strip() if ":" in verdict_line else ""
    next_step = "research_agent" if verdict_line.startswith("NEEDS_MORE_RESEARCH") else "funding_advisor"

    return {
        "pitch_outline": outline,
        "next_step": next_step,
        "feedback_notes": reason,
        "revision_count": revision_count + 1,
    }
