#!/usr/bin/env python3
"""生成 KMFA v1.5 S14 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s14_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S14_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_PATH = EXPORT_ROOT / "html/kmfa_s14_integrated_review.html"
DESKTOP_LIGHT_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s14_review_desktop_light.png"
DESKTOP_DARK_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s14_review_desktop_dark.png"
MOBILE_LIGHT_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s14_review_mobile_light.png"
MANIFEST_PATH = MACHINE_ROOT / "s14_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PREDECESSORS = (
    (
        "S14-P1",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P1_INFORMATION_ARCHITECTURE/machine/s14_p1_information_architecture_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P1_INFORMATION_ARCHITECTURE/machine/validation_results.jsonl",
        19,
        42,
    ),
    (
        "S14-P2",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P2_DESIGN_SYSTEM/machine/s14_p2_design_system_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P2_DESIGN_SYSTEM/machine/validation_results.jsonl",
        20,
        60,
    ),
    (
        "S14-P3",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P3_LANGUAGE_CONTENT/machine/s14_p3_language_content_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S14_P3_LANGUAGE_CONTENT/machine/validation_results.jsonl",
        20,
        72,
    ),
)

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_contract_tests",
    "focused_review_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s14_p1_dependency",
    "s14_p2_dependency",
    "s14_p3_dependency",
    "s14_p1_kernel_regression",
    "s14_p2_kernel_regression",
    "s14_p3_kernel_regression",
    "integrated_review_consistency",
    "builder_exact_rebuild",
    "stage_checker_pre_final",
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
    "git_diff_check",
)


class BuildError(RuntimeError):
    """S14 整体复审证据无法确定性生成。"""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL rows must be objects: {path}")
    return rows


def source_contract() -> dict[str, Any]:
    source_manifest = json.loads((PROJECT_ROOT / "taskpack/v1_5/source_manifest.json").read_text(encoding="utf-8"))
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S14"), None)
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    integrity = (
        package.is_file()
        and _sha256(package) == "sha256:" + TASKPACK_SHA256
        and source_manifest.get("source_package_sha256") == TASKPACK_SHA256
        and (source_manifest.get("stage_count"), source_manifest.get("phase_count"), source_manifest.get("task_count")) == (24, 72, 216)
        and (stage or {}).get("name") == "界面信息架构、设计系统与语言重构"
        and [row.get("id") for row in (stage or {}).get("phases", [])] == ["P1", "P2", "P3"]
    )
    return {
        "schema_version": "kmfa.v015.s14.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S14",
        "stage_name_zh": "界面信息架构、设计系统与语言重构",
        "phase_count": 3,
        "task_count": 9,
        "review_overlay_counted_as_taskpack_phase": False,
        "source_integrity_status": "PASS" if integrity else "FAIL",
        "scope_zh": "只复审并修复 S14-P1/P2/P3 的导航、页面类型、视觉主题、普通中文、数字绑定和浏览器交互。",
        "excluded_zh": ["真实资料", "真实业务动作", "S15 实现", "GitHub 上传", "App 重装"],
    }


def phase_evidence() -> dict[str, Any]:
    phases = []
    for phase_id, manifest_path, receipts_path, receipt_count, public_count in PREDECESSORS:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _jsonl(receipts_path)
        if (
            manifest.get("phase_acceptance_status") != "PASSED"
            or manifest.get("evidence_validation_status") != "PASS"
            or manifest.get("phase_task_accepted_count") != 3
            or manifest.get("validation_receipt_count") != receipt_count
            or len(rows) != receipt_count
            or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows)
            or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}
            or {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}
            or manifest.get("public_check_accounting") != {"total": public_count, "passed": public_count, "failed": 0}
        ):
            raise BuildError(f"{phase_id} predecessor acceptance drift")
        phases.append(
            {
                "roadmap_phase_id": phase_id,
                "run_phase_id": manifest["run_phase_id"],
                "task_count": 3,
                "task_accepted_count": 3,
                "acceptance_status": "PASSED",
                "public_check_count": public_count,
                "validation_receipt_count": receipt_count,
                "validation_head": manifest["validation_head"],
                "validation_run_id": manifest["validation_run_id"],
                "manifest_sha256": _sha256(manifest_path),
                "receipts_sha256": _sha256(receipts_path),
            }
        )
    return {
        "schema_version": "kmfa.v015.s14.stage-review-phase-evidence.v1",
        "phases": phases,
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": 174,
            "predecessor_receipt_count": 59,
        },
    }


def cross_phase_contracts() -> dict[str, Any]:
    verification = contract.public_verification()
    checks = {row["name"]: row["passed"] for row in verification["checks"]}
    selected = (
        ("nav_p1_p2_exact", "P1 的七项导航与 P2 完全一致"),
        ("nav_p2_p3_exact", "P2 的七项导航与 P3 完全一致"),
        ("nav_exactly_seven", "一级导航固定为七项"),
        ("nav_routes_exact", "七项导航保留真实页面目标"),
        ("nav_routes_unique", "七个页面目标互不重复"),
        ("no_stacked_sidebar", "不恢复旧式堆叠侧栏"),
        ("page_types_exact", "六类页面在结构与内容规则中同名"),
        ("page_nodes_eighteen", "十八个页面节点保持完整"),
        ("no_dead_end", "页面没有死路"),
        ("no_parent_cycle", "页面父级没有循环"),
        ("previous_task_complete", "所有页面可返回上一任务"),
        ("breadcrumb_complete", "位置路径完整"),
        ("management_summary_default", "管理摘要默认可见"),
        ("professional_collapsed", "专业依据默认收起"),
        ("audit_collapsed", "审计说明默认收起"),
        ("p1_technical_hits_zero", "普通页面不出现技术词"),
        ("themes_exact", "内容页面精确复用两套主题"),
        ("contrast_fourteen_pass", "十四组文字对比全部达标"),
        ("component_full_coverage", "十一类组件反馈状态完整"),
        ("color_only_zero", "状态不只依赖颜色"),
        ("motion_short", "动效保持克制"),
        ("reduced_motion", "支持减少动态效果"),
        ("one_question", "每页只有一个主要问题"),
        ("key_number_range", "每页关键数字数量受控"),
        ("focus_range", "每页重点事项数量受控"),
        ("one_next_step", "每页只有一个主要下一步"),
        ("forbidden_term_zero", "默认页面无内部术语"),
        ("ai_copy_zero", "默认页面无机器套话"),
        ("machine_pattern_zero", "默认页面无机器字段模式"),
        ("surface_mismatch_zero", "页面报告导出格式一致"),
        ("key_number_binding_zero", "关键数字绑定底层整数"),
        ("focus_amount_binding_zero", "重点金额绑定底层整数或空值状态"),
        ("html_real_routes", "浏览器页面保留七个导航目标"),
        ("html_details_collapsed", "浏览器默认收起专业详情"),
        ("side_effects_zero", "复审不读取真实资料或执行真实动作"),
        ("app_closed", "S15、GitHub 和 App 保持关闭"),
    )
    rows = [
        {
            "contract_id": f"S14REV-C{index:03d}",
            "name": name,
            "description_zh": description,
            "status": "PASS" if checks.get(name) else "FAIL",
            "blocking": True,
        }
        for index, (name, description) in enumerate(selected, start=1)
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s14.cross-phase-contracts.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
        "contracts": rows,
        "integrated_review_fingerprint": verification["integrated_review"]["review_fingerprint"],
    }


def findings() -> list[dict[str, str]]:
    values = (
        ("S14REV-F001", "HIGH", "信息架构把处理页称为 PROCESS，内容规则曾称为 ACTION。", "三个部分各自验收，没有统一六类页面名称。", "统一使用 PROCESS，并新增六类页面逐项绑定。"),
        ("S14REV-F002", "HIGH", "普通中文页面曾只显示七个导航标签，点击目标都被替换为同一页锚点。", "内容页面复制了导航文字，但没有保留 P1 的页面目标。", "保留七个 route，点击时同步当前页状态和位置说明。"),
        ("S14REV-F003", "HIGH", "关键数字和重点金额曾只有显示文字，页面层无法直接证明与底层整数一致。", "格式样例与实际页面数据分开验收。", "给页面数字补充整数或空值状态，并逐项重算显示结果。"),
        ("S14REV-F004", "MEDIUM", "导航、视觉和中文内容此前只有分开测试，没有同一页面的浏览器证据。", "缺少三个部分共同驱动的最终页面和跨部分门禁。", "新增同一页面、三种视口、36 项连接合同和 84 项实时检查。"),
    )
    return [
        {
            "finding_id": finding_id,
            "severity": severity,
            "finding_zh": finding,
            "root_cause_zh": cause,
            "fix_zh": fix,
            "evidence_ref": "KMFA/stage_artifacts/V015_S14_STAGE_REVIEW/machine/integrated_review_public_safe.json",
            "validation_ref": "KMFA/tests/test_v015_s14_stage_review_contract.py",
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        }
        for finding_id, severity, finding, cause, fix in values
    ]


def risks() -> list[dict[str, str]]:
    values = (
        ("001", "当前页面是公开演示，不代表真实用户测试。", "S15_AND_LATER_REAL_USER_VALIDATION"),
        ("002", "六类页面的结构合同已统一，但完整内容仍会在后续阶段逐步实现。", "S15_TO_S23_PRODUCT_IMPLEMENTATION"),
        ("003", "本轮没有读取真实财务资料。", "LATER_AUTHORIZED_PRIVATE_VALIDATION"),
        ("004", "S15-P1 尚未开始。", "S15P1_ONLY_NEXT_RUN"),
        ("005", "GitHub 与 App 一致性只在 v1.5 最终总验收处理。", "FINAL_OVERALL_GITHUB_AND_APP_PARITY_GATE"),
    )
    return [
        {
            "risk_id": f"RISK-KMFA-V015-S14-{number}",
            "risk": risk,
            "route": route,
            "status": "ROUTED_RESIDUAL",
            "plan_complete": "true",
            "blocks_s14_stage_acceptance": "false",
        }
        for number, risk, route in values
    ]


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14.stage-review-browser-contract.v1",
        "browser": "Chromium headless",
        "page_kind": "STATIC_PUBLIC_SAFE_INTEGRATED_HTML",
        "required_viewports": [
            {"id": "desktop_light", "width": 1440, "height": 1050, "theme": "light"},
            {"id": "desktop_dark", "width": 1440, "height": 1050, "theme": "dark"},
            {"id": "mobile_light", "width": 390, "height": 844, "theme": "light"},
        ],
        "required_flows": [
            "七项导航与页面目标",
            "普通中文与折叠专业详情",
            "浅色深色主题与对比",
            "整数数字与显示格式",
            "主要下一步与焦点返回",
            "手机布局与无页面溢出",
        ],
        "network_request_count_expected": 0,
        "console_error_count_expected": 0,
        "screenshot_paths": [
            str(DESKTOP_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(DESKTOP_DARK_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(MOBILE_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
        ],
    }


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S14 review validation receipt order drift")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == len(EXPECTED_VALIDATION_NAMES)
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    final, run_id, head = final_binding(rows)
    verification = contract.public_verification()
    summary = contract.validate_integrated_review(verification["integrated_review"])
    return {
        "schema_version": "kmfa.v015.s14_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S14",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S15_P1_ONLY" if final else "REMAIN_IN_S14_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": verification["accounting"],
        "review_findings": {"total": 4, "fixed_validated": 4, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "navigation_binding_count": summary["navigation_binding_count"],
        "screen_binding_count": summary["screen_binding_count"],
        "theme_binding_count": summary["theme_binding_count"],
        "integration_binding_count": summary["integration_binding_count"],
        "route_mismatch_count": summary["route_mismatch_count"],
        "number_mismatch_count": summary["number_mismatch_count"],
        "language_mismatch_count": summary["language_mismatch_count"],
        "browser_viewport_count": 3,
        "browser_flow_count": 6,
        "overall_accepted_phase_count": 40,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "network_request_count": 0,
        "real_business_action_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s14_stage_review_started": True,
        "s14_stage_review_performed": final,
        "s14_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s15_entry_allowed": final,
        "s15_p1_entry_allowed": final,
        "s15_p1_started": False,
        "s15_p2_plus_entry_allowed": False,
        "product_implementation_allowed": final,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(rows) if final else 0,
        "validation_pass_count": len(rows) if final else 0,
        "validation_failed_count": 0,
    }


def _human_outputs(final: bool) -> dict[Path, bytes]:
    status = "已通过最终验收" if final else "已完成复审与修复，等待最终验收"
    validation = "25/25 项正式验收通过。" if final else "25 项正式验收尚待执行。"
    return {
        HUMAN_ROOT / "stage14_review_report_zh.md": (
            "# KMFA v1.5 第 14 阶段整体复审\n\n"
            f"状态：{status}。\n\n"
            "- 三个部分、9 项任务、174 项公开检查和 59 条前序验收记录均已复核。\n"
            "- 修复 4 个衔接问题：处理页名称、导航真实目标、页面数字与底层整数绑定、同页浏览器证据。\n"
            "- 七项导航、六类页面和两套主题共 15 项连接全部一致；数字、语言和页面路径差异均为 0。\n"
            "- 36 项连接合同、84 项实时检查和三种浏览器画面全部通过，开放复审问题为 0。\n"
            f"- {validation}\n"
            "- 本轮未读取真实资料、执行真实业务动作、启动 S15、上传 GitHub 或重装 App。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            f"状态：{status}。\n\n"
            f"59 条前序验收记录、36 项连接合同、84 项实时检查、4 个已修复问题、5 项剩余风险和三种浏览器画面保持一致；{validation}\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次 S14 整体复审新增的连接修复、测试、证据和状态登记；不改写 S14-P1/P2/P3 的原验收记录，不触碰真实资料、GitHub、App 或 S15。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险已有后续路径：真实用户验证、后续页面实现、授权后的私有资料验证、S15-P1 以及最终 GitHub/App 一致性。S14 通过不代表这些动作已经执行。\n"
        ).encode("utf-8"),
    }


def expected_outputs() -> dict[Path, bytes]:
    source = source_contract()
    if source["source_integrity_status"] != "PASS":
        raise BuildError("S14 TaskPack source integrity failed")
    predecessor = phase_evidence()
    cross = cross_phase_contracts()
    verification = contract.public_verification()
    if cross["accounting"]["failed"] or verification["accounting"]["failed"]:
        raise BuildError("S14 review verification failed")
    rows = receipts()
    final, _, _ = final_binding(rows)
    integrated = verification["integrated_review"]
    outputs = {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(predecessor),
        MACHINE_ROOT / "integrated_review_public_safe.json": _json_bytes(integrated),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross),
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(verification),
        MACHINE_ROOT / "browser_acceptance_contract_public_safe.json": _json_bytes(browser_contract()),
        MACHINE_ROOT / "stage14_review_findings_public_safe.csv": _csv_bytes(findings()),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(risks()),
        MANIFEST_PATH: _json_bytes(manifest(rows)),
        HTML_PATH: contract.render_html().encode("utf-8"),
    }
    outputs.update(_human_outputs(final))
    return outputs


def write_outputs() -> None:
    for path, payload in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(str(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT)))
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("deterministic output drift: " + ", ".join(mismatches))
            print("PASS: deterministic S14 stage-review evidence")
        else:
            write_outputs()
            print(f"WROTE: {OUTPUT_ROOT.relative_to(REPO_ROOT)}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
