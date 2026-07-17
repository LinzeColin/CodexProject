#!/usr/bin/env python3
"""生成 KMFA v1.5 S15-P2 可复验、公开安全的身份与角色证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s15_p2_identity_roles as runtime
from KMFA.tools import v015_s15_p2_identity_roles as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "56158db407f013a30c95645444ce8ff75c395ea0"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s15_p1_dependency",
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
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"

MANIFEST_PATH = MACHINE_ROOT / "s15_p2_identity_roles_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
IDENTITY_CONTRACT_PATH = MACHINE_ROOT / "identity_role_contract_public_safe.json"
PERMISSION_CONTRACT_PATH = MACHINE_ROOT / "permission_matrix_public_safe.json"
AUDIT_CONTRACT_PATH = MACHINE_ROOT / "authorization_audit_contract_public_safe.json"
APPROVAL_CONTRACT_PATH = MACHINE_ROOT / "approval_separation_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_identity_roles.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_identity_roles_desktop.png",
    SCREENSHOT_ROOT / "kmfa_identity_roles_denied.png",
    SCREENSHOT_ROOT / "kmfa_identity_roles_approved.png",
    SCREENSHOT_ROOT / "kmfa_identity_roles_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_P1_APP_SHELL/machine/s15_p1_app_shell_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_P1_APP_SHELL/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    """S15-P2 证据无法形成。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S15_P1_APP_SHELL",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S15_P2_ONLY",
        "s15_p2_entry_allowed": True,
        "s15_p2_started": False,
        "validation_receipt_count": 20,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S15-P1 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S15-P1 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S15-P1 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S15-P1 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s15_p2_entry_allowed": True,
        "s15_p2_started": False,
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
        raise BuildError("S15-P2 验收记录顺序不一致")
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
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    contract = kernel.source_contract()
    contract.update(
        {
            "source_package_sha256": TASKPACK_SHA256,
            "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
            "scope": ["公开角色帽子", "五类最小权限", "默认拒绝和操作记录", "三类审批分离"],
            "excluded": ["生产身份认证", "真实账号和凭据", "S15-P3", "S15 整体复审", "真实资料", "GitHub 上传", "App 重装"],
        }
    )
    return contract


def identity_contract() -> dict[str, Any]:
    return {
        **kernel.build_contract(),
        "public_users": [
            {"user_id": user_id, "label_zh": value["label_zh"], "role_ids": list(value["role_ids"]), "company_ids": list(value["company_ids"])}
            for user_id, value in kernel.PUBLIC_USERS.items()
        ],
        "role_hats": [
            {"role_id": role_id, **value}
            for role_id, value in kernel.ROLE_HATS.items()
        ],
        "role_switch_policy": "只允许切换到用户已分配角色，并要求填写理由",
        "operation_binding_fields": ["actor_user_id", "actor_role", "company_id", "request_reason", "decision_zh"],
    }


def permission_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p2.permission_matrix.v1",
        "default_policy": "DENY",
        "resource_domain_count": len(kernel.RESOURCE_CATALOG),
        "permission_grant_count": sum(len(value) for value in kernel.ROLE_PERMISSIONS.values()),
        "resource_domains": [
            {
                "resource": resource,
                "label_zh": spec["label_zh"],
                "actions": [{"action": action, "label_zh": label} for action, label in spec["actions"].items()],
            }
            for resource, spec in kernel.RESOURCE_CATALOG.items()
        ],
        "role_grants": {
            role: [{"resource": resource, "action": action} for resource, action in sorted(grants)]
            for role, grants in kernel.ROLE_PERMISSIONS.items()
        },
        "sensitive_detail_policy": "经营负责人默认看不到敏感来源说明；财务角色可在已授权主体内查看",
        "unknown_resource_allowed": False,
        "ungranted_action_allowed": False,
    }


def _audit_examples() -> list[dict[str, Any]]:
    denied = kernel.authorization_decision(
        event_id="AUDIT-DEMO-001", occurred_at="DETERMINISTIC-T1", user_id="demo-owner",
        role_id="management", company_id="demo-north", resource="DATA_SOURCE",
        action="VIEW_SENSITIVE", reason="查看敏感来源说明",
    )
    allowed = kernel.authorization_decision(
        event_id="AUDIT-DEMO-002", occurred_at="DETERMINISTIC-T2", user_id="demo-owner",
        role_id="finance", company_id="demo-north", resource="DATA_SOURCE",
        action="VIEW_SENSITIVE", reason="核对财务来源说明",
    )
    switched = kernel.role_switch_decision(
        event_id="AUDIT-DEMO-003", occurred_at="DETERMINISTIC-T3", user_id="demo-owner",
        from_role="management", to_role="finance", company_id="demo-north", reason="核对财务来源",
    )
    return [denied, allowed, switched]


def audit_contract() -> dict[str, Any]:
    events = _audit_examples()
    return {
        "schema_version": "kmfa.v015.s15p2.authorization_audit_contract.v1",
        "event_count": len(events),
        "blocked_event_count": sum(not event["allowed"] for event in events),
        "role_and_reason_bound_count": sum(bool(event.get("actor_role") and event.get("request_reason")) for event in events),
        "unauthorized_access_logged": True,
        "real_business_action_count": 0,
        "events": events,
    }


def approval_contract() -> dict[str, Any]:
    created = kernel.approval_request_decision(
        event_id="APPROVAL-DEMO-001", request_id="REQUEST-DEMO-001", occurred_at="DETERMINISTIC-T1",
        action_type="REPORT_PUBLISH", user_id="demo-owner", role_id="finance",
        company_id="demo-north", reason="申请发布公开演示报告",
    )
    same_role = kernel.approval_confirmation_decision(
        event_id="APPROVAL-DEMO-002", occurred_at="DETERMINISTIC-T2", request=created["request"] or {},
        user_id="demo-owner", role_id="finance", company_id="demo-north", reason="尝试由原角色确认",
    )
    approved = kernel.approval_confirmation_decision(
        event_id="APPROVAL-DEMO-003", occurred_at="DETERMINISTIC-T3", request=created["request"] or {},
        user_id="demo-owner", role_id="reviewer", company_id="demo-north", reason="审核发布理由与公开范围",
    )
    return {
        "schema_version": "kmfa.v015.s15p2.approval_separation_contract.v1",
        "approval_flows": [{"action_type": key, **value} for key, value in kernel.APPROVAL_FLOWS.items()],
        "approval_flow_count": len(kernel.APPROVAL_FLOWS),
        "same_role_confirmation_allowed": same_role["allowed"],
        "same_person_different_role_confirmation_allowed": approved["allowed"],
        "same_person_different_role_recorded": approved["request"].get("approval", {}).get("same_person_different_role"),
        "invented_person_required": False,
        "real_business_action_count": 0,
        "example_request": created["request"],
        "example_same_role_denial": same_role["event"],
        "example_different_role_confirmation": approved,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p2.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": [
            "role_switch_changes_permissions_without_expansion",
            "unassigned_role_and_cross_company_denied",
            "role_persistence_with_reload_recheck",
            "same_person_different_role_approval",
            "keyboard_mobile_permission_table",
            "default_denied_and_approved_visual_evidence",
        ],
        "required_screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S15P2T01", "name_zh": "建立用户与角色帽子",
            "acceptance_zh": "同一人可以使用已分配的不同角色；每条操作记录当时角色和理由，未分配角色无法切换。",
            "status": status, "current_result": result,
            "evidence_refs": [str(IDENTITY_CONTRACT_PATH.relative_to(REPO_ROOT)), str(AUDIT_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P2T02", "name_zh": "建立最小权限",
            "acceptance_zh": "数据来源、公司主体、报告、参数和发布分别授权；未知或未授权操作默认拒绝并记录。",
            "status": status, "current_result": result,
            "evidence_refs": [str(PERMISSION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(AUDIT_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P2T03", "name_zh": "建立审批分离",
            "acceptance_zh": "三类高风险事项由不同角色发起和确认；小团队同一人可换已分配角色，但必须记录角色与理由。",
            "status": status, "current_result": result,
            "evidence_refs": [str(APPROVAL_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s15p2.task_acceptance_matrix.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "phase_acceptance_status": status,
        "phase_task_count": len(tasks),
        "phase_task_accepted_count": len(tasks) if final else 0,
        "tasks": tasks,
    }


def manifest() -> dict[str, Any]:
    predecessor = dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    core = kernel.build_contract()
    return {
        "schema_version": "kmfa.v015.s15p2.identity_roles_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "IMPLEMENT",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "predecessor": predecessor,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "decision": "GO_TO_S15_P3_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "s15_entry_allowed": True,
        "s15_p1_acceptance_status": "PASSED",
        "s15_p2_entry_allowed": False,
        "s15_p2_started": True,
        "s15_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s15_p3_entry_allowed": final,
        "s15_p3_started": False,
        "s15_stage_review_started": False,
        "product_implementation_allowed": True,
        "product_implementation_performed": True,
        "public_user_count": core["public_user_count"],
        "role_hat_count": core["role_hat_count"],
        "resource_domain_count": core["resource_domain_count"],
        "permission_grant_count": sum(len(value) for value in kernel.ROLE_PERMISSIONS.values()),
        "approval_flow_count": core["approval_flow_count"],
        "default_deny_enabled": core["default_deny_enabled"],
        "same_person_different_role_supported": core["same_person_different_role_supported"],
        "same_role_self_approval_allowed": core["same_role_self_approval_allowed"],
        "browser_viewport_count": 2,
        "browser_flow_count": 6,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "public_check_total": core["public_check_total"],
        "public_check_pass_count": core["public_check_pass_count"],
        "public_check_failed_count": core["public_check_failed_count"],
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
    }


def _human_documents(current_manifest: dict[str, Any]) -> dict[Path, str]:
    final = current_manifest["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "实现已完成，等待正式验收"
    validation_line = (
        f"- 正式验收：{current_manifest['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S15-P2 身份与角色实现记录

- 状态：{status}。
- 页面现在会明确显示“当前是谁、以什么角色、在看哪家公司”，操作前后都保留角色和理由。
- 同一个人可以在经营负责人、财务、税务、审核之间切换，但只能使用已经分配给自己的角色；越权切换会被阻止并记录。
- 数据来源、公司主体、报告、参数和发布分别授权。系统默认拒绝，敏感来源说明只给确有需要的角色查看。
- 高风险处理、参数变更和报告发布由不同角色发起和确认；小团队可以由同一个人切换角色完成，但原角色不能自批，切换与确认理由都必须保留。
- 当前只有公开演示账号和合成内容，没有真实账号、密码、身份接入或真实业务动作。
{validation_line}- 下一步只允许在新的独立 Run 中开始 S15-P3；本轮没有开始应用基础体验或整体复审。
"""
    guide = """# S15-P2 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s15_p2_identity_roles.py`。
2. 页面上方“当前操作身份”会显示示例用户、角色和切换理由。
3. 选择新角色并填写理由后才能切换；未分配角色和未授权公司会直接拒绝。
4. 权限表按数据来源、公司主体、经营报告、模型参数和报告发布五类说明当前角色能做什么。
5. 被拒绝的操作会显示中文原因并写入“最近操作记录”。
6. 报告发布演示必须先由财务或经营角色提出，再由审核角色确认；同一人可以换角色，但同一角色不能自批。

当前页面只演示权限规则，不代表真实账号已经开通，也不会真的发布报告或修改参数。
"""
    tests = f"""# S15-P2 测试结果

- 当前结论：{status}。
- 内核检查覆盖角色分配、越权切换、默认拒绝、敏感信息最小可见、跨公司拒绝和审批分离。
- localhost 检查覆盖身份、授权、操作记录和审批接口，未知操作一律失败关闭。
- 真实浏览器检查覆盖角色切换、权限变化、刷新后复核、跨主体阻断、同人不同角色审批、键盘操作和手机布局。
- 电脑默认、拒绝、审批通过和手机页面共保留 4 张公开演示截图。
{validation_line}- 原始资料读取、真实账号、凭据、外部网络和真实业务动作均为 0。
"""
    risks = """# S15-P2 风险与回退

- 当前是公开演示权限模型，不是生产登录系统；真实身份提供方、账号生命周期、密码或密钥管理仍未接入。
- 页面中的“允许”和“已确认”只验证规则，不会读取真实资料、发布真实报告或修改真实参数。
- 最小权限必须继续保持默认拒绝；后续接入真实身份时，不能把公开演示用户当作生产账号。
- 回退时只移除本阶段新增的 S15-P2 工具、测试、证据和治理登记，不回退已通过的 S15-P1，也不触碰原始资料。
"""
    return {
        IMPLEMENTATION_REPORT_PATH: implementation,
        USER_GUIDE_PATH: guide,
        TEST_RESULTS_PATH: tests,
        RISKS_ROLLBACK_PATH: risks,
    }


def expected_outputs() -> dict[Path, str]:
    current_manifest = manifest()
    outputs = {
        MANIFEST_PATH: _json(current_manifest),
        TASK_MATRIX_PATH: _json(task_matrix(current_manifest["phase_acceptance_status"] == "PASSED")),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        IDENTITY_CONTRACT_PATH: _json(identity_contract()),
        PERMISSION_CONTRACT_PATH: _json(permission_contract()),
        AUDIT_CONTRACT_PATH: _json(audit_contract()),
        APPROVAL_CONTRACT_PATH: _json(approval_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(current_manifest))
    return outputs


def write_outputs() -> None:
    for path, text in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, text in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file()]
    if missing:
        raise BuildError("浏览器截图缺失：" + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S15-P2 身份与角色证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S15-P2 identity roles evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
