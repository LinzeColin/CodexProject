"""PFI v0.2.5 Stage 7.3 formal parameter/interconnection/metric projection.

The projection is read-only.  It joins existing authoritative registries and
aggregate lineage contracts without persisting financial rows or inventing a
fallback value when an input is unavailable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from pfi_os.application.metrics.formula_governance import (
    build_parameter_consistency_report,
    load_formula_registry,
)
from pfi_os.application.read_model_status import build_v024_read_model_status
from pfi_os.application.read_models.unified import build_current_unified_read_model
from pfi_os.application.stage3_reconciliation import (
    TRANSACTION_CSV_PATH,
    build_interconnection_matrix,
    run_phase33_real_reconciliation,
)


VERSION = "v0.2.5"
PHASE_ID = "V025-S7-P7.3"
TASK_IDS = ("S7-P3-T1", "S7-P3-T2", "S7-P3-T3", "S7-P3-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN"
PARAMETER_CATALOG_RELATIVE = Path("config/pfi_parameters.yaml")
FORMULA_REGISTRY_RELATIVE = Path("config/formulas/v025_formula_registry.json")

_METRIC_LABELS_ZH = {
    "net_worth_cny": "净资产",
    "account_assets_cny": "账户资产",
    "cash_balance_cny": "现金余额",
    "liabilities_cny": "负债",
    "investment_market_value_cny": "投资市值",
    "investment_cost_basis_cny": "投资成本基础",
    "investment_unrealized_pnl_cny": "投资未实现损益",
    "total_consumption_outflow_cny": "消费总流出金额（用户定义活动口径）",
    "living_consumption_cny": "生活消费金额",
    "investment_funding_outflow_cny": "投资资金流出金额",
    "investment_allocation_amount_cny": "投资域内配置金额",
}
_STAGE5_EVENT_BINDINGS = {
    "total_consumption_outflow_cny": "activity_outflow",
    "living_consumption_cny": "living_consumption",
    "investment_allocation_amount_cny": "investment_allocation",
}
_OPERATIONAL_METRIC_FORMULAS = {
    "net_worth_cny": "FORM-PFI-012",
    "account_assets_cny": "FORM-PFI-011",
    "cash_balance_cny": "FORM-PFI-008",
    "liabilities_cny": "FORM-PFI-011",
    "investment_market_value_cny": "FORM-PFI-010",
    "investment_cost_basis_cny": "FORM-PFI-009",
    "investment_unrealized_pnl_cny": "FORM-PFI-010",
    "total_consumption_outflow_cny": "FORM-PFI-015",
    "living_consumption_cny": "FORM-PFI-015",
    "investment_funding_outflow_cny": "FORM-PFI-015",
    "investment_allocation_amount_cny": "FORM-PFI-015",
}
_EVENT_LABELS_ZH = {
    "credit_card_repayment": "信用卡还款",
    "fund_subscription": "基金申购",
    "gold_subscription": "黄金申购",
    "income": "收入",
    "investment_funding": "投资入金",
    "investment_purchase": "投资买入",
    "investment_sale": "投资卖出",
    "living_consumption": "生活消费",
    "own_account_transfer": "本人账户转账",
    "refund": "退款",
}


def _canonical_hash(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _source_observed_at(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", TRANSACTION_CSV_PATH],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    observed_at = completed.stdout.strip()
    if not observed_at:
        raise ValueError("transaction source commit timestamp is unavailable")
    return observed_at


def _public_parameter_value(value: object) -> object:
    if isinstance(value, str) and value.startswith(("/Users/", "/private/", "/Volumes/")):
        return "本机路径（页面不显示绝对地址）"
    if isinstance(value, Mapping):
        return {str(key): _public_parameter_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_public_parameter_value(item) for item in value]
    return value


def _build_parameter_center(pfi_root: Path) -> dict[str, Any]:
    catalog_path = pfi_root / PARAMETER_CATALOG_RELATIVE
    registry_path = pfi_root / FORMULA_REGISTRY_RELATIVE
    catalog = _json_object(catalog_path)
    registry = load_formula_registry(registry_path)
    raw_parameters = catalog.get("parameters")
    raw_parameters = raw_parameters if isinstance(raw_parameters, dict) else {}
    domains: list[dict[str, Any]] = []
    for raw_domain in catalog.get("domains", []):
        if not isinstance(raw_domain, dict):
            continue
        key = str(raw_domain.get("key") or "")
        entries: list[dict[str, Any]] = []
        domain_values = raw_parameters.get(key)
        if isinstance(domain_values, dict):
            for parameter_id, raw_entry in domain_values.items():
                entry = raw_entry if isinstance(raw_entry, dict) else {"value": raw_entry}
                entries.append(
                    {
                        "parameter_id": str(parameter_id),
                        "label_zh": str(entry.get("label_zh") or parameter_id),
                        "value": _public_parameter_value(entry.get("value")),
                        "description_zh": str(entry.get("description_zh") or "以 canonical 参数文件为准。"),
                        "impact_surfaces": [str(item) for item in entry.get("impact_surfaces", [])],
                        "user_editable": bool(entry.get("user_editable") is True),
                    }
                )
        domains.append(
            {
                "domain_id": key,
                "label_zh": str(raw_domain.get("label_zh") or key),
                "description_zh": str(raw_domain.get("description_zh") or ""),
                "entry_count": len(entries),
                "entries": entries,
            }
        )
    formulas = [
        {
            "formula_id": str(formula.get("formula_id") or ""),
            "version": str(formula.get("version") or ""),
            "label_zh": str(formula.get("label_zh") or formula.get("formula_id") or "公式"),
            "definition_zh": str(formula.get("definition_zh") or ""),
            "parameter_ids": [str(item) for item in formula.get("parameters", [])],
            "formula_hash": str(formula.get("formula_hash") or ""),
            "validation_status": str(formula.get("validation_status") or "blocked"),
            "lifecycle_status": str(formula.get("lifecycle_status") or "draft"),
        }
        for formula in registry.get("formulas", [])
        if isinstance(formula, dict)
    ]
    consistency = build_parameter_consistency_report()
    payload = {
        "schema": "PFIV025Stage7Phase73ParameterCenterV1",
        "status": "ready" if consistency.get("status") == "pass" else "blocked_inconsistent",
        "title_zh": "参数中心",
        "description_zh": "集中查看当前参数、公式版本、影响范围与可修改边界。",
        "parameter_version": str(catalog.get("parameter_version") or ""),
        "parameter_hash": _file_hash(catalog_path),
        "formula_registry_version": str(registry.get("registry_version") or ""),
        "formula_registry_hash": _file_hash(registry_path),
        "domain_count": len(domains),
        "parameter_count": sum(item["entry_count"] for item in domains),
        "formula_count": len(formulas),
        "domains": domains,
        "formulas": formulas,
        "consistency_status": consistency.get("status"),
        "consistency_conflict_count": int(consistency.get("conflict_count") or 0),
        "source_refs": [
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/formulas/v025_formula_registry.json",
            "PFI/docs/governance/parameter_registry.csv",
        ],
        "write_enabled": False,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def _blocked_interconnection(data_hash: str | None = None) -> dict[str, Any]:
    payload = {
        "schema": "PFIV025Stage7Phase73InterconnectionMapV1",
        "status": "not_loaded",
        "title_zh": "Interconnection Map",
        "blocking_reason_zh": "当前运行未加载真实事件来源，关联数量保持未知。",
        "data_hash": data_hash,
        "read_model_hash": None,
        "nodes": [],
        "edges": [],
        "event_types": [],
        "lineage_complete_count": None,
        "lineage_missing_count": None,
        "financial_values_emitted": 0,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def _build_interconnection_map(run: Any) -> dict[str, Any]:
    summary = run.reconciliation_summary
    lineage = run.lineage_samples_redacted
    read_model = run.read_model_contract
    matrix = build_interconnection_matrix(run)
    source_hash = str(run.idempotency_result.get("input_content_hash") or "")
    nodes = [
        {"node_id": "source_records", "label_zh": "真实来源记录", "count": summary["input_record_count"], "route": "/data/sources"},
        {"node_id": "review_queue", "label_zh": "待复核", "count": summary["review_queue_record_count"], "route": "/data/review"},
        {"node_id": "normalized_transactions", "label_zh": "标准化交易", "count": summary["published_record_count"], "route": "/data/interconnection?node=normalized_transactions"},
        {"node_id": "interconnection_groups", "label_zh": "关联分组", "count": read_model["unique_economic_event_count"], "route": "/data/interconnection?node=interconnection_groups"},
        {"node_id": "economic_events", "label_zh": "经济事件", "count": read_model["unique_economic_event_count"], "route": "/data/interconnection?node=economic_events"},
        {"node_id": "ledger_events", "label_zh": "账本事件", "count": read_model["input_ledger_event_count"], "route": "/ledger/list"},
        {"node_id": "metrics", "label_zh": "指标下钻", "count": len(read_model["metrics"]), "route": "/reports/metric-drilldown"},
    ]
    edges = [
        {"from": "source_records", "to": "review_queue", "label_zh": "缺结构化证据时 fail-closed"},
        {"from": "source_records", "to": "normalized_transactions", "label_zh": "解析与标准化"},
        {"from": "normalized_transactions", "to": "interconnection_groups", "label_zh": "显式关联策略"},
        {"from": "interconnection_groups", "to": "economic_events", "label_zh": "确定性身份"},
        {"from": "economic_events", "to": "ledger_events", "label_zh": "幂等发布"},
        {"from": "ledger_events", "to": "metrics", "label_zh": "同一事件每指标最多一次"},
    ]
    event_types = [
        {
            "event_type": str(item.get("event_type") or ""),
            "label_zh": _EVENT_LABELS_ZH.get(str(item.get("event_type") or ""), str(item.get("event_type") or "")),
            "published_count": int(item.get("real_snapshot_published_count") or 0),
            "review_count": int(item.get("real_snapshot_review_count") or 0),
            "unresolved_policy": str(item.get("unresolved_policy") or ""),
            "impact_flags": dict(item.get("impact_flags") or {}),
        }
        for item in matrix.get("event_types", [])
        if isinstance(item, dict)
    ]
    payload = {
        "schema": "PFIV025Stage7Phase73InterconnectionMapV1",
        "status": "ready" if matrix.get("status") == "pass" and lineage.get("status") == "pass" else "blocked",
        "title_zh": "Interconnection Map",
        "description_zh": "从真实来源记录到指标的可点击聚合关系；不显示私有金额或身份。",
        "source_id": "SRC-TRANSACTIONS-ALIPAY",
        "data_hash": source_hash,
        "read_model_hash": str(read_model.get("read_model_hash") or ""),
        "policy_version": str(matrix.get("policy_version") or ""),
        "lineage_order": list(lineage.get("lineage_order") or []),
        "lineage_complete_count": int(lineage.get("complete_lineage_count") or 0),
        "lineage_missing_count": int(lineage.get("missing_lineage_count") or 0),
        "same_economic_event_per_metric_max_count": int(read_model.get("same_economic_event_per_metric_max_count") or 0),
        "silent_drop_count": int(summary.get("silent_drop_count") or 0),
        "nodes": nodes,
        "edges": edges,
        "event_types": event_types,
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def _operational_interconnection_map(
    base: Mapping[str, Any], operational_ledger: Mapping[str, Any]
) -> dict[str, Any]:
    """Make the current SQLite ledger the displayed runtime lineage authority."""

    ledger_count = int(operational_ledger.get("ledger_count") or 0)
    pending_count = int(operational_ledger.get("pending_review_count") or 0)
    posted_count = int(operational_ledger.get("posted_count") or 0)
    count_by_node = {
        "source_records": ledger_count,
        "review_queue": pending_count,
        "normalized_transactions": ledger_count,
        "interconnection_groups": 0,
        "economic_events": 0,
        "ledger_events": ledger_count,
    }
    base_nodes = base.get("nodes") if isinstance(base.get("nodes"), list) else []
    if not base_nodes:
        base_nodes = [
            {"node_id": "source_records", "label_zh": "真实来源记录", "route": "/data/sources"},
            {"node_id": "review_queue", "label_zh": "待复核", "route": "/data/review"},
            {"node_id": "normalized_transactions", "label_zh": "标准化交易", "route": "/data/interconnection?node=normalized_transactions"},
            {"node_id": "interconnection_groups", "label_zh": "关联分组", "route": "/data/interconnection?node=interconnection_groups"},
            {"node_id": "economic_events", "label_zh": "经济事件", "route": "/data/interconnection?node=economic_events"},
            {"node_id": "ledger_events", "label_zh": "账本事件", "route": "/ledger/list"},
            {"node_id": "metrics", "label_zh": "指标下钻", "route": "/reports/metric-drilldown"},
        ]
    nodes = [
        {
            **dict(node),
            "count": count_by_node.get(
                str(node.get("node_id")),
                len(_OPERATIONAL_METRIC_FORMULAS) if node.get("node_id") == "metrics" else 0,
            ),
        }
        for node in base_nodes
        if isinstance(node, Mapping)
    ]
    edges = base.get("edges") if isinstance(base.get("edges"), list) else []
    if not edges:
        edges = [
            {"from": "source_records", "to": "review_queue", "label_zh": "缺结构化证据时 fail-closed"},
            {"from": "source_records", "to": "normalized_transactions", "label_zh": "解析与标准化"},
            {"from": "normalized_transactions", "to": "interconnection_groups", "label_zh": "显式关联策略"},
            {"from": "interconnection_groups", "to": "economic_events", "label_zh": "确定性身份"},
            {"from": "economic_events", "to": "ledger_events", "label_zh": "幂等发布"},
            {"from": "ledger_events", "to": "metrics", "label_zh": "同一事件每指标最多一次"},
        ]
    payload = {
        **dict(base),
        "status": "blocked",
        "blocking_reason_zh": (
            "SQLite ledger 已接入，但 Stage 3 economic_event/interconnection adapter 尚未完成；"
            "禁止将来源分类或 ledger entry 冒充经济事件 lineage。"
        ),
        "description_zh": "当前 SQLite ledger 的真实节点与目标架构；经济事件关联保持阻断。",
        "source_id": "v025_sqlite_unified_operational_ledger",
        "data_hash": operational_ledger.get("data_hash"),
        "read_model_hash": operational_ledger.get("read_model_hash"),
        "lineage_complete_count": 0,
        "lineage_missing_count": ledger_count,
        "same_economic_event_per_metric_max_count": None,
        "silent_drop_count": 0,
        "nodes": nodes,
        "edges": edges,
        "event_types": [],
        "economic_event_adapter_ready": False,
        "operational_ledger_authority": True,
        "financial_values_emitted": 0,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def _operational_metric_rows(
    operational_ledger: Mapping[str, Any],
    *,
    formula_by_id: Mapping[str, Mapping[str, Any]],
    parameter_hash: str,
) -> list[dict[str, Any]]:
    source_ids = [str(item) for item in operational_ledger.get("source_ids", [])]
    source_range = operational_ledger.get("data_range")
    source_range = source_range if isinstance(source_range, Mapping) else {}
    data_hash = operational_ledger.get("data_hash")
    read_model_hash = operational_ledger.get("read_model_hash")
    activity_metrics = {
        "total_consumption_outflow_cny",
        "living_consumption_cny",
        "investment_funding_outflow_cny",
        "investment_allocation_amount_cny",
    }
    rows: list[dict[str, Any]] = []
    for metric_id, formula_id in _OPERATIONAL_METRIC_FORMULAS.items():
        if metric_id in activity_metrics:
            status = "blocked_economic_event_adapter"
            reason = (
                "SQLite ledger 已接入，但 Stage 3 economic_event/interconnection adapter 尚未完成；"
                "禁止推断 FORM-PFI-015 值。"
            )
            bound_source_ids = source_ids
            bound_data_hash = data_hash
            bound_read_model_hash = read_model_hash
            coverage_start = source_range.get("start")
            coverage_end = source_range.get("end")
        else:
            status = "blocked_source_dependency"
            reason = "该指标所需账户快照、负债、持仓估值或成本基础尚未接入 Stage 7 authority。"
            bound_source_ids = []
            bound_data_hash = None
            bound_read_model_hash = None
            coverage_start = None
            coverage_end = None
        raw = {
            "metric_id": metric_id,
            "label_zh": _METRIC_LABELS_ZH[metric_id],
            "status": status,
            "value": None,
            "currency": "CNY",
            "record_count": None,
            "formula_id": formula_id,
            "data_hash": bound_data_hash,
            "read_model_hash": bound_read_model_hash,
            "source_ids": bound_source_ids,
            "coverage_start": coverage_start,
            "coverage_end": coverage_end,
            "blocking_reason_zh": reason,
            "calculation_state": "blocked",
        }
        rows.append(
            _metric_record(
                raw,
                formula_by_id=formula_by_id,
                parameter_hash=parameter_hash,
                event_contract={},
                fallback_read_model_hash=bound_read_model_hash,
                source_range=source_range,
            )
        )
    return rows


def _metric_payload(
    metrics: list[dict[str, Any]], *, private_runtime_only: bool
) -> dict[str, Any]:
    metric_ids = [str(item.get("metric_id") or "") for item in metrics]
    false_zero_count = sum(
        1 for item in metrics if bool(item.get("non_ready_source_value_present"))
    )
    required_hash_fields = ("formula_hash", "parameter_hash", "data_hash", "read_model_hash")
    ready_metrics = [item for item in metrics if item.get("status") in {"ready", "confirmed_zero"}]
    ready_contract_complete = bool(ready_metrics) and all(
        all(isinstance(item.get(field), str) and str(item.get(field)).startswith("sha256:") for field in required_hash_fields)
        and bool(item.get("source_ids"))
        for item in ready_metrics
    )
    payload = {
        "schema": "PFIV025Stage7Phase73MetricDrilldownV1",
        "status": "ready" if metrics and false_zero_count == 0 and ready_contract_complete else "blocked",
        "metric_count": len(metrics),
        "metric_ids": metric_ids,
        "metrics": metrics,
        "required_fields": [
            "data_range", "formula_hash", "parameter_hash", "data_hash",
            "read_model_hash", "source_ids", "event_lineage", "blocking_reason_zh",
        ],
        "non_ready_false_zero_count": false_zero_count,
        "ready_metric_count": len(ready_metrics),
        "ready_metric_contract_complete": ready_contract_complete,
        "private_runtime_only": private_runtime_only,
        "persist_private_values_to_evidence_allowed": False,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def _formula_map(registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("formula_id") or ""): dict(item)
        for item in registry.get("formulas", [])
        if isinstance(item, dict) and item.get("formula_id")
    }


def _metric_record(
    metric: Mapping[str, Any],
    *,
    formula_by_id: Mapping[str, Mapping[str, Any]],
    parameter_hash: str,
    event_contract: Mapping[str, Any] | None,
    fallback_read_model_hash: str | None,
    source_range: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    status = str(metric.get("status") or "not_loaded")
    ready = status in {"ready", "confirmed_zero"}
    non_ready_source_value_present = not ready and metric.get("value") is not None
    formula_id = str(metric.get("formula_id") or "")
    formula = formula_by_id.get(formula_id, {})
    sources = metric.get("source_ids")
    if not isinstance(sources, list):
        source_id = metric.get("source_id")
        sources = [source_id] if isinstance(source_id, str) and source_id else []
    coverage_start = metric.get("coverage_start")
    coverage_end = metric.get("coverage_end")
    as_of = metric.get("data_as_of") or metric.get("as_of")
    if isinstance(source_range, Mapping):
        coverage_start = coverage_start or source_range.get("coverage_start")
        coverage_end = coverage_end or source_range.get("coverage_end")
        as_of = as_of or source_range.get("coverage_end")
    data_hash = metric.get("data_hash")
    read_model_hash = metric.get("read_model_hash") or fallback_read_model_hash
    payload = {
        "metric_id": str(metric.get("metric_id") or ""),
        "label_zh": str(metric.get("label_zh") or _METRIC_LABELS_ZH.get(str(metric.get("metric_id") or ""), metric.get("metric_id") or "指标")),
        "status": status,
        "value": metric.get("value") if ready else None,
        "currency": metric.get("currency"),
        "record_count": metric.get("record_count"),
        "data_range": {"start": coverage_start, "end": coverage_end, "as_of": as_of},
        "formula_id": formula_id,
        "formula_version": metric.get("formula_version") or formula.get("version"),
        "formula_label_zh": formula.get("label_zh"),
        "formula_definition_zh": formula.get("definition_zh"),
        "formula_hash": metric.get("formula_hash") or formula.get("formula_hash"),
        "parameter_hash": metric.get("parameter_hash") or parameter_hash,
        "data_hash": data_hash,
        "read_model_hash": read_model_hash,
        "source_ids": [str(item) for item in sources],
        "event_lineage": dict(event_contract or {}),
        "blocking_reason_zh": None if ready else str(metric.get("blocking_reason_zh") or "真实输入未就绪，指标保持阻断。"),
        "calculation_state": metric.get("calculation_state") or ("calculated" if ready else "blocked"),
        "non_ready_value_is_null": not ready and metric.get("value") is None,
        "non_ready_source_value_present": non_ready_source_value_present,
    }
    payload["drilldown_hash"] = _canonical_hash(payload)
    return payload


def _build_metric_drilldowns(
    pfi_root: Path,
    run: Any | None,
    *,
    read_model_status: Mapping[str, Any] | None = None,
    operational_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = load_formula_registry(pfi_root / FORMULA_REGISTRY_RELATIVE)
    formula_by_id = _formula_map(registry)
    parameter_hash = _file_hash(pfi_root / PARAMETER_CATALOG_RELATIVE)
    if operational_ledger is not None:
        return _metric_payload(
            _operational_metric_rows(
                operational_ledger,
                formula_by_id=formula_by_id,
                parameter_hash=parameter_hash,
            ),
            private_runtime_only=True,
        )
    if read_model_status is None:
        unified = build_current_unified_read_model(pfi_root.parent)
        private_status = build_v024_read_model_status(pfi_root)
    else:
        unified = dict(read_model_status)
        private_status = {}
    event_metrics = run.read_model_contract.get("metrics", {}) if run is not None else {}
    metrics = [
        _metric_record(
            item,
            formula_by_id=formula_by_id,
            parameter_hash=parameter_hash,
            event_contract=None,
            fallback_read_model_hash=str(unified.get("read_model_hash") or "") or None,
        )
        for item in unified.get("core_metric_states", [])
        if isinstance(item, dict)
    ]
    stage5 = private_status.get("stage5_financial_model") if isinstance(private_status, dict) else None
    if isinstance(stage5, dict):
        stage5_source = stage5.get("source") if isinstance(stage5.get("source"), dict) else {}
        surface_hashes = stage5.get("surface_payload_hashes") if isinstance(stage5.get("surface_payload_hashes"), dict) else {}
        for item in stage5.get("components", []):
            if not isinstance(item, dict):
                continue
            metric_id = str(item.get("metric_id") or "")
            event_key = _STAGE5_EVENT_BINDINGS.get(metric_id)
            if event_key:
                event_contract = dict(event_metrics.get(event_key) or {})
                event_contract["metric_event_key"] = event_key
            elif metric_id == "investment_funding_outflow_cny":
                event_contract = {
                    "metric_event_key": "investment_funding",
                    "economic_event_count": 0,
                    "economic_event_set_hash": _canonical_hash([]),
                    "maximum_count_per_economic_event": 1,
                }
            else:
                event_contract = {}
            enriched = {
                **item,
                "formula_hash": formula_by_id.get(str(item.get("formula_id") or ""), {}).get("formula_hash"),
                "parameter_hash": parameter_hash,
                "data_hash": stage5_source.get("source_snapshot_hash"),
                "read_model_hash": surface_hashes.get("report"),
                "source_ids": [stage5_source.get("source_id")] if stage5_source.get("source_id") else [],
                "coverage_start": stage5_source.get("coverage_start"),
                "coverage_end": stage5_source.get("coverage_end"),
            }
            metrics.append(
                _metric_record(
                    enriched,
                    formula_by_id=formula_by_id,
                    parameter_hash=parameter_hash,
                    event_contract=event_contract,
                    fallback_read_model_hash=str(surface_hashes.get("report") or "") or None,
                    source_range=stage5_source,
                )
            )
    return _metric_payload(metrics, private_runtime_only=read_model_status is None)


def build_stage7_phase73_payload(
    project_root: Path | str | None = None,
    *,
    read_model_status: Mapping[str, Any] | None = None,
    operational_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pfi_root = Path(project_root).expanduser().resolve() if project_root is not None else Path(__file__).resolve().parents[4]
    parameter_center = _build_parameter_center(pfi_root)
    run = None
    if operational_ledger is not None:
        interconnection = _operational_interconnection_map(
            _blocked_interconnection(), operational_ledger
        )
    elif read_model_status is None:
        run = run_phase33_real_reconciliation(
            pfi_root,
            observed_at=_source_observed_at(pfi_root.parent),
        )
        interconnection = _build_interconnection_map(run)
    else:
        interconnection = _blocked_interconnection()
    metric_drilldown = _build_metric_drilldowns(
        pfi_root,
        run,
        read_model_status=read_model_status,
        operational_ledger=operational_ledger,
    )
    operational_fail_closed_ready = (
        operational_ledger is not None
        and parameter_center["status"] == "ready"
        and interconnection.get("status") == "blocked"
        and interconnection.get("economic_event_adapter_ready") is False
        and metric_drilldown.get("status") == "blocked"
        and metric_drilldown.get("metric_count") == len(_OPERATIONAL_METRIC_FORMULAS)
        and metric_drilldown.get("non_ready_false_zero_count") == 0
        and len(metric_drilldown.get("metrics", [])) == len(_OPERATIONAL_METRIC_FORMULAS)
        and all(
            item.get("value") is None and bool(item.get("blocking_reason_zh"))
            for item in metric_drilldown.get("metrics", [])
            if isinstance(item, Mapping)
        )
    )
    payload = {
        "schema": "PFIV025Stage7Phase73FormalWorkflowV1",
        "version": VERSION,
        "stage": 7,
        "phase": "7.3",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "status": "ready" if (operational_fail_closed_ready or (
            parameter_center["status"] == "ready"
            and interconnection["status"] == "ready"
            and metric_drilldown["status"] == "ready"
        )) else "blocked",
        "calculation_status": "blocked" if operational_fail_closed_ready else metric_drilldown["status"],
        "parameter_center": parameter_center,
        "interconnection_map": interconnection,
        "metric_drilldown": metric_drilldown,
        "formal_routes": [
            "/settings/parameters",
            "/data/interconnection",
            "/reports/metric-drilldown",
        ],
        "sidecar_html_used": False,
        "finder_used": False,
        "external_network_used": False,
        "write_operation_count": 0,
        "contains_private_values": read_model_status is None or operational_ledger is not None,
        "evidence_must_redact_metric_values": True,
        "whole_stage_review_started": False,
        "next_phase_started": False,
    }
    payload["projection_hash"] = _canonical_hash(payload)
    return payload


def build_stage7_phase73_evidence_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metric_drilldown") if isinstance(payload.get("metric_drilldown"), Mapping) else {}
    interconnection = payload.get("interconnection_map") if isinstance(payload.get("interconnection_map"), Mapping) else {}
    parameters = payload.get("parameter_center") if isinstance(payload.get("parameter_center"), Mapping) else {}
    metric_rows = metrics.get("metrics") if isinstance(metrics.get("metrics"), list) else []

    def required_values_valid(item: Mapping[str, Any]) -> bool:
        hashes = ("formula_hash", "parameter_hash")
        if not all(
            isinstance(item.get(field), str) and str(item.get(field)).startswith("sha256:")
            for field in hashes
        ):
            return False
        data_range = item.get("data_range")
        if not isinstance(data_range, Mapping) or not isinstance(item.get("event_lineage"), Mapping):
            return False
        if item.get("status") in {"ready", "confirmed_zero"}:
            return (
                isinstance(item.get("data_hash"), str)
                and str(item.get("data_hash")).startswith("sha256:")
                and bool(item.get("source_ids"))
                and bool(data_range.get("start"))
                and bool(data_range.get("end"))
            )
        if item.get("status") == "blocked_economic_event_adapter":
            return (
                item.get("value") is None
                and bool(item.get("blocking_reason_zh"))
                and all(
                    isinstance(item.get(field), str) and str(item.get(field)).startswith("sha256:")
                    for field in ("data_hash", "read_model_hash")
                )
                and bool(item.get("source_ids"))
            )
        if item.get("status") == "blocked_source_dependency":
            return (
                item.get("value") is None
                and bool(item.get("blocking_reason_zh"))
                and item.get("data_hash") is None
                and item.get("read_model_hash") is None
                and not item.get("source_ids")
            )
        return item.get("value") is None and bool(item.get("blocking_reason_zh"))

    return {
        "schema": "PFIV025Stage7Phase73EvidenceProjectionV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "pass" if payload.get("status") == "ready" else "fail",
        "formal_routes": list(payload.get("formal_routes") or []),
        "parameter_center": {
            "status": parameters.get("status"),
            "parameter_hash": parameters.get("parameter_hash"),
            "formula_registry_hash": parameters.get("formula_registry_hash"),
            "domain_count": parameters.get("domain_count"),
            "parameter_count": parameters.get("parameter_count"),
            "formula_count": parameters.get("formula_count"),
        },
        "interconnection_map": {
            "status": interconnection.get("status"),
            "data_hash": interconnection.get("data_hash"),
            "read_model_hash": interconnection.get("read_model_hash"),
            "node_count": len(interconnection.get("nodes") or []),
            "edge_count": len(interconnection.get("edges") or []),
            "lineage_complete_count": interconnection.get("lineage_complete_count"),
            "lineage_missing_count": interconnection.get("lineage_missing_count"),
        },
        "metric_drilldown": {
            "status": metrics.get("status"),
            "metric_count": metrics.get("metric_count"),
            "metric_ids": list(metrics.get("metric_ids") or []),
            "non_ready_false_zero_count": metrics.get("non_ready_false_zero_count"),
            "all_required_fields_present": all(
                all(field in item for field in metrics.get("required_fields", []))
                for item in metric_rows
                if isinstance(item, dict)
            ),
            "required_field_values_valid": bool(metric_rows) and all(
                required_values_valid(item)
                for item in metric_rows
                if isinstance(item, Mapping)
            ),
            "drilldown_hashes": [item.get("drilldown_hash") for item in metric_rows if isinstance(item, dict)],
        },
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "sidecar_html_used": bool(payload.get("sidecar_html_used")),
        "write_operation_count": int(payload.get("write_operation_count") or 0),
    }
