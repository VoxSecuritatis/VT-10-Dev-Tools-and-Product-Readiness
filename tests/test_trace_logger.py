# ================================================================
# Trace Logger Tests
# ================================================================
# Objective:
#       Verify log_event() writes one well-formed JSONL line per call
#       and appends correctly across multiple calls in the same run.
# ================================================================

import json

from observability import trace_logger


def test_log_event_writes_expected_jsonl_line(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(trace_logger, "LOGS_DIR", tmp_path)

    state_before = {"domain": "fintech", "feedback_notes": "", "revision_count": 0}
    update = {"research_findings": "- trend one"}

    trace_logger.log_event(run_id="test-run", agent="research_agent", state_before=state_before, update=update)

    log_path = tmp_path / "run_test-run.jsonl"
    assert log_path.exists()

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    event = json.loads(lines[0])
    assert event["run_id"] == "test-run"
    assert event["agent"] == "research_agent"
    assert event["state_written"] == update
    assert event["state_read"]["domain"] == "fintech"


def test_log_event_appends_multiple_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(trace_logger, "LOGS_DIR", tmp_path)

    state_before = {"domain": "fintech", "feedback_notes": "", "revision_count": 0}
    trace_logger.log_event("test-run", "research_agent", state_before, {"a": 1})
    trace_logger.log_event("test-run", "funding_advisor", state_before, {"b": 2})

    log_path = tmp_path / "run_test-run.jsonl"
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
