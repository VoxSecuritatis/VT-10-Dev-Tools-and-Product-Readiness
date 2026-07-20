# ================================================================
# Azure Telemetry Tests
# ================================================================
# Objective:
#       Verify send_trace() degrades gracefully (logs an [INFO] line,
#       makes no network call) when Azure is not configured. This is
#       the required behavior since the project must run end to end
#       with zero Azure setup.
# ================================================================

import logging

from observability import azure_telemetry


def test_send_trace_noop_when_not_configured(monkeypatch, caplog) -> None:
    monkeypatch.setattr(azure_telemetry, "AZURE_APPINSIGHTS_CONNECTION_STRING", "")
    monkeypatch.setattr(azure_telemetry, "_azure_monitor_configured", False)

    with caplog.at_level(logging.INFO):
        azure_telemetry.send_trace(
            run_id="test-run",
            agent="research_agent",
            state_before={"domain": "fintech", "revision_count": 0},
            update={"next_step": "end"},
        )

    assert "Azure telemetry not configured" in caplog.text
