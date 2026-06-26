from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SYSTEM_AUDIT_DIR = ROOT / "data" / "report_artifacts" / "system_audit"


@dataclass(frozen=True)
class DoctorCheck:
    check_id: str
    category: str
    status: str
    severity: str
    observed: str
    expected: str
    next_action: str


def build_workflow_doctor(as_of: str, *, root: Path = ROOT) -> dict[str, Any]:
    checks: list[DoctorCheck] = []
    checks.extend(_required_file_checks(root))
    checks.extend(_runtime_checks())
    checks.extend(_cli_command_checks(root))
    checks.extend(_audit_artifact_checks(root, as_of))
    checks.extend(_workflow_script_checks(root))
    status_counts = Counter(check.status for check in checks)
    severity_counts = Counter(check.severity for check in checks)
    audit_status = "Blocked" if any(check.status == "fail" and check.severity == "P0" for check in checks) else "Review" if any(check.status != "pass" for check in checks) else "Pass"
    return {
        "schema": "AIResearchCodexWorkflowDoctorV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "check_count": len(checks),
        "status_counts": dict(sorted(status_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "assumptions": [
            "doctor.py is read-only unless --write-report is used to write its own audit bundle.",
            "Missing pytest in system Python is a Review item, not a blocker, because Makefile can use the Codex bundled Python test wrapper.",
            "Audit artifact checks verify local files only; they do not regenerate evidence or refresh external data.",
        ],
        "checks": [asdict(check) for check in checks],
    }


def write_workflow_doctor_report(as_of: str, *, root: Path = ROOT) -> dict[str, Any]:
    payload = build_workflow_doctor(as_of, root=root)
    target_dir = root / "data" / "report_artifacts" / "system_audit"
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"codex_workflow_doctor_{as_of}"
    json_path = target_dir / f"{stem}.json"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = _doctor_markdown(payload)
    markdown_path.write_text(markdown, encoding="utf-8")
    try:
        from src.monitoring.data_trust import _write_pdf

        _write_pdf(pdf_path, markdown)
    except Exception as exc:
        payload["pdf_error"] = str(exc)
    payload["outputs"] = {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path) if pdf_path.exists() else "",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-Research-System workflow doctor")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when audit_status is not Pass.")
    args = parser.parse_args()
    payload = write_workflow_doctor_report(args.date) if args.write_report else build_workflow_doctor(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"WORKFLOW_DOCTOR: {payload['audit_status']} {payload['as_of']}")
        print(f"checks: {payload['check_count']}")
        print(f"status_counts: {payload['status_counts']}")
        if payload.get("outputs"):
            for key, value in payload["outputs"].items():
                print(f"{key}: {value}")
    return 1 if args.strict and payload["audit_status"] != "Pass" else 0


def _required_file_checks(root: Path) -> list[DoctorCheck]:
    required = [
        "AGENTS.md",
        "HANDOFF.md",
        "README.md",
        "pyproject.toml",
        "src/cli.py",
        "docs/RunContract.md",
        "docs/CodexWorkflowLayer.md",
        "Makefile",
        "setup.sh",
    ]
    return [
        _check(
            check_id=f"required_file:{path}",
            category="required_files",
            ok=(root / path).exists(),
            severity="P0" if path in {"AGENTS.md", "HANDOFF.md", "src/cli.py"} else "P1",
            observed="exists" if (root / path).exists() else "missing",
            expected="exists",
            next_action=f"Create or restore {path}.",
        )
        for path in required
    ]


def _runtime_checks() -> list[DoctorCheck]:
    checks = [
        DoctorCheck(
            check_id="runtime:python_version",
            category="runtime",
            status="pass" if tuple(map(int, platform.python_version_tuple()[:2])) >= (3, 10) else "fail",
            severity="P0",
            observed=platform.python_version(),
            expected="Python >= 3.10",
            next_action="Use Python 3.10+.",
        )
    ]
    for module, severity in [("certifi", "P1"), ("reportlab", "P1"), ("tzdata", "P2")]:
        exists = importlib.util.find_spec(module) is not None
        checks.append(
            _check(
                check_id=f"runtime:module:{module}",
                category="runtime",
                ok=exists,
                severity=severity,
                observed="available" if exists else "missing",
                expected="available",
                next_action=f"Install or use a runtime that provides {module}.",
            )
        )
    pytest_available = importlib.util.find_spec("pytest") is not None
    configured_pytest_runtime = os.environ.get("CODEX_PYTHON", "").strip()
    configured_pytest = bool(configured_pytest_runtime and Path(configured_pytest_runtime).expanduser().exists())
    checks.append(
        _check(
            check_id="runtime:module:pytest_or_codex_runtime",
            category="runtime",
            ok=pytest_available or configured_pytest,
            severity="P2",
            observed="available" if pytest_available else "available_via_configured_runtime" if configured_pytest else "missing",
            expected="pytest available in current Python or CODEX_PYTHON runtime",
            next_action="Use Makefile test targets with CODEX_PYTHON or install pytest in the active runtime.",
        )
    )
    return checks


def _cli_command_checks(root: Path) -> list[DoctorCheck]:
    cli_text = (root / "src" / "cli.py").read_text(encoding="utf-8") if (root / "src" / "cli.py").exists() else ""
    commands = [
        "data-trust-audit",
        "reconciliation-audit",
        "manual-review-audit",
        "entity-registry-audit",
        "evidence-decision-audit",
        "report-layer-audit",
        "automation-health",
        "report-quality-check",
        "research-bus-sync",
    ]
    return [
        _check(
            check_id=f"cli_command:{command}",
            category="cli_commands",
            ok=command in cli_text,
            severity="P1",
            observed="registered" if command in cli_text else "missing",
            expected="registered",
            next_action=f"Register CLI command {command} in src/cli.py.",
        )
        for command in commands
    ]


def _audit_artifact_checks(root: Path, as_of: str) -> list[DoctorCheck]:
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    stems = [
        "data_trust_audit",
        "reconciliation_audit",
        "manual_review_queue",
        "entity_registry",
        "evidence_decision_matrix",
        "report_layer_audit",
    ]
    suffixes = ["json", "csv", "md", "pdf"]
    checks = []
    for stem in stems:
        for suffix in suffixes:
            if stem == "entity_registry" and suffix == "csv":
                path = audit_dir / f"{stem}_{as_of}.csv"
            else:
                path = audit_dir / f"{stem}_{as_of}.{suffix}"
            checks.append(
                _check(
                    check_id=f"audit_artifact:{path.name}",
                    category="audit_artifacts",
                    ok=path.exists(),
                    severity="P1",
                    observed="exists" if path.exists() else "missing",
                    expected="exists",
                    next_action=f"Run the audit stack target to generate {path.name}.",
                )
            )
    alias_path = audit_dir / f"alias_map_{as_of}.csv"
    checks.append(
        _check(
            check_id=f"audit_artifact:{alias_path.name}",
            category="audit_artifacts",
            ok=alias_path.exists(),
            severity="P1",
            observed="exists" if alias_path.exists() else "missing",
            expected="exists",
            next_action="Run entity-registry-audit to generate alias map.",
        )
    )
    return checks


def _workflow_script_checks(root: Path) -> list[DoctorCheck]:
    scripts = [
        ("setup.sh", os.X_OK, "executable"),
        ("scripts/run_report_automation.sh", os.X_OK, "executable"),
        ("scripts/watch_research_bus.sh", os.X_OK, "executable"),
    ]
    checks = []
    for path_text, mode, expected in scripts:
        path = root / path_text
        ok = path.exists() and os.access(path, mode)
        checks.append(
            _check(
                check_id=f"script:{path_text}",
                category="workflow_scripts",
                ok=ok,
                severity="P1",
                observed=expected if ok else "missing_or_not_executable",
                expected=expected,
                next_action=f"Run chmod +x {path_text} or restore the script.",
            )
        )
    return checks


def _check(
    *,
    check_id: str,
    category: str,
    ok: bool,
    severity: str,
    observed: str,
    expected: str,
    next_action: str,
) -> DoctorCheck:
    return DoctorCheck(
        check_id=check_id,
        category=category,
        status="pass" if ok else "fail" if severity == "P0" else "warn",
        severity=severity,
        observed=observed,
        expected=expected,
        next_action=next_action if not ok else "No action required.",
    )


def _doctor_markdown(payload: dict[str, Any]) -> str:
    rows = list(payload["checks"])
    non_pass = [row for row in rows if row["status"] != "pass"]
    lines = [
        f"# AI-Research-System Codex Workflow Doctor {payload['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {payload['system']}",
        f"- Generated At: {payload['generated_at']}",
        f"- Audit Status: {payload['audit_status']}",
        f"- Checks: {payload['check_count']}",
        "",
        "## Status Summary",
        _markdown_table([{"status": key, "count": value} for key, value in payload["status_counts"].items()], ["status", "count"]),
        "",
        "## Non-Pass Checks",
        _markdown_table(non_pass, ["severity", "category", "check_id", "observed", "expected", "next_action"]),
        "",
        "## All Checks",
        _markdown_table(rows, ["status", "severity", "category", "check_id", "observed"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload["assumptions"]],
    ]
    return "\n".join(lines)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "暂无数据"
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_clean_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def _clean_cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "/").strip()
    return text[:220] + "..." if len(text) > 220 else text


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
