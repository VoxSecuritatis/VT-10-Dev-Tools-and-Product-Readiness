# ================================================================
# Workflow Graph
# ================================================================
# Objective:
#       Wire the Research Agent, Funding Advisor, and Pitch Coach into
#       a LangGraph StateGraph: a fixed sequential path
#       (research -> funding -> pitch coach) plus a conditional edge
#       out of the Pitch Coach that implements the feedback loop,
#       routing back to whichever agent needs to refine its output.
#       Memory persistence and trace logging are owned here, in the
#       node wrapper functions, keeping agents/ free of I/O.
# Inputs:
#       - A startup domain string, via run_workflow()
# Outputs:
#       - The final WorkflowState, including pitch_outline and the
#         full revision history implied by revision_count
# Notes:
#   - The feedback loop is capped by config.MAX_PITCH_REVISIONS
#     (enforced inside agents/pitch_coach.py) so it always terminates.
# ================================================================

import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from agents import funding_advisor, pitch_coach, research_agent
from memory.vector_store import add_finding, query_similar
from observability.azure_telemetry import send_trace
from observability.trace_logger import log_event
from workflow.state import WorkflowState


def research_node(state: WorkflowState) -> dict[str, Any]:
    """Run the Research Agent, persist its finding to memory, and log the transition."""
    prior_context = query_similar(state["domain"], agent="research_agent")
    update = research_agent.run(state, prior_context=prior_context)
    add_finding(domain=state["domain"], agent="research_agent", text=update["research_findings"])
    log_event(state["run_id"], "research_agent", state, update)
    send_trace(state["run_id"], "research_agent", state, update)
    return update


def funding_node(state: WorkflowState) -> dict[str, Any]:
    """Run the Funding Advisor, persist its finding to memory, and log the transition."""
    prior_context = query_similar(state["domain"], agent="funding_advisor")
    update = funding_advisor.run(state, prior_context=prior_context)
    add_finding(domain=state["domain"], agent="funding_advisor", text=update["funding_findings"])
    log_event(state["run_id"], "funding_advisor", state, update)
    send_trace(state["run_id"], "funding_advisor", state, update)
    return update


def pitch_node(state: WorkflowState) -> dict[str, Any]:
    """Run the Pitch Coach and log the transition, including its routing decision."""
    update = pitch_coach.run(state)
    log_event(state["run_id"], "pitch_coach", state, update)
    send_trace(state["run_id"], "pitch_coach", state, update)
    return update


def route_after_pitch_coach(state: WorkflowState) -> str:
    """Read the Pitch Coach's next_step decision and route the graph accordingly."""
    return state["next_step"]


def build_graph():
    """Build and compile the research -> funding -> pitch coach LangGraph workflow."""
    graph = StateGraph(WorkflowState)
    graph.add_node("research_agent", research_node)
    graph.add_node("funding_advisor", funding_node)
    graph.add_node("pitch_coach", pitch_node)

    graph.set_entry_point("research_agent")
    graph.add_edge("research_agent", "funding_advisor")
    graph.add_edge("funding_advisor", "pitch_coach")
    graph.add_conditional_edges(
        "pitch_coach",
        route_after_pitch_coach,
        {
            "end": END,
            "research_agent": "research_agent",
            "funding_advisor": "funding_advisor",
        },
    )

    return graph.compile()


def run_workflow(domain: str) -> WorkflowState:
    """Run the full workflow for a startup domain and return the final state.

    This is the single entry point shared by interface/cli.py and
    interface/notebook_gui.ipynb, so both interfaces execute identical logic.
    """
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    initial_state: WorkflowState = {
        "run_id": run_id,
        "domain": domain,
        "research_findings": "",
        "funding_findings": "",
        "pitch_outline": "",
        "feedback_notes": "",
        "revision_count": 0,
        "next_step": "",
    }
    app = build_graph()
    return app.invoke(initial_state)
