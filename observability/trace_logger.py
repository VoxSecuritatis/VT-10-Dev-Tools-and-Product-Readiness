# ================================================================
# Trace Logger
# ================================================================
# Objective:
#       Write one structured JSONL line per workflow node transition,
#       capturing agent name, revision number, a summary of state read
#       and written, and a timestamp. This is the always-on logging
#       path required by the rubric ("structured local logging") and
#       is independent of whether Azure telemetry is configured.
# Inputs:
#       - run_id, agent name, state before the node ran, and the
#         partial state update the node returned
# Outputs:
#       - Appends to logs/run_<run_id>.jsonl
# Notes:
#   - Kept deliberately simple (plain JSON lines) so the log is easy
#     to read, diff, or replay without any extra tooling.
# ================================================================

import json
from datetime import datetime, timezone
from typing import Any

from config import LOGS_DIR


def log_event(run_id: str, agent: str, state_before: dict[str, Any], update: dict[str, Any]) -> None:
    """Append one structured trace event for a workflow node transition."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "agent": agent,
        "revision_count": state_before.get("revision_count", 0),
        "state_read": {
            "domain": state_before.get("domain", ""),
            "feedback_notes": state_before.get("feedback_notes", ""),
        },
        "state_written": update,
    }
    log_path = LOGS_DIR / f"run_{run_id}.jsonl"
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(event) + "\n")
