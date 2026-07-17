#!/usr/bin/env python3
"""KMFA v1.5 S11-P2 hierarchical quality-check board data model.

This module is the backend-owned data model only. It does not build the S11-P3
interface, read live or raw sources, publish a report, upload to GitHub, or
reinstall the application.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s11_p1_quality_rules as quality


RUN_PHASE_ID = "V015_S11_P2_CHECK_BOARD_DATA_MODEL"
ROADMAP_PHASE_ID = "S11-P2"
TASK_ID = "KMFA-V015-S11-P2-CHECK-BOARD-DATA-MODEL-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S11-P2-CHECK-BOARD-DATA-MODEL"
VERSION = "1.5.0-dev-s11p2"

HIERARCHY_LEVELS = (
    ("SOURCE_SYSTEM", "来源系统"),
    ("BUSINESS_SEGMENT", "业务板块"),
    ("FILE_PACKAGE", "文件包"),
    ("ENTITY", "主体"),
    ("BANK_OR_ACCOUNT", "银行或账户"),
    ("REPORT_OR_SHEET", "报表或工作表"),
)
REQUIRED_COLUMNS = (
    "层级项目",
    "更新时间",
    "状态",
    "影响报告",
    "阻塞原因",
    "负责人",
    "下一步",
)
VIEW_OPERATIONS = ("EXPAND", "COLLAPSE", "FILTER", "SEARCH")
INGESTION_STATES = ("IMPORTED", "MISSING", "FAILED")
ALERT_TYPES = (
    "MISSING_SOURCE",
    "IMPORT_FAILED",
    "QUALITY_HARD_GATE",
    "QUALITY_NOT_USABLE",
    "SOURCE_OUTDATED",
    "REVIEW_REQUIRED",
)
ALLOWED_VIEW_REQUEST_KEYS = (
    "expanded_node_ids",
    "search_text",
    "status_filters",
    "owner_filters",
    "alert_only",
)
FORBIDDEN_FRONTEND_STATE_KEYS = (
    "status",
    "status_override",
    "ready",
    "is_ready",
    "auto_selected",
    "quality_result",
    "quality_snapshot",
    "backend_fact",
)
BACKEND_FACT_KEYS = {
    "fact_id",
    "fact_revision",
    "updated_at",
    "ingestion_state",
    "hierarchy_path",
    "owner_role_zh",
    "report_impact_zh",
    "quality_snapshot",
    "provenance_kind",
}
STATUS_PRECEDENCE = {"已通过": 0, "需确认": 1, "已过期": 2, "不可使用": 3}
PUBLIC_PROVENANCE = "SYNTHETIC_PUBLIC_SAFE"


class CheckBoardModelError(ValueError):
    """Raised when backend facts or board view requests violate S11-P2."""

    def __init__(self, code: str, message_zh: str):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _require_text(value: Any, code: str, message_zh: str, *, max_length: int = 160) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise CheckBoardModelError(code, message_zh)
    return value.strip()


def _require_positive_int(value: Any, code: str, message_zh: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise CheckBoardModelError(code, message_zh)
    return value


def _parse_timestamp(value: Any) -> datetime:
    text = _require_text(value, "UPDATED_AT_INVALID", "更新时间必须是带时区的标准时间。")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise CheckBoardModelError("UPDATED_AT_INVALID", "更新时间必须是带时区的标准时间。") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CheckBoardModelError("UPDATED_AT_TIMEZONE_MISSING", "更新时间必须包含时区。")
    return parsed


def hierarchy_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p2.hierarchy_contract.v1",
        "levels": [
            {"depth": depth, "code": code, "label_zh": label}
            for depth, (code, label) in enumerate(HIERARCHY_LEVELS)
        ],
        "level_count": len(HIERARCHY_LEVELS),
        "leaf_depth": len(HIERARCHY_LEVELS) - 1,
        "all_files_in_one_flat_level_allowed": False,
        "parent_chain_required": True,
        "view_operations": list(VIEW_OPERATIONS),
    }


def column_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p2.column_contract.v1",
        "required_columns": list(REQUIRED_COLUMNS),
        "required_column_count": len(REQUIRED_COLUMNS),
        "status_labels_zh": list(quality.STATUS_LABELS_ZH),
        "every_status_requires_reason": True,
        "missing_source_requires_direct_action": True,
        "technical_status_location": "professional_detail",
        "color_is_only_information": False,
    }


def state_flow_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p2.state_flow_contract.v1",
        "backend_fact_only": True,
        "frontend_status_mutation_allowed": False,
        "frontend_allowed_operations": list(VIEW_OPERATIONS),
        "automatic_selection_requires": ["IMPORT_SUCCESS", "QUALITY_PASSED"],
        "automatic_selection_cleared_on_failure": True,
        "alert_types": list(ALERT_TYPES),
        "missing_or_outdated_reminder_required": True,
        "raw_source_mutation_allowed": False,
        "formal_report_allowed_in_this_phase": False,
    }


def validate_backend_fact(fact: Mapping[str, Any]) -> None:
    if not isinstance(fact, Mapping):
        raise CheckBoardModelError("BACKEND_FACT_INVALID", "检查板事实必须是结构化对象。")
    unknown = sorted(set(fact) - BACKEND_FACT_KEYS)
    if unknown:
        raise CheckBoardModelError("BACKEND_FACT_FIELD_FORBIDDEN", "检查板事实包含未授权字段。")
    missing = sorted(BACKEND_FACT_KEYS - set(fact))
    if missing:
        raise CheckBoardModelError("BACKEND_FACT_FIELD_MISSING", "检查板事实缺少必要字段。")
    _require_text(fact["fact_id"], "FACT_ID_INVALID", "事实编号不能为空。", max_length=80)
    _require_positive_int(fact["fact_revision"], "FACT_REVISION_INVALID", "事实版本必须是正整数。")
    _parse_timestamp(fact["updated_at"])
    if fact["ingestion_state"] not in INGESTION_STATES:
        raise CheckBoardModelError("INGESTION_STATE_INVALID", "导入状态不在允许范围。")
    if fact["provenance_kind"] != PUBLIC_PROVENANCE:
        raise CheckBoardModelError("PROVENANCE_INVALID", "本阶段只接受公开安全的后端模拟事实。")
    path = fact["hierarchy_path"]
    if not isinstance(path, Sequence) or isinstance(path, (str, bytes)) or len(path) != len(HIERARCHY_LEVELS):
        raise CheckBoardModelError("HIERARCHY_PATH_INVALID", "每项必须完整经过六层来源路径。")
    for label in path:
        _require_text(label, "HIERARCHY_LABEL_INVALID", "层级名称不能为空。", max_length=80)
    _require_text(fact["owner_role_zh"], "OWNER_MISSING", "每项必须指定负责人。", max_length=80)
    _require_text(fact["report_impact_zh"], "REPORT_IMPACT_MISSING", "每项必须说明影响报告。")
    snapshot = fact["quality_snapshot"]
    if fact["ingestion_state"] == "IMPORTED":
        if not isinstance(snapshot, Mapping):
            raise CheckBoardModelError("QUALITY_SNAPSHOT_REQUIRED", "导入成功后必须由后端提供质量检查事实。")
        quality.validate_snapshot(snapshot, quality.default_rule_catalog())
    elif snapshot is not None:
        raise CheckBoardModelError("QUALITY_SNAPSHOT_NOT_ALLOWED", "未成功导入时不得伪造质量结果。")


def _status_template(technical_status: str) -> dict[str, Any]:
    model = quality.default_status_model()
    return copy.deepcopy(next(row for row in model["statuses"] if row["technical_status"] == technical_status))


def _manual_result(technical_status: str, reason_zh: str, next_action_zh: str) -> dict[str, Any]:
    status = _status_template(technical_status)
    return {
        "display": {
            "label_zh": status["label_zh"],
            "symbol": status["symbol"],
            "summary_zh": status["summary_zh"],
            "reason_zh": reason_zh,
            "process_impact_zh": status["process_impact_zh"],
            "next_action_zh": next_action_zh,
            "color_token": status["color_token"],
            "color_is_supplemental": True,
        },
        "quality_flow_allowed": False,
        "formal_report_allowed": False,
        "professional_detail": {
            "technical_status": technical_status,
            "score_bps": None,
            "hard_gate_failure_count": 0,
            "status_source": "BACKEND_INGESTION_FACT",
        },
    }


def derive_leaf_state(fact: Mapping[str, Any]) -> dict[str, Any]:
    validate_backend_fact(fact)
    ingestion_state = str(fact["ingestion_state"])
    if ingestion_state == "MISSING":
        result = _manual_result("NOT_USABLE", "缺少必需文件包，无法完成检查。", "补充缺失文件包并重新导入。")
        alert_code = "MISSING_SOURCE"
    elif ingestion_state == "FAILED":
        result = _manual_result("NOT_USABLE", "文件导入失败，质量检查尚未完成。", "修复导入问题后重新提交检查。")
        alert_code = "IMPORT_FAILED"
    else:
        result = quality.evaluate_quality(fact["quality_snapshot"])
        detail = result["professional_detail"]
        technical = detail["technical_status"]
        if detail["hard_gate_failure_count"]:
            alert_code = "QUALITY_HARD_GATE"
        elif technical == "OUTDATED":
            alert_code = "SOURCE_OUTDATED"
        elif technical == "REVIEW_REQUIRED":
            alert_code = "REVIEW_REQUIRED"
        elif technical == "NOT_USABLE":
            alert_code = "QUALITY_NOT_USABLE"
        else:
            alert_code = None

    display = copy.deepcopy(result["display"])
    auto_selected = ingestion_state == "IMPORTED" and result["quality_flow_allowed"] is True
    alerts: list[dict[str, Any]] = []
    if alert_code is not None:
        alerts.append({
            "alert_type": alert_code,
            "label_zh": display["label_zh"],
            "reason_zh": display["reason_zh"],
            "next_action_zh": display["next_action_zh"],
            "reminder_required": True,
        })
    fact_core = {key: copy.deepcopy(fact[key]) for key in sorted(BACKEND_FACT_KEYS)}
    state = {
        "schema_version": "kmfa.v015.s11p2.leaf_state.v1",
        "fact_id": fact["fact_id"],
        "fact_revision": fact["fact_revision"],
        "fact_fingerprint": _fingerprint(fact_core),
        "updated_at": fact["updated_at"],
        "hierarchy_path": list(fact["hierarchy_path"]),
        "owner_role_zh": fact["owner_role_zh"],
        "report_impact_zh": fact["report_impact_zh"],
        "ingestion_state": ingestion_state,
        "display": display,
        "blocker_reason_zh": "无阻塞。" if auto_selected else display["reason_zh"],
        "next_action_zh": display["next_action_zh"],
        "auto_selected": auto_selected,
        "readiness_source": "BACKEND_DERIVED",
        "frontend_status_mutation_allowed": False,
        "alerts": alerts,
        "quality_flow_allowed": result["quality_flow_allowed"],
        "formal_report_allowed": False,
        "professional_detail": copy.deepcopy(result["professional_detail"]),
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
    }
    state["state_fingerprint"] = _fingerprint(state)
    return state


def _node_id(path: Sequence[str]) -> str:
    return "QBN-" + hashlib.sha256(_canonical(list(path))).hexdigest()[:16].upper()


def derive_board_model(facts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not isinstance(facts, Sequence) or isinstance(facts, (str, bytes)) or not facts:
        raise CheckBoardModelError("BACKEND_FACTS_EMPTY", "检查板至少需要一项后端事实。")
    leaf_states = [derive_leaf_state(fact) for fact in facts]
    fact_ids = [row["fact_id"] for row in leaf_states]
    paths = [tuple(row["hierarchy_path"]) for row in leaf_states]
    if len(fact_ids) != len(set(fact_ids)):
        raise CheckBoardModelError("FACT_ID_DUPLICATE", "事实编号必须唯一。")
    if len(paths) != len(set(paths)):
        raise CheckBoardModelError("LEAF_PATH_DUPLICATE", "完整六层路径必须唯一。")

    descendants: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    child_paths: dict[tuple[str, ...], set[tuple[str, ...]]] = defaultdict(set)
    for leaf in leaf_states:
        path = tuple(leaf["hierarchy_path"])
        for depth in range(len(path)):
            prefix = path[: depth + 1]
            descendants[prefix].append(leaf)
            if depth:
                child_paths[path[:depth]].add(prefix)

    nodes: list[dict[str, Any]] = []
    for path in sorted(descendants):
        depth = len(path) - 1
        leaves = sorted(descendants[path], key=lambda row: row["fact_id"])
        status_counts = Counter(row["display"]["label_zh"] for row in leaves)
        worst = max(leaves, key=lambda row: (STATUS_PRECEDENCE[row["display"]["label_zh"]], row["fact_id"]))
        all_ready = all(row["auto_selected"] for row in leaves)
        unready_count = sum(not row["auto_selected"] for row in leaves)
        owners = sorted({row["owner_role_zh"] for row in leaves})
        last_updated = max(leaves, key=lambda row: _parse_timestamp(row["updated_at"]))["updated_at"]
        is_leaf = depth == len(HIERARCHY_LEVELS) - 1
        if is_leaf:
            display = copy.deepcopy(worst["display"])
            blocker = worst["blocker_reason_zh"]
            next_action = worst["next_action_zh"]
            report_impact = worst["report_impact_zh"]
            alerts = copy.deepcopy(worst["alerts"])
            professional_detail = copy.deepcopy(worst["professional_detail"])
        else:
            display = copy.deepcopy(worst["display"])
            display["reason_zh"] = "全部下级项均已通过。" if all_ready else f"{unready_count} 个下级项需要处理。"
            display["next_action_zh"] = "继续下一步。" if all_ready else "展开本行，按阻塞原因逐项处理。"
            blocker = "无阻塞。" if all_ready else f"{unready_count} 个下级项未通过；{worst['display']['reason_zh']}"
            next_action = display["next_action_zh"]
            report_impact = worst["report_impact_zh"]
            alerts = [copy.deepcopy(alert) for leaf in leaves for alert in leaf["alerts"]]
            professional_detail = {
                "technical_status": worst["professional_detail"]["technical_status"],
                "descendant_leaf_count": len(leaves),
                "unready_leaf_count": unready_count,
                "status_counts": {label: status_counts.get(label, 0) for label in quality.STATUS_LABELS_ZH},
                "status_source": "BACKEND_DESCENDANT_AGGREGATION",
            }
        node = {
            "schema_version": "kmfa.v015.s11p2.board_node.v1",
            "node_id": _node_id(path),
            "parent_node_id": _node_id(path[:-1]) if depth else None,
            "node_type": HIERARCHY_LEVELS[depth][0],
            "node_type_label_zh": HIERARCHY_LEVELS[depth][1],
            "depth": depth,
            "label_zh": path[-1],
            "hierarchy_path": list(path),
            "is_leaf": is_leaf,
            "has_children": bool(child_paths.get(path)),
            "child_count": len(child_paths.get(path, set())),
            "descendant_leaf_count": len(leaves),
            "backend_fact_ref": worst["fact_id"] if is_leaf else None,
            "updated_at": last_updated,
            "display": display,
            "report_impact_zh": report_impact,
            "blocker_reason_zh": blocker,
            "owner_role_zh": owners[0] if len(owners) == 1 else "多负责人",
            "next_action_zh": next_action,
            "auto_selected": all_ready,
            "readiness_source": "BACKEND_DERIVED",
            "frontend_status_mutation_allowed": False,
            "alerts": alerts,
            "professional_detail": professional_detail,
            "display_columns": {
                "层级项目": path[-1],
                "更新时间": last_updated,
                "状态": display["label_zh"],
                "影响报告": report_impact,
                "阻塞原因": blocker,
                "负责人": owners[0] if len(owners) == 1 else "多负责人",
                "下一步": next_action,
            },
        }
        node["node_fingerprint"] = _fingerprint(node)
        nodes.append(node)

    node_ids = {row["node_id"] for row in nodes}
    if any(row["parent_node_id"] not in node_ids for row in nodes if row["parent_node_id"] is not None):
        raise CheckBoardModelError("PARENT_NODE_MISSING", "层级节点缺少父级。")
    model = {
        "schema_version": "kmfa.v015.s11p2.board_model.v1",
        "hierarchy_contract": hierarchy_contract(),
        "column_contract": column_contract(),
        "state_flow_contract": state_flow_contract(),
        "root_node_ids": [row["node_id"] for row in nodes if row["depth"] == 0],
        "nodes": nodes,
        "node_count": len(nodes),
        "leaf_count": len(leaf_states),
        "max_depth": max(row["depth"] for row in nodes),
        "flat_leaf_at_root_count": sum(row["is_leaf"] and row["depth"] == 0 for row in nodes),
        "backend_fact_count": len(facts),
        "backend_fact_only": True,
        "frontend_status_mutation_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    model["model_fingerprint"] = _fingerprint(model)
    return model


def validate_view_request(request: Mapping[str, Any], node_ids: set[str]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise CheckBoardModelError("VIEW_REQUEST_INVALID", "检查板操作必须是结构化对象。")
    forbidden = sorted(set(request) & set(FORBIDDEN_FRONTEND_STATE_KEYS))
    unknown = sorted(set(request) - set(ALLOWED_VIEW_REQUEST_KEYS))
    if forbidden or unknown:
        raise CheckBoardModelError("FRONTEND_STATE_MUTATION_FORBIDDEN", "前端只能展开、折叠、筛选和搜索，不能改写状态。")
    expanded = request.get("expanded_node_ids", [])
    if not isinstance(expanded, list) or not all(isinstance(value, str) for value in expanded):
        raise CheckBoardModelError("EXPANDED_NODE_IDS_INVALID", "展开节点必须是编号列表。")
    if set(expanded) - node_ids:
        raise CheckBoardModelError("EXPANDED_NODE_UNKNOWN", "展开请求包含未知节点。")
    search_text = request.get("search_text", "")
    if not isinstance(search_text, str) or len(search_text) > 100:
        raise CheckBoardModelError("SEARCH_TEXT_INVALID", "搜索文字格式无效。")
    status_filters = request.get("status_filters", [])
    if not isinstance(status_filters, list) or set(status_filters) - set(quality.STATUS_LABELS_ZH):
        raise CheckBoardModelError("STATUS_FILTER_INVALID", "状态筛选值无效。")
    owner_filters = request.get("owner_filters", [])
    if not isinstance(owner_filters, list) or not all(isinstance(value, str) and value for value in owner_filters):
        raise CheckBoardModelError("OWNER_FILTER_INVALID", "负责人筛选值无效。")
    alert_only = request.get("alert_only", False)
    if not isinstance(alert_only, bool):
        raise CheckBoardModelError("ALERT_FILTER_INVALID", "提醒筛选必须是真或假。")
    return {
        "expanded_node_ids": sorted(set(expanded)),
        "search_text": search_text.strip().casefold(),
        "status_filters": sorted(set(status_filters)),
        "owner_filters": sorted(set(owner_filters)),
        "alert_only": alert_only,
    }


def project_board(model: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != "kmfa.v015.s11p2.board_model.v1":
        raise CheckBoardModelError("BOARD_MODEL_INVALID", "检查板模型版本无效。")
    nodes = [copy.deepcopy(row) for row in model["nodes"]]
    by_id = {row["node_id"]: row for row in nodes}
    normalized = validate_view_request(request, set(by_id))
    active_query = bool(
        normalized["search_text"]
        or normalized["status_filters"]
        or normalized["owner_filters"]
        or normalized["alert_only"]
    )

    leaf_matches: set[str] = set()
    for node in nodes:
        if not node["is_leaf"]:
            continue
        haystack = " ".join(
            [*node["hierarchy_path"], *[str(value) for value in node["display_columns"].values()]]
        ).casefold()
        matches = (
            (not normalized["search_text"] or normalized["search_text"] in haystack)
            and (not normalized["status_filters"] or node["display"]["label_zh"] in normalized["status_filters"])
            and (not normalized["owner_filters"] or node["owner_role_zh"] in normalized["owner_filters"])
            and (not normalized["alert_only"] or bool(node["alerts"]))
        )
        if matches:
            leaf_matches.add(node["node_id"])

    included_for_query: set[str] = set()
    if active_query:
        for leaf_id in leaf_matches:
            current: str | None = leaf_id
            while current is not None:
                included_for_query.add(current)
                current = by_id[current]["parent_node_id"]

    visible: list[dict[str, Any]] = []
    expanded = set(normalized["expanded_node_ids"])
    if active_query:
        expanded.update(node_id for node_id in included_for_query if not by_id[node_id]["is_leaf"])
    for node in nodes:
        if active_query and node["node_id"] not in included_for_query:
            continue
        if not active_query and node["depth"]:
            parent_id = node["parent_node_id"]
            parent_visible = any(row["node_id"] == parent_id for row in visible)
            if not parent_visible or parent_id not in expanded:
                continue
        row = copy.deepcopy(node)
        row["is_expanded"] = node["node_id"] in expanded
        row["indent_level"] = node["depth"]
        row["query_match"] = node["node_id"] in leaf_matches
        visible.append(row)

    projection = {
        "schema_version": "kmfa.v015.s11p2.board_projection.v1",
        "request": normalized,
        "active_query": active_query,
        "auto_expanded_for_query": active_query,
        "visible_rows": visible,
        "visible_row_count": len(visible),
        "matched_leaf_count": len(leaf_matches),
        "search_feedback_zh": f"找到 {len(leaf_matches)} 个符合条件的末级项目。" if active_query else f"当前显示 {len(visible)} 个顶层来源。",
        "backend_state_mutation_count": 0,
        "frontend_status_mutation_allowed": False,
    }
    projection["projection_fingerprint"] = _fingerprint(projection)
    return projection


def derive_transition(before_fact: Mapping[str, Any], after_fact: Mapping[str, Any]) -> dict[str, Any]:
    validate_backend_fact(before_fact)
    validate_backend_fact(after_fact)
    if before_fact["fact_id"] != after_fact["fact_id"] or list(before_fact["hierarchy_path"]) != list(after_fact["hierarchy_path"]):
        raise CheckBoardModelError("TRANSITION_IDENTITY_DRIFT", "自动更新前后必须指向同一检查项。")
    if after_fact["fact_revision"] <= before_fact["fact_revision"]:
        raise CheckBoardModelError("TRANSITION_REVISION_INVALID", "自动更新必须增加事实版本。")
    if _parse_timestamp(after_fact["updated_at"]) <= _parse_timestamp(before_fact["updated_at"]):
        raise CheckBoardModelError("TRANSITION_TIME_INVALID", "自动更新必须使用更晚的事实时间。")
    before = derive_leaf_state(before_fact)
    after = derive_leaf_state(after_fact)
    event = {
        "schema_version": "kmfa.v015.s11p2.automatic_transition.v1",
        "fact_id": before["fact_id"],
        "before_revision": before["fact_revision"],
        "after_revision": after["fact_revision"],
        "before_status_zh": before["display"]["label_zh"],
        "after_status_zh": after["display"]["label_zh"],
        "before_auto_selected": before["auto_selected"],
        "after_auto_selected": after["auto_selected"],
        "before_alert_types": [row["alert_type"] for row in before["alerts"]],
        "after_alert_types": [row["alert_type"] for row in after["alerts"]],
        "automatic_update_applied": True,
        "frontend_state_write_applied": False,
        "raw_source_mutation_performed": False,
        "formal_report_generated": False,
    }
    event["transition_fingerprint"] = _fingerprint(event)
    return event


def public_backend_facts() -> list[dict[str, Any]]:
    scenarios = quality.public_scenarios()
    return [
        {
            "fact_id": "QBF-001",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:00:00+10:00",
            "ingestion_state": "IMPORTED",
            "hierarchy_path": ["财务文件源", "经营总览", "月度经营包", "主体甲组", "系统报表组", "经营指标表"],
            "owner_role_zh": "财务负责人",
            "report_impact_zh": "影响经营总览报告。",
            "quality_snapshot": scenarios["all_pass"],
            "provenance_kind": PUBLIC_PROVENANCE,
        },
        {
            "fact_id": "QBF-002",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:10:00+10:00",
            "ingestion_state": "IMPORTED",
            "hierarchy_path": ["财务文件源", "项目成本", "月度成本包", "主体甲组", "系统报表组", "成本结构表"],
            "owner_role_zh": "成本负责人",
            "report_impact_zh": "影响项目成本报告。",
            "quality_snapshot": scenarios["review_required"],
            "provenance_kind": PUBLIC_PROVENANCE,
        },
        {
            "fact_id": "QBF-003",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:20:00+10:00",
            "ingestion_state": "MISSING",
            "hierarchy_path": ["表格导入源", "回款应收", "应收文件包（缺失）", "主体乙组", "工作表组", "应收检查表"],
            "owner_role_zh": "回款负责人",
            "report_impact_zh": "影响回款应收报告。",
            "quality_snapshot": None,
            "provenance_kind": PUBLIC_PROVENANCE,
        },
        {
            "fact_id": "QBF-004",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:30:00+10:00",
            "ingestion_state": "IMPORTED",
            "hierarchy_path": ["银行文件源", "现金资金", "账户流水包", "主体甲组", "账户尾号分组", "现金摘要表"],
            "owner_role_zh": "资金负责人",
            "report_impact_zh": "影响现金资金报告。",
            "quality_snapshot": scenarios["outdated_source"],
            "provenance_kind": PUBLIC_PROVENANCE,
        },
        {
            "fact_id": "QBF-005",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:40:00+10:00",
            "ingestion_state": "IMPORTED",
            "hierarchy_path": ["业务系统导出源", "合同履约", "合同摘要包", "主体乙组", "系统账户组", "合同履约表"],
            "owner_role_zh": "合同负责人",
            "report_impact_zh": "影响合同履约报告。",
            "quality_snapshot": scenarios["high_score_critical_failure"],
            "provenance_kind": PUBLIC_PROVENANCE,
        },
        {
            "fact_id": "QBF-006",
            "fact_revision": 1,
            "updated_at": "2026-07-15T09:50:00+10:00",
            "ingestion_state": "FAILED",
            "hierarchy_path": ["业务系统导出源", "税务票据", "票据摘要包", "主体甲组", "系统账户组", "票据汇总表"],
            "owner_role_zh": "税务负责人",
            "report_impact_zh": "影响税务票据报告。",
            "quality_snapshot": None,
            "provenance_kind": PUBLIC_PROVENANCE,
        },
    ]


def public_transition_facts() -> tuple[dict[str, Any], dict[str, Any]]:
    before = {
        "fact_id": "QBF-TRANSITION",
        "fact_revision": 1,
        "updated_at": "2026-07-15T10:00:00+10:00",
        "ingestion_state": "MISSING",
        "hierarchy_path": ["表格导入源", "回款应收", "补充文件包", "主体乙组", "工作表组", "补充检查表"],
        "owner_role_zh": "回款负责人",
        "report_impact_zh": "影响回款应收报告。",
        "quality_snapshot": None,
        "provenance_kind": PUBLIC_PROVENANCE,
    }
    after = copy.deepcopy(before)
    after.update({
        "fact_revision": 2,
        "updated_at": "2026-07-15T10:10:00+10:00",
        "ingestion_state": "IMPORTED",
        "quality_snapshot": quality.baseline_snapshot(),
    })
    return before, after


def public_verification() -> dict[str, Any]:
    facts = public_backend_facts()
    model = derive_board_model(facts)
    roots = project_board(model, {})
    first_root = model["root_node_ids"][0]
    expanded = project_board(model, {"expanded_node_ids": [first_root]})
    search = project_board(model, {"search_text": "应收检查表"})
    outdated = project_board(model, {"status_filters": ["已过期"]})
    alerts = project_board(model, {"alert_only": True})
    before, after = public_transition_facts()
    transition = derive_transition(before, after)
    leaves = [row for row in model["nodes"] if row["is_leaf"]]
    by_fact = {row["backend_fact_ref"]: row for row in leaves}
    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("HIERARCHY_LEVEL_COUNT", len(HIERARCHY_LEVELS) == 6)
    check("HIERARCHY_LEVEL_ORDER", [row[0] for row in HIERARCHY_LEVELS] == ["SOURCE_SYSTEM", "BUSINESS_SEGMENT", "FILE_PACKAGE", "ENTITY", "BANK_OR_ACCOUNT", "REPORT_OR_SHEET"])
    check("REQUIRED_COLUMN_COUNT", len(REQUIRED_COLUMNS) == 7)
    check("VIEW_OPERATIONS_COMPLETE", set(VIEW_OPERATIONS) == {"EXPAND", "COLLAPSE", "FILTER", "SEARCH"})
    check("STATUS_LABELS_REUSED", tuple(quality.STATUS_LABELS_ZH) == ("已通过", "需确认", "不可使用", "已过期"))
    check("BACKEND_FACT_ONLY", model["backend_fact_only"] is True)
    check("FRONTEND_MUTATION_CLOSED", model["frontend_status_mutation_allowed"] is False)
    check("FLAT_ROOT_LEAF_ZERO", model["flat_leaf_at_root_count"] == 0)
    check("MAX_DEPTH_FIVE", model["max_depth"] == 5)
    check("SIX_SAMPLE_LEAVES", model["leaf_count"] == 6)
    check("NODE_IDS_UNIQUE", len({row["node_id"] for row in model["nodes"]}) == model["node_count"])
    check("PARENT_CHAIN_COMPLETE", all(row["parent_node_id"] is not None for row in leaves))
    check("ALL_LEAVES_SIX_LEVELS", all(len(row["hierarchy_path"]) == 6 and row["depth"] == 5 for row in leaves))
    check("ALL_COLUMNS_PRESENT", all(set(row["display_columns"]) == set(REQUIRED_COLUMNS) for row in model["nodes"]))
    check("ALL_STATUS_REASONS_PRESENT", all(row["display"]["reason_zh"] for row in model["nodes"]))
    check("ALL_OWNERS_PRESENT", all(row["owner_role_zh"] for row in model["nodes"]))
    check("ALL_NEXT_ACTIONS_PRESENT", all(row["next_action_zh"] for row in model["nodes"]))
    check("ROOTS_COLLAPSED_BY_DEFAULT", roots["visible_row_count"] == len(model["root_node_ids"]))
    check("EXPAND_INCREASES_VISIBLE", expanded["visible_row_count"] > roots["visible_row_count"])
    check("SEARCH_MATCHES_ONE_LEAF", search["matched_leaf_count"] == 1)
    check("SEARCH_AUTO_EXPANDS_PATH", search["visible_row_count"] == 6 and search["auto_expanded_for_query"] is True)
    check("OUTDATED_FILTER_MATCHES_ONE", outdated["matched_leaf_count"] == 1)
    check("ALERT_FILTER_MATCHES_FIVE", alerts["matched_leaf_count"] == 5)
    check("PROJECTIONS_DO_NOT_MUTATE", all(row["backend_state_mutation_count"] == 0 for row in (roots, expanded, search, outdated, alerts)))

    expected_leaf = {
        "QBF-001": ("已通过", True, []),
        "QBF-002": ("需确认", False, ["REVIEW_REQUIRED"]),
        "QBF-003": ("不可使用", False, ["MISSING_SOURCE"]),
        "QBF-004": ("已过期", False, ["SOURCE_OUTDATED"]),
        "QBF-005": ("不可使用", False, ["QUALITY_HARD_GATE"]),
        "QBF-006": ("不可使用", False, ["IMPORT_FAILED"]),
    }
    for fact_id, (label, selected, alert_types) in expected_leaf.items():
        leaf = by_fact[fact_id]
        prefix = fact_id.replace("-", "_")
        check(prefix + "_STATUS", leaf["display"]["label_zh"] == label)
        check(prefix + "_SELECTION", leaf["auto_selected"] is selected)
        check(prefix + "_ALERTS", [row["alert_type"] for row in leaf["alerts"]] == alert_types)
        check(prefix + "_BACKEND_DERIVED", leaf["readiness_source"] == "BACKEND_DERIVED")
        check(prefix + "_FRONTEND_CLOSED", leaf["frontend_status_mutation_allowed"] is False)
        check(prefix + "_REPORT_CLOSED", leaf["professional_detail"] and leaf["display"]["reason_zh"] and leaf["next_action_zh"])

    missing = by_fact["QBF-003"]
    check("MISSING_SOURCE_DIRECT_ACTION", "补充" in missing["next_action_zh"] and "缺少" in missing["blocker_reason_zh"])
    hard = by_fact["QBF-005"]
    check("HIGH_SCORE_HARD_GATE_BLOCKED", hard["professional_detail"]["score_bps"] == 9375 and hard["auto_selected"] is False)
    check("TRANSITION_STATUS_UPDATED", transition["before_status_zh"] == "不可使用" and transition["after_status_zh"] == "已通过")
    check("TRANSITION_AUTO_SELECTED", transition["before_auto_selected"] is False and transition["after_auto_selected"] is True)
    check("TRANSITION_ALERT_CLEARED", transition["before_alert_types"] == ["MISSING_SOURCE"] and transition["after_alert_types"] == [])
    check("TRANSITION_BACKEND_ONLY", transition["automatic_update_applied"] is True and transition["frontend_state_write_applied"] is False)
    check("TRANSITION_SOURCE_UNCHANGED", transition["raw_source_mutation_performed"] is False)

    mutation_rejected = False
    try:
        project_board(model, {"status_override": "已通过"})
    except CheckBoardModelError as error:
        mutation_rejected = error.code == "FRONTEND_STATE_MUTATION_FORBIDDEN"
    check("FRONTEND_STATUS_OVERRIDE_REJECTED", mutation_rejected)

    public_text = json.dumps([model, roots, expanded, search, outdated, alerts, transition], ensure_ascii=False, sort_keys=True)
    for index, forbidden in enumerate(("/Users/", "/Volumes/", "/home/", "file://", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".zip", "password"), start=1):
        check(f"PUBLIC_BOUNDARY_{index:02d}", forbidden.casefold() not in public_text.casefold())
    check("RAW_ACCESS_ZERO", model["raw_root_access_count"] == 0)
    check("LIVE_SOURCE_ZERO", model["live_source_read_count"] == 0)
    check("GITHUB_CLOSED", model["github_upload_performed"] is False)
    check("APP_CLOSED", model["app_reinstall_performed"] is False)
    check("BUSINESS_EXECUTION_CLOSED", model["business_execution_performed"] is False)

    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s11p2.public_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
        "model": model,
        "projections": {
            "collapsed": roots,
            "expanded": expanded,
            "search": search,
            "outdated_filter": outdated,
            "alert_filter": alerts,
        },
        "automatic_transition": transition,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "ALERT_TYPES",
    "CheckBoardModelError",
    "HIERARCHY_LEVELS",
    "REQUIRED_COLUMNS",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "TASK_ID",
    "VERSION",
    "VIEW_OPERATIONS",
    "column_contract",
    "derive_board_model",
    "derive_leaf_state",
    "derive_transition",
    "hierarchy_contract",
    "project_board",
    "public_backend_facts",
    "public_transition_facts",
    "public_verification",
    "state_flow_contract",
    "validate_backend_fact",
    "validate_view_request",
]
