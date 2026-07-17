#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S17-P3 项目处理流程与专题报告。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s17_p3_project_workflow as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s17_p3_project_workflow.py','KMFA/tools/run_v015_s17_p3_project_workflow.py','KMFA/tools/build_v015_s17_p3_project_workflow.py','KMFA/tools/check_v015_s17_p3_project_workflow.py','KMFA/tools/run_v015_s17_p3_browser_tests.py','KMFA/tools/run_v015_s17_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_unit_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p3_project_workflow",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p3_project_workflow_runtime",
    ),
    (
        "focused_browser_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s17_p3_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p3_project_workflow_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p3_project_workflow_governance",
    ),
    (
        "s17_p2_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p3_project_workflow.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s17_p3_project_workflow.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p3_project_workflow.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S17_P3_PENDING_FINAL_VALIDATION",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p3_project_workflow.py --clean-governance-sync-check",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p3_project_workflow.py --taskpack-source-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p3_project_workflow.py --public-boundary-check",
    ),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/.gitignore",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S17_P3_PROJECT_WORKFLOW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s17_p3_project_workflow.py",
    "KMFA/tests/test_v015_s17_p3_project_workflow_runtime.py",
    "KMFA/tests/test_v015_s17_p3_project_workflow_browser.py",
    "KMFA/tests/test_v015_s17_p3_project_workflow_artifacts.py",
    "KMFA/tests/test_v015_s17_p3_project_workflow_governance.py",
    "KMFA/tools/build_v015_s17_p3_project_report.mjs",
    "KMFA/tools/build_v015_s17_p3_project_workflow.py",
    "KMFA/tools/check_v015_s17_p3_project_workflow.py",
    "KMFA/tools/run_v015_s17_p3_browser_tests.py",
    "KMFA/tools/run_v015_s17_p3_project_workflow.py",
    "KMFA/tools/run_v015_s17_p3_validations.py",
    "KMFA/tools/no_omission_check.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s17_p3_project_workflow.py",
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
    """S17-P3 验收检查失败。"""


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
        raise CheckError("S17-P3 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S17-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    expected = {
        "acceptance_status": "PASSED",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 48,
        "s17_p3_entry_allowed": True,
        "s17_p3_started": False,
    }
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch:
        raise CheckError("S17-P2 依赖不完整：" + ", ".join(mismatch))


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    for key, value in {
        "source_package_sha256": builder.TASKPACK_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }.items():
        if source_manifest.get(key) != value:
            raise CheckError(f"tracked TaskPack source manifest drifted: {key}")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S17"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P3"), None)
    expected = [
        ("T01", "处理未归集成本", "显示候选项目、依据、影响并经确认写入事件。", "处理流。", "不修改源数据，可撤销。", "端到端测试。", "低置信自动归集失败。"),
        ("T02", "处理项目差异", "并排比较来源，解释差异，预览影响后重算。", "差异流。", "处理后报告同步。", "持久化和重跑测试。", "只改页面状态失败。"),
        ("T03", "生成项目成本专题报告", "输出 HTML、PDF、Excel 附表和证据索引。", "项目报告。", "与页面和黄金基准一致。", "导出零差异测试。", "任一分差异失败。"),
    ]
    actual = [
        tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop"))
        for task in (phase or {}).get("tasks", [])
    ]
    if (
        not stage
        or stage.get("name") != "项目列表、项目详情与成本分析流程"
        or not phase
        or phase.get("name") != "项目处理流程"
        or actual != expected
    ):
        raise CheckError("S17-P3 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    unallocated = _json(builder.UNALLOCATED_CONTRACT_PATH)
    variance = _json(builder.VARIANCE_CONTRACT_PATH)
    report = _json(builder.REPORT_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    if (
        unallocated.get("candidate_count") != 3
        or unallocated.get("basis_present_count") != 3
        or unallocated.get("high_confidence_bps") != 9600
        or unallocated.get("low_confidence_bps") != 5200
        or unallocated.get("low_auto_allocation_allowed") is not False
        or unallocated.get("reversible") is not True
        or unallocated.get("source_data_write_count") != 0
    ):
        raise CheckError("未归集成本合同不完整")
    if (
        variance.get("source_count") != 2
        or variance.get("explanation_present") is not True
        or variance.get("impact_preview_passed") is not True
        or variance.get("event_count") != 5
        or variance.get("reversal_event_count") != 1
        or variance.get("report_sync_status") != "PASS"
        or variance.get("projection_difference_cents") != 0
    ):
        raise CheckError("项目差异处理合同不完整")
    if (
        report.get("format_count") != 3
        or report.get("workbook_sheet_count") != 5
        or report.get("workbook_preview_count") != 5
        or report.get("pdf_preview_count") != 1
        or report.get("page_golden_difference_cents") != 0
        or report.get("category_page_difference_cents") != 0
        or report.get("money_tolerance_cents") != 0
        or report.get("report_sync_status") != "PASS"
    ):
        raise CheckError("项目成本专题报告合同不完整")
    if len(checks) != 69 or not all(row.get("passed") is True for row in checks):
        raise CheckError("69 项公开检查未全部通过")
    if len(browser.get("required_flows", [])) != 10 or browser.get("horizontal_page_overflow_allowed") is not False:
        raise CheckError("浏览器验收流程不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width < 1000 or height < 800 for width, height in sizes[:5]):
        raise CheckError("电脑视觉证据尺寸漂移")
    if sizes[5][0] != 390 or sizes[5][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")
    payload = _json(builder.REPORT_PAYLOAD_PATH)
    actual_budget = sum(row["budget_cents"] for row in payload["cost_rows"])
    actual_cost = sum(row["actual_cents"] for row in payload["cost_rows"])
    if actual_budget != payload["summary"]["budget_cents"] or actual_cost != payload["summary"]["cost_cents"]:
        raise CheckError("报告总额与明细不一致")


def _check_public_boundary() -> None:
    forbidden = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [
        path
        for path in builder.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".md"}
    ]
    files.extend(
        [
            builder.PROJECT_ROOT / "tools/v015_s17_p3_project_workflow.py",
            builder.PROJECT_ROOT / "tools/run_v015_s17_p3_project_workflow.py",
            builder.PROJECT_ROOT / "tools/build_v015_s17_p3_project_report.mjs",
        ]
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count",
        "live_source_read_count",
        "external_network_request_count",
        "real_identity_count",
        "credential_count",
        "real_business_action_count",
        "source_data_write_count",
        "fact_layer_write_count",
    ):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S17_P3_PASSED" if accepted else "S17_P3_PENDING_FINAL_VALIDATION"
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
    tokens = (
        "governance_model_count: 13",
        "active_formula_count: 383",
        "active_parameter_count: 2180",
        'current_parameter_range: "PARAM-KMFA-2546..2565"',
        "stage_execution_percentage: 100",
        "s17_p3_started: true",
        "s17_p3_candidate_count: 3",
        "s17_p3_money_tolerance_cents: 0",
        "s17_p3_projection_difference_cents: 0",
        "s17_stage_review_started: false",
    )
    current_phase_tokens = {
        "docs/governance/project.yaml": 'current_phase_id: "V015_S17_P3_PROJECT_WORKFLOW"',
        "metadata/project/project.yaml": 'current_phase: "V015_S17_P3_PROJECT_WORKFLOW"',
        "docs/governance/roadmap.yaml": 'current_phase_id: "V015_S17_P3_PROJECT_WORKFLOW"',
    }
    for relative, phase_token in current_phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*tokens, phase_token) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if any(len(row) != len(rows[0]) for row in rows[:21]):
        raise CheckError("S17-P3 parameter registry column count drifted")


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
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
            raise CheckError("pre-final manifest must remain pending")
        if value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final tasks cannot be accepted")
        if (
            value.get("s17_p2_acceptance_status") != "PASSED"
            or value.get("s17_p3_started") is not True
            or value.get("s17_p3_completed") is not False
            or value.get("s17_overall_review_entry_allowed") is not False
            or value.get("s17_overall_review_started") is not False
            or value.get("s17_stage_review_entry_allowed") is not False
            or value.get("s17_stage_review_started") is not False
            or value.get("overall_accepted_phase_count") != 48
        ):
            raise CheckError("pre-final must remain inside S17-P3")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S17-P3 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S17-P3 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 49:
            raise CheckError("accepted TaskPack phase count must advance to 49")
        if (
            value.get("s17_p3_completed") is not True
            or value.get("s17_overall_review_entry_allowed") is not True
            or value.get("s17_overall_review_started") is not False
            or value.get("s17_stage_review_entry_allowed") is not True
            or value.get("s17_stage_review_started") is not False
            or value.get("next_gate_id") != "S17-OVERALL-REVIEW"
        ):
            raise CheckError("final state must open but not start S17 overall review")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S17-P3 项目处理流程")
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
    print("PASS: S17-P3 project workflow " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
