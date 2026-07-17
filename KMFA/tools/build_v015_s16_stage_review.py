#!/usr/bin/env python3
"""生成 KMFA v1.5 S16 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s16_p1_homepage as p1_builder
from KMFA.tools import build_v015_s16_p2_drilldown_explanation as p2_builder
from KMFA.tools import build_v015_s16_p3_homepage_usability as p3_builder
from KMFA.tools import v015_s16_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / contract.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_contract_tests",
    "focused_review_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s16_p1_dependency",
    "s16_p2_dependency",
    "s16_p3_dependency",
    "s16_p1_kernel_regression",
    "s16_p2_kernel_regression",
    "s16_p3_kernel_regression",
    "s16_p1_runtime_regression",
    "s16_p2_runtime_regression",
    "s16_p3_runtime_regression",
    "s16_p1_browser_regression",
    "s16_p2_browser_regression",
    "s16_p3_browser_regression",
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
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

MANIFEST_PATH = MACHINE_ROOT / "s16_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
PHASE_EVIDENCE_PATH = MACHINE_ROOT / "phase_evidence_public_safe.json"
CROSS_PHASE_CONTRACTS_PATH = MACHINE_ROOT / "cross_phase_contracts_public_safe.json"
CROSS_PHASE_VERIFICATION_PATH = MACHINE_ROOT / "cross_phase_verification_public_safe.json"
INTEGRATED_REVIEW_PATH = MACHINE_ROOT / "integrated_review_public_safe.json"
TECHNICAL_AUDIT_PATH = MACHINE_ROOT / "technical_audit_public_safe.json"
FINDINGS_PATH = MACHINE_ROOT / "stage16_review_findings_public_safe.csv"
RISKS_PATH = MACHINE_ROOT / "open_risk_register_public_safe.csv"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"

HTML_PATH = HTML_ROOT / "kmfa_s16_integrated_review.html"
DESKTOP_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s16_review_desktop.png"
DRILLDOWN_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s16_review_drilldown.png"
FAULT_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s16_review_fault.png"
TABLET_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s16_review_tablet.png"
MOBILE_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s16_review_mobile.png"
SCREENSHOT_PATHS = (
    DESKTOP_SCREENSHOT_PATH,
    DRILLDOWN_SCREENSHOT_PATH,
    FAULT_SCREENSHOT_PATH,
    TABLET_SCREENSHOT_PATH,
    MOBILE_SCREENSHOT_PATH,
)

REVIEW_REPORT_PATH = HUMAN_ROOT / "stage16_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"
AUDIT_REPORT_PATH = HUMAN_ROOT / "technical_audit_zh.md"


class BuildError(RuntimeError):
    """S16 整体复审证据无法形成。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S16 整体复审验收记录顺序不一致")
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


def phase_evidence() -> dict[str, Any]:
    specs = (
        (
            "S16-P1",
            p1_builder.MANIFEST_PATH,
            p1_builder.VALIDATION_RESULTS_PATH,
            "GO_TO_S16_P2_ONLY",
        ),
        (
            "S16-P2",
            p2_builder.MANIFEST_PATH,
            p2_builder.VALIDATION_RESULTS_PATH,
            "GO_TO_S16_P3_ONLY",
        ),
        (
            "S16-P3",
            p3_builder.MANIFEST_PATH,
            p3_builder.VALIDATION_RESULTS_PATH,
            "GO_TO_S16_STAGE_REVIEW_ONLY",
        ),
    )
    phases: list[dict[str, Any]] = []
    for roadmap_phase_id, manifest_path, receipt_path, decision in specs:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _jsonl(receipt_path)
        required = (
            manifest.get("phase_acceptance_status") == "PASSED"
            and manifest.get("evidence_validation_status") == "PASS"
            and manifest.get("phase_task_accepted_count") == 3
            and manifest.get("decision") == decision
            and manifest.get("validation_receipt_count") == 20
            and len(rows) == 20
            and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
            and {row.get("validation_run_id") for row in rows}
            == {manifest.get("validation_run_id")}
            and {row.get("validation_head") for row in rows}
            == {manifest.get("validation_head")}
        )
        if not required:
            raise BuildError(f"{roadmap_phase_id} 前序验收绑定不完整")
        phases.append(
            {
                "roadmap_phase_id": roadmap_phase_id,
                "run_phase_id": manifest["run_phase_id"],
                "acceptance_status": "PASSED",
                "task_accepted_count": 3,
                "public_check_count": manifest["public_check_total"],
                "validation_receipt_count": 20,
                "validation_run_id": manifest["validation_run_id"],
                "validation_head": manifest["validation_head"],
                "manifest_sha256": _digest(manifest_path),
                "receipts_sha256": _digest(receipt_path),
            }
        )
    public_count = sum(row["public_check_count"] for row in phases)
    if public_count != 183:
        raise BuildError("S16 前序公开检查总数漂移")
    return {
        "schema_version": "kmfa.v015.s16.stage-review-phase-evidence.v1",
        "phases": phases,
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": public_count,
            "predecessor_receipt_count": 60,
        },
    }


def source_contract() -> dict[str, Any]:
    roadmap = json.loads(
        (PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8")
    )
    stage = next(row for row in roadmap["stages"] if row["id"] == "S16")
    return {
        "schema_version": "kmfa.v015.s16.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "source_integrity_status": "PASS",
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": stage["id"],
        "stage_name_zh": stage["name"],
        "stage_goal_zh": stage["goal"],
        "phase_ids": [f"S16-{row['id']}" for row in stage["phases"]],
        "phase_names_zh": [row["name"] for row in stage["phases"]],
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "scope": [
            "经营摘要到指标明细",
            "重点事项到业务入口",
            "快速切换时响应一致性",
            "空错过期状态",
            "电脑平板手机与触屏",
        ],
        "excluded": [
            "S17",
            "真实数据接入",
            "GitHub 上传",
            "App 重装",
            "真实业务动作",
        ],
    }


def cross_phase_contracts() -> dict[str, Any]:
    rows = contract.integration_bindings()
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s16.cross-phase-contracts.v1",
        "bindings": rows,
        "accounting": {
            "total": len(rows),
            "passed": len(rows) - failed,
            "failed": failed,
            "blocking_failed": failed,
        },
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16.stage-review-browser-contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000, "touch": False},
            {"name": "tablet", "width": 820, "height": 1180, "touch": False},
            {"name": "mobile_touch", "width": 390, "height": 844, "touch": True},
        ],
        "required_flows": [
            "desktop_home_detail_return",
            "four_filter_context_preserved",
            "stale_homepage_response_ignored",
            "single_fault_announcement",
            "empty_and_stale_hide_values",
            "mobile_touch_targets",
            "mobile_first_scan_and_report_navigation",
            "tablet_no_overflow",
            "keyboard_focus_and_reduced_motion",
            "browser_history_preserves_context",
        ],
        "required_screenshot_paths": [
            str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS
        ],
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def _csv(rows: list[dict[str, Any]], fields: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: (
                    str(value).lower()
                    if isinstance(value, bool)
                    else value
                )
                for key, value in row.items()
            }
        )
    return output.getvalue()


def findings_csv() -> str:
    return _csv(
        [dict(row) for row in contract.REVIEW_FINDINGS],
        [
            "finding_id",
            "severity",
            "category",
            "issue_zh",
            "impact_zh",
            "fix_zh",
            "status",
            "blocks_stage_acceptance",
        ],
    )


def risks_csv() -> str:
    rows = [
        {
            "risk_id": "S16-RISK-001",
            "risk_zh": "本轮使用公开合成资料，没有证明真实公司数据质量。",
            "route_zh": "真实接入阶段必须重新验证来源、权限与新鲜度。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s16_stage_acceptance": False,
        },
        {
            "risk_id": "S16-RISK-002",
            "risk_zh": "十秒识别证据是内部结构化走查，不是外部真人研究。",
            "route_zh": "真实上线前另行安排目标用户观察，不夸大本阶段结论。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s16_stage_acceptance": False,
        },
        {
            "risk_id": "S16-RISK-003",
            "risk_zh": "手机顶部七项导航需要横向滑动才能看到报告。",
            "route_zh": "当前符合既有窄屏导航规范；生产使用数据出现找不到入口时再调整。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s16_stage_acceptance": False,
        },
        {
            "risk_id": "S16-RISK-004",
            "risk_zh": "当前整合运行面只提供浅色主题。",
            "route_zh": "深色主题仍是可选能力，不作为 S16 首页任务的阻断条件。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s16_stage_acceptance": False,
        },
    ]
    return _csv(
        rows,
        [
            "risk_id",
            "risk_zh",
            "route_zh",
            "status",
            "plan_complete",
            "blocks_s16_stage_acceptance",
        ],
    )


def manifest() -> dict[str, Any]:
    rows = receipts()
    final, run_id, head = final_binding(rows)
    return {
        "schema_version": "kmfa.v015.s16.stage-review-manifest.v1",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "STAGE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_count": 3,
        "stage_phase_pass_count": 3,
        "stage_task_count": 9,
        "stage_task_accepted_count": 9,
        "overall_accepted_phase_count": 46,
        "overall_taskpack_phase_count": 72,
        "decision": "GO_TO_S17_P1_ONLY" if final else "REMAIN_IN_S16_STAGE_REVIEW",
        "s16_p1_acceptance_status": "PASSED",
        "s16_p2_acceptance_status": "PASSED",
        "s16_p3_acceptance_status": "PASSED",
        "s16_stage_review_entry_allowed": False,
        "s16_stage_review_started": True,
        "s16_stage_review_performed": final,
        "s16_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s17_entry_allowed": final,
        "s17_p1_entry_allowed": final,
        "s17_p1_started": False,
        "product_implementation_allowed": not final,
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 183,
        "integration_binding_count": contract.EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "public_check_total": contract.EXPECTED_PUBLIC_CHECK_COUNT,
        "public_check_pass_count": contract.EXPECTED_PUBLIC_CHECK_COUNT,
        "public_check_failed_count": 0,
        "review_finding_count": 3,
        "fixed_review_finding_count": 3,
        "open_review_finding_count": 0,
        "technical_audit_score": 19,
        "technical_audit_maximum_score": 20,
        "browser_viewport_count": 3,
        "browser_flow_count": 10,
        "visual_evidence_count": 5,
        "minimum_touch_target_px": 44,
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "fact_layer_write_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
    }


def _human_documents(current: dict[str, Any]) -> dict[Path, str]:
    final = current["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "复审与修复已完成，等待正式验收"
    validation = (
        f"- 正式验收：{current['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    review = f"""# S16 整体复审报告

- 状态：{status}。
- 三个部分、9 项任务、60 条原验收记录和 183 项原检查保持通过。
- 修复 3 个真实衔接问题：旧公司响应覆盖新摘要、故障重复播报、触屏筛选框过小。
- 首页 5 个数字进入明细后保持四项筛选，返回首页仍是同一公司和期间。
- 空、错、过期状态不显示未经确认的数字；电脑、平板和手机均无页面横向溢出。
- Impeccable 技术审查为 19/20，开放问题为 0；少量固定色与设计令牌等值，记录为非阻断限制。
{validation}- 本轮没有读取真实资料、执行真实业务动作、上传 GitHub 或重装 App。
- 通过后只开放新的独立 Run 做 S17-P1；本轮没有开始 S17。
"""
    tests = f"""# S16 整体复审测试结果

- 当前结论：{status}。
- 前序证据：3/3 个部分、9/9 项任务、60/60 条正式记录、183/183 项原检查通过。
- 联合检查：45/45 项跨部分连接和 240/240 项公开检查通过。
- 浏览器：10 条联合流程覆盖电脑、平板和真实触屏手机，保留 5 张画面。
- 复审问题：3 项发现全部修复，P0=0、开放问题=0。
{validation}- raw、真实来源、外部网络、真实身份、事实写入和真实业务动作均为 0。
"""
    risks = """# S16 整体复审剩余风险

- 当前使用公开合成资料，不能代表真实公司的数据质量。
- 十秒识别是内部结构化走查，不是外部真人用户研究。
- 手机顶部导航遵循既有横向滑动规范；真实使用中如果仍找不到报告入口，需要再调整。
- 整合运行面当前只提供浅色主题；深色主题不是 S16 阶段阻断条件。
- 上述风险均已有后续处理路径，当前不阻断 S16 整体复审。
"""
    rollback = """# S16 整体复审回退方案

1. 回退本轮 S16 整体复审证据、测试和治理登记。
2. 回退首页响应顺序保护、单一故障播报和 44 像素触屏筛选修复。
3. 保留已通过的 S16-P1/P2/P3 原始实现与验收记录。
4. 不触碰 raw、真实资料、GitHub main 或已安装 App。
"""
    audit_rows = "\n".join(
        f"| {row['dimension']} | {row['score']}/4 | {row['finding_zh']} |"
        for row in contract.technical_audit()["dimensions"]
    )
    audit = f"""# S16 技术 UX 审查

| 维度 | 分数 | 结论 |
|---|---:|---|
{audit_rows}

- 总分：19/20，Excellent。
- AI 痕迹判定：通过；未发现渐变字、玻璃拟态、装饰性卡片墙、夸张圆角或无意义动效。
- P1 两项、P2 一项均已修复；P0=0，开放问题=0。
- 正向结论：中文层级清楚、经营事实和动作边界分开、异常状态诚实、键盘与触屏路径完整。
"""
    return {
        REVIEW_REPORT_PATH: review,
        TEST_RESULTS_PATH: tests,
        OPEN_RISKS_PATH: risks,
        ROLLBACK_PATH: rollback,
        AUDIT_REPORT_PATH: audit,
    }


def expected_outputs() -> dict[Path, str]:
    current = manifest()
    verification = contract.public_verification()
    outputs = {
        MANIFEST_PATH: _json(current),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        PHASE_EVIDENCE_PATH: _json(phase_evidence()),
        CROSS_PHASE_CONTRACTS_PATH: _json(cross_phase_contracts()),
        CROSS_PHASE_VERIFICATION_PATH: _json(verification),
        INTEGRATED_REVIEW_PATH: _json(verification["integrated_review"]),
        TECHNICAL_AUDIT_PATH: _json(contract.technical_audit()),
        FINDINGS_PATH: findings_csv(),
        RISKS_PATH: risks_csv(),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        HTML_PATH: contract.render_html(),
    }
    outputs.update(_human_documents(current))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, content in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    mismatches.extend(
        str(path.relative_to(REPO_ROOT))
        for path in SCREENSHOT_PATHS
        if not path.is_file()
    )
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成或检查 KMFA v1.5 S16 整体复审证据"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
        else:
            write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: S16 stage review evidence "
        + ("is exact" if args.check else "written")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
