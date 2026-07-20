# ================================================================
# Workflow Graph Tests
# ================================================================
# Objective:
#       Verify the compiled LangGraph workflow end to end against
#       mocked OpenAI models: the happy path (no feedback loop) and a
#       feedback-loop path where the Pitch Coach routes back to the
#       Research Agent once before completing. Memory and logging
#       calls are mocked so tests don't touch disk or require network.
# ================================================================

from unittest.mock import MagicMock, patch

from workflow.graph import run_workflow


class FakeResponse:
    """Stand-in for a langchain_openai ChatOpenAI response."""

    def __init__(self, content: str) -> None:
        self.content = content


def make_fake_llm(contents: list[str]) -> MagicMock:
    """Return a mock LLM whose invoke() yields the given contents in order."""
    llm = MagicMock()
    llm.invoke.side_effect = [FakeResponse(content) for content in contents]
    return llm


def test_happy_path_completes_without_looping() -> None:
    with (
        patch("agents.research_agent.get_llm", return_value=make_fake_llm(["- market trend"])),
        patch("agents.funding_advisor.get_llm", return_value=make_fake_llm(["- funding program"])),
        patch("agents.pitch_coach.get_llm", return_value=make_fake_llm(["Problem: ...\nCOMPLETE"])),
        patch("workflow.graph.add_finding"),
        patch("workflow.graph.query_similar", return_value=""),
        patch("workflow.graph.log_event"),
        patch("workflow.graph.send_trace"),
    ):
        final_state = run_workflow("fintech")

    assert final_state["next_step"] == "end"
    assert "Problem" in final_state["pitch_outline"]
    assert final_state["revision_count"] == 0


def test_feedback_loop_routes_back_then_completes() -> None:
    with (
        patch(
            "agents.research_agent.get_llm",
            return_value=make_fake_llm(["- market trend v1", "- market trend v2"]),
        ),
        patch(
            "agents.funding_advisor.get_llm",
            return_value=make_fake_llm(["- funding program v1", "- funding program v2"]),
        ),
        patch(
            "agents.pitch_coach.get_llm",
            return_value=make_fake_llm(
                [
                    "Problem: ...\nNEEDS_MORE_RESEARCH: need market size",
                    "Problem: ...\nCOMPLETE",
                ]
            ),
        ),
        patch("workflow.graph.add_finding"),
        patch("workflow.graph.query_similar", return_value=""),
        patch("workflow.graph.log_event"),
        patch("workflow.graph.send_trace"),
    ):
        final_state = run_workflow("healthtech")

    assert final_state["next_step"] == "end"
    assert final_state["revision_count"] == 1
