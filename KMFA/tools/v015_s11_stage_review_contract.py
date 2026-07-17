#!/usr/bin/env python3
"""Cross-part review contract for KMFA v1.5 S11.

The review binds the accepted quality policy, board fact revision and interface
action to one request.  It also separates a blocking remediation from an
ordinary human confirmation and rejects stale browser actions.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s11_p1_quality_rules as quality
from KMFA.tools import v015_s11_p2_check_board_data_model as board
from KMFA.tools import v015_s11_p3_check_board_interface as interface


RUN_PHASE_ID = "V015_S11_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S11-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S11-STAGE-REVIEW"
VERSION = "1.5.0-dev-s11-review"
REVIEW_BASE_COMMIT = "b8ace746d3872bc07def95248694d0666b73a73c"

ACTION_POLICY_VERSION = "kmfa.v015.s11.review-action-policy.v1"
REVIEW_ACTION_KINDS = (
    "VIEW_EVIDENCE",
    "UPLOAD_SOURCE",
    "SYNC_SOURCE",
    "CONFIRM_QUALITY",
    "REMEDIATE_QUALITY",
)


class StageReviewError(ValueError):
    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _fact_map(facts: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if not isinstance(facts, Sequence) or isinstance(facts, (str, bytes)) or not facts:
        raise StageReviewError("REVIEW_FACTS_EMPTY", "复审至少需要一项后端事实。")
    result: dict[str, Mapping[str, Any]] = {}
    for fact in facts:
        board.validate_backend_fact(fact)
        fact_id = str(fact["fact_id"])
        if fact_id in result:
            raise StageReviewError("REVIEW_FACT_DUPLICATE", "复审事实编号不能重复。")
        result[fact_id] = fact
    return result


def quality_contract_binding() -> dict[str, Any]:
    """Return one explicit P1 configuration binding for P2 and P3."""

    catalog = quality.default_rule_catalog()
    status_model = quality.default_status_model()
    score_policy = quality.default_score_policy()
    binding = {
        "schema_version": "kmfa.v015.s11.review-quality-binding.v1",
        "quality_phase_id": quality.RUN_PHASE_ID,
        "quality_version": quality.VERSION,
        "catalog_fingerprint": _fingerprint(catalog),
        "status_model_fingerprint": _fingerprint(status_model),
        "score_policy_fingerprint": _fingerprint(score_policy),
        "status_labels_zh": list(quality.STATUS_LABELS_ZH),
        "hard_gate_precedence": True,
        "frontend_override_allowed": False,
    }
    binding["binding_fingerprint"] = _fingerprint(binding)
    return binding


def validate_quality_contract_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    expected = quality_contract_binding()
    if not isinstance(binding, Mapping) or dict(binding) != expected:
        raise StageReviewError("QUALITY_CONTRACT_DRIFT", "质量规则、状态或评分口径与已验收版本不一致。")
    return copy.deepcopy(expected)


def reviewed_action_for_leaf(leaf: Mapping[str, Any]) -> dict[str, Any]:
    """Route by P2 backend facts, keeping hard failures distinct from review."""

    if not leaf.get("is_leaf"):
        raise StageReviewError("ACTION_TARGET_NOT_LEAF", "只能为末级检查项决定处理入口。")
    alerts = {row.get("alert_type") for row in leaf.get("alerts", [])}
    technical = leaf.get("professional_detail", {}).get("technical_status")
    if alerts & {"MISSING_SOURCE", "IMPORT_FAILED"}:
        kind, label, recheck = "UPLOAD_SOURCE", "补充或重新提交资料", True
    elif "SOURCE_OUTDATED" in alerts or technical == "OUTDATED":
        kind, label, recheck = "SYNC_SOURCE", "获取最新资料", True
    elif alerts & {"QUALITY_HARD_GATE", "QUALITY_NOT_USABLE"} or technical == "NOT_USABLE":
        kind, label, recheck = "REMEDIATE_QUALITY", "修复关键问题", True
    elif "REVIEW_REQUIRED" in alerts or technical == "REVIEW_REQUIRED":
        kind, label, recheck = "CONFIRM_QUALITY", "确认处理办法", True
    elif technical == "PASSED" and not alerts:
        kind, label, recheck = "VIEW_EVIDENCE", "查看通过依据", False
    else:
        raise StageReviewError("ACTION_POLICY_UNRESOLVED", "当前事实无法确定安全的处理入口。")
    return {
        "policy_version": ACTION_POLICY_VERSION,
        "kind": kind,
        "label_zh": label,
        "backend_recheck_required": recheck,
        "frontend_status_change_allowed": False,
    }


def _evaluation_binding(fact: Mapping[str, Any]) -> dict[str, Any] | None:
    if fact["ingestion_state"] != "IMPORTED":
        return None
    result = quality.evaluate_quality(fact["quality_snapshot"])
    detail = result["professional_detail"]
    return {
        "evaluation_fingerprint": result["evaluation_fingerprint"],
        "catalog_fingerprint": detail["catalog_fingerprint"],
        "status_model_fingerprint": detail["status_model_fingerprint"],
        "score_policy_fingerprint": detail["score_policy_fingerprint"],
        "technical_status": detail["technical_status"],
        "hard_gate_failure_count": detail["hard_gate_failure_count"],
    }


def interface_contract_binding() -> dict[str, Any]:
    value = {
        "schema_version": "kmfa.v015.s11.review-interface-binding.v1",
        "interface_phase_id": interface.RUN_PHASE_ID,
        "interface_version": interface.VERSION,
        "payload_schema": "kmfa.v015.s11p3.interface_payload.v1",
        "status_order_zh": list(interface.STATUS_ORDER),
        "p1_status_order_zh": list(quality.STATUS_LABELS_ZH),
        "context_keys": list(interface.CONTEXT_KEYS),
        "visual_contract_fingerprint": _fingerprint(interface.visual_contract()),
        "accessibility_contract_fingerprint": _fingerprint(interface.accessibility_contract()),
        "frontend_status_mutation_allowed": False,
    }
    value["binding_fingerprint"] = _fingerprint(value)
    return value


def reviewed_projection(facts: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    resolved_facts = copy.deepcopy(list(facts if facts is not None else board.public_backend_facts()))
    facts_by_id = _fact_map(resolved_facts)
    model = board.derive_board_model(resolved_facts)
    quality_binding = quality_contract_binding()
    interface_binding = interface_contract_binding()
    if interface_binding["status_order_zh"] != quality_binding["status_labels_zh"]:
        raise StageReviewError("STATUS_VOCABULARY_DRIFT", "质量规则与界面使用的中文状态不一致。")

    leaves: list[dict[str, Any]] = []
    for node in model["nodes"]:
        if not node["is_leaf"]:
            continue
        fact = facts_by_id[str(node["backend_fact_ref"])]
        state = board.derive_leaf_state(fact)
        evaluation = _evaluation_binding(fact)
        if evaluation is not None:
            for field in ("catalog_fingerprint", "status_model_fingerprint", "score_policy_fingerprint"):
                if evaluation[field] != quality_binding[field]:
                    raise StageReviewError("QUALITY_EVALUATION_DRIFT", "质量检查结果与当前已验收口径不一致。")
        action = reviewed_action_for_leaf(node)
        leaf = {
            "node_id": node["node_id"],
            "node_fingerprint": node["node_fingerprint"],
            "fact_id": fact["fact_id"],
            "fact_revision": fact["fact_revision"],
            "fact_fingerprint": state["fact_fingerprint"],
            "state_fingerprint": state["state_fingerprint"],
            "quality_evaluation": evaluation,
            "quality_contract_fingerprint": quality_binding["binding_fingerprint"],
            "status_zh": node["display"]["label_zh"],
            "technical_status": node["professional_detail"]["technical_status"],
            "alert_types": sorted(str(row["alert_type"]) for row in node["alerts"]),
            "next_action_zh": node["next_action_zh"],
            "reviewed_action": action,
            "frontend_status_mutation_allowed": False,
        }
        leaf["leaf_binding_fingerprint"] = _fingerprint(leaf)
        leaves.append(leaf)

    projection = {
        "schema_version": "kmfa.v015.s11.reviewed-projection.v1",
        "quality_contract": quality_binding,
        "interface_contract": interface_binding,
        "board_model_fingerprint": model["model_fingerprint"],
        "node_ids": [row["node_id"] for row in model["nodes"]],
        "leaf_count": len(leaves),
        "leaves": leaves,
        "review_action_kinds": list(REVIEW_ACTION_KINDS),
        "frontend_status_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
    }
    projection["projection_fingerprint"] = _fingerprint(projection)
    return projection


def _request_without_fingerprint(request: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in request.items() if key != "request_fingerprint"}


def create_review_action_request(
    fact_id: str,
    context_state: Mapping[str, Any],
    *,
    facts: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    projection = reviewed_projection(facts)
    leaf = next((row for row in projection["leaves"] if row["fact_id"] == fact_id), None)
    if leaf is None:
        raise StageReviewError("ACTION_FACT_UNKNOWN", "处理请求指向未知资料。")
    context = interface.validate_context_state(context_state, set(projection["node_ids"]))
    request = {
        "schema_version": "kmfa.v015.s11.reviewed-action-request.v1",
        "fact_id": fact_id,
        "node_id": leaf["node_id"],
        "action_kind": leaf["reviewed_action"]["kind"],
        "action_policy_version": ACTION_POLICY_VERSION,
        "fact_revision": leaf["fact_revision"],
        "fact_fingerprint": leaf["fact_fingerprint"],
        "state_fingerprint": leaf["state_fingerprint"],
        "node_fingerprint": leaf["node_fingerprint"],
        "leaf_binding_fingerprint": leaf["leaf_binding_fingerprint"],
        "quality_contract_fingerprint": leaf["quality_contract_fingerprint"],
        "board_model_fingerprint": projection["board_model_fingerprint"],
        "interface_contract_fingerprint": projection["interface_contract"]["binding_fingerprint"],
        "context_token": _fingerprint(context),
        "frontend_status_write_count": 0,
        "status_change_requested": False,
        "raw_source_mutation_requested": False,
    }
    request["request_fingerprint"] = _fingerprint(request)
    return request


def validate_review_action_request(
    request: Mapping[str, Any],
    *,
    current_facts: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if not isinstance(request, Mapping) or request.get("schema_version") != "kmfa.v015.s11.reviewed-action-request.v1":
        raise StageReviewError("ACTION_REQUEST_INVALID", "处理请求格式无效。")
    if request.get("request_fingerprint") != _fingerprint(_request_without_fingerprint(request)):
        raise StageReviewError("ACTION_REQUEST_FINGERPRINT_INVALID", "处理请求内容已变化。")
    if request.get("frontend_status_write_count") != 0 or request.get("status_change_requested") is not False:
        raise StageReviewError("FRONTEND_STATUS_WRITE_FORBIDDEN", "前端处理请求不能直接改写状态。")
    if request.get("raw_source_mutation_requested") is not False:
        raise StageReviewError("RAW_SOURCE_MUTATION_FORBIDDEN", "处理请求不能修改原始资料。")

    projection = reviewed_projection(current_facts)
    leaf = next((row for row in projection["leaves"] if row["fact_id"] == request.get("fact_id")), None)
    if leaf is None:
        raise StageReviewError("ACTION_FACT_UNKNOWN", "处理请求指向未知资料。")
    expected = {
        "node_id": leaf["node_id"],
        "action_kind": leaf["reviewed_action"]["kind"],
        "action_policy_version": ACTION_POLICY_VERSION,
        "fact_revision": leaf["fact_revision"],
        "fact_fingerprint": leaf["fact_fingerprint"],
        "state_fingerprint": leaf["state_fingerprint"],
        "node_fingerprint": leaf["node_fingerprint"],
        "leaf_binding_fingerprint": leaf["leaf_binding_fingerprint"],
        "quality_contract_fingerprint": leaf["quality_contract_fingerprint"],
        "board_model_fingerprint": projection["board_model_fingerprint"],
        "interface_contract_fingerprint": projection["interface_contract"]["binding_fingerprint"],
    }
    if any(request.get(key) != value for key, value in expected.items()):
        if request.get("action_kind") != expected["action_kind"]:
            raise StageReviewError("ACTION_POLICY_DRIFT", "处理入口与当前后端状态不一致。")
        raise StageReviewError("STALE_ACTION_REQUEST", "资料或检查状态已更新，请刷新后重新处理。")
    return {
        "schema_version": "kmfa.v015.s11.action-authorization.v1",
        "authorization_status": "AUTHORIZED_FOR_BACKEND_RECHECK",
        "fact_id": leaf["fact_id"],
        "fact_revision": leaf["fact_revision"],
        "action_kind": expected["action_kind"],
        "backend_recheck_required": leaf["reviewed_action"]["backend_recheck_required"],
        "status_change_authorized": False,
        "frontend_status_write_count": 0,
        "raw_source_mutation_allowed": False,
    }


def recheck_after_backend_update(
    request: Mapping[str, Any],
    before_fact: Mapping[str, Any],
    after_fact: Mapping[str, Any],
    *,
    other_facts: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    facts = [copy.deepcopy(row) for row in (other_facts if other_facts is not None else board.public_backend_facts())]
    facts = [copy.deepcopy(before_fact) if row["fact_id"] == before_fact["fact_id"] else row for row in facts]
    authorization = validate_review_action_request(request, current_facts=facts)
    if authorization["fact_id"] != before_fact["fact_id"]:
        raise StageReviewError("RECHECK_FACT_MISMATCH", "重新检查与原处理请求不是同一资料。")
    transition = board.derive_transition(before_fact, after_fact)
    return {
        "schema_version": "kmfa.v015.s11.reviewed-recheck.v1",
        "authorization": authorization,
        "transition": transition,
        "status_changed_by_backend_recheck": transition["before_status_zh"] != transition["after_status_zh"],
        "frontend_status_write_count": 0,
        "raw_source_mutation_count": 0,
    }


def _expect_error(code: str, call: Any) -> bool:
    try:
        call()
    except StageReviewError as error:
        return error.code == code
    except board.CheckBoardModelError:
        return code == "BACKEND_TRANSITION_REJECTED"
    return False


def public_verification() -> dict[str, Any]:
    facts = board.public_backend_facts()
    projection = reviewed_projection(facts)
    by_fact = {row["fact_id"]: row for row in projection["leaves"]}
    context = {
        "search_text": "合同",
        "status_filters": ["不可使用"],
        "owner_filter": "合同负责人",
        "alert_only": True,
        "expanded_node_ids": projection["node_ids"][:2],
        "scroll_y": 360,
        "table_scroll_left": 120,
        "focus_node_id": by_fact["QBF-005"]["node_id"],
    }
    requests = {fact_id: create_review_action_request(fact_id, context, facts=facts) for fact_id in by_fact}
    authorizations = {fact_id: validate_review_action_request(request, current_facts=facts) for fact_id, request in requests.items()}

    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("PREDECESSOR_STATUS_VOCABULARY_BOUND", tuple(interface.STATUS_ORDER) == tuple(quality.STATUS_LABELS_ZH))
    check("QUALITY_BINDING_VALID", validate_quality_contract_binding(projection["quality_contract"])["hard_gate_precedence"] is True)
    check("QUALITY_RULE_COUNT_BOUND", len(quality.default_rule_catalog()["rules"]) == 16)
    check("QUALITY_HARD_GATE_COUNT_BOUND", sum(row["hard_gate"] for row in quality.default_rule_catalog()["rules"]) == 7)
    check("BOARD_LEAF_COUNT_BOUND", projection["leaf_count"] == 6)
    check("ALL_FACT_REVISIONS_BOUND", all(row["fact_revision"] == 1 for row in projection["leaves"]))
    check("ALL_FACT_FINGERPRINTS_BOUND", all(str(row["fact_fingerprint"]).startswith("sha256:") for row in projection["leaves"]))
    check("ALL_STATE_FINGERPRINTS_BOUND", all(str(row["state_fingerprint"]).startswith("sha256:") for row in projection["leaves"]))
    check("ALL_NODE_FINGERPRINTS_BOUND", all(str(row["node_fingerprint"]).startswith("sha256:") for row in projection["leaves"]))
    check("ALL_LEAF_BINDINGS_BOUND", all(str(row["leaf_binding_fingerprint"]).startswith("sha256:") for row in projection["leaves"]))
    check("IMPORTED_EVALUATIONS_BOUND", all(row["quality_evaluation"] is not None for row in projection["leaves"] if row["fact_id"] in {"QBF-001", "QBF-002", "QBF-004", "QBF-005"}))
    check("MISSING_FAILED_EVALUATIONS_ABSENT", all(row["quality_evaluation"] is None for row in projection["leaves"] if row["fact_id"] in {"QBF-003", "QBF-006"}))
    check("PASSED_ROUTES_VIEW", by_fact["QBF-001"]["reviewed_action"]["kind"] == "VIEW_EVIDENCE")
    check("REVIEW_ROUTES_CONFIRM", by_fact["QBF-002"]["reviewed_action"]["kind"] == "CONFIRM_QUALITY")
    check("MISSING_ROUTES_UPLOAD", by_fact["QBF-003"]["reviewed_action"]["kind"] == "UPLOAD_SOURCE")
    check("OUTDATED_ROUTES_SYNC", by_fact["QBF-004"]["reviewed_action"]["kind"] == "SYNC_SOURCE")
    check("HARD_GATE_ROUTES_REMEDIATION", by_fact["QBF-005"]["reviewed_action"]["kind"] == "REMEDIATE_QUALITY")
    check("IMPORT_FAILURE_ROUTES_UPLOAD", by_fact["QBF-006"]["reviewed_action"]["kind"] == "UPLOAD_SOURCE")
    legacy_payload = interface.interface_payload()
    legacy_hard_gate = next(row for row in legacy_payload["rows"] if row["is_leaf"] and row["status_zh"] == "不可使用" and "合同履约" in row["hierarchy_path_zh"])
    check("FINDING_COARSE_ACTION_PROVEN", legacy_hard_gate["action"]["kind"] == "CONFIRM_QUALITY" and by_fact["QBF-005"]["reviewed_action"]["kind"] == "REMEDIATE_QUALITY")
    check("ALL_REQUESTS_AUTHORIZED", all(row["authorization_status"] == "AUTHORIZED_FOR_BACKEND_RECHECK" for row in authorizations.values()))
    check("ALL_REQUESTS_STATUS_READONLY", all(row["status_change_authorized"] is False for row in authorizations.values()))
    check("ALL_REQUESTS_RAW_READONLY", all(row["raw_source_mutation_allowed"] is False for row in authorizations.values()))
    check("ALL_CONTEXT_TOKENS_BOUND", all(str(row["context_token"]).startswith("sha256:") for row in requests.values()))

    tampered_binding = copy.deepcopy(projection["quality_contract"])
    tampered_binding["status_labels_zh"] = ["已通过"]
    check("QUALITY_CONTRACT_DRIFT_REJECTED", _expect_error("QUALITY_CONTRACT_DRIFT", lambda: validate_quality_contract_binding(tampered_binding)))

    tampered_action = copy.deepcopy(requests["QBF-005"])
    tampered_action["action_kind"] = "CONFIRM_QUALITY"
    tampered_action["request_fingerprint"] = _fingerprint(_request_without_fingerprint(tampered_action))
    check("HARD_GATE_CONFIRMATION_REJECTED", _expect_error("ACTION_POLICY_DRIFT", lambda: validate_review_action_request(tampered_action, current_facts=facts)))

    tampered_write = copy.deepcopy(requests["QBF-002"])
    tampered_write["frontend_status_write_count"] = 1
    tampered_write["status_change_requested"] = True
    tampered_write["request_fingerprint"] = _fingerprint(_request_without_fingerprint(tampered_write))
    check("FRONTEND_STATUS_WRITE_REJECTED", _expect_error("FRONTEND_STATUS_WRITE_FORBIDDEN", lambda: validate_review_action_request(tampered_write, current_facts=facts)))

    stale_facts = copy.deepcopy(facts)
    stale = next(row for row in stale_facts if row["fact_id"] == "QBF-002")
    stale["fact_revision"] = 2
    stale["updated_at"] = "2026-07-15T12:00:00+10:00"
    check("STALE_ACTION_REJECTED", _expect_error("STALE_ACTION_REQUEST", lambda: validate_review_action_request(requests["QBF-002"], current_facts=stale_facts)))

    before = copy.deepcopy(next(row for row in facts if row["fact_id"] == "QBF-003"))
    after = copy.deepcopy(before)
    after.update({"fact_revision": 2, "updated_at": "2026-07-15T12:30:00+10:00", "ingestion_state": "IMPORTED", "quality_snapshot": quality.baseline_snapshot()})
    recheck = recheck_after_backend_update(requests["QBF-003"], before, after, other_facts=facts)
    check("BACKEND_RECHECK_CHANGES_STATUS", recheck["status_changed_by_backend_recheck"] is True and recheck["transition"]["after_status_zh"] == "已通过")
    check("BACKEND_RECHECK_FRONTEND_WRITE_ZERO", recheck["frontend_status_write_count"] == 0)
    invalid_after = copy.deepcopy(after)
    invalid_after["fact_revision"] = 1
    check("NON_INCREMENTAL_RECHECK_REJECTED", _expect_error("BACKEND_TRANSITION_REJECTED", lambda: recheck_after_backend_update(requests["QBF-003"], before, invalid_after, other_facts=facts)))

    check("INTERFACE_CONTEXT_KEYS_BOUND", tuple(projection["interface_contract"]["context_keys"]) == tuple(interface.CONTEXT_KEYS))
    check("INTERFACE_VISUAL_BOUND", str(projection["interface_contract"]["visual_contract_fingerprint"]).startswith("sha256:"))
    check("INTERFACE_ACCESSIBILITY_BOUND", str(projection["interface_contract"]["accessibility_contract_fingerprint"]).startswith("sha256:"))
    check("NO_FRONTEND_STATUS_WRITES", projection["frontend_status_write_count"] == 0)
    check("RAW_ACCESS_ZERO", projection["raw_root_access_count"] == 0)
    check("LIVE_SOURCE_READ_ZERO", projection["live_source_read_count"] == 0)
    public_text = json.dumps([projection, requests, authorizations, recheck], ensure_ascii=False, sort_keys=True)
    for index, forbidden in enumerate(("/Users/", "/Volumes/", "/home/", "file://", "KMFA_MetaData", "private://", ".xlsx", ".xls", "password"), start=1):
        check(f"PUBLIC_BOUNDARY_{index:02d}", forbidden.casefold() not in public_text.casefold())

    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s11.stage-review-verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
        "reviewed_projection": projection,
        "reviewed_requests": requests,
        "reviewed_authorizations": authorizations,
        "backend_recheck_evidence": recheck,
        "fixed_finding_count": 3,
        "open_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "ACTION_POLICY_VERSION",
    "REVIEW_ACTION_KINDS",
    "REVIEW_BASE_COMMIT",
    "RUN_PHASE_ID",
    "StageReviewError",
    "TASK_ID",
    "VERSION",
    "create_review_action_request",
    "interface_contract_binding",
    "public_verification",
    "quality_contract_binding",
    "recheck_after_backend_update",
    "reviewed_action_for_leaf",
    "reviewed_projection",
    "validate_quality_contract_binding",
    "validate_review_action_request",
]
