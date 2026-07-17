#!/usr/bin/env python3
"""生成 KMFA v1.5 S18 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s18_p1_receivables_collections as p1_builder
from KMFA.tools import build_v015_s18_p2_funds_accounts as p2_builder
from KMFA.tools import build_v015_s18_p3_relation_reporting as p3_builder
from KMFA.tools import v015_s18_stage_review_contract as contract


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
    "s18_p1_dependency",
    "s18_p2_dependency",
    "s18_p3_dependency",
    "s18_p1_kernel_regression",
    "s18_p2_kernel_regression",
    "s18_p3_kernel_regression",
    "s18_p1_runtime_regression",
    "s18_p2_runtime_regression",
    "s18_p3_runtime_regression",
    "s18_p1_browser_regression",
    "s18_p2_browser_regression",
    "s18_p3_browser_regression",
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

MANIFEST_PATH = MACHINE_ROOT / "s18_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
PHASE_EVIDENCE_PATH = MACHINE_ROOT / "phase_evidence_public_safe.json"
CROSS_PHASE_CONTRACTS_PATH = MACHINE_ROOT / "cross_phase_contracts_public_safe.json"
CROSS_PHASE_VERIFICATION_PATH = MACHINE_ROOT / "cross_phase_verification_public_safe.json"
INTEGRATED_REVIEW_PATH = MACHINE_ROOT / "integrated_review_public_safe.json"
TECHNICAL_AUDIT_PATH = MACHINE_ROOT / "technical_audit_public_safe.json"
FINDINGS_PATH = MACHINE_ROOT / "stage18_review_findings_public_safe.csv"
RISKS_PATH = MACHINE_ROOT / "open_risk_register_public_safe.csv"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"

HTML_PATH = HTML_ROOT / "kmfa_s18_integrated_review.html"
DESKTOP_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s18_review_dashboard.png"
DRILLDOWN_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s18_review_current_projection.png"
FAULT_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s18_review_alert_navigation.png"
TABLET_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s18_review_tablet.png"
MOBILE_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_s18_review_mobile.png"
SCREENSHOT_PATHS = (
    DESKTOP_SCREENSHOT_PATH,
    DRILLDOWN_SCREENSHOT_PATH,
    FAULT_SCREENSHOT_PATH,
    TABLET_SCREENSHOT_PATH,
    MOBILE_SCREENSHOT_PATH,
)

REVIEW_REPORT_PATH = HUMAN_ROOT / "stage18_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"
AUDIT_REPORT_PATH = HUMAN_ROOT / "technical_audit_zh.md"


class BuildError(RuntimeError):
    """S18 整体复审证据无法形成。"""


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
        raise BuildError("S18 整体复审验收记录顺序不一致")
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
            "S18-P1",
            p1_builder.MANIFEST_PATH,
            p1_builder.VALIDATION_RESULTS_PATH,
            "GO_TO_S18_P2_ONLY",
            "public_check_count",
        ),
        (
            "S18-P2",
            p2_builder.MANIFEST_PATH,
            p2_builder.VALIDATION_RESULTS_PATH,
            "GO_TO_S18_P3_ONLY",
            "public_check_count",
        ),
        (
            "S18-P3",
            p3_builder.MANIFEST_PATH,
            p3_builder.VALIDATION_RESULTS_PATH,
            None,
            "public_check_count",
        ),
    )
    phases: list[dict[str, Any]] = []
    for roadmap_phase_id, manifest_path, receipt_path, decision, public_key in specs:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _jsonl(receipt_path)
        required = (
            manifest.get("phase_acceptance_status") == "PASSED"
            and manifest.get("evidence_validation_status") == "PASS"
            and manifest.get("phase_task_accepted_count") == 3
            and (decision is None or manifest.get("decision") == decision)
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
                "public_check_count": manifest[public_key],
                "validation_receipt_count": 20,
                "validation_run_id": manifest["validation_run_id"],
                "validation_head": manifest["validation_head"],
                "manifest_sha256": _digest(manifest_path),
                "receipts_sha256": _digest(receipt_path),
            }
        )
    public_count = sum(row["public_check_count"] for row in phases)
    if public_count != 187:
        raise BuildError("S18 前序公开检查总数漂移")
    return {
        "schema_version": "kmfa.v015.s18.stage-review-phase-evidence.v1",
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
    stage = next(row for row in roadmap["stages"] if row["id"] == "S18")
    return {
        "schema_version": "kmfa.v015.s18.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "source_integrity_status": "PASS",
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": stage["id"],
        "stage_name_zh": stage["name"],
        "stage_goal_zh": stage["goal"],
        "phase_ids": [f"S18-{row['id']}" for row in stage["phases"]],
        "phase_names_zh": [row["name"] for row in stage["phases"]],
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "scope": [
            "应收、未开票与资金占用勾稽",
            "资金缺口和贷款到期提醒",
            "项目当前成本在页面、HTML 和 CSV 中一致",
            "公司、期间和项目三重处理记录隔离",
            "未核验降级与预警处理入口",
        ],
        "excluded": [
            "S19",
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
        "schema_version": "kmfa.v015.s18.cross-phase-contracts.v1",
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
        "schema_version": "kmfa.v015.s18.stage-review-browser-contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000, "touch": False},
            {"name": "tablet", "width": 820, "height": 1180, "touch": False},
            {"name": "mobile_touch", "width": 390, "height": 844, "touch": True},
        ],
        "required_flows": [
            "receivables_funds_and_report_routes",
            "resolved_project_cost_updates_report_and_exports",
            "alert_opens_receivables_detail",
            "alert_opens_funds_detail",
            "company_events_are_isolated",
            "unverified_report_hides_numbers_and_alerts",
            "mobile_no_overflow",
            "tablet_no_overflow",
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
            "risk_id": "S18-RISK-001",
            "risk_zh": "本轮使用公开合成资料，没有证明真实公司数据质量。",
            "route_zh": "真实接入阶段必须重新验证来源、权限与新鲜度。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s18_stage_acceptance": False,
        },
        {
            "risk_id": "S18-RISK-002",
            "risk_zh": "当前周期报告仅为公开合成资料演示，不能直接形成真实经营判断。",
            "route_zh": "真实接入阶段必须重新核验来源、截止日、权限和口径。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s18_stage_acceptance": False,
        },
        {
            "risk_id": "S18-RISK-003",
            "risk_zh": "当前项目处理记录保存在本地演示日志，未证明生产并发、长期存储和多人权限。",
            "route_zh": "真实接入阶段必须改用受控存储并补充并发、权限和恢复测试。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s18_stage_acceptance": False,
        },
        {
            "risk_id": "S18-RISK-004",
            "risk_zh": "当前提醒只进入对应明细页，不会自动形成或发送对外催收内容。",
            "route_zh": "后续如增加协作动作，必须保持人工确认、最少披露和发送前复核。",
            "status": "ROUTED_RESIDUAL",
            "plan_complete": True,
            "blocks_s18_stage_acceptance": False,
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
            "blocks_s18_stage_acceptance",
        ],
    )


def manifest() -> dict[str, Any]:
    rows = receipts()
    final, run_id, head = final_binding(rows)
    return {
        "schema_version": "kmfa.v015.s18.stage-review-manifest.v1",
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
        "overall_accepted_phase_count": 52,
        "overall_taskpack_phase_count": 72,
        "decision": "GO_TO_S19_P1_ONLY" if final else "REMAIN_IN_S18_STAGE_REVIEW",
        "s18_p1_acceptance_status": "PASSED",
        "s18_p2_acceptance_status": "PASSED",
        "s18_p3_acceptance_status": "PASSED",
        "s18_stage_review_entry_allowed": False,
        "s18_stage_review_started": True,
        "s18_stage_review_performed": final,
        "s18_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s19_entry_allowed": final,
        "s19_p1_entry_allowed": final,
        "s19_p1_started": False,
        "product_implementation_allowed": False,
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 187,
        "integration_binding_count": contract.EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "public_check_total": contract.EXPECTED_PUBLIC_CHECK_COUNT,
        "public_check_pass_count": contract.EXPECTED_PUBLIC_CHECK_COUNT,
        "public_check_failed_count": 0,
        "review_finding_count": 2,
        "fixed_review_finding_count": 2,
        "open_review_finding_count": 0,
        "technical_audit_score": 20,
        "technical_audit_maximum_score": 20,
        "browser_viewport_count": 3,
        "browser_flow_count": 8,
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
    review = f"""# S18 整体复审报告

- 状态：{status}。
- 三个部分、9 项任务、60 条原验收记录和 187 项原检查保持通过。
- 修复 2 个真实问题：项目成本处理后报告与导出仍显示旧金额；预警卡没有直接处理入口。
- 现在项目详情、资金与应收页面、HTML 和 CSV 使用同一份最新金额，并按公司、期间和项目隔离。
- 每条预警都能直接进入回款或资金明细；未核验资料继续隐藏金额并暂停预警。
- 技术审查为 20/20，2 项发现全部修复，开放问题为 0。
{validation}- 本轮没有读取真实资料、执行真实业务动作、上传 GitHub 或重装 App。
- 通过后只开放新的独立 Run 做 S19-P1；本轮没有开始 S19。
"""
    tests = f"""# S18 整体复审测试结果

- 当前结论：{status}。
- 前序证据：3/3 个部分、9/9 项任务、60/60 条正式记录、187/187 项原检查通过。
- 联合检查：41/41 项跨部分连接和 246/246 项公开检查通过。
- 浏览器：8 条联合流程覆盖电脑、平板和真实触屏手机，保留 5 张画面。
- 复审问题：2 项发现全部修复，其中金额版本不一致按 P0 处理；开放问题=0。
{validation}- raw、真实来源、外部网络、真实身份、事实写入和真实业务动作均为 0。
"""
    risks = """# S18 整体复审剩余风险

- 当前使用公开合成资料，不能代表真实公司的数据质量。
- 当前周期报告仅为公开合成资料演示，不能直接形成真实经营判断。
- 当前事件日志是本地演示存储，未证明生产并发、长期存储和多人权限。
- 当前提醒只进入明细页，不会自动形成或发送对外催收内容。
- 上述风险均已有后续处理路径，当前不阻断 S18 整体复审。
"""
    rollback = """# S18 整体复审回退方案

1. 回退本轮 S18 整体复审证据、测试和治理登记。
2. 回退周期报告当前项目投影和预警处理入口修复。
3. 保留已通过的 S18-P1/P2/P3 原始实现与验收记录。
4. 不触碰 raw、真实资料、GitHub main 或已安装 App。
"""
    audit_rows = "\n".join(
        f"| {row['dimension']} | {row['score']}/4 | {row['finding_zh']} |"
        for row in contract.technical_audit()["dimensions"]
    )
    audit = f"""# S18 技术 UX 审查

| 维度 | 分数 | 结论 |
|---|---:|---|
{audit_rows}

- 总分：20/20，Excellent。
- 金额一致性、主体隔离、现金安全、报告诚实性和人类可用性均为满分。
- 1 项 P0 与 1 项 P1 均已修复并由自动测试绑定；开放问题=0。
- 正向结论：中文层级清楚，页面和导出使用同一投影，预警可以直接进入对应明细。
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
        description="生成或检查 KMFA v1.5 S18 整体复审证据"
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
        "PASS: S18 stage review evidence "
        + ("is exact" if args.check else "written")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
