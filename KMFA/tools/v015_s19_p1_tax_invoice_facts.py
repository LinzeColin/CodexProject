#!/usr/bin/env python3
"""KMFA v1.5 S19-P1 税务与发票事实、匹配和项目税负视图。

本模块只处理公开合成资料。税率必须来自票据或合同事实；未知税率保持
未知。所有金额使用整数分，结果只供内部管理分析，不形成申报或调税动作。
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S19_P1_TAX_INVOICE_FACTS"
ROADMAP_PHASE_ID = "S19-P1"
TASK_ID = "KMFA-V015-S19-P1-TAX-INVOICE-FACTS-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S19-P1-TAX-INVOICE-FACTS"
VERSION = "1.5.0-dev-s19p1"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
POLICY_PATH = Path(__file__).resolve().parents[1] / "config/v015_s19_p1_tax_invoice_policy.json"

COMPANY_FACTORS = {"demo-north": 100, "demo-south": 80, "demo-west": 60}
PERIODS = ("2026-07", "2026-Q2", "2026-H1")
PROJECTS = {
    "PUB-PROJ-001": ("厂房升级项目", "工程实施"),
    "PUB-PROJ-002": ("设备交付项目", "设备服务"),
    "PUB-PROJ-003": ("运维服务项目", "运维咨询"),
}
RATE_LABELS = {600: "6%", 900: "9%", 1300: "13%"}
INCLUSIVE_LABELS = {"INCLUSIVE": "含税", "EXCLUSIVE": "未税", "UNKNOWN": "含税状态待确认"}
STATUS_LABELS = {"ISSUED": "已开具", "RECEIVED": "已收到", "PENDING_CONFIRMATION": "待确认"}
DIRECTION_LABELS = {"OUTPUT": "销项", "INPUT": "进项"}
ANOMALY_LABELS = {
    "UNKNOWN_TAX_RATE": "税率待确认",
    "ENTITY_MISMATCH": "主体不一致",
    "PROJECT_MISMATCH": "项目不一致",
    "PERIOD_MISMATCH": "期间不一致",
    "TAX_RATE_MISMATCH": "税率不一致",
}


class TaxInvoiceError(ValueError):
    """税票事实请求违反 S19-P1 公开演示合同。"""


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p1.source_contract.v1",
        "stage_id": "S19",
        "stage_name_zh": "税务、发票、政策资格与证据准备",
        "stage_goal_zh": "支持税务风险与政策证据准备，不替代申报和专业签字。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "税务与发票事实",
        "task_ids": ["S19P1T01", "S19P1T02", "S19P1T03"],
        "task_names_zh": ["建立销项、进项和税率事实", "实现进销项与合同匹配", "实现项目税负视图"],
        "acceptance_zh": ["税率、含税状态和发票状态明确。", "异常有证据。", "明确只是管理分析。"],
        "stop_conditions_zh": ["未知税率不自动推断。", "不自动做税务调整。", "不得输出正式申报结论。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def load_policy() -> dict[str, Any]:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version", "policy_version", "money_unit", "tax_rate_unit",
        "explicit_demo_tax_rates_bps", "tax_inclusive_states", "invoice_statuses",
        "matching_dimensions", "unknown_tax_rate_action",
        "automatic_tax_adjustment_allowed", "formal_filing_conclusion_allowed",
        "management_analysis_only", "rate_note_zh",
    }
    if not required.issubset(policy):
        raise TaxInvoiceError("tax invoice policy is incomplete")
    if policy["unknown_tax_rate_action"] != "BLOCK_NO_INFERENCE":
        raise TaxInvoiceError("unknown tax rates must remain blocked")
    if policy["automatic_tax_adjustment_allowed"] or policy["formal_filing_conclusion_allowed"]:
        raise TaxInvoiceError("tax adjustment and filing conclusions must remain disabled")
    return policy


def format_money(cents: int | None) -> str:
    if cents is None:
        return "待确认"
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TaxInvoiceError("money must use integer cents")
    sign = "-" if cents < 0 else ""
    yuan, fen = divmod(abs(cents), 100)
    return f"{sign}¥{yuan:,}.{fen:02d}"


def format_rate(rate_bps: int | None) -> str:
    if rate_bps is None:
        return "待确认"
    if isinstance(rate_bps, bool) or not isinstance(rate_bps, int):
        raise TaxInvoiceError("tax rate must use integer basis points")
    return RATE_LABELS.get(rate_bps, f"{rate_bps / 100:.2f}%")


def _scale(cents: int, company_id: str) -> int:
    if company_id not in COMPANY_FACTORS:
        raise TaxInvoiceError("unsupported public company")
    return cents * COMPANY_FACTORS[company_id] // 100


def _mismatch_period(period: str) -> str:
    return {"2026-07": "2026-06", "2026-Q2": "2026-Q1", "2026-H1": "2025-H2"}[period]


def _base_definitions(period: str) -> tuple[dict[str, Any], ...]:
    return (
        {"invoice_id": "TAX-OUT-001", "direction": "OUTPUT", "project_id": "PUB-PROJ-001", "expected_project_id": "PUB-PROJ-001", "net_cents": 100_000_000, "tax_rate_bps": 900, "contract_tax_rate_bps": 900, "tax_inclusive_state": "INCLUSIVE", "invoice_status": "ISSUED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-IN-001", "direction": "INPUT", "project_id": "PUB-PROJ-001", "expected_project_id": "PUB-PROJ-001", "net_cents": 40_000_000, "tax_rate_bps": 1300, "contract_tax_rate_bps": 1300, "tax_inclusive_state": "EXCLUSIVE", "invoice_status": "RECEIVED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-OUT-002", "direction": "OUTPUT", "project_id": "PUB-PROJ-002", "expected_project_id": "PUB-PROJ-002", "net_cents": 60_000_000, "tax_rate_bps": 600, "contract_tax_rate_bps": 600, "tax_inclusive_state": "EXCLUSIVE", "invoice_status": "ISSUED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-IN-002", "direction": "INPUT", "project_id": "PUB-PROJ-002", "expected_project_id": "PUB-PROJ-002", "net_cents": 20_000_000, "tax_rate_bps": 1300, "contract_tax_rate_bps": 1300, "tax_inclusive_state": "INCLUSIVE", "invoice_status": "RECEIVED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-OUT-003", "direction": "OUTPUT", "project_id": "PUB-PROJ-003", "expected_project_id": "PUB-PROJ-003", "net_cents": None, "gross_cents": 30_000_000, "tax_rate_bps": None, "contract_tax_rate_bps": None, "tax_inclusive_state": "UNKNOWN", "invoice_status": "PENDING_CONFIRMATION", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-IN-003", "direction": "INPUT", "project_id": "PUB-PROJ-001", "expected_project_id": "PUB-PROJ-001", "net_cents": 15_000_000, "tax_rate_bps": 900, "contract_tax_rate_bps": 900, "tax_inclusive_state": "EXCLUSIVE", "invoice_status": "RECEIVED", "entity_id": "ENTITY-B", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
        {"invoice_id": "TAX-OUT-004", "direction": "OUTPUT", "project_id": "PUB-PROJ-002", "expected_project_id": "PUB-PROJ-002", "net_cents": 25_000_000, "tax_rate_bps": 600, "contract_tax_rate_bps": 600, "tax_inclusive_state": "INCLUSIVE", "invoice_status": "ISSUED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": _mismatch_period(period), "contract_period": period},
        {"invoice_id": "TAX-IN-004", "direction": "INPUT", "project_id": "PUB-PROJ-003", "expected_project_id": "PUB-PROJ-002", "net_cents": 18_000_000, "tax_rate_bps": 1300, "contract_tax_rate_bps": 900, "tax_inclusive_state": "EXCLUSIVE", "invoice_status": "RECEIVED", "entity_id": "ENTITY-A", "expected_entity_id": "ENTITY-A", "invoice_period": period, "contract_period": period},
    )


def tax_invoice_facts(company_id: str = "demo-north", period: str = "2026-07") -> list[dict[str, Any]]:
    policy = load_policy()
    if company_id not in COMPANY_FACTORS:
        raise TaxInvoiceError("unsupported public company")
    if period not in PERIODS:
        raise TaxInvoiceError("unsupported public period")
    rows: list[dict[str, Any]] = []
    for definition in _base_definitions(period):
        project_id = str(definition["project_id"])
        project_name, business_type = PROJECTS[project_id]
        rate = definition["tax_rate_bps"]
        net = definition.get("net_cents")
        if rate is None:
            tax = None
            net_cents = None
            gross = _scale(int(definition["gross_cents"]), company_id)
        else:
            net_cents = _scale(int(net), company_id)
            tax = net_cents * int(rate) // 10_000
            gross = net_cents + tax
        invoice_id = str(definition["invoice_id"])
        direction = str(definition["direction"])
        expected_project_id = str(definition["expected_project_id"])
        row = {
            **definition,
            "company_id": company_id,
            "company_zh": {"demo-north": "北方演示公司", "demo-south": "南方演示公司", "demo-west": "西部演示公司"}[company_id],
            "project_name_zh": project_name,
            "business_type_zh": business_type,
            "expected_project_name_zh": PROJECTS[expected_project_id][0],
            "direction_zh": DIRECTION_LABELS[direction],
            "net_cents": net_cents,
            "tax_cents": tax,
            "gross_cents": gross,
            "tax_rate_display_zh": format_rate(rate),
            "tax_inclusive_zh": INCLUSIVE_LABELS[str(definition["tax_inclusive_state"])],
            "invoice_status_zh": STATUS_LABELS[str(definition["invoice_status"])],
            "rate_source": None if rate is None else "EXPLICIT_INVOICE_FACT",
            "rate_inferred": False,
            "unknown_rate_blocked": rate is None,
            "links": {
                "contract_ref": f"PUBLIC-SYNTHETIC:CONTRACT:{company_id}:{invoice_id}",
                "project_ref": f"PUBLIC-SYNTHETIC:PROJECT:{company_id}:{project_id}",
                "voucher_ref": f"PUBLIC-SYNTHETIC:VOUCHER:{company_id}:{invoice_id}",
                "cash_ref": f"PUBLIC-SYNTHETIC:{'COLLECTION' if direction == 'OUTPUT' else 'PAYMENT'}:{company_id}:{invoice_id}",
            },
            "source_ref": f"PUBLIC-SYNTHETIC:TAX-INVOICE:{company_id}:{period}:{invoice_id}",
            "data_classification": DATA_CLASSIFICATION,
            "policy_version": policy["policy_version"],
        }
        rows.append(row)
    _validate_facts(rows, company_id, period, policy)
    return rows


def _validate_facts(rows: Sequence[Mapping[str, Any]], company_id: str, period: str, policy: Mapping[str, Any]) -> None:
    if len(rows) != 8 or len({row.get("invoice_id") for row in rows}) != 8:
        raise TaxInvoiceError("exactly eight unique synthetic invoice facts are required")
    for row in rows:
        if row.get("company_id") != company_id or row.get("contract_period") != period:
            raise TaxInvoiceError("company or requested period scope drifted")
        if row.get("data_classification") != DATA_CLASSIFICATION:
            raise TaxInvoiceError("only public synthetic facts are allowed")
        if set(row.get("links", {})) != {"contract_ref", "project_ref", "voucher_ref", "cash_ref"}:
            raise TaxInvoiceError("contract, project, voucher and cash links are required")
        if row.get("tax_inclusive_state") not in policy["tax_inclusive_states"] or row.get("invoice_status") not in policy["invoice_statuses"]:
            raise TaxInvoiceError("invoice state is not registered")
        rate = row.get("tax_rate_bps")
        if rate is None:
            if not row.get("unknown_rate_blocked") or row.get("rate_inferred") or row.get("net_cents") is not None or row.get("tax_cents") is not None:
                raise TaxInvoiceError("unknown tax rate was inferred or exposed")
        else:
            if isinstance(rate, bool) or not isinstance(rate, int) or rate not in policy["explicit_demo_tax_rates_bps"]:
                raise TaxInvoiceError("tax rate must be an explicit registered demo fact")
            money = (row.get("net_cents"), row.get("tax_cents"), row.get("gross_cents"))
            if any(isinstance(value, bool) or not isinstance(value, int) for value in money):
                raise TaxInvoiceError("known-rate money must use integer cents")
            if row["tax_cents"] != row["net_cents"] * rate // 10_000 or row["gross_cents"] != row["net_cents"] + row["tax_cents"]:
                raise TaxInvoiceError("tax invoice amount equation drifted")


def match_invoice(row: Mapping[str, Any]) -> dict[str, Any]:
    anomaly_types: list[str] = []
    if row.get("tax_rate_bps") is None:
        anomaly_types.append("UNKNOWN_TAX_RATE")
    if row.get("entity_id") != row.get("expected_entity_id"):
        anomaly_types.append("ENTITY_MISMATCH")
    if row.get("project_id") != row.get("expected_project_id"):
        anomaly_types.append("PROJECT_MISMATCH")
    if row.get("invoice_period") != row.get("contract_period"):
        anomaly_types.append("PERIOD_MISMATCH")
    invoice_rate, contract_rate = row.get("tax_rate_bps"), row.get("contract_tax_rate_bps")
    if invoice_rate is not None and contract_rate is not None and invoice_rate != contract_rate:
        anomaly_types.append("TAX_RATE_MISMATCH")
    evidence = [
        {
            "anomaly_type": anomaly,
            "label_zh": ANOMALY_LABELS[anomaly],
            "invoice_ref": row["source_ref"],
            "contract_ref": row["links"]["contract_ref"],
            "fact_zh": {
                "UNKNOWN_TAX_RATE": "票据和合同均未提供明确税率。",
                "ENTITY_MISMATCH": f"票据主体 {row['entity_id']}，合同主体 {row['expected_entity_id']}。",
                "PROJECT_MISMATCH": f"票据项目 {row['project_id']}，合同项目 {row['expected_project_id']}。",
                "PERIOD_MISMATCH": f"票据期间 {row['invoice_period']}，合同期间 {row['contract_period']}。",
                "TAX_RATE_MISMATCH": f"票据税率 {format_rate(invoice_rate)}，合同税率 {format_rate(contract_rate)}。",
            }[anomaly],
        }
        for anomaly in anomaly_types
    ]
    return {
        "invoice_id": row["invoice_id"],
        "company_id": row["company_id"],
        "match_state": "MATCHED" if not anomaly_types else "REVIEW_REQUIRED",
        "match_state_zh": "已匹配" if not anomaly_types else "需复核",
        "anomaly_types": anomaly_types,
        "anomaly_labels_zh": [ANOMALY_LABELS[item] for item in anomaly_types],
        "evidence": evidence,
        "evidence_count": len(evidence),
        "automatic_tax_adjustment_allowed": False,
        "recommended_internal_step_zh": "保留原值并人工核对票据与合同依据" if anomaly_types else "无需税务调整，仅保留匹配证据",
    }


def match_results(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [match_invoice(row) for row in rows]


def project_tax_burden(rows: Sequence[Mapping[str, Any]], matches: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    match_by_id = {row["invoice_id"]: row for row in matches}
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["project_id"])].append(row)
    result: list[dict[str, Any]] = []
    for project_id in PROJECTS:
        project_rows = grouped.get(project_id, [])
        included = [row for row in project_rows if match_by_id[row["invoice_id"]]["match_state"] == "MATCHED" and row.get("tax_cents") is not None]
        output_tax = sum(int(row["tax_cents"]) for row in included if row["direction"] == "OUTPUT")
        input_tax = sum(int(row["tax_cents"]) for row in included if row["direction"] == "INPUT")
        unknown_count = sum(row.get("tax_rate_bps") is None for row in project_rows)
        review_count = sum(match_by_id[row["invoice_id"]]["match_state"] == "REVIEW_REQUIRED" for row in project_rows)
        project_name, business_type = PROJECTS[project_id]
        result.append({
            "project_id": project_id,
            "project_name_zh": project_name,
            "business_type_zh": business_type,
            "output_tax_cents": output_tax,
            "eligible_input_tax_cents": input_tax,
            "management_net_tax_pressure_cents": output_tax - input_tax,
            "included_fact_count": len(included),
            "excluded_review_count": review_count,
            "unknown_rate_count": unknown_count,
            "completeness": "REVIEW_REQUIRED" if review_count else "COMPLETE_FOR_DEMO",
            "completeness_zh": "存在待复核资料" if review_count else "公开演示资料完整",
            "scope_limitation_zh": "仅为项目管理分析；待复核票据不计入，不是正式申报结论。",
            "formal_filing_conclusion": False,
        })
    return result


def tax_invoice_view(
    company_id: str = "demo-north",
    period: str = "2026-07",
    *,
    project: str = "",
    business_type: str = "",
    direction: str = "",
    invoice_status: str = "",
    match_state: str = "",
) -> dict[str, Any]:
    facts = tax_invoice_facts(company_id, period)
    matches = match_results(facts)
    match_by_id = {row["invoice_id"]: row for row in matches}
    combined = [{**row, **match_by_id[row["invoice_id"]]} for row in facts]
    filters = {
        "project": project,
        "business_type": business_type,
        "direction": direction,
        "invoice_status": invoice_status,
        "match_state": match_state,
    }
    valid_values = {
        "project": set(PROJECTS),
        "business_type": {value[1] for value in PROJECTS.values()},
        "direction": set(DIRECTION_LABELS),
        "invoice_status": set(STATUS_LABELS),
        "match_state": {"MATCHED", "REVIEW_REQUIRED"},
    }
    for key, value in filters.items():
        if value and value not in valid_values[key]:
            raise TaxInvoiceError(f"unsupported {key} filter")
    filtered = [
        row for row in combined
        if (not project or row["project_id"] == project)
        and (not business_type or row["business_type_zh"] == business_type)
        and (not direction or row["direction"] == direction)
        and (not invoice_status or row["invoice_status"] == invoice_status)
        and (not match_state or row["match_state"] == match_state)
    ]
    burden = project_tax_burden(facts, matches)
    anomalies = [item for row in filtered for item in row["evidence"]]
    known = [row for row in filtered if row["tax_cents"] is not None]
    summary = {
        "fact_count": len(filtered),
        "matched_count": sum(row["match_state"] == "MATCHED" for row in filtered),
        "review_count": sum(row["match_state"] == "REVIEW_REQUIRED" for row in filtered),
        "unknown_rate_count": sum(row["tax_rate_bps"] is None for row in filtered),
        "explicit_tax_cents": sum(int(row["tax_cents"]) for row in known),
    }
    return {
        "allowed": True,
        "schema_version": "kmfa.v015.s19p1.tax_invoice_view.v1",
        "company_id": company_id,
        "period": period,
        "filters": filters,
        "summary": summary,
        "rows": filtered,
        "all_fact_count": len(facts),
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "project_burden": burden,
        "project_burden_count": len(burden),
        "policy": load_policy(),
        "management_analysis_only": True,
        "formal_filing_conclusion": False,
        "automatic_tax_adjustment_count": 0,
        "rate_inference_count": 0,
        "business_action_count": 0,
        "raw_root_access_count": 0,
        "cross_company_leak_count": sum(row["company_id"] != company_id for row in filtered),
    }


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail_zh: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail_zh": detail_zh})

    contract, policy = source_contract(), load_policy()
    add("source_phase", contract["roadmap_phase_id"] == "S19-P1", "来源合同绑定 S19-P1")
    add("source_tasks", contract["task_ids"] == ["S19P1T01", "S19P1T02", "S19P1T03"], "三项任务完整")
    add("public_only", policy["data_classification"] == DATA_CLASSIFICATION, "只使用公开合成资料")
    add("integer_money", policy["money_unit"] == "INTEGER_CENTS", "金额只用整数分")
    add("no_rate_inference", policy["unknown_tax_rate_action"] == "BLOCK_NO_INFERENCE", "未知税率禁止推断")
    add("no_auto_adjustment", policy["automatic_tax_adjustment_allowed"] is False, "禁止自动调税")
    add("no_filing_conclusion", policy["formal_filing_conclusion_allowed"] is False, "禁止正式申报结论")
    add("matching_dimensions", policy["matching_dimensions"] == ["entity", "project", "period", "tax_rate"], "主体项目期间税率均核对")

    rows = tax_invoice_facts()
    matches = match_results(rows)
    for row in rows:
        prefix = row["invoice_id"].lower().replace("-", "_")
        add(prefix + "_scope", row["company_id"] == "demo-north" and row["data_classification"] == DATA_CLASSIFICATION, "公司与资料范围明确")
        add(prefix + "_links", set(row["links"]) == {"contract_ref", "project_ref", "voucher_ref", "cash_ref"}, "合同项目凭证现金链齐全")
        money_ok = (row["unknown_rate_blocked"] and row["net_cents"] is None and row["tax_cents"] is None) if row["tax_rate_bps"] is None else (row["gross_cents"] == row["net_cents"] + row["tax_cents"] and row["tax_cents"] == row["net_cents"] * row["tax_rate_bps"] // 10_000)
        add(prefix + "_money", money_ok, "金额公式或未知阻断正确")
        add(prefix + "_states", row["tax_inclusive_state"] in policy["tax_inclusive_states"] and row["invoice_status"] in policy["invoice_statuses"] and row["rate_inferred"] is False, "税率含税和发票状态明确")
    for match in matches:
        prefix = match["invoice_id"].lower().replace("-", "_")
        evidence_ok = (match["match_state"] == "MATCHED" and match["evidence_count"] == 0) or (match["match_state"] == "REVIEW_REQUIRED" and match["evidence_count"] == len(match["anomaly_types"]) > 0 and all(item["invoice_ref"] and item["contract_ref"] and item["fact_zh"] for item in match["evidence"]))
        add(prefix + "_match_evidence", evidence_ok, "匹配结果与异常证据一致")
        add(prefix + "_no_adjustment", match["automatic_tax_adjustment_allowed"] is False, "匹配不触发自动调税")
    burden = project_tax_burden(rows, matches)
    for row in burden:
        prefix = row["project_id"].lower().replace("-", "_")
        add(prefix + "_burden_equation", row["management_net_tax_pressure_cents"] == row["output_tax_cents"] - row["eligible_input_tax_cents"] and all(type(row[key]) is int for key in ("output_tax_cents", "eligible_input_tax_cents", "management_net_tax_pressure_cents")), "项目税负金额与整数分一致")
        add(prefix + "_burden_scope", row["formal_filing_conclusion"] is False and "不是正式申报结论" in row["scope_limitation_zh"], "项目税负明确管理范围")
    views = {company: tax_invoice_view(company) for company in COMPANY_FACTORS}
    add("company_isolation", all(view["cross_company_leak_count"] == 0 and all(row["company_id"] == company for row in view["rows"]) for company, view in views.items()) and len({view["summary"]["explicit_tax_cents"] for view in views.values()}) == 3, "三家公司隔离且金额不同")
    base = views["demo-north"]
    add("zero_execution_boundary", base["raw_root_access_count"] == base["automatic_tax_adjustment_count"] == base["rate_inference_count"] == base["business_action_count"] == 0 and base["formal_filing_conclusion"] is False, "读取执行推断申报均为零")
    if len(checks) != 64:
        raise TaxInvoiceError(f"public check contract drifted: {len(checks)}")
    return checks


def public_summary() -> dict[str, Any]:
    view = tax_invoice_view()
    checks = public_checks()
    return {
        "phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "public_check_count": len(checks),
        "public_check_pass_count": sum(row["status"] == "PASS" for row in checks),
        "fact_count": view["all_fact_count"],
        "matched_count": view["summary"]["matched_count"],
        "review_count": view["summary"]["review_count"],
        "anomaly_count": view["anomaly_count"],
        "project_burden_count": view["project_burden_count"],
        "unknown_rate_count": view["summary"]["unknown_rate_count"],
        "rate_inference_count": view["rate_inference_count"],
        "automatic_tax_adjustment_count": view["automatic_tax_adjustment_count"],
        "formal_filing_conclusion_count": int(view["formal_filing_conclusion"]),
        "raw_root_access_count": view["raw_root_access_count"],
    }


if __name__ == "__main__":
    print(json.dumps(public_summary(), ensure_ascii=False, indent=2, sort_keys=True))
