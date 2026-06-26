from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.policy import build_policy_radar, write_policy_radar


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the PFI_OS Policy Intelligence Radar snapshot.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--entry-path", default=None, help="Optional policy opportunity JSON path.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/policy.")
    parser.add_argument("--opportunity-limit", type=int, default=300, help="Maximum policy opportunities to include.")
    parser.add_argument("--json-only", action="store_true", help="Build and print JSON without writing files.")
    parser.add_argument("--summary-json", action="store_true", help="Print only PFIOSPolicyIntelligenceRuntimeSummaryV1 for low-token checks.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "entry_path": Path(args.entry_path).expanduser() if args.entry_path else None,
        "opportunity_limit": args.opportunity_limit,
    }
    if args.json_only or args.summary_json:
        payload = build_policy_radar(**common)
        if args.summary_json:
            print(json.dumps(payload.get("runtime_summary", {}), ensure_ascii=False, indent=2, default=str))
            return
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    payload = write_policy_radar(output_dir=Path(args.output_dir).expanduser() if args.output_dir else None, **common)
    summary = payload["summary"]
    print(
        "PFI_OS_POLICY_RADAR: "
        f"status={payload['policy_status']} "
        f"opportunities={payload['opportunity_count']} "
        f"actionable={summary.get('actionable_count', 0)} "
        f"missing_evidence={summary.get('missing_evidence_count', 0)} "
        f"as_of={payload['as_of']}"
    )
    print(f"PFI_OS_POLICY_RUNTIME_STATUS: {payload.get('runtime_summary', {}).get('status')}")
    print(f"PFI_OS_POLICY_OUTPUTS: {payload.get('outputs', {})}")


if __name__ == "__main__":
    main()
