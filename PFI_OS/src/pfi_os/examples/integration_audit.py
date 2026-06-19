from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.integrations.research_bus import RESEARCH_BUS_DB_PATH
from pfi_os.system import build_pfi_os_integration_audit, write_pfi_os_integration_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the read-only PFIOS integration audit.")
    parser.add_argument("--date", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="PFIOS report root.")
    parser.add_argument("--db-path", default=str(RESEARCH_BUS_DB_PATH), help="ResearchBus SQLite path.")
    parser.add_argument("--ai-research-root", default=None, help="Optional AI-Research-System root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for JSON/Markdown artifacts.")
    parser.add_argument("--no-write", action="store_true", help="Do not write audit artifacts.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON payload.")
    args = parser.parse_args()

    common = {
        "as_of": args.date,
        "project_root": Path(args.project_root).expanduser(),
        "report_root": Path(args.report_root).expanduser(),
        "db_path": Path(args.db_path).expanduser(),
        "ai_research_root": Path(args.ai_research_root).expanduser() if args.ai_research_root else None,
    }
    if args.no_write:
        payload = build_pfi_os_integration_audit(**common)
    else:
        payload = write_pfi_os_integration_audit(
            **common,
            output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    print(f"PFI_INTEGRATION_AUDIT: {payload['status']} {payload['as_of']}")
    print(f"summary: {payload['summary']}")
    for item in payload["items"]:
        print(f"- {item['layer']}: {item['status']} - {item['summary']}")
    if not args.no_write and "outputs" in payload:
        print(f"json: {payload['outputs']['json']}")
        print(f"markdown: {payload['outputs']['markdown']}")


if __name__ == "__main__":
    main()
