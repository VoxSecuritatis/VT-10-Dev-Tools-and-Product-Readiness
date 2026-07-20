# ================================================================
# CLI Interface
# ================================================================
# Objective:
#       Command-line entry point for running the multi-agent workflow
#       end to end: accept a startup domain, run the workflow, and
#       print the resulting pitch deck outline plus the trace log path.
# Inputs:
#       - --domain command-line argument (e.g. "fintech")
# Outputs:
#       - Printed pitch deck outline
#       - logs/run_<run_id>.jsonl written as a side effect of the workflow
# Notes:
#   - Calls workflow.graph.run_workflow(), the same entry point used by
#     interface/notebook_gui.ipynb, so both interfaces share one path.
# ================================================================

import argparse

from config import LOGS_DIR
from workflow.graph import run_workflow


def parse_args() -> argparse.Namespace:
    """Parse the --domain command-line argument."""
    parser = argparse.ArgumentParser(
        description="Generate a pitch deck outline for a startup domain via the "
        "Research Agent, Funding Advisor, and Pitch Coach."
    )
    parser.add_argument(
        "--domain",
        required=True,
        help='Startup domain or industry, e.g. "fintech" or "healthtech".',
    )
    return parser.parse_args()


def main() -> None:
    """Run the workflow for the given domain and print the resulting pitch outline."""
    args = parse_args()
    final_state = run_workflow(args.domain)

    log_path = LOGS_DIR / f"run_{final_state['run_id']}.jsonl"
    print(f"\nPitch deck outline for domain: {final_state['domain']}\n")
    print(final_state["pitch_outline"])
    print(f"\n[INFO] Trace log written to {log_path}")


if __name__ == "__main__":
    main()
