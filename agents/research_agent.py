# ================================================================
# Research Agent
# ================================================================
# Objective:
#       Gather domain-specific market trends and insights for a startup
#       domain. Pure LLM-calling logic only -- memory lookups/writes and
#       trace logging are owned by workflow/graph.py, not this module.
# Inputs:
#       - WorkflowState (reads: domain, feedback_notes)
#       - Optional prior_context string retrieved from vector memory
# Outputs:
#       - Partial state update: {"research_findings": str}
# Notes:
#   - When feedback_notes is set (Pitch Coach asked for more detail),
#     the prompt includes it so this pass can address the gap.
# ================================================================

from typing import Any

from config import get_llm
from workflow.state import WorkflowState

RESEARCH_PROMPT = """You are the Research Agent for a startup accelerator.

Startup domain: {domain}
{prior_context_section}{feedback_section}
Identify 3-5 concise, specific, current market trends and insights relevant to a
founder pitching in this domain. Avoid generic filler. Respond as a short
bulleted list."""


def run(state: WorkflowState, prior_context: str = "") -> dict[str, Any]:
    """Call the configured OpenAI model to produce market trends and insights for the given domain."""
    prior_context_section = f"\nPrior research on record for this domain:\n{prior_context}\n" if prior_context else ""
    feedback_section = (
        f"\nThe Pitch Coach asked for more detail: {state['feedback_notes']}\n"
        if state.get("feedback_notes")
        else ""
    )
    prompt = RESEARCH_PROMPT.format(
        domain=state["domain"],
        prior_context_section=prior_context_section,
        feedback_section=feedback_section,
    )
    response = get_llm().invoke(prompt)
    return {"research_findings": response.content}
