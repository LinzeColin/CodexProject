#!/usr/bin/env python3
"""KMFA v1.5 S15-P2 严格、回执绑定的身份与角色验收检查。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s15_p2_identity_roles as builder
from KMFA.tools import v015_s15_p2_identity_roles as kernel


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s15_p2_identity_roles.py','KMFA/tools/run_v015_s15_p2_identity_roles.py','KMFA/tools/build_v015_s15_p2_identity_roles.py','KMFA/tools/check_v015_s15_p2_identity_roles.py','KMFA/tools/run_v015_s15_p2_browser_tests.py','KMFA/tools/run_v015_s15_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p2_identity_roles"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p2_identity_roles_runtime"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s15_p2_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p2_identity_roles_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p2_identity_roles_governance"),
    ("s15_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p2_identity_roles.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s15_p2_identity_roles.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p2_identity_roles.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S15_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p2_identity_roles.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p2_identity_roles.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p2_identity_roles.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S15_P2_IDENTITY_ROLES/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s15_p2_identity_roles.py",
    "KMFA/tests/test_v015_s15_p2_identity_roles_runtime.py",
    "KMFA/tests/test_v015_s15_p2_identity_roles_browser.py",
    "KMFA/tests/test_v015_s15_p2_identity_roles_artifacts.py",
    "KMFA/tests/test_v015_s15_p2_identity_roles_governance.py",
    "KMFA/tools/build_v015_s15_p2_identity_roles.py",
    "KMFA/tools/check_v015_s15_p2_identity_roles.py",
    "KMFA/tools/run_v015_s15_p2_identity_roles.py",
    "KMFA/tools/run_v015_s15_p2_browser_tests.py",
    "KMFA/tools/run_v015_s15_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s15_p2_identity_roles.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)

PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml",
    "KMFA/machine/",
    "KMFA/文档/",
)


class CheckError(RuntimeError):
    """S15-P2 验收检查失败。"""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S15-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S15-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 20:
        raise CheckError("S15-P1 dependency is not accepted")
    if value.get("s15_p2_entry_allowed") is not True or value.get("s15_p2_started") is not False:
        raise CheckError("S15-P1 did not open exactly S15-P2")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if any(
        source_manifest.get(key) != value
        for key, value in {"source_package_sha256": builder.TASKPACK_SHA256, "stage_count": 24, "phase_count": 72, "task_count": 216}.items()
    ):
        raise CheckError("tracked TaskPack source manifest drifted")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S15"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "建立用户与角色帽子", "操作记录包含当时角色。", "角色切换不得越权。"),
        ("T02", "建立最小权限", "默认拒绝，敏感详情最小可见。", "未授权访问必须阻止并记录。"),
        ("T03", "建立审批分离", "小团队可用，不强制虚构多人。", "同一人多角色时仍记录角色与理由。"),
    ]
    actual = [(task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop")) for task in (phase or {}).get("tasks", [])]
    if not stage or stage.get("name") != "应用外壳、角色权限与多主体上下文" or not phase or phase.get("name") != "身份与角色" or actual != expected:
        raise CheckError("S15-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    identity = _json(builder.IDENTITY_CONTRACT_PATH)
    permission = _json(builder.PERMISSION_CONTRACT_PATH)
    audit = _json(builder.AUDIT_CONTRACT_PATH)
    approval = _json(builder.APPROVAL_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    if identity.get("role_hat_count") != 4 or identity.get("public_user_count") != 2:
        raise CheckError("identity and role contract incomplete")
    if permission.get("default_policy") != "DENY" or permission.get("resource_domain_count") != 5 or permission.get("permission_grant_count") != 28:
        raise CheckError("minimum permission contract incomplete")
    if audit.get("unauthorized_access_logged") is not True or audit.get("role_and_reason_bound_count") != audit.get("event_count"):
        raise CheckError("authorization audit contract incomplete")
    if approval.get("approval_flow_count") != 3 or approval.get("same_role_confirmation_allowed") is not False:
        raise CheckError("approval separation contract incomplete")
    if approval.get("same_person_different_role_confirmation_allowed") is not True or approval.get("invented_person_required") is not False:
        raise CheckError("small-team role separation contract incomplete")
    if len(browser.get("required_flows", [])) != 6:
        raise CheckError("browser acceptance contract incomplete")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if sizes[:3] != [(1440, 1000), (1440, 1000), (1440, 1000)]:
        raise CheckError("desktop visual evidence viewport drifted")
    if sizes[3][0] != 390 or sizes[3][1] < 844:
        raise CheckError("mobile visual evidence viewport drifted")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = ("当前操作身份", "fetch('/api/identity?'", "post('/api/authorize'", "post('/api/approvals'", "localStorage", "KMFA_ROLE_TEST", "aria-live")
    missing = [token for token in required if token not in html]
    if missing:
        raise CheckError("runtime HTML contract missing: " + ", ".join(missing))


def _check_public_boundary() -> None:
    forbidden = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() != ".png"]
    files.extend([builder.PROJECT_ROOT / "tools/v015_s15_p2_identity_roles.py", builder.PROJECT_ROOT / "tools/run_v015_s15_p2_identity_roles.py"])
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    manifest = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "live_source_read_count", "external_network_request_count", "real_identity_count", "credential_count", "real_business_action_count"):
        if manifest.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    state = "S15_P2_PASSED" if _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED" else "S15_P2_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        ["python3", "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise CheckError("governance sync drifted: " + (result.stdout + result.stderr)[-3000:])


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    manifest = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    rows = builder.receipts()
    if pre_final:
        if manifest.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
            raise CheckError("pre-final manifest must remain pending")
        if manifest.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final tasks cannot be accepted")
        if manifest.get("s15_p3_entry_allowed") is not False or manifest.get("s15_p3_started") is not False:
            raise CheckError("pre-final S15-P3 must remain closed")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or manifest.get("phase_acceptance_status") != "PASSED" or manifest.get("evidence_validation_status") != "PASS":
            raise CheckError("final S15-P2 acceptance receipts are incomplete")
        if manifest.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S15-P2 tasks must be accepted")
        if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if manifest.get("s15_p3_entry_allowed") is not True or manifest.get("s15_p3_started") is not False:
            raise CheckError("final state must open but not start S15-P3")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_report_generated"):
        if manifest.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S15-P2 身份与角色")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_governance_sync()
        else:
            check(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S15-P2 identity roles " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
