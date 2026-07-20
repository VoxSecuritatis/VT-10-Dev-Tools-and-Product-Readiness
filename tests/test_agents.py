# ================================================================
# Agent Unit Tests
# ================================================================
# Objective:
#       Verify each agent's pure input/output behavior against a
#       mocked OpenAI model, including the Pitch Coach's feedback-loop
#       routing decision. No real API calls are made.
# ================================================================

from unittest.mock import MagicMock, patch

from agents import funding_advisor, pitch_coach, research_agent
from config import MAX_PITCH_REVISIONS


class FakeResponse:
    """Stand-in for a langchain_openai ChatOpenAI response."""

    def __init__(self, content: str) -> None:
        self.content = content


def make_fake_llm(content: str) -> MagicMock:
    llm = MagicMock()
    llm.invoke.return_value = FakeResponse(content)
    return llm


def test_research_agent_returns_findings() -> None:
    state = {"domain": "fintech", "feedback_notes": ""}
    with patch("agents.research_agent.get_llm", return_value=make_fake_llm("- trend one\n- trend two")):
        update = research_agent.run(state)
    assert update["research_findings"] == "- trend one\n- trend two"


def test_research_agent_includes_feedback_notes_in_prompt() -> None:
    state = {"domain": "fintech", "feedback_notes": "need more detail on regulation"}
    fake_llm = make_fake_llm("- trend")
    with patch("agents.research_agent.get_llm", return_value=fake_llm):
        research_agent.run(state)
    prompt_sent = fake_llm.invoke.call_args[0][0]
    assert "need more detail on regulation" in prompt_sent


def test_funding_advisor_returns_findings() -> None:
    state = {"domain": "fintech", "research_findings": "- trend", "feedback_notes": ""}
    with patch("agents.funding_advisor.get_llm", return_value=make_fake_llm("- grant one")):
        update = funding_advisor.run(state)
    assert update["funding_findings"] == "- grant one"


def test_pitch_coach_completes_when_verdict_is_complete() -> None:
    state = {
        "domain": "fintech",
        "research_findings": "- trend",
        "funding_findings": "- grant",
        "revision_count": 0,
    }
    outline_text = "Problem: ...\nSolution: ...\nCOMPLETE"
    with patch("agents.pitch_coach.get_llm", return_value=make_fake_llm(outline_text)):
        update = pitch_coach.run(state)
    assert update["next_step"] == "end"
    assert "COMPLETE" not in update["pitch_outline"]


def test_pitch_coach_routes_back_for_more_research() -> None:
    state = {
        "domain": "fintech",
        "research_findings": "- trend",
        "funding_findings": "- grant",
        "revision_count": 0,
    }
    outline_text = "Problem: ...\nNEEDS_MORE_RESEARCH: missing market size data"
    with patch("agents.pitch_coach.get_llm", return_value=make_fake_llm(outline_text)):
        update = pitch_coach.run(state)
    assert update["next_step"] == "research_agent"
    assert update["feedback_notes"] == "missing market size data"
    assert update["revision_count"] == 1


def test_pitch_coach_stops_looping_at_max_revisions() -> None:
    state = {
        "domain": "fintech",
        "research_findings": "- trend",
        "funding_findings": "- grant",
        "revision_count": MAX_PITCH_REVISIONS,
    }
    outline_text = "Problem: ...\nNEEDS_MORE_RESEARCH: still missing data"
    with patch("agents.pitch_coach.get_llm", return_value=make_fake_llm(outline_text)):
        update = pitch_coach.run(state)
    assert update["next_step"] == "end"
