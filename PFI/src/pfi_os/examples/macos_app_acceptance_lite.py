from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.system import build_macos_app_acceptance_lite, write_macos_app_acceptance_lite


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a lightweight macOS PFI app acceptance check without full smoke.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for JSON artifacts.")
    parser.add_argument("--skip-codesign", action="store_true", help="Skip codesign verification for fixture/testing use.")
    parser.add_argument("--skip-dry-run", action="store_true", help="Skip PFI_APP_LAUNCH_DRY_RUN launcher checks.")
    parser.add_argument("--skip-status-script", action="store_true", help="Skip scripts/statusPFI.sh execution.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSMacOSAppAcceptanceLiteV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "skip_codesign": args.skip_codesign,
        "run_dry_run": not args.skip_dry_run,
        "run_status_script": not args.skip_status_script,
    }
    if args.output_dir:
        payload = write_macos_app_acceptance_lite(output_dir=Path(args.output_dir).expanduser(), **common)
    else:
        payload = build_macos_app_acceptance_lite(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str))
        return
    summary = payload["summary"]
    print(
        "PFI_MACOS_APP_ACCEPTANCE_LITE: "
        f"status={payload['status']} "
        f"pass={summary['pass']} "
        f"fail={summary['fail']} "
        f"info={summary['info']} "
        f"runtime={payload['runtime_status']['status']}"
    )
    print(f"PFI_MACOS_APP_ACCEPTANCE_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_MACOS_APP_ACCEPTANCE_OUTPUTS: {payload['outputs']}")


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "runtime_status": payload.get("runtime_status"),
        "heavy_smoke_policy": payload.get("heavy_smoke_policy"),
        "safety_boundary": payload.get("safety_boundary"),
        "next_action": payload.get("next_action"),
    }


if __name__ == "__main__":
    main()
