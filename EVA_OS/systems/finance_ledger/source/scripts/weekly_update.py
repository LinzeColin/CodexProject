#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from econ_bleed_analyzer.ledger import build_master_ledger
from econ_bleed_analyzer.validate_outputs import has_failures, validate_all
from audit_chatgpt_reference import run_audit as run_chatgpt_audit
from audit_goal_completion import run_audit as run_goal_completion_audit


DEFAULT_LEDGER_DB = "data/finance_ledger/finance_ledger.sqlite"
DEFAULT_SOURCE_ROOT = "data/finance_ledger/sources"
DEFAULT_RULES = "configs/classification_rules.json"
DEFAULT_OUTPUT = "outputs/finance_ledger_latest"


def _downloads_candidates() -> list[Path]:
    downloads = Path.home() / "Downloads"
    patterns = [
        "支付宝交易明细*.zip",
        "支付宝交易明细*.csv",
        "支付宝交易明细*.xlsx",
        "微信支付账单*.zip",
        "微信支付账单*.csv",
        "微信支付账单*.xlsx",
    ]
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(downloads.glob(pattern))
    return sorted({path for path in candidates if path.is_file()}, key=lambda path: path.stat().st_mtime, reverse=True)


def _auto_inputs() -> list[str]:
    candidates = _downloads_candidates()
    if not candidates:
        raise FileNotFoundError("未在 Downloads 自动发现支付宝/微信账单。请使用 --input 指定文件或目录。")
    return [str(candidates[0])]


def _expand_weekly_inputs(raw_inputs: list[str]) -> list[str]:
    suffixes = {".csv", ".xlsx", ".zip"}
    expanded: list[Path] = []
    for raw in raw_inputs:
        path = Path(raw).expanduser()
        if path.is_dir():
            expanded.extend(child for child in path.rglob("*") if child.is_file() and child.suffix.casefold() in suffixes)
        else:
            expanded.append(path)
    unique = sorted({path.resolve() for path in expanded})
    if not unique:
        raise FileNotFoundError("未找到可导入的 CSV/XLSX/ZIP 账单文件。")
    return [str(path) for path in unique]


def _result_counts(validation_results: list[Any]) -> dict[str, int]:
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for item in validation_results:
        counts[item.status] = counts.get(item.status, 0) + 1
    return counts


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a repeatable weekly ledger update: import, rebuild reports, validate, and write an audit manifest.")
    parser.add_argument("--input", nargs="+", help="Alipay/WeChat CSV/XLSX/ZIP files or directories. If omitted, the latest matching Downloads bill is used.")
    parser.add_argument("--ledger-db", default=DEFAULT_LEDGER_DB, help="Shared ledger SQLite path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Analysis output directory.")
    parser.add_argument("--source-root", default=DEFAULT_SOURCE_ROOT, help="Archived extracted source CSV directory.")
    parser.add_argument("--rules", default=DEFAULT_RULES, help="Classification rule JSON path.")
    parser.add_argument("--review-decisions", default="", help="Optional confirmed review_decisions_confirmed.csv path.")
    parser.add_argument("--tag-library", default="", help="Optional tag_library_custom.json/CSV path exported from tag_library.html.")
    parser.add_argument("--manifest", default="", help="Optional run manifest path. Defaults to <output>/audit/weekly_update_manifest.json.")
    parser.add_argument("--skip-validation", action="store_true", help="Only rebuild outputs; do not run validation.")
    parser.add_argument("--json", action="store_true", help="Print the final run summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_paths = _expand_weekly_inputs(args.input or _auto_inputs())
    started_at = datetime.now().isoformat(timespec="seconds")

    import_result = build_master_ledger(
        inputs=input_paths,
        ledger_db=args.ledger_db,
        output_dir=args.output,
        source_root=args.source_root,
        rules_path=args.rules,
        review_decisions_path=args.review_decisions,
        tag_library_path=args.tag_library,
    )
    chatgpt_reference_audit = run_chatgpt_audit(
        SimpleNamespace(output_dir=args.output, scan_dir=["chatgpt_reference", "requirements"], input=[], json=False)
    )
    goal_completion_audit = run_goal_completion_audit(
        SimpleNamespace(output_dir=args.output, ledger_db=args.ledger_db, json=False)
    )

    validation_results = []
    validation_failed = False
    if not args.skip_validation:
        validation_results = validate_all(args.output, args.ledger_db, require_ledger=True)
        validation_failed = has_failures(validation_results)

    output_dir = Path(args.output)
    manifest_path = Path(args.manifest) if args.manifest else output_dir / "audit" / "weekly_update_manifest.json"
    validation_counts = _result_counts(validation_results)
    summary = {
        "run_type": "weekly_update",
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": input_paths,
        "ledger_db": str(args.ledger_db),
        "output_dir": str(args.output),
        "source_root": str(args.source_root),
        "review_decisions": str(args.review_decisions),
        "tag_library": str(args.tag_library),
        "import_result": import_result,
        "chatgpt_reference_audit": chatgpt_reference_audit,
        "goal_completion_audit": goal_completion_audit,
        "validation": {
            "skipped": bool(args.skip_validation),
            "failed": validation_failed,
            "counts": validation_counts,
            "results": [item.to_dict() for item in validation_results],
        },
        "next_review_workbench": str(output_dir / "review" / "review_workbench.html"),
        "next_report_portal": str(output_dir / "reports" / "index.html"),
        "notes": [
            "单笔一万元以上且未确认的大额交易仍留在复核队列，不自动进入生产统计。",
            "候选复核只用于下拉选择加速；必须导出确认表并通过 --review-decisions 重跑后才会回灌。",
        ],
    }
    _write_manifest(manifest_path, summary)

    if args.json:
        print(json.dumps(_json_ready(summary), ensure_ascii=False, indent=2))
    else:
        print(f"weekly_update_manifest: {manifest_path}")
        print(f"ledger_db: {args.ledger_db}")
        print(f"output_dir: {args.output}")
        print(f"source_count: {import_result['source_count']}")
        print(f"transaction_count: {import_result['transaction_count']}")
        print(f"date_range: {import_result['date_start']} 至 {import_result['date_end']}")
        if args.skip_validation:
            print("validation: skipped")
        else:
            print(f"validation: ok={validation_counts.get('ok', 0)} warn={validation_counts.get('warn', 0)} fail={validation_counts.get('fail', 0)}")
        print(f"review_workbench: {output_dir / 'review' / 'review_workbench.html'}")
        print(f"report_portal: {output_dir / 'reports' / 'index.html'}")
    return 1 if validation_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
