from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.system.dev_readiness import build_dev_ready_check, write_dev_ready_check


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the lightweight PFI_OS development readiness check.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for JSON artifacts.")
    parser.add_argument("--skip-status-script", action="store_true", help="Skip scripts/statusPFI.sh execution.")
    parser.add_argument("--skip-cache-preview", action="store_true", help="Skip cache cleanup dry-run summary.")
    parser.add_argument("--skip-git-status", action="store_true", help="Skip git status inspection.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSDevReadyCheckV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "run_status_script": not args.skip_status_script,
        "include_cache_preview": not args.skip_cache_preview,
        "check_git_status": not args.skip_git_status,
    }
    if args.output_dir:
        payload = write_dev_ready_check(output_dir=Path(args.output_dir).expanduser(), **common)
    else:
        payload = build_dev_ready_check(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str))
        return
    summary = payload["summary"]
    print(
        "PFI_OS_DEV_READY_CHECK: "
        f"status={payload['status']} "
        f"pass={summary['pass']} "
        f"fail={summary['fail']} "
        f"info={summary['info']} "
        f"runtime={payload['runtime_status']['status']} "
        f"cache_candidates={payload['cache_preview'].get('candidate_count', 'skipped')} "
        f"git={payload['git_status'].get('status', 'Skipped')}"
    )
    print(f"PFI_OS_DEV_READY_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_DEV_READY_OUTPUTS: {payload['outputs']}")


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "runtime_status": payload.get("runtime_status"),
        "cache_preview": payload.get("cache_preview"),
        "git_status": payload.get("git_status"),
        "default_gate_policy": payload.get("default_gate_policy"),
        "safety_boundary": payload.get("safety_boundary"),
        "next_action": payload.get("next_action"),
    }


if __name__ == "__main__":
    main()
