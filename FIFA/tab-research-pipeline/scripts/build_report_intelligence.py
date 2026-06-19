#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tab_research.report_intelligence import write_report_intelligence_bundle
from tab_research.paths import resolve_output_dir, resolve_workspace_root


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))
DB_PATH = OUTPUT_DIR / "tab_fifa_reports.sqlite3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the TAB FIFA report intelligence JSON/Markdown/PDF bundle.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = write_report_intelligence_bundle(args.output_dir, args.db_path)
    summary = {
        "status": "ok",
        "json": payload.get("artifacts", {}).get("json", "report_intelligence_latest.json"),
        "markdown": payload.get("artifacts", {}).get("markdown", "report_intelligence_latest.md"),
        "pdf": payload.get("artifacts", {}).get("pdf", "report_intelligence_latest.pdf"),
        "trusted_report_date": (payload.get("executive_status") or {}).get("trusted_report_date", ""),
        "buy_count": (payload.get("recommendation_summary") or {}).get("buy_count", 0),
        "backfill_queue_count": (payload.get("timeline_health") or {}).get("backfill_queue_count", 0),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
