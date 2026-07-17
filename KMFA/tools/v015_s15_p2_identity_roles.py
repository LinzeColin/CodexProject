#!/usr/bin/env python3
"""KMFA v1.5 S15-P2 公开演示身份、角色、最小权限与审批分离内核。"""

from __future__ import annotations

from typing import Any, Mapping

from KMFA.tools import v015_s15_p1_app_shell as app_shell


RUN_PHASE_ID = "V015_S15_P2_IDENTITY_ROLES"
ROADMAP_PHASE_ID = "S15-P2"
TASK_ID = "KMFA-V015-S15-P2-IDENTITY-ROLES-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S15-P2-IDENTITY-ROLES"
VERSION = "1.5.0-dev-s15p2"

PUBLIC_USERS: dict[str, dict[str, Any]] = {
    "demo-owner": {
        "label_zh": "示例负责人",
        "role_ids": ("management", "finance", "tax", "reviewer"),
        "company_ids": ("demo-north", "demo-south", "demo-west"),
    },
    "demo-finance": {
        "label_zh": "示例财务专员",
        "role_ids": ("finance", "reviewer"),
        "company_ids": ("demo-north",),
    },
}

ROLE_HATS: dict[str, dict[str, Any]] = {
    "management": {
        "label_zh": "经营负责人",
        "purpose_zh": "查看经营全局、提出处理或发布申请。",
    },
    "finance": {
        "label_zh": "财务",
        "purpose_zh": "核对财务来源、起草报告、提出参数建议。",
    },
    "tax": {
        "label_zh": "税务",
        "purpose_zh": "查看税务范围和相关来源，不处理无关敏感内容。",
    },
    "reviewer": {
        "label_zh": "审核",
        "purpose_zh": "查看审计依据并确认高风险申请。",
    },
}

RESOURCE_CATALOG: dict[str, dict[str, Any]] = {
    "DATA_SOURCE": {
        "label_zh": "数据来源",
        "actions": {
            "VIEW_SUMMARY": "查看来源概况",
            "VIEW_SENSITIVE": "查看敏感来源说明",
            "MANAGE": "管理来源配置",
            "VIEW_AUDIT": "查看来源审计记录",
        },
    },
    "COMPANY": {
        "label_zh": "公司主体",
        "actions": {"VIEW": "查看已授权主体"},
    },
    "REPORT": {
        "label_zh": "经营报告",
        "actions": {"VIEW": "查看报告", "DRAFT": "起草报告"},
    },
    "PARAMETER": {
        "label_zh": "模型参数",
        "actions": {
            "VIEW": "查看参数说明",
            "PROPOSE_CHANGE": "提出参数变更",
            "APPROVE_CHANGE": "确认参数变更",
        },
    },
    "PUBLISH": {
        "label_zh": "报告发布",
        "actions": {
            "REQUEST": "申请发布报告",
            "APPROVE": "确认发布报告",
        },
    },
}

ROLE_PERMISSIONS: dict[str, frozenset[tuple[str, str]]] = {
    "management": frozenset(
        {
            ("DATA_SOURCE", "VIEW_SUMMARY"),
            ("COMPANY", "VIEW"),
            ("REPORT", "VIEW"),
            ("REPORT", "DRAFT"),
            ("PARAMETER", "VIEW"),
            ("PARAMETER", "PROPOSE_CHANGE"),
            ("PUBLISH", "REQUEST"),
        }
    ),
    "finance": frozenset(
        {
            ("DATA_SOURCE", "VIEW_SUMMARY"),
            ("DATA_SOURCE", "VIEW_SENSITIVE"),
            ("DATA_SOURCE", "MANAGE"),
            ("COMPANY", "VIEW"),
            ("REPORT", "VIEW"),
            ("REPORT", "DRAFT"),
            ("PARAMETER", "VIEW"),
            ("PARAMETER", "PROPOSE_CHANGE"),
            ("PUBLISH", "REQUEST"),
        }
    ),
    "tax": frozenset(
        {
            ("DATA_SOURCE", "VIEW_SUMMARY"),
            ("DATA_SOURCE", "VIEW_SENSITIVE"),
            ("COMPANY", "VIEW"),
            ("REPORT", "VIEW"),
            ("PARAMETER", "VIEW"),
        }
    ),
    "reviewer": frozenset(
        {
            ("DATA_SOURCE", "VIEW_SUMMARY"),
            ("DATA_SOURCE", "VIEW_AUDIT"),
            ("COMPANY", "VIEW"),
            ("REPORT", "VIEW"),
            ("PARAMETER", "VIEW"),
            ("PARAMETER", "APPROVE_CHANGE"),
            ("PUBLISH", "APPROVE"),
        }
    ),
}

APPROVAL_FLOWS: dict[str, dict[str, Any]] = {
    "HIGH_RISK_PROCESS": {
        "label_zh": "高风险处理",
        "initiator_roles": ("finance", "tax"),
        "approver_roles": ("management", "reviewer"),
    },
    "PARAMETER_CHANGE": {
        "label_zh": "参数变更",
        "initiator_roles": ("management", "finance"),
        "approver_roles": ("reviewer",),
    },
    "REPORT_PUBLISH": {
        "label_zh": "报告发布",
        "initiator_roles": ("management", "finance"),
        "approver_roles": ("reviewer",),
    },
}

DEFAULT_IDENTITY = {
    "user_id": "demo-owner",
    "role_id": "management",
    "company_id": app_shell.DEFAULT_CONTEXT["company"],
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _actor_validation(user_id: str, role_id: str, company_id: str) -> tuple[bool, str, str]:
    user = PUBLIC_USERS.get(user_id)
    if not user:
        return False, "USER_NOT_FOUND", "这个公开演示用户不存在。"
    if role_id not in ROLE_HATS:
        return False, "ROLE_NOT_FOUND", "这个角色不存在。"
    if role_id not in user["role_ids"]:
        return False, "ROLE_NOT_ASSIGNED", "当前用户没有这个角色，角色切换已被阻止。"
    if company_id not in user["company_ids"]:
        return False, "COMPANY_NOT_GRANTED", "当前用户没有查看这个公司主体的权限。"
    return True, "ACTOR_VALID", "用户、角色和公司主体均在公开演示授权范围内。"


def identity_snapshot(user_id: str, role_id: str, company_id: str) -> dict[str, Any]:
    valid, reason_code, reason_zh = _actor_validation(user_id, role_id, company_id)
    if not valid:
        return {
            "schema_version": "kmfa.v015.s15p2.identity_snapshot.v1",
            "allowed": False,
            "reason_code": reason_code,
            "reason_zh": reason_zh,
        }
    user = PUBLIC_USERS[user_id]
    permissions = ROLE_PERMISSIONS[role_id]
    return {
        "schema_version": "kmfa.v015.s15p2.identity_snapshot.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "user_id": user_id,
        "user_label_zh": user["label_zh"],
        "role_id": role_id,
        "role_label_zh": ROLE_HATS[role_id]["label_zh"],
        "role_purpose_zh": ROLE_HATS[role_id]["purpose_zh"],
        "company_id": company_id,
        "assigned_roles": [
            {"role_id": value, **ROLE_HATS[value]} for value in user["role_ids"]
        ],
        "company_ids": list(user["company_ids"]),
        "permission_summary": [
            {
                "resource": resource,
                "resource_label_zh": spec["label_zh"],
                "allowed_actions": [
                    {"action": action, "label_zh": label}
                    for action, label in spec["actions"].items()
                    if (resource, action) in permissions
                ],
            }
            for resource, spec in RESOURCE_CATALOG.items()
        ],
    }


def authorization_decision(
    *,
    event_id: str,
    occurred_at: str,
    user_id: str,
    role_id: str,
    company_id: str,
    resource: str,
    action: str,
    reason: str,
) -> dict[str, Any]:
    actor_valid, reason_code, reason_zh = _actor_validation(user_id, role_id, company_id)
    allowed = False
    if actor_valid and resource not in RESOURCE_CATALOG:
        reason_code, reason_zh = "RESOURCE_NOT_FOUND", "这个受控范围不存在，系统默认拒绝。"
    elif actor_valid and action not in RESOURCE_CATALOG[resource]["actions"]:
        reason_code, reason_zh = "ACTION_NOT_FOUND", "这个操作不存在，系统默认拒绝。"
    elif actor_valid and (resource, action) not in ROLE_PERMISSIONS[role_id]:
        reason_code, reason_zh = "PERMISSION_NOT_GRANTED", "当前角色没有这项权限，操作已被阻止并记录。"
    elif actor_valid:
        allowed = True
        reason_code, reason_zh = "PERMISSION_GRANTED", "当前角色拥有这项权限。"
    role_label = ROLE_HATS.get(role_id, {}).get("label_zh", "未知角色")
    return {
        "schema_version": "kmfa.v015.s15p2.authorization_event.v1",
        "event_id": event_id,
        "event_type": "AUTHORIZATION_DECISION",
        "data_classification": "PUBLIC_SYNTHETIC",
        "occurred_at": occurred_at,
        "actor_user_id": user_id,
        "actor_role": role_id,
        "actor_role_label_zh": role_label,
        "company_id": company_id,
        "resource": resource,
        "action": action,
        "request_reason": _text(reason) or "公开演示操作",
        "allowed": allowed,
        "decision_zh": "允许" if allowed else "已阻止",
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "operation_performed": False,
    }


def role_switch_decision(
    *,
    event_id: str,
    occurred_at: str,
    user_id: str,
    from_role: str,
    to_role: str,
    company_id: str,
    reason: str,
) -> dict[str, Any]:
    user = PUBLIC_USERS.get(user_id)
    allowed = True
    reason_code = "ROLE_SWITCH_ALLOWED"
    reason_zh = "角色帽子已切换，后续操作会记录当前角色。"
    if not user:
        allowed, reason_code, reason_zh = False, "USER_NOT_FOUND", "这个公开演示用户不存在。"
    elif from_role not in user["role_ids"]:
        allowed, reason_code, reason_zh = False, "CURRENT_ROLE_NOT_ASSIGNED", "当前角色不属于这个用户。"
    elif to_role not in user["role_ids"]:
        allowed, reason_code, reason_zh = False, "ROLE_NOT_ASSIGNED", "当前用户没有目标角色，切换已被阻止。"
    elif company_id not in user["company_ids"]:
        allowed, reason_code, reason_zh = False, "COMPANY_NOT_GRANTED", "当前用户没有这个公司主体的权限。"
    elif to_role == from_role:
        allowed, reason_code, reason_zh = False, "ROLE_UNCHANGED", "目标角色与当前角色相同，无需切换。"
    elif len(_text(reason)) < 4:
        allowed, reason_code, reason_zh = False, "REASON_REQUIRED", "切换角色前请说明本次工作的理由。"
    return {
        "schema_version": "kmfa.v015.s15p2.role_switch_event.v1",
        "event_id": event_id,
        "event_type": "ROLE_SWITCH",
        "data_classification": "PUBLIC_SYNTHETIC",
        "occurred_at": occurred_at,
        "actor_user_id": user_id,
        "actor_role": from_role,
        "actor_role_label_zh": ROLE_HATS.get(from_role, {}).get("label_zh", "未知角色"),
        "target_role": to_role,
        "target_role_label_zh": ROLE_HATS.get(to_role, {}).get("label_zh", "未知角色"),
        "company_id": company_id,
        "request_reason": _text(reason),
        "allowed": allowed,
        "decision_zh": "已切换" if allowed else "已阻止",
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "operation_performed": allowed,
    }


def approval_request_decision(
    *,
    event_id: str,
    request_id: str,
    occurred_at: str,
    action_type: str,
    user_id: str,
    role_id: str,
    company_id: str,
    reason: str,
) -> dict[str, Any]:
    actor_valid, reason_code, reason_zh = _actor_validation(user_id, role_id, company_id)
    flow = APPROVAL_FLOWS.get(action_type)
    allowed = actor_valid
    if actor_valid and not flow:
        allowed, reason_code, reason_zh = False, "FLOW_NOT_FOUND", "这个审批事项不存在，系统默认拒绝。"
    elif actor_valid and role_id not in flow["initiator_roles"]:
        allowed, reason_code, reason_zh = False, "INITIATOR_ROLE_NOT_ALLOWED", "当前角色不能发起这项高风险申请。"
    elif actor_valid and len(_text(reason)) < 4:
        allowed, reason_code, reason_zh = False, "REASON_REQUIRED", "发起高风险申请前请说明理由。"
    elif actor_valid:
        reason_code, reason_zh = "APPROVAL_REQUEST_CREATED", "申请已记录，等待不同的确认角色处理。"
    event = {
        "schema_version": "kmfa.v015.s15p2.approval_event.v1",
        "event_id": event_id,
        "event_type": "APPROVAL_REQUEST",
        "data_classification": "PUBLIC_SYNTHETIC",
        "occurred_at": occurred_at,
        "actor_user_id": user_id,
        "actor_role": role_id,
        "actor_role_label_zh": ROLE_HATS.get(role_id, {}).get("label_zh", "未知角色"),
        "company_id": company_id,
        "action_type": action_type,
        "request_reason": _text(reason),
        "allowed": allowed,
        "decision_zh": "已提交" if allowed else "已阻止",
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "operation_performed": False,
    }
    request = None
    if allowed:
        request = {
            "schema_version": "kmfa.v015.s15p2.approval_request.v1",
            "request_id": request_id,
            "action_type": action_type,
            "action_label_zh": flow["label_zh"],
            "company_id": company_id,
            "state": "PENDING",
            "state_zh": "等待确认",
            "initiator_user_id": user_id,
            "initiator_role": role_id,
            "initiator_role_label_zh": ROLE_HATS[role_id]["label_zh"],
            "initiator_reason": _text(reason),
            "created_at": occurred_at,
            "approver_roles": list(flow["approver_roles"]),
            "approval": None,
            "real_business_action_performed": False,
        }
    return {"allowed": allowed, "event": event, "request": request}


def approval_confirmation_decision(
    *,
    event_id: str,
    occurred_at: str,
    request: Mapping[str, Any],
    user_id: str,
    role_id: str,
    company_id: str,
    reason: str,
) -> dict[str, Any]:
    actor_valid, reason_code, reason_zh = _actor_validation(user_id, role_id, company_id)
    action_type = _text(request.get("action_type"))
    flow = APPROVAL_FLOWS.get(action_type)
    allowed = actor_valid
    if actor_valid and request.get("state") != "PENDING":
        allowed, reason_code, reason_zh = False, "REQUEST_NOT_PENDING", "这项申请已经处理，不能重复确认。"
    elif actor_valid and request.get("company_id") != company_id:
        allowed, reason_code, reason_zh = False, "COMPANY_MISMATCH", "申请与当前公司主体不一致。"
    elif actor_valid and not flow:
        allowed, reason_code, reason_zh = False, "FLOW_NOT_FOUND", "这个审批事项不存在。"
    elif actor_valid and role_id == request.get("initiator_role"):
        allowed, reason_code, reason_zh = False, "SAME_ROLE_SEPARATION_REQUIRED", "发起角色不能同时确认；请切换到另一项已分配角色。"
    elif actor_valid and role_id not in flow["approver_roles"]:
        allowed, reason_code, reason_zh = False, "APPROVER_ROLE_NOT_ALLOWED", "当前角色不能确认这项申请。"
    elif actor_valid and len(_text(reason)) < 4:
        allowed, reason_code, reason_zh = False, "REASON_REQUIRED", "确认高风险申请前请说明理由。"
    elif actor_valid:
        reason_code, reason_zh = "APPROVAL_CONFIRMED", "确认角色和理由已记录；公开演示不会执行真实业务动作。"
    event = {
        "schema_version": "kmfa.v015.s15p2.approval_event.v1",
        "event_id": event_id,
        "event_type": "APPROVAL_CONFIRMATION",
        "data_classification": "PUBLIC_SYNTHETIC",
        "occurred_at": occurred_at,
        "actor_user_id": user_id,
        "actor_role": role_id,
        "actor_role_label_zh": ROLE_HATS.get(role_id, {}).get("label_zh", "未知角色"),
        "company_id": company_id,
        "action_type": action_type,
        "request_id": request.get("request_id"),
        "request_reason": _text(reason),
        "allowed": allowed,
        "decision_zh": "已确认" if allowed else "已阻止",
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "operation_performed": False,
    }
    updated = dict(request)
    if allowed:
        updated.update(
            {
                "state": "APPROVED_DEMO_ONLY",
                "state_zh": "已确认（仅演示）",
                "approval": {
                    "approver_user_id": user_id,
                    "approver_role": role_id,
                    "approver_role_label_zh": ROLE_HATS[role_id]["label_zh"],
                    "approval_reason": _text(reason),
                    "approved_at": occurred_at,
                    "same_person_different_role": user_id == request.get("initiator_user_id"),
                },
                "real_business_action_performed": False,
            }
        )
    return {"allowed": allowed, "event": event, "request": updated}


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p2.source_contract.v1",
        "stage_id": "S15",
        "stage_name_zh": "应用外壳、角色权限与多主体上下文",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "身份与角色",
        "task_ids": ["S15P2T01", "S15P2T02", "S15P2T03"],
        "task_names_zh": ["建立用户与角色帽子", "建立最小权限", "建立审批分离"],
        "acceptance_zh": [
            "每项操作记录当时用户、角色、公司主体和理由。",
            "数据来源、主体、报告、参数和发布分别授权；默认拒绝并记录未授权访问。",
            "高风险事项由不同角色发起和确认；同一人多角色时保留角色与理由。",
        ],
        "stop_conditions_zh": [
            "角色切换不得越权。",
            "未授权访问必须阻止并记录。",
            "不得虚构多人；同一角色不得同时发起和确认。",
        ],
    }


def acceptance_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("two_public_users", len(PUBLIC_USERS) == 2, str(len(PUBLIC_USERS)))
    add("four_role_hats", len(ROLE_HATS) == 4, str(len(ROLE_HATS)))
    add("five_separate_resources", set(RESOURCE_CATALOG) == {"DATA_SOURCE", "COMPANY", "REPORT", "PARAMETER", "PUBLISH"}, ",".join(RESOURCE_CATALOG))
    add("default_deny_unknown", not authorization_decision(event_id="E1", occurred_at="T", user_id="demo-owner", role_id="management", company_id="demo-north", resource="UNKNOWN", action="VIEW", reason="test")["allowed"], "unknown resource denied")
    add("unassigned_role_denied", not role_switch_decision(event_id="E2", occurred_at="T", user_id="demo-finance", from_role="finance", to_role="tax", company_id="demo-north", reason="核对税务事项")["allowed"], "demo-finance cannot become tax")
    add("cross_company_denied", not authorization_decision(event_id="E3", occurred_at="T", user_id="demo-finance", role_id="finance", company_id="demo-south", resource="REPORT", action="VIEW", reason="test")["allowed"], "demo-finance limited to north")
    add("sensitive_detail_minimized", ("DATA_SOURCE", "VIEW_SENSITIVE") not in ROLE_PERMISSIONS["management"] and ("DATA_SOURCE", "VIEW_SENSITIVE") in ROLE_PERMISSIONS["finance"], "management denied finance allowed")
    add("three_approval_flows", len(APPROVAL_FLOWS) == 3, str(len(APPROVAL_FLOWS)))
    created = approval_request_decision(event_id="E4", request_id="R1", occurred_at="T", action_type="REPORT_PUBLISH", user_id="demo-owner", role_id="finance", company_id="demo-north", reason="发布公开演示报告")
    same_role = approval_confirmation_decision(event_id="E5", occurred_at="T", request=created["request"] or {}, user_id="demo-owner", role_id="finance", company_id="demo-north", reason="确认公开演示报告")
    different_role = approval_confirmation_decision(event_id="E6", occurred_at="T", request=created["request"] or {}, user_id="demo-owner", role_id="reviewer", company_id="demo-north", reason="审核公开演示报告")
    add("same_role_approval_denied", created["allowed"] and not same_role["allowed"], same_role["event"]["reason_code"])
    add("same_person_different_role_allowed", different_role["allowed"] and different_role["request"]["approval"]["same_person_different_role"], "role separation without invented people")
    add("real_action_remains_zero", different_role["request"]["real_business_action_performed"] is False, "demo authorization only")
    add("all_events_bind_role_and_reason", all(row["event"].get("actor_role") and row["event"].get("request_reason") for row in (created, same_role, different_role)), "role and reason present")
    return checks


def build_contract() -> dict[str, Any]:
    checks = acceptance_checks()
    failed = [item for item in checks if item["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s15p2.identity_roles_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "version": VERSION,
        "public_user_count": len(PUBLIC_USERS),
        "role_hat_count": len(ROLE_HATS),
        "resource_domain_count": len(RESOURCE_CATALOG),
        "approval_flow_count": len(APPROVAL_FLOWS),
        "default_deny_enabled": True,
        "same_person_different_role_supported": True,
        "same_role_self_approval_allowed": False,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "public_check_total": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
    }
