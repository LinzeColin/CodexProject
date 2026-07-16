"""PFI v0.2.5 Stage 9.2 truthful report analysis and validation views.

The builder consumes only tracked, redacted aggregate evidence from accepted
earlier stages.  It never reads raw financial rows or a database and it never
publishes financial amounts.  Missing sources, lineage, scores or ground truth
remain explicit blocked states instead of being converted into conclusions.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from pfi_os.application.reports.contracts import (
    canonical_hash,
    derive_report_status,
    file_hash,
    validate_phase91_report_pack,
)


VERSION = "v0.2.5"
STAGE = 9
PHASE = "9.2"
PHASE_ID = "V025-S9-P9.2"
TASK_IDS = ("S9-P2-T1", "S9-P2-T2", "S9-P2-T3", "S9-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE9-WHOLE-REVIEW"
FINANCIAL_REPORT_TYPES = (
    "net_worth",
    "cash",
    "investment",
    "consumption",
    "cashflow",
)
FORMULA_IDS = tuple(f"FORM-PFI-{number:03d}" for number in range(15, 21))

PFI_ROOT = Path(__file__).resolve().parents[4]
PHASE91_MANIFEST_RELATIVE = Path(
    "reports/pfi_v025/stage_9/phase_9_1/report_manifest.json"
)
SOURCE_MANIFEST_RELATIVE = Path(
    "reports/pfi_v025/stage_2/phase_2_1/source_manifest.json"
)
READ_MODEL_STATUS_RELATIVE = Path(
    "reports/pfi_v025/stage_4/phase_4_3/read_model_status.json"
)
WORKFLOW_VALIDATION_RELATIVE = Path(
    "reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json"
)
MODEL_CARD_RELATIVE = Path(
    "reports/pfi_v025/stage_5/phase_5_3/model_validation_card.json"
)
SENSITIVITY_RELATIVE = Path(
    "reports/pfi_v025/stage_5/phase_5_3/sensitivity_results.json"
)
INVARIANT_RELATIVE = Path(
    "reports/pfi_v025/stage_5/phase_5_3/invariant_results.json"
)
METAMORPHIC_RELATIVE = Path(
    "reports/pfi_v025/stage_5/phase_5_3/metamorphic_results.json"
)
FORMULA_REGISTRY_RELATIVE = Path("config/formulas/v025_formula_registry.json")
PARAMETER_CATALOG_RELATIVE = Path("config/pfi_parameters.yaml")
COMPLETENESS_RULES_RELATIVE = Path(
    "config/reports/v025_completeness_rules.json"
)
BUILDER_RELATIVE = Path("src/pfi_os/application/analysis/report_analysis.py")

_REPORT_TITLES = {
    "net_worth": "净资产报告",
    "cash": "现金报告",
    "investment": "投资报告",
    "consumption": "消费报告",
    "cashflow": "现金流报告",
}
_REPORT_FORMULAS = {
    "net_worth": ("FORM-PFI-016",),
    "cash": ("FORM-PFI-016", "FORM-PFI-019"),
    "investment": ("FORM-PFI-017", "FORM-PFI-018"),
    "consumption": ("FORM-PFI-015", "FORM-PFI-020"),
    "cashflow": ("FORM-PFI-019", "FORM-PFI-015"),
}
_FORMULA_REPORTS = {
    formula_id: tuple(
        report_type
        for report_type, formula_ids in _REPORT_FORMULAS.items()
        if formula_id in formula_ids
    )
    for formula_id in FORMULA_IDS
}
_FORMULA_SENSITIVITY = {
    "FORM-PFI-015": ("SENS-MONEY-QUANTUM",),
    "FORM-PFI-016": ("SENS-MONEY-QUANTUM",),
    "FORM-PFI-017": ("SENS-MONEY-QUANTUM",),
    "FORM-PFI-018": ("SENS-XIRR-POLICY",),
    "FORM-PFI-019": ("SENS-CASHFLOW-WINDOW",),
    "FORM-PFI-020": ("SENS-CLASSIFICATION-THRESHOLD",),
}
_REVIEW_ROUTE_BY_SOURCE = {
    "SRC-TRANSACTIONS-ALIPAY": "/data/sources",
    "SRC-ACCOUNT-BALANCES": "/accounts/reconcile",
    "SRC-LIABILITIES": "/accounts/reconcile",
    "SRC-HOLDINGS": "/investment/holdings",
    "SRC-MARKET-PRICES": "/investment/holdings",
    "SRC-FX-SNAPSHOT": "/settings/data-system",
}
_ACTION_BY_SOURCE = {
    "SRC-TRANSACTIONS-ALIPAY": "复核交易来源覆盖与待复核队列",
    "SRC-ACCOUNT-BALANCES": "挂接并复核账户余额快照",
    "SRC-LIABILITIES": "挂接并复核负债余额快照",
    "SRC-HOLDINGS": "挂接并复核真实持仓快照",
    "SRC-MARKET-PRICES": "挂接并复核估值价格快照",
    "SRC-FX-SNAPSHOT": "挂接并复核生产 FX snapshot",
}
_REPORT_REVIEW_IDS = {
    "net_worth": (
        "REVIEW-SRC-ACCOUNT-BALANCES",
        "REVIEW-SRC-LIABILITIES",
        "REVIEW-SRC-HOLDINGS",
        "REVIEW-SRC-MARKET-PRICES",
        "REVIEW-SRC-FX-SNAPSHOT",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    ),
    "cash": (
        "REVIEW-SRC-ACCOUNT-BALANCES",
        "REVIEW-SRC-LIABILITIES",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    ),
    "investment": (
        "REVIEW-SRC-HOLDINGS",
        "REVIEW-SRC-MARKET-PRICES",
        "REVIEW-SRC-FX-SNAPSHOT",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    ),
    "consumption": (
        "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    ),
    "cashflow": (
        "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    ),
}
_COMPONENT_METRIC_IDS = {
    "net_worth": (
        "net_worth_cny",
        "cash_balance_cny",
        "investment_market_value_cny",
        "liabilities_cny",
    ),
    "cash": ("cash_balance_cny", "liabilities_cny"),
    "investment": (
        "investment_market_value_cny",
        "investment_cost_basis_cny",
        "investment_unrealized_pnl_cny",
    ),
    "consumption": (
        "total_consumption_outflow_cny",
        "living_consumption_cny",
        "investment_funding_outflow_cny",
        "investment_allocation_amount_cny",
    ),
    "cashflow": ("external_inflow_cny", "external_outflow_cny", "net_cashflow_cny"),
}


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _assert_public_redacted(label: str, payload: Mapping[str, Any]) -> None:
    private_flag = payload.get("contains_private_values")
    if private_flag not in (None, False):
        raise ValueError(f"{label} contains private values")
    financial_values_emitted = payload.get("financial_values_emitted")
    if financial_values_emitted not in (None, 0):
        raise ValueError(f"{label} emitted financial values")


def build_phase92_contract() -> dict[str, object]:
    return {
        "schema": "PFIV025Stage9Phase92ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "risk_tier": "T3_FINANCIAL_MODEL_VALIDATION_UI",
        "current_phase_only": True,
        "phase_9_1_required": True,
        "phase_9_2_analysis_implementation": True,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
        "automatic_trading_allowed": False,
        "financial_fixture_acceptance_allowed": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def _dependency_states(
    source_manifest: Mapping[str, Any],
    workflow_validation: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for source in source_manifest.get("sources", []):
        if not isinstance(source, Mapping):
            raise ValueError("source manifest entries must be objects")
        source_id = str(source.get("source_id") or "")
        if not source_id or source_id in states:
            raise ValueError("source IDs must be non-empty and unique")
        states[source_id] = {
            "status": str(source.get("status") or "not_loaded"),
        }
    interconnection = workflow_validation["workflows"]["metric_lineage"][
        "interconnection_map"
    ]
    states["economic_event_adapter"] = {
        "status": (
            "ready"
            if interconnection.get("status") == "ready"
            and interconnection.get("lineage_missing_count") == 0
            else "blocked"
        )
    }
    states["financial_analysis_implementation"] = {"status": "ready"}
    return states


def _source_review_index(
    source_manifest: Mapping[str, Any],
    workflow_validation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    by_id = {
        str(row["source_id"]): row
        for row in source_manifest["sources"]
        if isinstance(row, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for source_id in _REVIEW_ROUTE_BY_SOURCE:
        source = by_id[source_id]
        coverage = source.get("coverage")
        rows.append(
            {
                "review_id": f"REVIEW-{source_id}",
                "issue_type": "source_dependency",
                "source_id": source_id,
                "label_zh": str(source.get("label") or source_id),
                "status": str(source.get("status") or "not_loaded"),
                "coverage": deepcopy(coverage) if isinstance(coverage, Mapping) else {"start": None, "end": None},
                "record_count": source.get("record_count"),
                "as_of": source.get("as_of"),
                "blocking_reason_zh": source.get("blocking_reason_zh"),
                "resolution_task_ids": list(source.get("resolution_task_ids") or []),
                "review_route": _REVIEW_ROUTE_BY_SOURCE[source_id],
                "action_label_zh": _ACTION_BY_SOURCE[source_id],
                "contains_private_values": False,
            }
        )
    interconnection = workflow_validation["workflows"]["metric_lineage"][
        "interconnection_map"
    ]
    rows.append(
        {
            "review_id": "REVIEW-ECONOMIC-EVENT-ADAPTER",
            "issue_type": "lineage_dependency",
            "source_id": "economic_event_adapter",
            "label_zh": "Economic Event lineage",
            "status": str(interconnection.get("status") or "blocked"),
            "coverage": {"start": None, "end": None},
            "record_count": int(interconnection.get("lineage_complete_count") or 0),
            "as_of": None,
            "blocking_reason_zh": (
                f"lineage complete={int(interconnection.get('lineage_complete_count') or 0)}、"
                f"missing={int(interconnection.get('lineage_missing_count') or 0)}；"
                "未完整前不能生成确定性财务结论。"
            ),
            "resolution_task_ids": ["S9-P2-T4"],
            "review_route": "/data/interconnection",
            "action_label_zh": "复核 Economic Event 映射与缺失 lineage",
            "contains_private_values": False,
        }
    )
    return rows


def _sensitivity_previews(sensitivity: Mapping[str, Any]) -> list[dict[str, Any]]:
    windows = []
    for row in sensitivity["cashflow_window_sensitivity"]:
        windows.append(
            {
                "window_days": int(row["window_days"]),
                "coverage_start": str(row["coverage_start"]),
                "coverage_end": str(row["coverage_end"]),
                "record_count": int(row["record_count"]),
                "incremental_record_count": int(row["incremental_record_count"]),
                "financial_fingerprint": str(row["financial_value_fingerprint"]),
            }
        )
    return [
        {
            "sensitivity_id": "SENS-CASHFLOW-WINDOW",
            "title_zh": "现金流窗口敏感性",
            "formula_ids": ["FORM-PFI-019"],
            "parameter_ids": ["PARAM-PFI-086"],
            "status": "partial_ready_nonfinancial_impact",
            "impact_visible": True,
            "impact_summary_zh": "窗口增大时覆盖记录数单调不减；可比较覆盖变化与指纹。",
            "observations": windows,
            "limitation_zh": "金额影响不在公开证据中输出；窗口结果只证明覆盖与计算指纹变化。",
            "review_route": "/reports/metric-drilldown?formula=FORM-PFI-019",
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
        {
            "sensitivity_id": "SENS-CLASSIFICATION-THRESHOLD",
            "title_zh": "分类阈值敏感性",
            "formula_ids": ["FORM-PFI-020"],
            "parameter_ids": ["PARAM-PFI-087"],
            "status": str(sensitivity["classification_threshold_sensitivity"]["status"]),
            "impact_visible": False,
            "impact_summary_zh": "缺少逐笔 score vector 与 ground-truth labels，调整影响不可验证。",
            "observations": [],
            "limitation_zh": str(sensitivity["classification_threshold_sensitivity"]["reason"]),
            "review_route": "/settings/parameters?parameter=PARAM-PFI-087",
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
        {
            "sensitivity_id": "SENS-XIRR-POLICY",
            "title_zh": "XIRR 参数敏感性",
            "formula_ids": ["FORM-PFI-018"],
            "parameter_ids": [
                "PARAM-PFI-089",
                "PARAM-PFI-090",
                "PARAM-PFI-091",
                "PARAM-PFI-092",
            ],
            "status": str(sensitivity["xirr_parameter_sensitivity"]["status"]),
            "impact_visible": False,
            "impact_summary_zh": "缺完整 dated funding/return/terminal-value chain，不预演 XIRR 数值。",
            "observations": [],
            "limitation_zh": str(sensitivity["xirr_parameter_sensitivity"]["reason"]),
            "review_route": "/reports/metric-drilldown?formula=FORM-PFI-018",
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
        {
            "sensitivity_id": "SENS-MONEY-QUANTUM",
            "title_zh": "金额精度与核心财务边界",
            "formula_ids": ["FORM-PFI-015", "FORM-PFI-016", "FORM-PFI-017"],
            "parameter_ids": ["PARAM-PFI-081"],
            "status": "blocked_missing_required_sources",
            "impact_visible": False,
            "impact_summary_zh": "余额、持仓、价格与 FX 未加载，不生成金额精度调整影响。",
            "observations": [],
            "limitation_zh": "当前只保留 Decimal/no-float contract；真实数值影响等待来源 ready。",
            "review_route": "/settings/parameters?parameter=PARAM-PFI-081",
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
    ]


def _formula_drilldowns(
    registry: Mapping[str, Any],
    model_card: Mapping[str, Any],
) -> list[dict[str, Any]]:
    formulas = {
        str(row["formula_id"]): row
        for row in registry["formulas"]
        if isinstance(row, Mapping)
    }
    validations = {
        str(row["formula_id"]): row
        for row in model_card["formula_validation"]
        if isinstance(row, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for formula_id in FORMULA_IDS:
        formula = formulas[formula_id]
        validation = validations[formula_id]
        if formula.get("formula_hash") != validation.get("formula_hash"):
            raise ValueError(f"{formula_id} validation hash differs from registry")
        rows.append(
            {
                "formula_id": formula_id,
                "formula_version": str(formula["version"]),
                "formula_hash": str(formula["formula_hash"]),
                "label_zh": str(formula["label_zh"]),
                "definition_zh": str(formula["definition_zh"]),
                "inputs": list(formula["inputs"]),
                "outputs": list(formula["outputs"]),
                "unit": str(formula["unit"]),
                "parameters": list(formula["parameters"]),
                "dependencies": list(formula["dependencies"]),
                "boundaries_zh": list(formula["boundaries_zh"]),
                "validation_status": str(validation["status"]),
                "limitation": str(validation["limitation"]),
                "report_types": list(_FORMULA_REPORTS[formula_id]),
                "sensitivity_ids": list(_FORMULA_SENSITIVITY[formula_id]),
                "review_route": f"/reports/metric-drilldown?formula={formula_id}",
                "financial_values_emitted": 0,
                "contains_private_values": False,
            }
        )
    return rows


def _calculable_components(
    report_type: str,
    model_card: Mapping[str, Any],
    sensitivity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if report_type == "consumption":
        source = model_card["input_snapshot"]
        return [
            {
                "component_id": "real_source_partition",
                "status": "partial",
                "input_record_count": int(source["input_record_count"]),
                "published_record_count": int(source["published_record_count"]),
                "review_queue_record_count": int(source["review_queue_record_count"]),
                "silent_drop_count": 0,
                "coverage_start": str(source["coverage_start"]),
                "coverage_end": str(source["coverage_end"]),
            }
        ]
    if report_type == "cashflow":
        return [
            {
                "component_id": "seven_window_coverage",
                "status": "partial",
                "windows": [
                    {
                        "window_days": int(row["window_days"]),
                        "coverage_start": str(row["coverage_start"]),
                        "coverage_end": str(row["coverage_end"]),
                        "record_count": int(row["record_count"]),
                        "incremental_record_count": int(row["incremental_record_count"]),
                        "financial_fingerprint": str(row["financial_value_fingerprint"]),
                    }
                    for row in sensitivity["cashflow_window_sensitivity"]
                ],
            }
        ]
    return []


def _build_reports(
    base_manifest: Mapping[str, Any],
    rules: Mapping[str, Any],
    states: Mapping[str, Mapping[str, Any]],
    registry: Mapping[str, Any],
    model_card: Mapping[str, Any],
    sensitivity: Mapping[str, Any],
    hashes: Mapping[str, str],
    *,
    observed_at: str,
) -> list[dict[str, Any]]:
    base_by_type = {
        str(row["report_type"]): row
        for row in base_manifest["reports"]
        if isinstance(row, Mapping)
    }
    registry_by_id = {
        str(row["formula_id"]): row
        for row in registry["formulas"]
        if isinstance(row, Mapping)
    }
    reports: list[dict[str, Any]] = []
    for report_type in FINANCIAL_REPORT_TYPES:
        base = base_by_type[report_type]
        status, partial_scope = derive_report_status(report_type, states, rules)
        if status == "partial":
            conclusions = [
                {
                    "scope": "source_coverage_only",
                    "statement_zh": (
                        "当前只确认真实交易来源覆盖、发布/待复核分区或窗口记录变化；"
                        "lineage 未完整，因此不生成金额或确定性财务结论。"
                    ),
                    "evidence_refs": [
                        "PFI/reports/pfi_v025/stage_5/phase_5_3/model_validation_card.json",
                        "PFI/reports/pfi_v025/stage_5/phase_5_3/sensitivity_results.json",
                    ],
                }
            ]
            status_statement = "部分可算：只展示真实来源覆盖与非金额敏感性。"
        else:
            conclusions = []
            status_statement = "关键真实输入未 ready；只展示公式、限制与复核入口。"
        formula_ids = list(_REPORT_FORMULAS[report_type])
        parameter_ids = sorted(
            {
                str(parameter_id)
                for formula_id in formula_ids
                for parameter_id in registry_by_id[formula_id]["parameters"]
            }
        )
        review_ids = list(_REPORT_REVIEW_IDS[report_type])
        report: dict[str, Any] = {
            "schema": "PFIV025Stage9Phase92FinancialReportV1",
            "report_id": str(base["report_id"]),
            "report_type": report_type,
            "title_zh": _REPORT_TITLES[report_type],
            "status": status,
            "status_statement_zh": status_statement,
            "version": VERSION,
            "analysis_version": "pfi-v025-stage9-phase92-analysis-v1",
            "generated_at": observed_at,
            "report_as_of": base["report_as_of"],
            "data_range": deepcopy(base["data_range"]),
            "sample_counts": deepcopy(base["sample_counts"]),
            "coverage": deepcopy(base["coverage"]),
            "base_snapshot_hash": str(base["snapshot_hash"]),
            "hashes": dict(hashes),
            "analysis_implementation_status": "ready",
            "formula_ids": formula_ids,
            "parameter_ids": parameter_ids,
            "component_metric_ids": list(_COMPONENT_METRIC_IDS[report_type]),
            "calculable_components": _calculable_components(
                report_type, model_card, sensitivity
            ),
            "conclusions": conclusions,
            "scope_explanation_zh": (
                "消费总流出是用户定义的 gross activity 口径；生活消费、投资资金流出与"
                "投资域内配置必须拆分展示，投资活动不等于净资产损失。"
                if report_type == "consumption"
                else "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。"
            ),
            "model_validation_status": str(model_card["status"]),
            "limitations": list(base["limitations"]) + [
                "Phase 9.2 不生成建议、交易动作或 Phase 9.3 导出。",
                "公开 Evidence 不保存财务金额；本机私有运行时金额仍受同一 hash 与完整度门禁。",
            ],
            "counter_evidence": list(model_card["counter_evidence"]),
            "partial_scope": partial_scope,
            "review_entry_ids": review_ids,
            "anomaly_ids": list(review_ids),
            "financial_values_emitted": 0,
            "contains_private_values": False,
            "immutable": True,
        }
        report["snapshot_hash"] = canonical_hash(report)
        reports.append(report)
    return reports


def _model_validation_card(
    model_card: Mapping[str, Any],
    invariant: Mapping[str, Any],
    metamorphic: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage9Phase92ModelValidationCardV1",
        "model_id": str(model_card["model_id"]),
        "model_version": str(model_card["model_version"]),
        "status": str(model_card["status"]),
        "invariant_status": str(invariant["status"]),
        "metamorphic_status": str(metamorphic["status"]),
        "formula_validation": deepcopy(model_card["formula_validation"]),
        "coverage_dimensions": deepcopy(model_card["coverage_dimensions"]),
        "historical_out_of_sample_validation": deepcopy(
            model_card["historical_out_of_sample_validation"]
        ),
        "limitations": list(model_card["limitations"]),
        "counter_evidence": list(model_card["counter_evidence"]),
        "report_types": list(FINANCIAL_REPORT_TYPES),
        "formal_ui_contract_embedded": True,
        "automatic_trading_allowed": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "production_accepted": False,
    }


def _ui_contract(
    reports: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    sensitivity: list[dict[str, Any]],
    model_cards: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    hashes: Mapping[str, str],
) -> dict[str, Any]:
    status_zh = {"complete": "完整", "partial": "部分可算", "blocked": "已阻断"}
    return {
        "schema": "PFIV025Stage9Phase92UIContractV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "title_zh": "财务分析与模型验证",
        "subtitle_zh": "只展示当前可计算内容；公式、参数影响、模型限制与来源复核入口保持可见。",
        "report_count": len(reports),
        "report_cards": [
            {
                "report_id": row["report_id"],
                "report_type": row["report_type"],
                "title_zh": row["title_zh"],
                "status": row["status"],
                "status_zh": status_zh[row["status"]],
                "status_statement_zh": row["status_statement_zh"],
                "formula_ids": row["formula_ids"],
                "parameter_ids": row["parameter_ids"],
                "data_range": row["data_range"],
                "transaction_record_count": row["sample_counts"]["transaction_record_count"],
                "review_entry_ids": row["review_entry_ids"],
                "primary_review_route": next(
                    review["review_route"]
                    for review in reviews
                    if review["review_id"] == row["review_entry_ids"][0]
                ),
                "scope_explanation_zh": row["scope_explanation_zh"],
                "financial_values_emitted": 0,
            }
            for row in reports
        ],
        "formula_cards": [
            {
                "formula_id": row["formula_id"],
                "label_zh": row["label_zh"],
                "validation_status": row["validation_status"],
                "parameters": row["parameters"],
                "report_types": row["report_types"],
                "limitation": row["limitation"],
                "review_route": row["review_route"],
            }
            for row in formulas
        ],
        "sensitivity_cards": [
            {
                "sensitivity_id": row["sensitivity_id"],
                "title_zh": row["title_zh"],
                "status": row["status"],
                "parameter_ids": row["parameter_ids"],
                "impact_visible": row["impact_visible"],
                "impact_summary_zh": row["impact_summary_zh"],
                "observation_count": len(row["observations"]),
                "review_route": row["review_route"],
            }
            for row in sensitivity
        ],
        "model_cards": [
            {
                "model_id": row["model_id"],
                "model_version": row["model_version"],
                "status": row["status"],
                "invariant_status": row["invariant_status"],
                "metamorphic_status": row["metamorphic_status"],
                "historical_out_of_sample_status": row[
                    "historical_out_of_sample_validation"
                ]["status"],
                "limitation_count": len(row["limitations"]),
                "counter_evidence_count": len(row["counter_evidence"]),
            }
            for row in model_cards
        ],
        "review_cards": [
            {
                "review_id": row["review_id"],
                "label_zh": row["label_zh"],
                "status": row["status"],
                "action_label_zh": row["action_label_zh"],
                "review_route": row["review_route"],
            }
            for row in reviews
        ],
        "hashes": {
            key: hashes[key]
            for key in (
                "data_manifest_hash",
                "read_model_hash",
                "formula_registry_hash",
                "parameter_hash",
                "base_report_manifest_hash",
            )
        },
        "phase_9_3_started": False,
        "automatic_trading_allowed": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def build_phase92_analysis_pack(
    pfi_root: Path | str | None = None,
    *,
    observed_at: str,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    base_manifest = _json_object(root / PHASE91_MANIFEST_RELATIVE)
    if validate_phase91_report_pack(base_manifest, pfi_root=root)["status"] != "pass":
        raise ValueError("Phase 9.1 report manifest is not current and passing")
    source_manifest = _json_object(root / SOURCE_MANIFEST_RELATIVE)
    read_model = _json_object(root / READ_MODEL_STATUS_RELATIVE)
    workflow = _json_object(root / WORKFLOW_VALIDATION_RELATIVE)
    model_card = _json_object(root / MODEL_CARD_RELATIVE)
    sensitivity = _json_object(root / SENSITIVITY_RELATIVE)
    invariant = _json_object(root / INVARIANT_RELATIVE)
    metamorphic = _json_object(root / METAMORPHIC_RELATIVE)
    registry = _json_object(root / FORMULA_REGISTRY_RELATIVE)
    rules = _json_object(root / COMPLETENESS_RULES_RELATIVE)
    for label, payload in (
        ("source manifest", source_manifest),
        ("read model", read_model),
        ("workflow validation", workflow),
        ("model card", model_card),
        ("sensitivity", sensitivity),
        ("invariant", invariant),
        ("metamorphic", metamorphic),
    ):
        _assert_public_redacted(label, payload)
    if workflow.get("status") != "pass":
        raise ValueError("Stage 7 workflow validation is not passing")
    if set(FORMULA_IDS) != {
        str(row.get("formula_id")) for row in model_card["formula_validation"]
    }:
        raise ValueError("model card formula set is incomplete")
    base_hashes = base_manifest["hashes"]
    if base_hashes["formula_registry_hash"] != file_hash(root / FORMULA_REGISTRY_RELATIVE):
        raise ValueError("formula registry differs from Phase 9.1 binding")
    if base_hashes["parameter_hash"] != file_hash(root / PARAMETER_CATALOG_RELATIVE):
        raise ValueError("parameter catalog differs from Phase 9.1 binding")
    hashes = {
        **dict(base_hashes),
        "base_report_manifest_hash": str(base_manifest["manifest_hash"]),
        "model_validation_card_hash": file_hash(root / MODEL_CARD_RELATIVE),
        "sensitivity_results_hash": file_hash(root / SENSITIVITY_RELATIVE),
        "invariant_results_hash": file_hash(root / INVARIANT_RELATIVE),
        "metamorphic_results_hash": file_hash(root / METAMORPHIC_RELATIVE),
        "analysis_builder_hash": file_hash(root / BUILDER_RELATIVE),
    }
    states = _dependency_states(source_manifest, workflow)
    reviews = _source_review_index(source_manifest, workflow)
    formula_rows = _formula_drilldowns(registry, model_card)
    sensitivity_rows = _sensitivity_previews(sensitivity)
    model_rows = [_model_validation_card(model_card, invariant, metamorphic)]
    reports = _build_reports(
        base_manifest,
        rules,
        states,
        registry,
        model_card,
        sensitivity,
        hashes,
        observed_at=observed_at,
    )
    pack: dict[str, Any] = {
        "schema": "PFIV025Stage9Phase92AnalysisPackV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "risk_tier": "T3_FINANCIAL_MODEL_VALIDATION_UI",
        "status": "candidate_pass",
        "observed_at": observed_at,
        "analysis_implementation_status": "ready",
        "base_report_manifest_hash": str(base_manifest["manifest_hash"]),
        "hashes": hashes,
        "report_set": reports,
        "formula_drilldowns": formula_rows,
        "sensitivity_previews": sensitivity_rows,
        "model_validation_cards": model_rows,
        "source_review_index": reviews,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
        "automatic_trading_allowed": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
    }
    pack["ui_contract"] = _ui_contract(
        reports,
        formula_rows,
        sensitivity_rows,
        model_rows,
        reviews,
        hashes,
    )
    pack["pack_hash"] = canonical_hash(pack)
    return pack


def _contains_financial_values(payload: object) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return bool(
        re.search(r"\bCNY\s+-?[0-9]", serialized)
        or re.search(r'"(?:value|amount|financial_value)"\s*:', serialized)
        or re.search(r'"[a-z0-9_]+_cny"\s*:', serialized)
    )


def validate_phase92_analysis_pack(
    pack: Mapping[str, Any],
    *,
    pfi_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    errors: list[str] = []
    observed_at = pack.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at:
        errors.append("observed_at is required")
        rebuilt: dict[str, Any] | None = None
    else:
        try:
            rebuilt = build_phase92_analysis_pack(root, observed_at=observed_at)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            rebuilt = None
            errors.append(f"current-input rebuild failed: {type(exc).__name__}")
    if rebuilt is not None and dict(pack) != rebuilt:
        errors.append("analysis pack differs from current-input rebuild")
    reports = pack.get("report_set")
    formulas = pack.get("formula_drilldowns")
    previews = pack.get("sensitivity_previews")
    model_cards = pack.get("model_validation_cards")
    reviews = pack.get("source_review_index")
    if not isinstance(reports, list) or len(reports) != 5:
        reports = []
        errors.append("report set must contain five reports")
    if not isinstance(formulas, list) or len(formulas) != 6:
        formulas = []
        errors.append("formula drilldown set must contain six rows")
    if not isinstance(previews, list) or len(previews) != 4:
        previews = []
        errors.append("sensitivity preview set must contain four rows")
    if not isinstance(model_cards, list) or len(model_cards) != 1:
        model_cards = []
        errors.append("model validation card set must contain one row")
    if not isinstance(reviews, list) or len(reviews) != 7:
        reviews = []
        errors.append("source review index must contain seven rows")
    if _contains_financial_values(pack):
        errors.append("public analysis pack contains a financial value")
    if pack.get("financial_values_emitted") != 0:
        errors.append("financial values emitted")
    if pack.get("contains_private_values") is not False:
        errors.append("private values emitted")
    if pack.get("phase_9_3_started") is not False:
        errors.append("Phase 9.3 scope leak")
    if pack.get("automatic_trading_allowed") is not False:
        errors.append("automatic trading is forbidden")
    expected_hashes = pack.get("hashes")
    cross_hashes = bool(reports) and isinstance(expected_hashes, Mapping) and all(
        isinstance(row, Mapping) and row.get("hashes") == expected_hashes
        for row in reports
    )
    if not cross_hashes:
        errors.append("cross-report hashes differ")
    return {
        "schema": "PFIV025Stage9Phase92AnalysisValidationV1",
        "phase_id": PHASE_ID,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "report_count": len(reports),
        "formula_drilldown_count": len(formulas),
        "sensitivity_preview_count": len(previews),
        "model_validation_card_count": len(model_cards),
        "source_review_count": len(reviews),
        "cross_report_hashes_consistent": cross_hashes,
        "financial_values_emitted": int(pack.get("financial_values_emitted") or 0),
        "contains_private_values": bool(pack.get("contains_private_values")),
    }
