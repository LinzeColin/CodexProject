from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.system import run_macos_runtime_acceptance, write_macos_runtime_acceptance


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled macOS runtime acceptance without full smoke.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for JSON artifacts.")
    parser.add_argument("--start-timeout", type=int, default=90, help="Seconds to wait for local Streamlit health after start.")
    parser.add_argument("--stop-timeout", type=int, default=45, help="Seconds to wait for local Streamlit health to disappear after stop.")
    parser.add_argument("--skip-app-acceptance", action="store_true", help="Skip macOS app acceptance lite precheck.")
    parser.add_argument("--launch-method", choices=["script", "app"], default="script", help="Use quiet script start or real PFI.app open.")
    parser.add_argument("--app-path", default=None, help="Optional PFI.app path when --launch-method app is used.")
    parser.add_argument(
        "--allow-existing-service",
        action="store_true",
        help="Allow using and stopping a pre-existing local service. Default is fail-closed.",
    )
    parser.add_argument("--json", action="store_true", help="Print PFIOSMacOSRuntimeAcceptanceV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()
    start_timeout = args.start_timeout
    if args.launch_method == "app" and start_timeout == 90:
        start_timeout = 300

    common = {
        "project_root": Path(args.project_root),
        "start_timeout_seconds": start_timeout,
        "stop_timeout_seconds": args.stop_timeout,
        "include_app_acceptance": not args.skip_app_acceptance,
        "allow_existing_service": args.allow_existing_service,
        "launch_method": args.launch_method,
        "app_path": Path(args.app_path).expanduser() if args.app_path else None,
    }
    if args.output_dir:
        payload = write_macos_runtime_acceptance(output_dir=Path(args.output_dir).expanduser(), **common)
    else:
        payload = run_macos_runtime_acceptance(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str))
        return
    summary = payload["summary"]
    print(
        "PFI_OS_MACOS_RUNTIME_ACCEPTANCE: "
        f"status={payload['status']} "
        f"pass={summary['pass']} "
        f"fail={summary['fail']} "
        f"info={summary['info']} "
        f"started_by_acceptance={payload['started_by_acceptance']}"
    )
    print(f"PFI_OS_MACOS_RUNTIME_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_MACOS_RUNTIME_OUTPUTS: {payload['outputs']}")


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "pre_existing_healthy_ports": payload.get("pre_existing_healthy_ports"),
        "post_healthy_ports": payload.get("post_healthy_ports"),
        "started_by_acceptance": payload.get("started_by_acceptance"),
        "launch_method": payload.get("launch_method"),
        "app_acceptance": payload.get("app_acceptance"),
        "failed_checks": [
            row
            for row in payload.get("checks", [])
            if isinstance(row, dict) and row.get("status") == "Fail"
        ],
        "heavy_smoke_policy": payload.get("heavy_smoke_policy"),
        "safety_boundary": payload.get("safety_boundary"),
        "next_action": payload.get("next_action"),
    }


if __name__ == "__main__":
    main()
