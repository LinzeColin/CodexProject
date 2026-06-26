from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.system import build_daily_readiness, write_daily_readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a read-only PFIOS daily readiness check.")
    parser.add_argument("--date", default=None, help="Readiness date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="PFIOS report root.")
    parser.add_argument("--output-dir", default="", help="Optional output directory for JSON/Markdown/PDF readiness artifacts.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON payload.")
    args = parser.parse_args()

    common = {
        "as_of": args.date,
        "project_root": Path(args.project_root).expanduser(),
        "report_root": Path(args.report_root).expanduser(),
    }
    if args.output_dir:
        payload = write_daily_readiness(
            **common,
            output_dir=Path(args.output_dir).expanduser(),
        )
    else:
        payload = build_daily_readiness(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    print(f"PFI_DAILY_READINESS: {payload['readiness_status']} {payload['as_of']}")
    print(f"health_summary: {payload['health_summary']}")
    print(f"provider_summary: {payload['provider_summary']}")
    print("")
    print("Core Gates:")
    for row in payload["core_gates"]:
        print(f"- {row['gate']}: {row['status']} - {row['evidence']}")
    print("")
    print("Action Items:")
    for item in payload["action_items"]:
        print(f"- {item}")
    if args.output_dir and "outputs" in payload:
        print("")
        print(f"json: {payload['outputs']['json']}")
        print(f"markdown: {payload['outputs']['markdown']}")
        print(f"pdf: {payload['outputs']['pdf']}")


if __name__ == "__main__":
    main()
