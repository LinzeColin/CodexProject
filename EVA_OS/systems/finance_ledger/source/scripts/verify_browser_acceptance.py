#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_RESULT_KEYS = {"page", "viewport", "marker_ok", "visual_ok", "overflow_x", "text_length"}
DEFAULT_HTML_PAGES = [
    "index.html",
    "dashboard.html",
    "operations_center.html",
    "data_access_hub.html",
    "acceptance_workbench.html",
    "reference_model_lab.html",
    "transaction_explorer.html",
    "behavior_analysis.html",
    "tag_library.html",
    "review_workbench.html",
]
DEFAULT_EXPECTED_COUNT = len(DEFAULT_HTML_PAGES) * 2


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], *, expected_count: int, audit_path: Path | None = None, html_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    results = payload.get("results")
    failures = payload.get("failures")
    if payload.get("checked_count") != expected_count:
        errors.append(f"checked_count expected {expected_count}, got {payload.get('checked_count')}")
    if payload.get("failure_count") != 0:
        errors.append(f"failure_count expected 0, got {payload.get('failure_count')}")
    if not isinstance(results, list) or len(results) != expected_count:
        errors.append(f"results expected {expected_count} rows")
    if failures not in ([], None):
        errors.append("failures must be empty")
    if isinstance(results, list):
        for index, row in enumerate(results):
            if not isinstance(row, dict):
                errors.append(f"results[{index}] is not an object")
                continue
            missing = REQUIRED_RESULT_KEYS - set(row)
            if missing:
                errors.append(f"results[{index}] missing keys: {', '.join(sorted(missing))}")
            if row.get("marker_ok") is not True:
                errors.append(f"results[{index}] marker_ok is not true")
            if row.get("visual_ok") is not True:
                errors.append(f"results[{index}] visual_ok is not true")
    if audit_path is not None and html_root is not None:
        errors.extend(validate_audit_freshness(audit_path, html_root))
    return errors


def validate_audit_freshness(audit_path: Path, html_root: Path) -> list[str]:
    errors: list[str] = []
    if not audit_path.exists() or not html_root.exists():
        return errors
    audit_mtime = audit_path.stat().st_mtime
    stale_pages: list[str] = []
    for page in DEFAULT_HTML_PAGES:
        html_path = html_root / page
        if html_path.exists() and html_path.stat().st_mtime > audit_mtime:
            stale_pages.append(page)
    if stale_pages:
        errors.append(
            "browser audit is older than current HTML pages: "
            + ", ".join(stale_pages)
            + "; rerun browser visual acceptance before final packaging"
        )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the browser visual acceptance audit JSON.")
    parser.add_argument("--audit", default="outputs/finance_ledger_20220605_20260603/audit/browser_visual_acceptance.json")
    parser.add_argument("--expected-count", type=int, default=DEFAULT_EXPECTED_COUNT)
    parser.add_argument("--html-root", help="Directory containing the rendered HTML pages. When set, fail if audit is older than those pages.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.audit)
    if not path.exists():
        errors = [f"missing audit file: {path}"]
        payload: dict[str, Any] = {}
    else:
        try:
            payload = load_payload(path)
        except Exception as exc:
            errors = [f"invalid audit json: {exc}"]
        else:
            html_root = Path(args.html_root) if args.html_root else None
            errors = validate_payload(payload, expected_count=args.expected_count, audit_path=path, html_root=html_root)
    result = {
        "audit": str(path),
        "ok": not errors,
        "checked_count": payload.get("checked_count"),
        "failure_count": payload.get("failure_count"),
        "generated_at": payload.get("generated_at"),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "OK" if result["ok"] else "FAIL"
        print(f"{status} browser_acceptance audit={path} checked={result['checked_count']} failures={result['failure_count']}")
        for error in errors:
            print(f"- {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
