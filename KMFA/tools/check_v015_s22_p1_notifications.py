#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S22-P1 notifications."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s22_p1_notifications as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s22_p1_notifications.py','KMFA/tools/run_v015_s22_p1_notifications.py','KMFA/tools/build_v015_s22_p1_notifications.py','KMFA/tools/check_v015_s22_p1_notifications.py','KMFA/tools/run_v015_s22_p1_browser_tests.py','KMFA/tools/run_v015_s22_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_core_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p1_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications_governance"),
    ("s21_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p1_notifications.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s22_p1_notifications.py"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p1_notifications.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S22_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p1_notifications.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p1_notifications.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p1_notifications.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S22_P1_NOTIFICATIONS/",
    "KMFA/taskpack/v1_5/", "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s22_p1_notifications.py", "KMFA/tests/test_v015_s22_p1_notifications_runtime.py",
    "KMFA/tests/test_v015_s22_p1_notifications_browser.py", "KMFA/tests/test_v015_s22_p1_notifications_artifacts.py",
    "KMFA/tests/test_v015_s22_p1_notifications_governance.py", "KMFA/tools/build_v015_s22_p1_notifications.py",
    "KMFA/tools/check_v015_s22_p1_notifications.py", "KMFA/tools/run_v015_s22_p1_browser_tests.py",
    "KMFA/tools/run_v015_s22_p1_notifications.py", "KMFA/tools/run_v015_s22_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py", "KMFA/tools/v015_s22_p1_notifications.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S22-P1 validation failed."""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S22-P1 base commit is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(line for line in _git(*args).splitlines() if line and not _preserved(line))
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S22-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value["acceptance_status"] != "PASSED" or value["overall_accepted_phase_count"] != 61 or value["s22_p1_entry_allowed"] is not True:
        raise CheckError("S21 review dependency is not the accepted 61/72 handoff")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S22"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P1"), None)
    expected = [
        ("T01", "实现报告完成提醒", "不得发送完整报告或金额明细。"),
        ("T02", "实现重大风险和数据缺失提醒", "未确认规则不得启用。"),
        ("T03", "实现通知记录与重试", "不得泄露凭据。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S22-P1 TaskPack source drift")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.RULES_PATH, builder.SAFETY_PATH,
        builder.FREQUENCY_RETRY_PATH, builder.BROWSER_PATH, builder.PUBLIC_CHECKS_PATH, builder.TASK_MATRIX_PATH,
        builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S22-P1 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S22-P1 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S22-P1 evidence")
    expected_manifest = {
        "run_phase_id": "V015_S22_P1_NOTIFICATIONS", "roadmap_phase_id": "S22-P1",
        "phase_task_count": 3, "overall_total_phase_count": 72, "public_check_count": 65,
        "public_check_pass_count": 65, "public_check_failed_count": 0, "browser_flow_count": 8,
        "visual_evidence_count": 6, "recipient_count": 1, "rule_catalog_count": 7,
        "enabled_confirmed_rule_count": 6, "unconfirmed_rule_enabled_count": 0, "alert_category_count": 5,
        "safe_body_field_count": 4, "full_report_body_count": 0, "amount_detail_count": 0,
        "attachment_count": 0, "credential_field_count": 0, "duplicate_dispatch_count": 0,
        "dedupe_window_minutes": 360, "frequency_limit_per_day": 3, "silence_action_count": 2,
        "retry_budget": 3, "failure_injection_recovery_count": 1, "idempotency_conflict_accept_count": 0,
        "transport_mode": "EMAIL_SANDBOX", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "raw_root_access_count": 0, "raw_write_count": 0, "external_network_request_count": 0,
        "external_email_delivery_count": 0, "s22_p1_started": True, "s22_p2_started": False,
        "s22_p3_started": False, "github_upload_performed": False, "app_reinstall_performed": False,
    }
    mismatch = [key for key, value in expected_manifest.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S22-P1 manifest mismatch: " + ", ".join(mismatch))
    rules, safety = _json(builder.RULES_PATH), _json(builder.SAFETY_PATH)
    frequency, browser = _json(builder.FREQUENCY_RETRY_PATH), _json(builder.BROWSER_PATH)
    checks, matrix = _json(builder.PUBLIC_CHECKS_PATH), _json(builder.TASK_MATRIX_PATH)
    if (rules.get("recipient"), rules.get("transport_mode"), rules.get("unconfirmed_rule_enabled_count")) != ("linzezhang35@gmail.com", "EMAIL_SANDBOX", 0):
        raise CheckError("notification rule safety contract failed")
    if (safety.get("safe_body_field_count"), safety.get("full_report_body_count"), safety.get("amount_detail_count"), safety.get("credential_field_count")) != (4, 0, 0, 0):
        raise CheckError("message safety contract failed")
    if (frequency.get("duplicate_dispatch_count"), frequency.get("retry_budget"), frequency.get("idempotency_conflict_accept_count")) != (0, 3, 0):
        raise CheckError("frequency or retry contract failed")
    if (browser.get("browser_flow_count"), browser.get("visual_evidence_count"), browser.get("external_network_request_count")) != (8, 6, 0):
        raise CheckError("browser contract failed")
    if (checks.get("status"), checks.get("public_check_count"), checks.get("public_check_failed_count")) != ("PASS", 65, 0):
        raise CheckError("public checks failed")
    if matrix.get("phase_task_count") != 3 or len(matrix.get("tasks", [])) != 3 or any(row.get("status") != "PASS" for row in matrix["tasks"]):
        raise CheckError("task acceptance matrix failed")
    for path in builder.FORMAL_SCREENSHOT_PATHS:
        if not path.is_file() or path.stat().st_size < 10_000:
            raise CheckError(f"missing browser visual: {path.relative_to(REPO_ROOT)}")
    expected_state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 62 if final else 61,
        "overall_phase_acceptance_percent": 86.1 if final else 84.7,
        "decision": "GO_TO_S22_P2_ONLY" if final else "REMAIN_IN_S22_P1_FINAL_VALIDATION",
        "next_gate_id": "S22-P2" if final else "S22-P1-FINAL-VALIDATION",
        "s22_p1_completed": final, "s22_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s22_p2_entry_allowed": final,
    }
    mismatch = [key for key, value in expected_state.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S22-P1 acceptance-state mismatch: " + ", ".join(mismatch))
    if not skip_receipts:
        rows = builder.receipts()
        if final:
            if len(rows) != 20 or [row.get("name") for row in rows] != list(builder.EXPECTED_VALIDATION_NAMES):
                raise CheckError("formal validation receipts are incomplete")
            if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
                raise CheckError("formal validation receipt failed")
            if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")} or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
                raise CheckError("formal validation receipt binding mismatch")
        elif rows:
            raise CheckError("pending evidence must not contain formal receipts")


def _check_public_boundary() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    zero_keys = ("raw_root_access_count", "raw_write_count", "external_network_request_count", "external_email_delivery_count")
    if any(manifest.get(key) != 0 for key in zero_keys):
        raise CheckError("public boundary counters are not zero")
    if manifest.get("github_upload_performed") is not False or manifest.get("app_reinstall_performed") is not False:
        raise CheckError("release boundary was crossed")
    source = _json(builder.SOURCE_CONTRACT_PATH)
    if source.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY" or "raw" not in source.get("excluded", []):
        raise CheckError("source boundary is not public-synthetic-only")
    kernel = (builder.PROJECT_ROOT / "tools/v015_s22_p1_notifications.py").read_text(encoding="utf-8")
    if "/Users/" in kernel or "KMFA_MetaData" in kernel or re.search(r"https?://", kernel):
        raise CheckError("S22-P1 kernel contains raw path or external URL")


def _check_clean_governance_sync() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    state = "S22_P1_PASSED" if manifest.get("phase_acceptance_status") == "PASSED" else "S22_P1_PENDING_FINAL_VALIDATION"
    result = subprocess.run(
        [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise CheckError("governance sync mismatch\n" + (result.stdout + result.stderr)[-4000:])


def run(*, require_final: bool | None = None, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts(require_final=require_final, skip_receipts=skip_validation_receipts)
    _check_public_boundary()
    _check_clean_governance_sync()


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S22-P1 安全通知")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        else:
            run(require_final=False if args.pre_final else None, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S22-P1 notifications are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
