# ================================================================
# Azure Telemetry (optional)
# ================================================================
# Objective:
#       Send workflow node transitions to Azure Application Insights as
#       trace spans, when configured. This is the real Azure
#       integration decided on for the "Deployment Readiness and
#       Scaling" tie-in -- it must never block a run when Azure is not
#       set up, since the local JSONL trace log (observability/
#       trace_logger.py) is always the source of truth regardless.
# Inputs:
#       - run_id, agent name, state before the node ran, and the
#         partial state update the node returned
# Outputs:
#       - Spans sent to Azure Monitor if AZURE_APPINSIGHTS_CONNECTION_STRING
#         is set; otherwise a single [INFO] log line, no network call
# Notes:
#   - configure_azure_monitor() wires up a process-wide OpenTelemetry
#     exporter and must only run once per process, so a module-level
#     guard is used here deliberately (not general mutable state).
# ================================================================

import logging
from typing import Any

from config import AZURE_APPINSIGHTS_CONNECTION_STRING

logger = logging.getLogger(__name__)

_azure_monitor_configured = False
_tracer = None


def _ensure_configured() -> bool:
    """Configure Azure Monitor once, on first use, if a connection string is present."""
    global _azure_monitor_configured, _tracer

    if not AZURE_APPINSIGHTS_CONNECTION_STRING:
        return False

    if not _azure_monitor_configured:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry import trace

        configure_azure_monitor(connection_string=AZURE_APPINSIGHTS_CONNECTION_STRING)
        _tracer = trace.get_tracer(__name__)
        _azure_monitor_configured = True

    return True


def send_trace(run_id: str, agent: str, state_before: dict[str, Any], update: dict[str, Any]) -> None:
    """Send one workflow node transition to Azure Application Insights, if configured."""
    if not _ensure_configured():
        logger.info("[INFO] Azure telemetry not configured, using local logging only.")
        return

    with _tracer.start_as_current_span(f"agent.{agent}") as span:
        span.set_attribute("run_id", run_id)
        span.set_attribute("agent", agent)
        span.set_attribute("domain", state_before.get("domain", ""))
        span.set_attribute("revision_count", state_before.get("revision_count", 0))
        span.set_attribute("next_step", update.get("next_step", ""))
