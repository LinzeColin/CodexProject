#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S21-P2 report generation."""

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

from pypdf import PdfReader

from KMFA.tools import build_v015_s21_p2_report_generation as builder
from KMFA.tools import v015_s21_p2_report_generation as model


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s21_p2_report_generation.py','KMFA/tools/run_v015_s21_p2_report_generation.py','KMFA/tools/build_v015_s21_p2_report_generation.py','KMFA/tools/check_v015_s21_p2_report_generation.py','KMFA/tools/run_v015_s21_p2_browser_tests.py','KMFA/tools/run_v015_s21_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_unit_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p2_report_generation"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p2_report_generation_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s21_p2_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p2_report_generation_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p2_report_generation_governance"),
    ("s21_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p2_report_generation.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s21_p2_report_generation.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p2_report_generation.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S21_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p2_report_generation.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p2_report_generation.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p2_report_generation.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S21_P2_REPORT_GENERATION/",
    "KMFA/taskpack/v1_5/", "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s21_p2_report_generation.py", "KMFA/tests/test_v015_s21_p2_report_generation_runtime.py",
    "KMFA/tests/test_v015_s21_p2_report_generation_browser.py", "KMFA/tests/test_v015_s21_p2_report_generation_artifacts.py",
    "KMFA/tests/test_v015_s21_p2_report_generation_governance.py", "KMFA/tools/build_v015_s21_p2_report_generation.py",
    "KMFA/tools/check_v015_s21_p2_report_generation.py", "KMFA/tools/run_v015_s21_p2_browser_tests.py",
    "KMFA/tools/run_v015_s21_p2_report_generation.py", "KMFA/tools/run_v015_s21_p2_validations.py",
    "KMFA/tools/no_omission_check.py", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s21_p2_report_generation.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S21-P2 validation failed."""


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
        raise CheckError("S21-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S21-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 20 or value.get("overall_accepted_phase_count") != 59:
        raise CheckError("S21-P1 依赖不完整")
    if value.get("s21_p2_entry_allowed") is not True or value.get("s21_p2_started") is not False:
        raise CheckError("S21-P1 没有只开放尚未开始的 S21-P2")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    for key, value in {"source_package_sha256": builder.TASKPACK_SHA256, "stage_count": 24, "phase_count": 72, "task_count": 216}.items():
        if source.get(key) != value:
            raise CheckError(f"tracked TaskPack source drifted: {key}")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S21"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "实现 HTML 报告", "响应式、可打印、章节导航和数据来源入口。", "HTML 报告。", "与实际应用设计系统一致。", "视觉回归和数据测试。", "不得与任务包样式脱节。"),
        ("T02", "实现 PDF 输出", "分页、页眉页脚、目录、表格和图表可读。", "PDF 报告。", "数字与 HTML 完全一致。", "PDF 提取对比。", "分页截断关键表格失败。"),
        ("T03", "实现 CSV 或 Excel 附表", "明细、公式说明、来源索引和差异清单可下载。", "专业附表。", "导出值与事实层一致。", "导出零差异测试。", "Excel 自动格式不得改变数值。"),
    ]
    actual = [tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop")) for task in (phase or {}).get("tasks", [])]
    if not stage or stage.get("name") != "经营报告、专业附表与导出" or not phase or phase.get("name") != "报告生成与可视化" or actual != expected:
        raise CheckError("S21-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    source, content, html_contract = (_json(path) for path in (builder.SOURCE_CONTRACT_PATH, builder.CONTENT_CONTRACT_PATH, builder.HTML_CONTRACT_PATH))
    pdf, appendix, consistency = (_json(path) for path in (builder.PDF_CONTRACT_PATH, builder.APPENDIX_CONTRACT_PATH, builder.CONSISTENCY_PATH))
    browser, checks = (_json(path) for path in (builder.BROWSER_PATH, builder.PUBLIC_CHECKS_PATH))
    if source.get("roadmap_phase_id") != "S21-P2" or source.get("task_ids") != ["S21P2T01", "S21P2T02", "S21P2T03"]:
        raise CheckError("公开来源合同不完整")
    if tuple(content.get(key) for key in ("project_count", "metric_count", "source_binding_count", "exact_numeric_value_count")) != (3, 6, 6, 21):
        raise CheckError("报告内容合同不完整")
    if tuple(html_contract.get(key) for key in ("responsive", "printable", "chapter_navigation_count", "source_entry_present", "raw_integer_marker_count")) != (True, True, 6, True, 21):
        raise CheckError("HTML 合同不完整")
    if pdf.get("page_count", 0) < 2 or pdf.get("page_number_present") is not True or pdf.get("repeating_header_present") is not True or pdf.get("professional_appendix_present") is not True or pdf.get("rendered_preview_count") != 2:
        raise CheckError("PDF 合同不完整")
    if tuple(appendix.get(key) for key in ("row_count", "exact_integer_value_count", "difference_integer", "executable_formula_cell_count")) != (21, 21, 0, 0):
        raise CheckError("专业附表合同不完整")
    if tuple(consistency.get(key) for key in ("status", "numeric_value_count", "html_value_count", "pdf_value_count", "csv_value_count", "difference_integer")) != ("PASS", 21, 21, 21, 21, 0):
        raise CheckError("跨格式一致性合同不完整")
    if checks.get("public_check_count") != 60 or checks.get("public_check_pass_count") != 60 or checks.get("public_check_failed_count") != 0 or len(checks.get("checks", [])) != 60:
        raise CheckError("60 项公开检查未全部通过")
    if browser.get("browser_flow_count") != 8 or browser.get("browser_visual_evidence_count") != 5 or browser.get("pdf_visual_evidence_count") != 2 or browser.get("minimum_touch_target_px") != 44 or browser.get("horizontal_page_overflow_allowed") is not False:
        raise CheckError("浏览器或 PDF 视觉合同不完整")
    browser_sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    pdf_sizes = [_png_size(path) for path in builder.PDF_PREVIEW_PATHS]
    if any(width < 1000 or height < 700 for width, height in browser_sizes[:3]) or any(width != 390 or height < 800 for width, height in browser_sizes[3:]):
        raise CheckError("电脑或手机视觉证据尺寸漂移")
    if any(width < 1200 or height < 1700 for width, height in pdf_sizes):
        raise CheckError("PDF 渲染证据尺寸漂移")
    if not builder.PDF_PATH.read_bytes().startswith(b"%PDF") or len(PdfReader(str(builder.PDF_PATH)).pages) < 2:
        raise CheckError("PDF 文件无效")


def _check_public_boundary() -> None:
    raw_literal = "/Users/" + "linzezhang/Downloads/" + "KMFA" + "_MetaData"
    forbidden = (
        re.escape(raw_literal), r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".csv", ".md"}]
    files.extend((builder.PROJECT_ROOT / "tools/v015_s21_p2_report_generation.py", builder.PROJECT_ROOT / "tools/run_v015_s21_p2_report_generation.py"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        if any(re.search(pattern, text) for pattern in forbidden):
            raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in ("history_overwrite_count", "raw_root_access_count", "raw_write_count", "external_network_request_count", "approval_or_publication_count", "s21_p3_execution_count"):
        if value.get(key) != 0:
            raise CheckError(f"boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S21_P2_PASSED" if accepted else "S21_P2_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=".")
    result = subprocess.run([sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError("governance roadmap sync drifted: " + (result.stdout + result.stderr)[-3000:])
    common = (
        "governance_model_count: 19", "active_formula_count: 398", "active_parameter_count: 2480",
        'current_parameter_range: "PARAM-KMFA-2846..2865"', "stage_execution_percentage: 67",
        "s21_p2_started: true", "s21_p2_format_count: 3", "s21_p2_exact_numeric_value_count: 21",
        "s21_p2_cross_format_difference_integer: 0", "s21_p2_public_check_count: 60",
        "s21_p3_started: false", "github_upload_performed: false", "app_reinstall_performed: false",
    )
    phase_tokens = {
        "docs/governance/project.yaml": ('current_phase_id: "V015_S21_P2_REPORT_GENERATION"',),
        "metadata/project/project.yaml": ('current_phase: "V015_S21_P2_REPORT_GENERATION"',),
        "docs/governance/roadmap.yaml": ('current_phase_id: "V015_S21_P2_REPORT_GENERATION"',),
    }
    for relative, specific in phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*common, *specific) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2846 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2865]
    if len(selected) != 20 or not all(row["model_id"] == "MOD-KMFA-CASH-REPORT-001" and row["formula_id"] == "FORM-KMFA-V015-S21-P2-REPORT-GENERATION-001" and row["status"] == "active" for row in selected):
        raise CheckError("S21-P2 parameter registry drifted")


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    _check_governance_sync()
    value, matrix, rows = _json(builder.MANIFEST_PATH), _json(builder.TASK_MATRIX_PATH), builder.receipts()
    if pre_final:
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION" or value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final manifest must remain pending")
        if value.get("s21_p1_acceptance_status") != "PASSED" or value.get("s21_p2_started") is not True or value.get("s21_p2_completed") is not False or value.get("s21_p3_entry_allowed") is not False or value.get("s21_p3_started") is not False or value.get("overall_accepted_phase_count") != 59:
            raise CheckError("pre-final must remain inside S21-P2")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S21-P2 receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3 or value.get("overall_accepted_phase_count") != 60:
            raise CheckError("three S21-P2 tasks and accepted phase count must be final")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("s21_p2_completed") is not True or value.get("s21_p3_entry_allowed") is not True or value.get("s21_p3_started") is not False or value.get("next_gate_id") != "S21-P3":
            raise CheckError("final state must open but not start S21-P3")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S21-P2 报告生成")
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
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError, model.ReportGenerationError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S21-P2 report generation is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
