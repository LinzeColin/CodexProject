from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.integrations.workspace_systems import compact_workspace_system_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize PFI_OS workspace systems for ResearchBus/UI use.")
    parser.add_argument("--systems-root", default="", help="Optional systems/ root.")
    parser.add_argument("--system", action="append", default=[], help="Limit output to one or more system ids.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any selected system is not adapter-ready.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    systems_root = Path(args.systems_root).expanduser() if args.systems_root else None
    system_ids = tuple(args.system) if args.system else None
    payload = compact_workspace_system_payload(
        systems_root=systems_root,
        system_ids=system_ids or ("finance_ledger", "industry_research", "policy_intelligence"),
    )
    payload["status"] = "Pass" if payload["review_count"] == 0 else "Review"
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{payload['status']}: {payload['ready_count']}/{payload['system_count']} workspace systems ready")
        if payload["review_systems"]:
            print("review_systems:", ", ".join(payload["review_systems"]))
    if args.check and payload["review_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
