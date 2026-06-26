#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from econ_bleed_analyzer.ledger import build_master_ledger
from audit_chatgpt_reference import run_audit as run_chatgpt_audit
from audit_goal_completion import run_audit as run_goal_completion_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import bill archives into the shared finance ledger database.")
    parser.add_argument("--input", nargs="+", required=True, help="Alipay/WeChat CSV/XLSX files, ZIP files containing CSV/XLSX, or directories.")
    parser.add_argument("--ledger-db", default="data/finance_ledger/finance_ledger.sqlite", help="Shared ledger SQLite path.")
    parser.add_argument("--output", default="outputs/finance_ledger_latest", help="Analysis output directory.")
    parser.add_argument("--source-root", default="data/finance_ledger/sources", help="Archived extracted source CSV directory.")
    parser.add_argument("--rules", default="configs/classification_rules.json", help="Classification rule JSON path.")
    parser.add_argument("--review-decisions", default="", help="Optional manual review decision CSV.")
    parser.add_argument("--tag-library", default="", help="Optional tag library JSON/CSV exported from tag_library.html.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_master_ledger(
        inputs=args.input,
        ledger_db=args.ledger_db,
        output_dir=args.output,
        source_root=args.source_root,
        rules_path=args.rules,
        review_decisions_path=args.review_decisions,
        tag_library_path=args.tag_library,
    )
    chatgpt_audit = run_chatgpt_audit(SimpleNamespace(output_dir=args.output, scan_dir=["chatgpt_reference", "requirements"], input=[], json=False))
    goal_audit = run_goal_completion_audit(SimpleNamespace(output_dir=args.output, ledger_db=args.ledger_db, json=False))
    print(f"ledger_db: {result['ledger_db']}")
    print(f"output_dir: {result['output_dir']}")
    print(f"source_count: {result['source_count']}")
    print(f"transaction_count: {result['transaction_count']}")
    print(f"date_range: {result['date_start']} 至 {result['date_end']}")
    print(f"chatgpt_reference_audit: {chatgpt_audit['status']}")
    print(f"goal_completion_pct: {goal_audit['summary']['machine_verifiable_pct']:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
