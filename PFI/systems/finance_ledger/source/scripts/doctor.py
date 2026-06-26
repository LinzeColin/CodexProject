#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "finance_ledger_20220605_20260603"
DEFAULT_LEDGER_DB = ROOT / "data" / "finance_ledger" / "finance_ledger.sqlite"


@dataclass(frozen=True)
class WorkflowCheck:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _ok(name: str, detail: str) -> WorkflowCheck:
    return WorkflowCheck(name, "ok", detail)


def _warn(name: str, detail: str) -> WorkflowCheck:
    return WorkflowCheck(name, "warn", detail)


def _fail(name: str, detail: str) -> WorkflowCheck:
    return WorkflowCheck(name, "fail", detail)


REQUIRED_FILES = [
    "AGENTS.md",
    "HANDOFF.md",
    "README.md",
    "pyproject.toml",
    "Makefile",
    "setup.sh",
    "docs/finance_ledger_data_contract.md",
    "docs/codex_workflow_contract.md",
    "docs/run_contract_template.md",
    "scripts/weekly_update.py",
    "scripts/validate_outputs.py",
    "scripts/finalize_delivery.py",
    "scripts/package_delivery.py",
    "scripts/doctor.py",
]

REQUIRED_DIRS = ["src/econ_bleed_analyzer", "scripts", "tests", "docs", "configs"]

CORE_TABLES = [
    "data_trust_transactions",
    "data_trust_sources",
    "reconciliation_checks",
    "manual_review_queue_audit",
    "entity_registry",
    "alias_map",
    "evidence_decision_matrix",
    "evidence_decision_summary",
]

CORE_VIEWS = [
    "v_data_trust_transactions",
    "v_reconciliation_checks",
    "v_manual_review_queue_audit",
    "v_entity_registry",
    "v_alias_map",
    "v_evidence_decision_matrix",
    "v_evidence_decision_summary",
]


def _exists_check(root: Path, relative: str) -> WorkflowCheck:
    path = root / relative
    return _ok(f"file:{relative}", str(path)) if path.is_file() else _fail(f"file:{relative}", f"missing: {path}")


def _dir_check(root: Path, relative: str) -> WorkflowCheck:
    path = root / relative
    return _ok(f"dir:{relative}", str(path)) if path.is_dir() else _fail(f"dir:{relative}", f"missing: {path}")


def _taskpack_check(root: Path) -> WorkflowCheck:
    patterns = ["*system_upgrade_taskpack*", "*升级总报告*", "*个人研究中台*"]
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(root.glob(pattern))
        matches.extend((root / "outputs").glob(pattern) if (root / "outputs").exists() else [])
    if matches:
        return _ok("upgrade_taskpack_or_report", ", ".join(str(path) for path in sorted(set(matches))[:5]))
    return _warn(
        "upgrade_taskpack_or_report",
        "not found in this project; use active goal, HANDOFF.md, AGENTS.md, and current files as authority",
    )


def _sqlite_objects(conn: sqlite3.Connection, object_type: str) -> set[str]:
    rows = conn.execute("select name from sqlite_master where type = ?", (object_type,)).fetchall()
    return {str(row[0]) for row in rows}


def _db_checks(db_path: Path) -> list[WorkflowCheck]:
    checks: list[WorkflowCheck] = []
    if not db_path.exists():
        return [_warn("ledger_db", f"missing: {db_path}")]
    checks.append(_ok("ledger_db", str(db_path)))
    try:
        conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        return checks + [_fail("ledger_db_open", str(exc))]
    try:
        tables = _sqlite_objects(conn, "table")
        views = _sqlite_objects(conn, "view")
        missing_tables = [name for name in CORE_TABLES if name not in tables]
        missing_views = [name for name in CORE_VIEWS if name not in views]
        checks.append(_ok("core_tables", "all core audit tables present") if not missing_tables else _fail("core_tables", "missing: " + ", ".join(missing_tables)))
        checks.append(_ok("core_views", "all core read-only views present") if not missing_views else _fail("core_views", "missing: " + ", ".join(missing_views)))
        for table in CORE_TABLES:
            if table in tables:
                count = conn.execute(f"select count(*) from {table}").fetchone()[0]
                status = "ok" if int(count) > 0 else "warn"
                checks.append(WorkflowCheck(f"rows:{table}", status, str(int(count))))
    finally:
        conn.close()
    return checks


def _output_layer_checks(output_dir: Path) -> list[WorkflowCheck]:
    checks: list[WorkflowCheck] = []
    if not output_dir.exists():
        return [_warn("output_dir", f"missing: {output_dir}")]
    checks.append(_ok("output_dir", str(output_dir)))
    expected_reports = [
        "data_trust_audit_report.pdf",
        "reconciliation_audit_report.pdf",
        "manual_review_queue_audit_report.pdf",
        "entity_registry_report.pdf",
        "evidence_decision_matrix_report.pdf",
    ]
    reports_dir = output_dir / "reports"
    for report in expected_reports:
        path = reports_dir / report
        checks.append(_ok(f"report:{report}", f"{path.stat().st_size} bytes") if path.exists() and path.stat().st_size > 20_000 else _warn(f"report:{report}", f"missing or too small: {path}"))
    return checks


def _validation_checks(output_dir: Path, db_path: Path) -> list[WorkflowCheck]:
    sys.path.insert(0, str(ROOT / "src"))
    from econ_bleed_analyzer.validate_outputs import has_failures, validate_all

    validation_output_dir = _project_relative_path(output_dir)
    validation_db_path = _project_relative_path(db_path)
    results = validate_all(validation_output_dir, validation_db_path, require_ledger=True)
    fail_count = sum(1 for item in results if item.status == "fail")
    warn_count = sum(1 for item in results if item.status == "warn")
    ok_count = sum(1 for item in results if item.status == "ok")
    if has_failures(results):
        return [_fail("validate_outputs", f"ok={ok_count} warn={warn_count} fail={fail_count}")]
    return [_ok("validate_outputs", f"ok={ok_count} warn={warn_count} fail={fail_count}")]


def _project_relative_path(path: Path) -> Path:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT)
    except ValueError:
        return path


def run_checks(
    *,
    root: Path = ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    db_path: Path = DEFAULT_LEDGER_DB,
    require_output: bool = False,
) -> list[WorkflowCheck]:
    checks: list[WorkflowCheck] = []
    checks.extend(_exists_check(root, item) for item in REQUIRED_FILES)
    checks.extend(_dir_check(root, item) for item in REQUIRED_DIRS)
    checks.append(_taskpack_check(root))
    checks.extend(_db_checks(db_path))
    checks.extend(_output_layer_checks(output_dir))
    if require_output:
        checks.extend(_validation_checks(output_dir, db_path))
    return checks


def has_failures(checks: list[WorkflowCheck]) -> bool:
    return any(item.status == "fail" for item in checks)


def _status_counts(checks: list[WorkflowCheck]) -> dict[str, int]:
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for item in checks:
        counts[item.status] = counts.get(item.status, 0) + 1
    return counts


def _payload(checks: list[WorkflowCheck], output_dir: Path, db_path: Path) -> dict[str, Any]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": "economic-bleed-analyzer",
        "root": str(ROOT),
        "output_dir": str(output_dir),
        "ledger_db": str(db_path),
        "counts": _status_counts(checks),
        "checks": [item.to_dict() for item in checks],
    }


def write_workflow_report(checks: list[WorkflowCheck], report_path: Path) -> Path:
    sys.path.insert(0, str(ROOT / "src"))
    from econ_bleed_analyzer.reports import write_report_pdf

    report_path.parent.mkdir(parents=True, exist_ok=True)
    counts = _status_counts(checks)
    markdown = "\n".join(
        [
            "# Codex Workflow Layer Report",
            "",
            f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Summary",
            "",
            f"- OK: {counts['ok']}",
            f"- Warn: {counts['warn']}",
            f"- Fail: {counts['fail']}",
            "",
            "## Workflow Artifacts",
            "",
            "- `AGENTS.md` defines project-level operating rules.",
            "- `docs/codex_workflow_contract.md` defines authority order and validation gates.",
            "- `docs/run_contract_template.md` defines run-end reporting.",
            "- `scripts/doctor.py` provides a local workflow health check.",
            "- `setup.sh` and `Makefile` provide simple repeatable commands.",
            "",
            "## Checks",
            "",
            "| Check | Status | Detail |",
            "|---|---|---|",
            *[f"| {item.name} | {item.status} | {item.detail.replace('|', '/')} |" for item in checks],
            "",
            "## Boundary",
            "",
            "This workflow layer does not change production amount formulas, classification rules, review decisions, or source bill data.",
        ]
    )
    md_path = report_path.with_suffix(".md")
    md_path.write_text(markdown, encoding="utf-8")
    write_report_pdf(markdown, report_path)
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check local Codex workflow readiness for the economic bleed analyzer.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Generated output directory to inspect.")
    parser.add_argument("--db", default=str(DEFAULT_LEDGER_DB), help="Ledger SQLite database to inspect.")
    parser.add_argument("--require-output", action="store_true", help="Also run full validate_outputs.py checks.")
    parser.add_argument("--json", action="store_true", help="Print JSON payload.")
    parser.add_argument("--write-audit", default="", help="Optional JSON audit output path.")
    parser.add_argument("--write-report", default="", help="Optional PDF workflow report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    db_path = Path(args.db)
    checks = run_checks(output_dir=output_dir, db_path=db_path, require_output=bool(args.require_output))
    payload = _payload(checks, output_dir, db_path)
    if args.write_audit:
        audit_path = Path(args.write_audit)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.write_report:
        write_workflow_report(checks, Path(args.write_report))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        width = max(len(item.name) for item in checks) if checks else 10
        for item in checks:
            print(f"{item.status.upper():4}  {item.name.ljust(width)}  {item.detail}")
    return 1 if has_failures(checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
