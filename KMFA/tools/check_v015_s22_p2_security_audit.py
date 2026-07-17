#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S22-P2 security and audit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s22_p2_security_audit as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s22_p2_security_audit.py','KMFA/tools/run_v015_s22_p2_security_audit.py','KMFA/tools/build_v015_s22_p2_security_audit.py','KMFA/tools/check_v015_s22_p2_security_audit.py','KMFA/tools/run_v015_s22_p2_browser_tests.py','KMFA/tools/run_v015_s22_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_core_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p2_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit_governance"),
    ("s22_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p2_security_audit.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s22_p2_security_audit.py"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p2_security_audit.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S22_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p2_security_audit.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p2_security_audit.py --taskpack-source-check"),
    ("secret_public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p2_security_audit.py --secret-public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S22_P2_SECURITY_AUDIT/", "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s22_p2_security_audit.py",
    "KMFA/tests/test_v015_s22_p2_security_audit_runtime.py",
    "KMFA/tests/test_v015_s22_p2_security_audit_browser.py",
    "KMFA/tests/test_v015_s22_p2_security_audit_artifacts.py",
    "KMFA/tests/test_v015_s22_p2_security_audit_governance.py",
    "KMFA/tools/build_v015_s22_p2_security_audit.py",
    "KMFA/tools/check_v015_s22_p2_security_audit.py",
    "KMFA/tools/run_v015_s22_p2_browser_tests.py",
    "KMFA/tools/run_v015_s22_p2_security_audit.py",
    "KMFA/tools/run_v015_s22_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s22_p2_security_audit.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/",
)


class CheckError(RuntimeError):
    """S22-P2 validation failed."""


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
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode:
        raise CheckError("S22-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S22-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if (
        value["acceptance_status"] != "PASSED"
        or value["overall_accepted_phase_count"] != 62
        or value["s22_p2_entry_allowed"] is not True
    ):
        raise CheckError("S22-P1 dependency is not the accepted 62/72 handoff")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S22"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P2"), None)
    expected = [
        ("T01", "实现认证、会话和权限审计", "审计关闭不得生产运行。"),
        ("T02", "实现秘密与凭据管理", "发现明文秘密立即阻塞。"),
        ("T03", "实现输入输出安全", "高危漏洞不得交付。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S22-P2 TaskPack source drift")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.AUTH_AUDIT_PATH,
        builder.SECRET_CONTRACT_PATH, builder.INPUT_OUTPUT_PATH, builder.BROWSER_PATH,
        builder.PUBLIC_CHECKS_PATH, builder.TASK_MATRIX_PATH, builder.IMPLEMENTATION_REPORT_PATH,
        builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S22-P2 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S22-P2 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S22-P2 evidence")
    expected_manifest = {
        "run_phase_id": "V015_S22_P2_SECURITY_AUDIT",
        "roadmap_phase_id": "S22-P2",
        "phase_task_count": 3,
        "overall_total_phase_count": 72,
        "public_check_count": 60,
        "public_check_pass_count": 60,
        "public_check_failed_count": 0,
        "core_test_count": 13,
        "runtime_test_count": 10,
        "browser_flow_count": 9,
        "visual_evidence_count": 6,
        "role_count": 4,
        "required_audit_action_type_count": 5,
        "audit_action_type_count": 6,
        "audit_event_count": 10,
        "audit_tamper_accept_count": 0,
        "production_audit_disabled_accept_count": 0,
        "secret_source_count": 1,
        "secret_reference_count": 2,
        "tracked_plaintext_secret_count": 0,
        "credential_exposure_count": 0,
        "attack_category_count": 5,
        "rejected_attack_count": 5,
        "high_vulnerability_count": 0,
        "public_link_count": 0,
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "s22_p2_started": True,
        "s22_p3_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    mismatch = [key for key, value in expected_manifest.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S22-P2 manifest mismatch: " + ", ".join(mismatch))
    audit = _json(builder.AUTH_AUDIT_PATH)
    secrets = _json(builder.SECRET_CONTRACT_PATH)
    security = _json(builder.INPUT_OUTPUT_PATH)
    browser = _json(builder.BROWSER_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    if (
        audit.get("role_count"), audit.get("required_audit_action_type_coverage_count"),
        audit.get("tamper_accept_count"), audit.get("production_audit_disabled_accept_count"),
    ) != (4, 5, 0, 0):
        raise CheckError("authentication or audit contract failed")
    if not all(audit.get(key) is True for key in ("audit_append_only", "audit_hash_linked", "audit_queryable")):
        raise CheckError("audit integrity controls are incomplete")
    if (
        secrets.get("secret_source_count"), secrets.get("secret_reference_count"),
        secrets.get("tracked_plaintext_secret_count"), secrets.get("audit_secret_exposure_count"),
    ) != (1, 2, 0, 0):
        raise CheckError("secret management contract failed")
    if (
        security.get("attack_category_count"), security.get("rejected_attack_count"),
        security.get("high_vulnerability_count"), security.get("public_link_count"),
    ) != (5, 5, 0, 0):
        raise CheckError("input/output security contract failed")
    for key in (
        "injection_accept_count", "path_traversal_accept_count", "malicious_file_accept_count",
        "formula_injection_accept_count", "public_sensitive_download_accept_count",
    ):
        if security.get(key) != 0:
            raise CheckError(f"dangerous sample accepted: {key}")
    if (
        browser.get("browser_flow_count"), browser.get("visual_evidence_count"),
        browser.get("page_secret_exposure_count"), browser.get("external_network_request_count"),
    ) != (9, 6, 0, 0):
        raise CheckError("browser contract failed")
    if (
        checks.get("status"), checks.get("public_check_count"),
        checks.get("public_check_pass_count"), checks.get("public_check_failed_count"),
    ) != ("PASS", 60, 60, 0):
        raise CheckError("public checks failed")
    if matrix.get("phase_task_count") != 3 or len(matrix.get("tasks", [])) != 3:
        raise CheckError("task acceptance matrix is incomplete")
    if any(row.get("status") != "PASS" for row in matrix["tasks"]):
        raise CheckError("task acceptance matrix contains a failed task")
    for path in builder.SCREENSHOT_PATHS:
        if not path.is_file() or path.stat().st_size < 10_000:
            raise CheckError(f"missing browser visual: {path.relative_to(REPO_ROOT)}")
    expected_state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 63 if final else 62,
        "overall_phase_acceptance_percent": 87.5 if final else 86.1,
        "decision": "GO_TO_S22_P3_ONLY" if final else "REMAIN_IN_S22_P2_FINAL_VALIDATION",
        "next_gate_id": "S22-P3" if final else "S22-P2-FINAL-VALIDATION",
        "s22_p2_completed": final,
        "s22_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s22_p3_entry_allowed": final,
    }
    mismatch = [key for key, value in expected_state.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S22-P2 acceptance-state mismatch: " + ", ".join(mismatch))
    if not skip_receipts:
        rows = builder.receipts()
        if final:
            if len(rows) != 20 or [row.get("name") for row in rows] != list(builder.EXPECTED_VALIDATION_NAMES):
                raise CheckError("formal validation receipts are incomplete")
            if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
                raise CheckError("formal validation receipt failed")
            if (
                {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}
                or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}
            ):
                raise CheckError("formal validation receipt binding mismatch")
        elif rows:
            raise CheckError("pending evidence must not contain formal receipts")


def _check_secret_public_boundary() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count", "raw_write_count", "external_network_request_count",
        "credential_exposure_count", "high_vulnerability_count", "public_link_count",
    ):
        if manifest.get(key) != 0:
            raise CheckError(f"public security boundary counter is nonzero: {key}")
    if manifest.get("github_upload_performed") is not False or manifest.get("app_reinstall_performed") is not False:
        raise CheckError("release boundary was crossed")
    source = _json(builder.SOURCE_CONTRACT_PATH)
    if source.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY" or "raw" not in source.get("excluded", []):
        raise CheckError("source boundary is not public-synthetic-only")
    paths = (
        builder.PROJECT_ROOT / "tools/v015_s22_p2_security_audit.py",
        builder.PROJECT_ROOT / "tools/run_v015_s22_p2_security_audit.py",
        builder.PROJECT_ROOT / "tools/build_v015_s22_p2_security_audit.py",
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    urls = re.findall(r"https?://[^\s\"']+", text)
    if (
        "/Users/" in text
        or "KMFA_MetaData" in text
        or any(not url.startswith(("http://{address}", "http://127.0.0.1", "http://localhost")) for url in urls)
    ):
        raise CheckError("S22-P2 phase contains a private path or external URL")
    token_patterns = (
        r"AKIA[0-9A-Z]{16}",
        r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )
    if any(re.search(pattern, text) for pattern in token_patterns):
        raise CheckError("tracked phase text contains a credential-shaped value")
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in builder.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".html", ".txt"}
    )
    for ref in builder.model.SECRET_REFERENCES:
        value = os.environ.get(ref)
        if value and value in public_text:
            raise CheckError(f"runtime secret value leaked into public evidence: {ref}")


def _check_clean_governance_sync() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    state = "S22_P2_PASSED" if manifest.get("phase_acceptance_status") == "PASSED" else "S22_P2_PENDING_FINAL_VALIDATION"
    result = subprocess.run(
        [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError("governance sync mismatch\n" + (result.stdout + result.stderr)[-4000:])


def run(*, require_final: bool | None = None, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts(require_final=require_final, skip_receipts=skip_validation_receipts)
    _check_secret_public_boundary()
    _check_clean_governance_sync()


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S22-P2 安全与审计")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--secret-public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--require-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.secret_public_boundary_check:
            _check_secret_public_boundary()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        else:
            required = True if args.require_final else (False if args.pre_final else None)
            run(require_final=required, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S22-P2 security and audit are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
