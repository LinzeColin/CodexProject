from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.system.macos_acceptance_hub import (
    acceptance_hub_summary,
    build_macos_acceptance_mode_guide,
    run_macos_acceptance_hub,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the user-friendly PFI_OS macOS acceptance hub.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument(
        "--mode",
        default="daily",
        choices=["daily", "app-entry", "lifecycle", "runtime", "app-runtime", "ui", "public-summary"],
        help="Acceptance mode. daily is the safe default.",
    )
    parser.add_argument("--list-modes", action="store_true", help="Print available modes and commands.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSMacOSAcceptanceHubV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()

    if args.list_modes:
        print(json.dumps(build_macos_acceptance_mode_guide(), ensure_ascii=False, indent=2, default=str))
        return

    payload = run_macos_acceptance_hub(project_root=Path(args.project_root), mode=args.mode)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(acceptance_hub_summary(payload), ensure_ascii=False, indent=2, default=str))
        return

    summary = payload["summary"]
    print(
        "PFI_OS_MACOS_ACCEPTANCE: "
        f"mode={payload['mode']} "
        f"status={payload['status']} "
        f"pass={summary['pass']} "
        f"fail={summary['fail']}"
    )
    print(f"PFI_OS_MACOS_ACCEPTANCE_NEXT_ACTION: {payload['next_action']}")


if __name__ == "__main__":
    main()
