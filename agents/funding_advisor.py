# ================================================================
# Funding Advisor
# ================================================================
# Objective:
#       Recommend grants and funding programs relevant to a startup
#       domain, using the Research Agent's findings as context. Pure
#       LLM-calling logic only -- memory lookups/writes and trace
#       logging are owned by workflow/graph.py, not this module.
# Inputs:
#       - WorkflowState (reads: domain, research_findings, feedback_notes)
#       - Optional prior_context string retrieved from vector memory
# Outputs:
#       - Partial state update: {"funding_findings": str}
# Notes:
#   - When feedback_notes is set (Pitch Coach asked for more detail),
#     the prompt includes it so this pass can address the gap.
# ================================================================

from typing import Any

from config import get_llm
from workflow.state import WorkflowState

FUNDING_PROMPT = """You are the Funding Advisor for a startup accelerator.

Startup domain: {domain}

Research Agent findings:
{research_findings}
{prior_context_section}{feedback_section}
Recommend 3-5 specific, real categories of grants or funding programs suited to
this domain and stage (for example: domain-specific accelerator grants,
government innovation grants, sector-focused VC funds). For each, note why it
fits the domain and research findings above. Respond as a short bulleted list."""


def run(state: WorkflowState, prior_context: str = "") -> dict[str, Any]:
    """Call the configured OpenAI model to produce funding recommendations grounded in the research findings."""
    prior_context_section = f"\nPrior funding notes on record for this domain:\n{prior_context}\n" if prior_context else ""
    feedback_section = (
        f"\nThe Pitch Coach asked for more detail: {state['feedback_notes']}\n"
        if state.get("feedback_notes")
        else ""
    )
    prompt = FUNDING_PROMPT.format(
        domain=state["domain"],
        research_findings=state["research_findings"],
        prior_context_section=prior_context_section,
        feedback_section=feedback_section,
    )
    response = get_llm().invoke(prompt)
    return {"funding_findings": response.content}
