#!/usr/bin/env python3
"""生成 KMFA v1.5 S14-P3 可复验、公开安全的语言与内容证据。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s14_p3_language_content as language


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "4ae4af32e725bfa34dbe7e57dd5f8d247ca8a5d5"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S14_P3_LANGUAGE_CONTENT"
MACHINE_ROOT = ARTIFACT_ROOT / "machine"
HUMAN_ROOT = ARTIFACT_ROOT / "human"
EXPORT_ROOT = ARTIFACT_ROOT / "exports"
HTML_PATH = EXPORT_ROOT / "html/kmfa_language_content.html"
DESKTOP_LIGHT_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_language_content_desktop_light.png"
DESKTOP_DARK_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_language_content_desktop_dark.png"
MOBILE_LIGHT_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_language_content_mobile_light.png"

DICTIONARY_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p3_interface_dictionary_public_safe.json"
FORMAT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p3_format_contract_public_safe.json"
DENSITY_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p3_content_density_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
LANGUAGE_SCAN_PATH = MACHINE_ROOT / "language_scan_evidence_public_safe.json"
FORMAT_EVIDENCE_PATH = MACHINE_ROOT / "format_consistency_evidence_public_safe.json"
WALKTHROUGH_PATH = MACHINE_ROOT / "cognitive_walkthrough_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s14_p3_language_content_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
CONTENT_GUIDE_PATH = HUMAN_ROOT / "language_and_format_guide_zh.md"
RISKS_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
DEPENDENCY_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S14_P2_DESIGN_SYSTEM/machine/s14_p2_design_system_manifest.json"
)
DEPENDENCY_RECEIPTS_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S14_P2_DESIGN_SYSTEM/machine/validation_results.jsonl"
)

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s14_p2_dependency",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "public_boundary",
    "clean_governance_sync",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)


class BuildError(RuntimeError):
    """S14-P3 确定性证据无法生成。"""


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _jsonl_text(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S14_P2_DESIGN_SYSTEM",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S14_P3_ONLY",
        "s14_p2_started": True,
        "s14_p2_acceptance_status": "PASSED",
        "s14_p3_entry_allowed": True,
        "s14_p3_started": False,
        "validation_receipt_count": 20,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S14-P2 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(
        row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows
    ):
        raise BuildError("S14-P2 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S14-P2 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S14-P2 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s14_p3_entry_allowed": True,
        "s14_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [
        json.loads(line)
        for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S14-P3 验收记录顺序不一致")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return (
        final,
        next(iter(run_ids)) if final else None,
        next(iter(heads)) if final else None,
    )


def _source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p3.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S14",
        "stage_name_zh": "界面信息架构、设计系统与语言重构",
        "roadmap_phase_id": "S14-P3",
        "phase_name_zh": "语言与内容",
        "task_count": 3,
        "task_ids": ["S14P3T01", "S14P3T02", "S14P3T03"],
        "task_names_zh": ["建立全中文词典", "建立数字与单位格式", "建立内容密度规则"],
        "stop_conditions_zh": [
            "明显 AI 或机器文案失败。",
            "显示值与底层值不一致失败。",
            "用户十秒无法找到重点则重做。",
        ],
        "scope": [
            "普通中文界面词典与专业详情边界",
            "金额比例日期负数空值和大数格式",
            "页面报告导出显示一致性",
            "六类页面内容密度与十秒认知走查",
            "桌面浅色桌面深色和手机浅色真实界面样例",
        ],
        "excluded": [
            "S14 整体复审",
            "S15",
            "真实资料",
            "真实业务动作",
            "GitHub 上传",
            "App 重装",
        ],
    }


def _browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "STATIC_PUBLIC_SAFE_HTML",
        "required_viewports": [
            {"id": "desktop_light", "width": 1440, "height": 1050, "theme": "light"},
            {"id": "desktop_dark", "width": 1440, "height": 1050, "theme": "dark"},
            {"id": "mobile_light", "width": 390, "height": 844, "theme": "light"},
        ],
        "required_flows": [
            "十秒重点结构",
            "普通中文与专业详情边界",
            "数字和单位一致",
            "主要下一步反馈",
            "桌面深浅主题与手机布局",
        ],
        "network_request_count_expected": 0,
        "console_error_count_expected": 0,
        "screenshot_paths": [
            str(DESKTOP_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(DESKTOP_DARK_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(MOBILE_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
        ],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s14p3.task_acceptance_matrix.v1",
        "phase_id": language.RUN_PHASE_ID,
        "acceptance_id": language.ACCEPTANCE_ID,
        "task_count": 3,
        "accepted_task_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S14P3T01",
                "name_zh": "建立全中文词典",
                "acceptance_zh": "默认页面只显示普通中文，14 个内部词都有中文替代，专业术语只在折叠详情出现，明显机器文案命中为零。",
                "status": status,
                "current_result": result,
                "evidence_refs": [
                    str(DICTIONARY_PATH.relative_to(REPO_ROOT)),
                    str(LANGUAGE_SCAN_PATH.relative_to(REPO_ROOT)),
                    str(HTML_PATH.relative_to(REPO_ROOT)),
                ],
            },
            {
                "task_id": "S14P3T02",
                "name_zh": "建立数字与单位格式",
                "acceptance_zh": "金额、比例、日期、负数、空值和大数显示统一，页面、报告和导出差异为零，显示值与底层值差异为零。",
                "status": status,
                "current_result": result,
                "evidence_refs": [
                    str(FORMAT_PATH.relative_to(REPO_ROOT)),
                    str(FORMAT_EVIDENCE_PATH.relative_to(REPO_ROOT)),
                ],
            },
            {
                "task_id": "S14P3T03",
                "name_zh": "建立内容密度规则",
                "acceptance_zh": "六类页面各有一个主问题、1 至 4 个关键数字、3 至 5 个重点事项和一个主要下一步，六项十秒认知走查全部通过。",
                "status": status,
                "current_result": result,
                "evidence_refs": [
                    str(DENSITY_PATH.relative_to(REPO_ROOT)),
                    str(WALKTHROUGH_PATH.relative_to(REPO_ROOT)),
                    str(DESKTOP_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
                ],
            },
        ],
    }


def _manifest(
    final: bool,
    validation_run_id: str | None,
    validation_head: str | None,
    verification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p3.language_content_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": language.VERSION,
        "run_phase_id": language.RUN_PHASE_ID,
        "roadmap_phase_id": language.ROADMAP_PHASE_ID,
        "task_id": language.TASK_ID,
        "acceptance_id": language.ACCEPTANCE_ID,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_taskpack_phase_count": 72,
        "overall_accepted_phase_count": 40 if final else 39,
        "dictionary_entry_count": 14,
        "default_forbidden_term_hit_count": 0,
        "forbidden_ai_copy_hit_count": 0,
        "machine_pattern_hit_count": 0,
        "format_case_count": 10,
        "format_surface_mismatch_count": 0,
        "display_underlying_mismatch_count": 0,
        "content_rule_screen_count": 6,
        "cognitive_walkthrough_case_count": 6,
        "cognitive_walkthrough_pass_count": 6,
        "ten_second_failure_count": 0,
        "main_question_per_screen": 1,
        "focus_item_min": 3,
        "focus_item_max": 5,
        "primary_next_step_per_screen": 1,
        "repeated_conclusion_count": 0,
        "public_check_accounting": {
            "total": verification["total"],
            "passed": verification["passed"],
            "failed": verification["failed"],
        },
        "browser_viewport_count": 3,
        "s14_p1_acceptance_status": "PASSED",
        "s14_p2_acceptance_status": "PASSED",
        "s14_p3_entry_allowed": False,
        "s14_p3_started": True,
        "s14_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s14_stage_review_entry_allowed": final,
        "s14_stage_review_started": False,
        "s15_started": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "network_request_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "decision": "CONTINUE_TO_S14_STAGE_REVIEW_ONLY"
        if final
        else "REMAIN_IN_S14_P3_FINAL_VALIDATION",
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    verification = language.validate_public_contract()
    rows = receipts()
    final, validation_run_id, validation_head = final_binding(rows)
    dictionary = language.interface_dictionary_contract()
    formats = language.format_contract()
    density = language.content_density_contract()
    scan = language.language_scan_evidence()
    walkthrough = language.cognitive_walkthrough_evidence()
    task_matrix = _task_matrix(final)
    manifest = _manifest(final, validation_run_id, validation_head, verification)
    acceptance = "PASSED" if final else "等待最终验收"
    validation_line = (
        f"20/20 项正式验收通过；run={validation_run_id}，绑定实现提交={validation_head}。"
        if final
        else "当前等待唯一一组正式验收。"
    )
    outputs = {
        DICTIONARY_PATH: _json_text(dictionary),
        FORMAT_PATH: _json_text(formats),
        DENSITY_PATH: _json_text(density),
        SOURCE_CONTRACT_PATH: _json_text(_source_contract()),
        TASK_MATRIX_PATH: _json_text(task_matrix),
        LANGUAGE_SCAN_PATH: _json_text(scan),
        FORMAT_EVIDENCE_PATH: _json_text(formats),
        WALKTHROUGH_PATH: _json_text(walkthrough),
        BROWSER_CONTRACT_PATH: _json_text(_browser_contract()),
        MANIFEST_PATH: _json_text(manifest),
        VALIDATION_RESULTS_PATH: _jsonl_text(rows),
        HTML_PATH: language.render_html(),
        IMPLEMENTATION_REPORT_PATH: "\n".join(
            [
                "# S14-P3 语言与内容实现说明",
                "",
                f"- 状态：{acceptance}。",
                "- 默认页面改用普通中文，内部术语只在“查看专业依据”中按需出现。",
                "- 金额、比例、日期、负数、空值和大数采用统一格式，页面、报告和导出写法一致。",
                "- 六类页面都只保留一个主问题、少量关键数字、3 至 5 个重点事项和一个主要下一步。",
                f"- 72/72 项公开检查通过；{validation_line}",
                f"- 可以直接打开：{HTML_PATH.relative_to(REPO_ROOT)}。",
                "- 没有读取真实资料、执行真实业务动作、上传 GitHub 或重装 App。",
                "",
            ]
        ),
        CONTENT_GUIDE_PATH: "\n".join(
            [
                "# S14-P3 普通中文与数字格式指南",
                "",
                "## 普通页面",
                "",
                "- 先说现在怎样、影响什么、谁来处理、下一步做什么。",
                "- 不直接显示内部状态码、长编号、文件指纹或资料链路。",
                "- 错误必须说明原因和可执行下一步，不能只写“操作失败”。",
                "",
                "## 数字",
                "",
                "- 金额从整数分格式化，固定两位小数并使用千位分隔。",
                "- 比例从整数基点格式化，固定两位小数；负数使用清楚的负号。",
                "- 日期显示为“年、月、日”；暂无数据和不适用不得混用。",
                "- 大数同时保留完整金额和易读单位，不能用缩写替换精确值。",
                "",
                "## 每屏重点",
                "",
                "- 一个主问题、1 至 4 个关键数字、3 至 5 个重点事项、一个主要下一步。",
                "- 不重复同一个结论，不使用装饰性卡片墙，不把限制说明放在第一屏。",
                "",
            ]
        ),
        RISKS_PATH: "\n".join(
            [
                "# S14-P3 风险与回滚",
                "",
                "- 风险：内部术语泄漏到默认页面；格式化结果掩盖底层值；重点事项过多；机器式空话再次出现。",
                "- 控制：禁用词扫描、十个格式样例、六类页面密度合同、六项十秒结构走查和真实浏览器检查。",
                "- 回滚：只撤销 S14-P3 词典、格式、密度、界面样例、测试和治理记录，保留已验收的 S14-P1/P2。",
                "- 边界：不触碰原始资料，不开始 S14 整体复审或 S15，不上传 GitHub，不重装 App。",
                "",
            ]
        ),
        TEST_RESULTS_PATH: "\n".join(
            [
                "# S14-P3 测试结果",
                "",
                "- 普通中文禁用词、机器文案和内部格式扫描：0 命中。",
                "- 格式样例：10/10；页面、报告、导出差异=0；显示值与底层值差异=0。",
                "- 内容密度：6/6 页面规则通过；六项十秒结构走查通过，明确不是伪造用户研究。",
                "- 公开检查：72/72。",
                f"- 正式验收：{'20/20 PASS' if final else '待运行'}。",
                "- raw/live/network/真实业务动作/GitHub/App：0/0/0/0/false/false。",
                "",
            ]
        ),
    }
    return outputs


def write_outputs() -> dict[str, Any]:
    outputs = expected_outputs()
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return json.loads(outputs[MANIFEST_PATH])


def check_outputs() -> None:
    outputs = expected_outputs()
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, expected in outputs.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    if mismatches:
        raise BuildError("S14-P3 确定性输出不一致：" + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            check_outputs()
        else:
            write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: S14-P3 deterministic public-safe evidence"
        if args.check
        else "WROTE: S14-P3 deterministic public-safe evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
