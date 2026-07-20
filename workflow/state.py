# ================================================================
# Workflow State
# ================================================================
# Objective:
#       Define the shared state object that flows through every node of
#       the LangGraph workflow. Each node reads the fields it needs and
#       returns a partial update; LangGraph merges updates into this
#       state, which is also what gets logged at every transition.
# Inputs:
#       - none (schema only)
# Outputs:
#       - WorkflowState TypedDict imported by agents/, workflow/graph.py,
#         and observability/trace_logger.py
# Notes:
#   - revision_count and feedback_notes exist to support the
#     feedback-driven loop: the Pitch Coach can send work back to an
#     earlier agent instead of finishing immediately.
# ================================================================

from typing import TypedDict


class WorkflowState(TypedDict):
    """Shared state passed between Research Agent, Funding Advisor, and Pitch Coach nodes."""

    run_id: str
    domain: str
    research_findings: str
    funding_findings: str
    pitch_outline: str
    feedback_notes: str
    revision_count: int
    next_step: str
