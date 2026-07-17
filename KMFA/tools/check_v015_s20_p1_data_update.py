#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S20-P1 数据更新流程。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s20_p1_data_update as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s20_p1_data_update.py','KMFA/tools/run_v015_s20_p1_data_update.py','KMFA/tools/build_v015_s20_p1_data_update.py','KMFA/tools/check_v015_s20_p1_data_update.py','KMFA/tools/run_v015_s20_p1_browser_tests.py','KMFA/tools/run_v015_s20_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_unit_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p1_data_update"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p1_data_update_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s20_p1_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p1_data_update_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p1_data_update_governance"),
    ("s19_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s20_p1_data_update.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s20_p1_data_update.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s20_p1_data_update.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S20_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s20_p1_data_update.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s20_p1_data_update.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s20_p1_data_update.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S20_P1_DATA_UPDATE/", "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s20_p1_data_update.py",
    "KMFA/tests/test_v015_s20_p1_data_update_runtime.py",
    "KMFA/tests/test_v015_s20_p1_data_update_browser.py",
    "KMFA/tests/test_v015_s20_p1_data_update_artifacts.py",
    "KMFA/tests/test_v015_s20_p1_data_update_governance.py",
    "KMFA/tools/build_v015_s20_p1_data_update.py",
    "KMFA/tools/check_v015_s20_p1_data_update.py",
    "KMFA/tools/run_v015_s20_p1_browser_tests.py",
    "KMFA/tools/run_v015_s20_p1_data_update.py",
    "KMFA/tools/run_v015_s20_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s20_p1_data_update.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/",
)


class CheckError(RuntimeError):
    """S20-P1 验收检查失败。"""


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
        raise CheckError("S20-P1 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S20-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 32 or value.get("overall_accepted_phase_count") != 55:
        raise CheckError("S19 整体复审依赖不完整")
    if value.get("s20_p1_entry_allowed") is not True or value.get("s20_p1_started") is not False:
        raise CheckError("S19 复审没有只开放尚未开始的 S20-P1")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    for key, value in {"source_package_sha256": builder.TASKPACK_SHA256, "stage_count": 24, "phase_count": 72, "task_count": 216}.items():
        if source_manifest.get(key) != value:
            raise CheckError(f"tracked TaskPack source manifest drifted: {key}")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S20"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P1"), None)
    expected = [
        ("T01", "实现来源选择与上传", "选择来源、主体、账户或板块、期间并上传。", "更新向导。", "步骤少、可返回、可取消。", "用户任务端到端测试。", "上传不得写原始只读目录。"),
        ("T02", "实现识别预览与确认", "展示识别文件、字段、期间和问题。", "预览页。", "用户确认后才进入处理。", "交互测试。", "自动猜测需明确标记。"),
        ("T03", "实现处理进度与结果", "显示导入、校验、重算和报告影响。", "进度页。", "刷新后可恢复。", "中断恢复测试。", "进度不可伪造。"),
    ]
    actual = [tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop")) for task in (phase or {}).get("tasks", [])]
    if not stage or stage.get("name") != "数据更新、人工确认与重新计算工作台" or not phase or phase.get("name") != "数据更新流程" or actual != expected:
        raise CheckError("S20-P1 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    source = _json(builder.SOURCE_CONTRACT_PATH)
    workflow = _json(builder.WORKFLOW_PATH)
    recovery = _json(builder.RECOVERY_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    if source.get("roadmap_phase_id") != "S20-P1" or source.get("task_ids") != ["S20P1T01", "S20P1T02", "S20P1T03"]:
        raise CheckError("公开来源合同不完整")
    if tuple(workflow.get(key) for key in ("step_count", "source_option_count", "entity_option_count", "scope_option_count", "supported_extension_count", "preview_field_count", "auto_detected_field_count")) != (3, 3, 3, 4, 8, 5, 1):
        raise CheckError("三步选择与预览合同不完整")
    if workflow.get("explicit_confirmation_required") is not True or workflow.get("back_allowed_before_commit") is not True or workflow.get("cancel_allowed_before_commit") is not True or workflow.get("raw_write_allowed") is not False:
        raise CheckError("人工确认、返回、取消或 raw 边界漂移")
    if tuple(recovery.get(key) for key in ("progress_stage_count", "actual_completed_stage_count", "not_executed_stage_count", "progress_fabrication_count")) != (7, 5, 2, 0):
        raise CheckError("进度合同不完整")
    if recovery.get("refresh_preview_restored") is not True or recovery.get("resumed_from_checkpoint") is not True or recovery.get("partial_commit_visible") is not False or recovery.get("recalculation_executed") is not False or recovery.get("report_refresh_executed") is not False:
        raise CheckError("刷新、中断或下游执行边界漂移")
    if checks.get("check_count") != 59 or checks.get("pass_count") != 59 or checks.get("fail_count") != 0 or len(checks.get("checks", [])) != 59 or not all(row.get("status") == "PASS" for row in checks.get("checks", [])):
        raise CheckError("59 项公开检查未全部通过")
    if browser.get("browser_flow_count") != 7 or browser.get("visual_evidence_count") != 4 or browser.get("minimum_touch_target_px") != 44 or browser.get("horizontal_page_overflow_allowed") is not False or browser.get("external_network_request_count") != 0:
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width < 1000 or height < 700 for width, height in sizes[:3]) or sizes[3][0] != 390 or sizes[3][1] < 800:
        raise CheckError("电脑或手机视觉证据尺寸漂移")


def _check_public_boundary() -> None:
    raw_literal = "/Users/" + "linzezhang/Downloads/" + "KMFA" + "_MetaData"
    forbidden = (
        re.escape(raw_literal),
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".csv", ".md"}]
    files.extend((builder.PROJECT_ROOT / "tools/v015_s20_p1_data_update.py", builder.PROJECT_ROOT / "tools/run_v015_s20_p1_data_update.py"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count", "raw_write_count", "source_original_mutation_count",
        "recalculation_execution_count", "report_refresh_execution_count",
        "external_network_request_count", "real_business_action_count", "progress_fabrication_count",
    ):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S20_P1_PASSED" if accepted else "S20_P1_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run([sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError("governance roadmap sync drifted: " + (result.stdout + result.stderr)[-3000:])
    common = (
        "governance_model_count: 19", "active_formula_count: 393", "active_parameter_count: 2380",
        'current_parameter_range: "PARAM-KMFA-2746..2765"', "stage_execution_percentage: 33",
        "s20_p1_started: true", "s20_p1_workflow_step_count: 3", "s20_p1_preview_field_count: 5",
        "s20_p1_progress_stage_count: 7", "s20_p1_progress_fabrication_count: 0",
        "s20_p1_raw_write_count: 0", "s20_p2_started: false",
        "github_upload_performed: false", "app_reinstall_performed: false",
    )
    phase_tokens = {
        "docs/governance/project.yaml": ('current_phase_id: "V015_S20_P1_DATA_UPDATE"',),
        "metadata/project/project.yaml": ('current_phase: "V015_S20_P1_DATA_UPDATE"',),
        "docs/governance/roadmap.yaml": ('current_phase_id: "V015_S20_P1_DATA_UPDATE"',),
    }
    for relative, specific in phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*common, *specific) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2746 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2765]
    if len(selected) != 20 or not all(row["model_id"] == "MOD-KMFA-FILE-IMPORT-001" and row["formula_id"] == "FORM-KMFA-V015-S20-P1-DATA-UPDATE-001" and row["status"] == "active" for row in selected):
        raise CheckError("S20-P1 parameter registry drifted")


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    _check_governance_sync()
    value = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    rows = builder.receipts()
    if pre_final:
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION" or value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final manifest must remain pending")
        if value.get("s19_stage_review_acceptance_status") != "PASSED" or value.get("s20_p1_started") is not True or value.get("s20_p1_completed") is not False or value.get("s20_p2_entry_allowed") is not False or value.get("s20_p2_started") is not False or value.get("overall_accepted_phase_count") != 55:
            raise CheckError("pre-final must remain inside S20-P1")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S20-P1 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S20-P1 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head or value.get("overall_accepted_phase_count") != 56:
            raise CheckError("final receipt binding or accepted phase count drifted")
        if value.get("s20_p1_completed") is not True or value.get("s20_p2_entry_allowed") is not True or value.get("s20_p2_started") is not False or value.get("next_gate_id") != "S20-P2":
            raise CheckError("final state must open but not start S20-P2")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S20-P1 数据更新流程")
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
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S20-P1 data update is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
