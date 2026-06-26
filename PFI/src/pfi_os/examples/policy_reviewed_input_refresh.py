from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.policy import refresh_policy_from_reviewed_input


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Policy Intelligence outputs from a local reviewed input file.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--entry-path", default=None, help="Reviewed policy input JSON. Defaults to data/private/policy/PolicyReviewedInput.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/policy.")
    parser.add_argument("--opportunity-limit", type=int, default=300, help="Maximum policy opportunities to include.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSPolicyReviewedInputRefreshV1 as JSON.")
    args = parser.parse_args()

    payload = refresh_policy_from_reviewed_input(
        as_of=args.as_of,
        project_root=Path(args.project_root),
        entry_path=Path(args.entry_path).expanduser() if args.entry_path else None,
        output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
        opportunity_limit=args.opportunity_limit,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    print(
        "PFI_OS_POLICY_REVIEWED_INPUT_REFRESH: "
        f"status={payload['status']} "
        f"policy_status={payload['policy_status']} "
        f"input_status={payload['input_status']} "
        f"opportunities={summary.get('opportunity_count')} "
        f"actionable={summary.get('actionable_count')} "
        f"max_impact={summary.get('max_impact_score')} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("next_action"):
        print(f"PFI_OS_POLICY_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_POLICY_REVIEWED_INPUT_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
