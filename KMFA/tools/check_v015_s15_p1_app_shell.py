#!/usr/bin/env python3
"""KMFA v1.5 S15-P1 严格、回执绑定的应用外壳验收检查。"""

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

from KMFA.tools import build_v015_s15_p1_app_shell as builder
from KMFA.tools import v015_s15_p1_app_shell as kernel


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s15_p1_app_shell.py','KMFA/tools/run_v015_s15_p1_app_shell.py','KMFA/tools/build_v015_s15_p1_app_shell.py','KMFA/tools/check_v015_s15_p1_app_shell.py','KMFA/tools/run_v015_s15_p1_browser_tests.py','KMFA/tools/run_v015_s15_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_kernel_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p1_app_shell",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p1_app_shell_runtime",
    ),
    (
        "focused_browser_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s15_p1_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p1_app_shell_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p1_app_shell_governance",
    ),
    (
        "s14_review_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p1_app_shell.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s15_p1_app_shell.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p1_app_shell.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S15_P1_PENDING_FINAL_VALIDATION",
    ),
    (
        "metadata_protocol",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py",
    ),
    (
        "project_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required",
    ),
    (
        "lean_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required",
    ),
    (
        "governance_sync",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p1_app_shell.py --clean-governance-sync-check",
    ),
    (
        "no_float_money",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    ),
    (
        "no_omission",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    ),
    (
        "taskpack_source",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p1_app_shell.py --taskpack-source-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s15_p1_app_shell.py --public-boundary-check",
    ),
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
    "KMFA/metadata/quality/v015_s15_p1_",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S15_P1_APP_SHELL/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s15_p1_app_shell.py",
    "KMFA/tests/test_v015_s15_p1_app_shell_runtime.py",
    "KMFA/tests/test_v015_s15_p1_app_shell_browser.py",
    "KMFA/tests/test_v015_s15_p1_app_shell_artifacts.py",
    "KMFA/tests/test_v015_s15_p1_app_shell_governance.py",
    "KMFA/tools/build_v015_s15_p1_app_shell.py",
    "KMFA/tools/check_v015_s15_p1_app_shell.py",
    "KMFA/tools/run_v015_s15_p1_app_shell.py",
    "KMFA/tools/run_v015_s15_p1_browser_tests.py",
    "KMFA/tools/run_v015_s15_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s15_p1_app_shell.py",
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
    """S15-P1 验收检查失败。"""


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
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) or path.startswith(prefix) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S15-P1 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S15-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 25:
        raise CheckError("S14 stage review dependency is not accepted")
    if value.get("s15_p1_entry_allowed") is not True or value.get("s15_p1_started") is not False:
        raise CheckError("S14 stage review did not open exactly S15-P1")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (
        source_manifest.get("source_package_sha256") != builder.TASKPACK_SHA256
        or source_manifest.get("stage_count") != 24
        or source_manifest.get("phase_count") != 72
        or source_manifest.get("task_count") != 216
    ):
        raise CheckError("tracked TaskPack source manifest drifted")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S15"), None)
    if not stage or stage.get("name") != "应用外壳、角色权限与多主体上下文":
        raise CheckError("S15 source stage missing or renamed")
    phase = next((item for item in stage.get("phases", []) if item.get("id") == "P1"), None)
    expected_tasks = [
        ("T01", "实现布局与路由", "路由刷新可恢复，深链接可用。", "静态 HTML 不算通过。"),
        ("T02", "实现全局筛选上下文", "切换影响明确且状态持久。", "跨主体数据泄露失败。"),
        ("T03", "实现加载和错误边界", "错误可恢复并有下一步。", "白屏或静默失败不通过。"),
    ]
    actual = [(task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop")) for task in (phase or {}).get("tasks", [])]
    if not phase or phase.get("name") != "应用外壳" or actual != expected_tasks:
        raise CheckError("S15-P1 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    runtime_contract = _json(builder.RUNTIME_CONTRACT_PATH)
    context_contract = _json(builder.CONTEXT_CONTRACT_PATH)
    error_contract = _json(builder.ERROR_CONTRACT_PATH)
    isolation_contract = _json(builder.ISOLATION_CONTRACT_PATH)
    if runtime_contract.get("static_html_only") is not False or runtime_contract.get("transport") != "LOCALHOST_HTTP":
        raise CheckError("runtime shell cannot be static-only")
    if runtime_contract.get("deep_link_route_count") != 18 or len(runtime_contract.get("deep_link_routes", [])) != 18:
        raise CheckError("deep-link route contract incomplete")
    if context_contract.get("dimension_count") != 4 or context_contract.get("persistence_mechanisms") != ["URL_QUERY", "LOCAL_STORAGE"]:
        raise CheckError("global context persistence contract incomplete")
    if len(error_contract.get("faults", [])) != 4 or error_contract.get("white_screen_allowed") is not False:
        raise CheckError("error boundary contract incomplete")
    if isolation_contract.get("guard_count") != 3 or isolation_contract.get("observed_cross_company_leak_count") != 0:
        raise CheckError("company isolation contract incomplete")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if sizes[:3] != [(1440, 1000), (1440, 1000), (1440, 1000)]:
        raise CheckError("desktop visual evidence viewport drifted")
    if sizes[3][0] != 390 or sizes[3][1] < 844:
        raise CheckError("mobile visual evidence viewport drifted")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = ("fetch('/api/context?'", "AbortController", "localStorage", "pushState", "aria-live", "prefers-reduced-motion")
    missing = [token for token in required if token not in html]
    if missing:
        raise CheckError("runtime HTML contract missing: " + ", ".join(missing))


def _check_public_boundary() -> None:
    forbidden_patterns = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() not in {".png"}]
    files.extend(
        [
            builder.PROJECT_ROOT / "tools/v015_s15_p1_app_shell.py",
            builder.PROJECT_ROOT / "tools/run_v015_s15_p1_app_shell.py",
        ]
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    manifest = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "live_source_read_count", "external_network_request_count", "real_business_action_count"):
        if manifest.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    state = "S15_P1_PASSED" if _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED" else "S15_P1_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        ["python3", "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
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
        if manifest.get("s15_p2_entry_allowed") is not False or manifest.get("s15_p2_started") is not False:
            raise CheckError("pre-final S15-P2 must remain closed")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or manifest.get("phase_acceptance_status") != "PASSED" or manifest.get("evidence_validation_status") != "PASS":
            raise CheckError("final S15-P1 acceptance receipts are incomplete")
        if manifest.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S15-P1 tasks must be accepted")
        if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if manifest.get("s15_p2_entry_allowed") is not True or manifest.get("s15_p2_started") is not False:
            raise CheckError("final state must open but not start S15-P2")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_report_generated"):
        if manifest.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S15-P1 应用外壳")
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
    print("PASS: S15-P1 app shell " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
