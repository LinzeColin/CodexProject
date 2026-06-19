from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.system import write_data_trust_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a read-only PFIOS Data Trust audit.")
    parser.add_argument("--date", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="PFIOS report root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for audit artifacts.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON payload.")
    args = parser.parse_args()

    payload = write_data_trust_audit(
        as_of=args.date,
        project_root=Path(args.project_root).expanduser(),
        report_root=Path(args.report_root).expanduser(),
        output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    print(f"PFI_DATA_TRUST_AUDIT: {payload['audit_status']} {payload['as_of']}")
    print(f"records: {payload['record_count']}")
    print(f"status_counts: {payload['status_counts']}")
    print(f"json: {payload['outputs']['json']}")
    print(f"csv: {payload['outputs']['csv']}")
    print(f"markdown: {payload['outputs']['markdown']}")
    print(f"pdf: {payload['outputs']['pdf']}")


if __name__ == "__main__":
    main()
