from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from quantlab.business import build_cashflow_command
from quantlab.config import PROJECT_ROOT, REPORT_ROOT_DIR
from quantlab.consumption import build_consumption_guard
from quantlab.policy import build_policy_radar
from quantlab.reports.catalog import latest_report_artifact, report_artifacts_frame
from quantlab.storage import atomic_write_json, atomic_write_text
from quantlab.system import MASTER_DISPLAY_NAME, MASTER_SYSTEM_ID, build_daily_readiness, build_quantlab_integration_audit
from quantlab.value import build_token_roi_ledger


def build_command_center(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    daily_readiness_payload: dict[str, Any] | None = None,
    integration_payload: dict[str, Any] | None = None,
    token_roi_payload: dict[str, Any] | None = None,
    cashflow_payload: dict[str, Any] | None = None,
    policy_payload: dict[str, Any] | None = None,
    consumption_payload: dict[str, Any] | None = None,
    report_artifacts: pd.DataFrame | None = None,
    artifact_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    integration = integration_payload or build_quantlab_integration_audit(
        as_of=audit_date,
        project_root=root,
        report_root=reports,
    )
    daily = daily_readiness_payload or build_daily_readiness(
        as_of=audit_date,
        project_root=root,
        report_root=reports,
        integration_payload=integration,
    )
    token_roi = token_roi_payload or _load_latest_token_roi(root) or build_token_roi_ledger(
        as_of=audit_date,
        project_root=root,
        report_root=reports,
        artifact_limit=artifact_limit,
    )
    cashflow = cashflow_payload or _load_latest_cashflow(root) or build_cashflow_command(
        as_of=audit_date,
        project_root=root,
    )
    policy = policy_payload or _load_latest_policy(root) or build_policy_radar(
        as_of=audit_date,
        project_root=root,
        opportunity_limit=artifact_limit,
    )
    consumption = consumption_payload or _load_latest_consumption(root) or build_consumption_guard(
        as_of=audit_date,
        project_root=root,
    )
    artifacts = report_artifacts if report_artifacts is not None else report_artifacts_frame(reports)
    latest = latest_report_artifact(artifacts) or {}
    risk_gates = _risk_gate_rows(daily, integration)
    business_systems = {
        "cashflow": cashflow,
        "policy": policy,
        "consumption": consumption,
    }
    scorecards = _scorecards(daily, integration, token_roi, latest, risk_gates, business_systems)
    action_queue = _action_queue(daily, integration, token_roi, latest, business_systems)
    status = _command_status(daily, integration, token_roi, latest, business_systems)
    business_summary = _business_system_summary(cashflow, policy, consumption)
    return {
        "schema": "EVACommandCenterV1",
        "system": MASTER_SYSTEM_ID,
        "display_name": MASTER_DISPLAY_NAME,
        "subsystem": "Executive Command Center",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "report_root": str(reports),
        "command_status": status,
        "status_reason": _status_reason(status, risk_gates, latest, business_summary),
        "scorecards": scorecards,
        "risk_gates": risk_gates,
        "action_queue": action_queue,
        "latest_report": latest,
        "evidence_sources": _evidence_sources(root, token_roi, latest, business_systems),
        "runtime_summary_sources": _runtime_summary_sources(root, token_roi, business_systems),
        "token_roi_summary": _token_roi_summary(token_roi),
        "business_system_summary": business_summary,
        "cashflow_summary": _cashflow_summary(cashflow),
        "policy_summary": _policy_summary(policy),
        "consumption_summary": _consumption_summary(consumption),
        "assumptions": [
            "总控驾驶舱只聚合本地证据，不刷新行情、不启动 Moomoo OpenD、不修改持仓、不连接实盘。",
            "所有输入必须进入证据层；没有证据的结论降级为观察或待复核。",
            "所有结论必须经过风控层；Blocked 或 NeedsReview 不应作为交易前参考。",
            "所有产出必须进入 Token ROI 台账；没有真实金额输入时不伪造收益、节省成本或 ROI。",
            "CashFlow、Policy、Consumption 只读取本地 latest 快照或 fail-closed fallback，不连接银行、支付、政府平台、支付宝、税务、工资或券商系统。",
            "总控优先读取 Token ROI、CashFlow、Policy、Consumption 的 compact runtime summary latest；缺失时才 fallback 到 full latest 或本地 fail-closed 构建。",
            "Research-only boundary remains active: no live trading, no real orders, no payments, no betting execution.",
        ],
    }


def write_command_center(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    output_dir: Path | str | None = None,
    artifact_limit: int = 300,
    daily_readiness_payload: dict[str, Any] | None = None,
    integration_payload: dict[str, Any] | None = None,
    token_roi_payload: dict[str, Any] | None = None,
    cashflow_payload: dict[str, Any] | None = None,
    policy_payload: dict[str, Any] | None = None,
    consumption_payload: dict[str, Any] | None = None,
    report_artifacts: pd.DataFrame | None = None,
) -> dict[str, Any]:
    payload = build_command_center(
        as_of=as_of,
        project_root=project_root,
        report_root=report_root,
        artifact_limit=artifact_limit,
        daily_readiness_payload=daily_readiness_payload,
        integration_payload=integration_payload,
        token_roi_payload=token_roi_payload,
        cashflow_payload=cashflow_payload,
        policy_payload=policy_payload,
        consumption_payload=consumption_payload,
        report_artifacts=report_artifacts,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "commandCenter"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"EVACommandCenter_{stamp}"
    json_path = target / f"{stem}.json"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "EVACommandCenter_latest.json"
    latest_markdown = target / "EVACommandCenter_latest.md"
    latest_pdf = target / "EVACommandCenter_latest.pdf"
    payload["outputs"] = {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_markdown),
        "latest_pdf": str(latest_pdf),
    }
    markdown = command_center_markdown(payload)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_command_center_pdf(pdf_path, payload)
    _write_command_center_pdf(latest_pdf, payload)
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def command_center_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# EVA_OS Command Center {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Status: `{payload.get('command_status', '')}`",
        f"- Reason: {payload.get('status_reason', '')}",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        "",
        "## Scorecards",
        _markdown_table(payload.get("scorecards", []), ["metric", "value", "status", "evidence"]),
        "",
        "## Risk Gates",
        _markdown_table(payload.get("risk_gates", []), ["gate", "status", "evidence", "next_action"]),
        "",
        "## Action Queue",
        _markdown_table(payload.get("action_queue", []), ["priority", "status", "owner", "action", "source"]),
        "",
        "## Evidence Sources",
        _markdown_table(payload.get("evidence_sources", []), ["source", "status", "path", "schema"]),
        "",
        "## Runtime Summary Sources",
        _markdown_table(payload.get("runtime_summary_sources", []), ["subsystem", "mode", "schema", "path"]),
        "",
        "## Token ROI Summary",
        _markdown_table([payload.get("token_roi_summary", {})], ["record_count", "quantified_records", "unquantified_records", "roi_status"]),
        "",
        "## Business Systems Summary",
        _markdown_table(payload.get("business_system_summary", []), ["subsystem", "status", "metric", "value", "evidence"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _command_status(
    daily: dict[str, Any],
    integration: dict[str, Any],
    token_roi: dict[str, Any],
    latest: dict[str, Any],
    business_systems: dict[str, dict[str, Any]],
) -> str:
    if daily.get("readiness_status") == "Blocked" or integration.get("status") == "Fail":
        return "Blocked"
    if any(_business_status_level(payload) == "Fail" for payload in business_systems.values()):
        return "Blocked"
    if daily.get("readiness_status") != "ReadyForResearch":
        return "NeedsReview"
    if integration.get("status") != "Pass":
        return "NeedsReview"
    if not latest.get("path"):
        return "NeedsReview"
    if int(token_roi.get("record_count", 0) or 0) <= 0:
        return "NeedsReview"
    if any(_business_status_level(payload) == "Review" for payload in business_systems.values()):
        return "NeedsReview"
    return "ReadyForResearch"


def _status_reason(status: str, gates: list[dict[str, str]], latest: dict[str, Any], business_summary: list[dict[str, Any]] | None = None) -> str:
    if status == "ReadyForResearch":
        return "核心证据闸门、报告证据和本地价值台账已闭合，可继续研究。"
    failed = [row["gate"] for row in gates if row.get("status") in {"Fail", "Blocked"}]
    review = [row["gate"] for row in gates if row.get("status") == "Review"]
    missing_latest = [] if latest.get("path") else ["LatestReport"]
    business_review = [str(row.get("subsystem", "")) for row in business_summary or [] if row.get("status") in {"Review", "Fail"}]
    return "需要复核：" + ", ".join([*failed, *review, *missing_latest, *business_review])


def _scorecards(
    daily: dict[str, Any],
    integration: dict[str, Any],
    token_roi: dict[str, Any],
    latest: dict[str, Any],
    gates: list[dict[str, str]],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    token_summary = _token_roi_summary(token_roi)
    rows = [
        {
            "metric": "Daily Readiness",
            "value": str(daily.get("readiness_status", "Missing")),
            "status": _metric_status(str(daily.get("readiness_status", "")), ready_value="ReadyForResearch"),
            "evidence": f"gates={len(daily.get('core_gates', []))}",
        },
        {
            "metric": "Integration Audit",
            "value": str(integration.get("status", "Missing")),
            "status": _metric_status(str(integration.get("status", "")), ready_value="Pass"),
            "evidence": f"summary={integration.get('summary', {})}",
        },
        {
            "metric": "Risk Gates",
            "value": f"{_count_gate_status(gates, 'Pass')}/{len(gates)} Pass",
            "status": "Pass" if gates and _count_gate_status(gates, "Pass") == len(gates) else "Review",
            "evidence": ", ".join(f"{row['gate']}={row['status']}" for row in gates),
        },
        {
            "metric": "Token ROI Ledger",
            "value": str(token_summary.get("record_count", 0)),
            "status": "Pass" if int(token_summary.get("record_count", 0) or 0) > 0 else "Review",
            "evidence": (
                f"quantified={token_summary.get('quantified_records', 0)}; "
                f"unquantified={token_summary.get('unquantified_records', 0)}; "
                f"schema={_payload_schema(token_roi)}"
            ),
        },
        {
            "metric": "Latest Report",
            "value": str(latest.get("name") or "Missing"),
            "status": "Pass" if latest.get("path") else "Review",
            "evidence": str(latest.get("path", "")),
        },
    ]
    business_rows = _business_system_summary(
        business_systems.get("cashflow", {}),
        business_systems.get("policy", {}),
        business_systems.get("consumption", {}),
    )
    for row in business_rows:
        rows.append(
            {
                "metric": str(row.get("subsystem", "")),
                "value": str(row.get("value", "")),
                "status": str(row.get("status", "Review")),
                "evidence": str(row.get("evidence", "")),
            }
        )
    return rows


def _risk_gate_rows(daily: dict[str, Any], integration: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in daily.get("core_gates", []):
        rows.append(
            {
                "gate": str(item.get("gate", "")),
                "status": str(item.get("status", "Review")),
                "evidence": str(item.get("evidence", "")),
                "next_action": str(item.get("next_action", "")),
            }
        )
    seen = {row["gate"] for row in rows}
    for item in integration.get("items", []):
        layer = str(item.get("layer", ""))
        if layer in seen:
            continue
        rows.append(
            {
                "gate": layer,
                "status": str(item.get("status", "Review")),
                "evidence": str(item.get("summary", "")),
                "next_action": str(item.get("next_action", "")),
            }
        )
    return rows


def _action_queue(
    daily: dict[str, Any],
    integration: dict[str, Any],
    token_roi: dict[str, Any],
    latest: dict[str, Any],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if integration.get("status") != "Pass":
        rows.append(
            {
                "priority": "P0",
                "status": "Open",
                "owner": "EVA_OS",
                "action": "复跑总集成审计并处理 Review/Fail 项。",
                "source": "Integration Audit",
            }
        )
    for item in daily.get("action_items", [])[:8]:
        priority = "P0" if "Fail" in str(item) or "REJECTED" in str(item) else "P1"
        rows.append(
            {
                "priority": priority,
                "status": "Open",
                "owner": "QuantLab",
                "action": str(item),
                "source": "Daily Readiness",
            }
        )
    if not latest.get("path"):
        rows.append(
            {
                "priority": "P1",
                "status": "Open",
                "owner": "QuantLab",
                "action": "生成一份带 RunMetadata、数据质量和风险闸门的正式 Word 研究报告。",
                "source": "Report Evidence",
            }
        )
    token_summary = _token_roi_summary(token_roi)
    if int(token_summary.get("unquantified_records", 0) or 0) > 0:
        rows.append(
            {
                "priority": "P2",
                "status": "Open",
                "owner": "Value Layer",
                "action": "为高价值产物补充真实节省时间、避免损失、复用价值或成本数据；未量化前 ROI 保持空值。",
                "source": "Token ROI Ledger",
            }
        )
    _append_business_actions(rows, business_systems.get("cashflow", {}), "Company CashFlow Command")
    _append_business_actions(rows, business_systems.get("policy", {}), "Policy Intelligence Radar")
    _append_business_actions(rows, business_systems.get("consumption", {}), "Consumption Guard")
    if not rows:
        rows.append(
            {
                "priority": "P2",
                "status": "Open",
                "owner": "EVA_OS",
                "action": "继续日常研究流程，所有结论保持证据化、风控化和研究用途。",
                "source": "Executive Command Center",
            }
        )
    return _dedupe_actions(rows)


def _evidence_sources(
    root: Path,
    token_roi: dict[str, Any],
    latest: dict[str, Any],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows = [
        _source_row("Daily Readiness", _latest_file(root / "data" / "systemAudit", "QuantLabDailyReadiness_*.json"), "QuantLabDailyReadinessV1"),
        _source_row("Integration Audit", _latest_file(root / "data" / "systemAudit", "QuantLabIntegrationAudit_*.json"), "QuantLabIntegrationAuditV1"),
        _source_row("Data Trust Audit", _latest_file(root / "data" / "systemAudit", "QuantLabDataTrustAudit_*.json"), "QuantLabDataTrustAuditV1"),
        _source_row(
            "Token ROI Ledger",
            _latest_payload_path(root, token_roi, "value", "EVATokenROIRuntimeSummary_latest.json", "EVATokenROILedger_latest.json"),
            _payload_schema(token_roi, "EVATokenROILedgerV1"),
        ),
        {
            "source": "Latest Report",
            "status": "Present" if latest.get("path") else "Missing",
            "path": str(latest.get("path", "")),
            "schema": str(latest.get("artifact_type", "")),
        },
    ]
    rows.extend(
        [
            _source_row(
                "Company CashFlow Command",
                _latest_payload_path(root, business_systems.get("cashflow", {}), "cashflow", "CompanyCashFlowRuntimeSummary_latest.json", "CompanyCashFlowCommand_latest.json"),
                _payload_schema(business_systems.get("cashflow", {}), "EVAOSCompanyCashFlowCommandV1"),
            ),
            _source_row(
                "Policy Intelligence Radar",
                _latest_payload_path(root, business_systems.get("policy", {}), "policy", "PolicyIntelligenceRuntimeSummary_latest.json", "PolicyIntelligenceRadar_latest.json"),
                _payload_schema(business_systems.get("policy", {}), "EVAOSPolicyIntelligenceRadarV1"),
            ),
            _source_row(
                "Consumption Guard",
                _latest_payload_path(root, business_systems.get("consumption", {}), "consumption", "ConsumptionGuardRuntimeSummary_latest.json", "ConsumptionGuard_latest.json"),
                _payload_schema(business_systems.get("consumption", {}), "EVAOSConsumptionGuardV1"),
            ),
        ]
    )
    return rows


def _runtime_summary_sources(root: Path, token_roi: dict[str, Any], business_systems: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
        _runtime_summary_source_row(root, "Token ROI", token_roi, "value", "EVATokenROIRuntimeSummary_latest.json", "EVATokenROILedger_latest.json"),
        _runtime_summary_source_row(root, "Company CashFlow Command", business_systems.get("cashflow", {}), "cashflow", "CompanyCashFlowRuntimeSummary_latest.json", "CompanyCashFlowCommand_latest.json"),
        _runtime_summary_source_row(root, "Policy Intelligence Radar", business_systems.get("policy", {}), "policy", "PolicyIntelligenceRuntimeSummary_latest.json", "PolicyIntelligenceRadar_latest.json"),
        _runtime_summary_source_row(root, "Consumption Guard", business_systems.get("consumption", {}), "consumption", "ConsumptionGuardRuntimeSummary_latest.json", "ConsumptionGuard_latest.json"),
    ]


def _runtime_summary_source_row(
    root: Path,
    subsystem: str,
    payload: dict[str, Any],
    folder: str,
    runtime_latest_name: str,
    full_latest_name: str,
) -> dict[str, str]:
    schema = _payload_schema(payload)
    mode = "runtime_summary" if schema.endswith("RuntimeSummaryV1") else ("full_snapshot" if schema else "fallback_build")
    return {
        "subsystem": subsystem,
        "mode": mode,
        "schema": schema,
        "path": str(_latest_payload_path(root, payload, folder, runtime_latest_name, full_latest_name)),
    }


def _source_row(source: str, path: Path | None, schema: str) -> dict[str, str]:
    return {
        "source": source,
        "status": "Present" if path and path.exists() else "Missing",
        "path": str(path or ""),
        "schema": schema,
    }


def _token_roi_summary(token_roi: dict[str, Any]) -> dict[str, Any]:
    if token_roi.get("schema") == "EVATokenROIRuntimeSummaryV1":
        return {
            "record_count": _safe_int(token_roi.get("record_count", 0)),
            "quantified_records": _safe_int(token_roi.get("quantified_records", 0)),
            "unquantified_records": _safe_int(token_roi.get("unquantified_records", 0)),
            "roi_status": "Unquantified" if _safe_int(token_roi.get("quantified_records", 0)) == 0 else "PartlyQuantified",
        }
    summary = token_roi.get("summary", {})
    return {
        "record_count": int(token_roi.get("record_count", 0) or 0),
        "quantified_records": int(summary.get("quantified_records", 0) or 0),
        "unquantified_records": int(summary.get("unquantified_records", 0) or 0),
        "roi_status": "Unquantified" if int(summary.get("quantified_records", 0) or 0) == 0 else "PartlyQuantified",
    }


def _business_system_summary(
    cashflow: dict[str, Any],
    policy: dict[str, Any],
    consumption: dict[str, Any],
) -> list[dict[str, Any]]:
    cashflow_summary = _cashflow_summary(cashflow)
    policy_summary = _policy_summary(policy)
    consumption_summary = _consumption_summary(consumption)
    return [
        {
            "subsystem": "Company CashFlow Command",
            "status": _business_status_level(cashflow),
            "metric": "cashflow_status",
            "value": cashflow_summary["cashflow_status"],
            "evidence": (
                f"balance={cashflow_summary['latest_balance']}; "
                f"net={cashflow_summary['net_cashflow']}; "
                f"runway_days={cashflow_summary['runway_days']}; "
                f"pending={cashflow_summary['pending_review_records']}; "
                f"missing_evidence={cashflow_summary['reviewed_missing_evidence_records']}"
            ),
        },
        {
            "subsystem": "Policy Intelligence Radar",
            "status": _business_status_level(policy),
            "metric": "policy_status",
            "value": policy_summary["policy_status"],
            "evidence": (
                f"opportunities={policy_summary['opportunity_count']}; "
                f"actionable={policy_summary['actionable_count']}; "
                f"watch={policy_summary['watch_count']}; "
                f"pending={policy_summary['pending_review_count']}; "
                f"missing_evidence={policy_summary['missing_evidence_count']}"
            ),
        },
        {
            "subsystem": "Consumption Guard",
            "status": _business_status_level(consumption),
            "metric": "guard_status",
            "value": consumption_summary["guard_status"],
            "evidence": (
                f"spend={consumption_summary['counted_spend']}; "
                f"impulse={consumption_summary['impulse_spend']}; "
                f"fixed={consumption_summary['fixed_cost']}; "
                f"pressure={consumption_summary['investable_cashflow_pressure']}; "
                f"pending={consumption_summary['pending_review_records']}; "
                f"missing_evidence={consumption_summary['reviewed_missing_evidence_records']}"
            ),
        },
    ]


def _cashflow_summary(cashflow: dict[str, Any]) -> dict[str, Any]:
    summary = cashflow.get("summary", {}) if isinstance(cashflow, dict) else {}
    return {
        "cashflow_status": str(cashflow.get("cashflow_status") or summary.get("cashflow_status") or "Missing"),
        "latest_balance": cashflow.get("latest_balance", summary.get("latest_balance")),
        "net_cashflow": float(cashflow.get("net_cashflow", summary.get("net_cashflow", 0.0)) or 0.0),
        "runway_days": cashflow.get("runway_days", summary.get("runway_days")),
        "pending_review_records": _safe_int(cashflow.get("pending_review_records", summary.get("pending_review_records", 0))),
        "reviewed_missing_evidence_records": _safe_int(cashflow.get("reviewed_missing_evidence_records", summary.get("reviewed_missing_evidence_records", 0))),
    }


def _policy_summary(policy: dict[str, Any]) -> dict[str, Any]:
    summary = policy.get("summary", {}) if isinstance(policy, dict) else {}
    return {
        "policy_status": str(policy.get("policy_status") or summary.get("policy_status") or "Missing"),
        "opportunity_count": _safe_int(policy.get("opportunity_count", summary.get("total_records", 0))),
        "actionable_count": _safe_int(policy.get("actionable_count", summary.get("actionable_count", 0))),
        "watch_count": _safe_int(policy.get("watch_count", summary.get("watch_count", 0))),
        "missing_evidence_count": _safe_int(policy.get("missing_evidence_count", summary.get("missing_evidence_count", 0))),
        "pending_review_count": _safe_int(policy.get("pending_review_count", summary.get("pending_review_count", 0))),
    }


def _consumption_summary(consumption: dict[str, Any]) -> dict[str, Any]:
    summary = consumption.get("summary", {}) if isinstance(consumption, dict) else {}
    return {
        "guard_status": str(consumption.get("guard_status") or summary.get("guard_status") or "Missing"),
        "counted_spend": float(consumption.get("counted_spend", summary.get("counted_spend", 0.0)) or 0.0),
        "impulse_spend": float(consumption.get("impulse_spend", summary.get("impulse_spend", 0.0)) or 0.0),
        "fixed_cost": float(consumption.get("fixed_cost", summary.get("fixed_cost", 0.0)) or 0.0),
        "investable_cashflow_pressure": consumption.get("investable_cashflow_pressure", summary.get("investable_cashflow_pressure")),
        "pending_review_records": _safe_int(consumption.get("pending_review_records", summary.get("pending_review_records", 0))),
        "reviewed_missing_evidence_records": _safe_int(consumption.get("reviewed_missing_evidence_records", summary.get("reviewed_missing_evidence_records", 0))),
    }


def _business_status_level(payload: dict[str, Any]) -> str:
    status = _business_status_text(payload)
    if status in {"Stable", "Observe", "Actionable"}:
        return "Pass"
    if status in {"Pass"}:
        return "Pass"
    if status in {"Critical", "StopBleeding", "Blocked"}:
        return "Fail"
    return "Review"


def _business_status_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "Missing"
    summary = payload.get("summary", {})
    return str(
        payload.get("cashflow_status")
        or payload.get("policy_status")
        or payload.get("guard_status")
        or payload.get("status")
        or summary.get("cashflow_status")
        or summary.get("policy_status")
        or summary.get("guard_status")
        or "Missing"
    )


def _append_business_actions(rows: list[dict[str, str]], payload: dict[str, Any], owner: str) -> None:
    status = _business_status_level(payload)
    raw_status = _business_status_text(payload)
    if status == "Pass" and raw_status != "Actionable":
        return
    actions = _payload_actions(payload)
    for item in actions[:4]:
        rows.append(
            {
                "priority": str(item.get("priority", "P1")),
                "status": str(item.get("status", "Open")),
                "owner": owner,
                "action": str(item.get("action", "")),
                "source": f"{owner}: {item.get('source', '')}",
            }
        )


def _payload_actions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    actions = payload.get("action_queue")
    if isinstance(actions, list):
        return [item for item in actions if isinstance(item, dict)]
    top_actions = payload.get("top_actions")
    if isinstance(top_actions, list):
        return [item for item in top_actions if isinstance(item, dict)]
    return []


def _latest_payload_path(root: Path, payload: dict[str, Any], folder: str, runtime_latest_name: str, full_latest_name: str) -> Path:
    outputs = payload.get("outputs", {}) if isinstance(payload, dict) else {}
    if isinstance(outputs, dict):
        for key in ("latest_runtime_summary_json", "runtime_summary_json", "latest_json"):
            value = outputs.get(key)
            if value:
                return Path(str(value)).expanduser()
    latest_name = runtime_latest_name if _payload_schema(payload).endswith("RuntimeSummaryV1") else full_latest_name
    return root / "data" / folder / latest_name


def _payload_schema(payload: dict[str, Any], default: str = "") -> str:
    return str(payload.get("schema", default) if isinstance(payload, dict) else default)


def _load_latest_cashflow(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "cashflow" / "CompanyCashFlowRuntimeSummary_latest.json", "EVAOSCompanyCashFlowRuntimeSummaryV1") or _load_latest_schema(root / "data" / "cashflow" / "CompanyCashFlowCommand_latest.json", "EVAOSCompanyCashFlowCommandV1")


def _load_latest_policy(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "policy" / "PolicyIntelligenceRuntimeSummary_latest.json", "EVAOSPolicyIntelligenceRuntimeSummaryV1") or _load_latest_schema(root / "data" / "policy" / "PolicyIntelligenceRadar_latest.json", "EVAOSPolicyIntelligenceRadarV1")


def _load_latest_consumption(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "consumption" / "ConsumptionGuardRuntimeSummary_latest.json", "EVAOSConsumptionGuardRuntimeSummaryV1") or _load_latest_schema(root / "data" / "consumption" / "ConsumptionGuard_latest.json", "EVAOSConsumptionGuardV1")


def _load_latest_schema(path: Path, schema: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) and payload.get("schema") == schema else None


def _load_latest_token_roi(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "value" / "EVATokenROIRuntimeSummary_latest.json", "EVATokenROIRuntimeSummaryV1") or _load_latest_schema(root / "data" / "value" / "EVATokenROILedger_latest.json", "EVATokenROILedgerV1")


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _latest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = [path for path in root.glob(pattern) if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda item: item.stat().st_mtime)


def _metric_status(value: str, *, ready_value: str) -> str:
    if value == ready_value:
        return "Pass"
    if value in {"Fail", "Blocked"}:
        return "Fail"
    return "Review"


def _count_gate_status(gates: list[dict[str, str]], status: str) -> int:
    return sum(1 for row in gates if row.get("status") == status)


def _dedupe_actions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in rows:
        key = row.get("action", "")
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _write_command_center_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    token_summary = payload.get("token_roi_summary", {})
    lines = [
        f"EVA_OS Command Center {payload.get('as_of', '')}",
        f"System: {payload.get('system', '')}",
        f"Status: {payload.get('command_status', '')}",
        f"Reason: {payload.get('status_reason', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        "",
        "Scorecards:",
    ]
    for row in payload.get("scorecards", [])[:8]:
        lines.append(f"- {row.get('metric')}: {row.get('value')} | {row.get('status')}")
    lines.extend(["", "Business Systems:"])
    for row in payload.get("business_system_summary", [])[:6]:
        lines.append(f"- {row.get('subsystem')}: {row.get('value')} | {row.get('status')}")
    lines.extend(["", "Top Actions:"])
    for row in payload.get("action_queue", [])[:12]:
        lines.append(f"- {row.get('priority')} {row.get('action')} [{row.get('source')}]")
    lines.extend(
        [
            "",
            "Token ROI:",
            f"- records={token_summary.get('record_count', 0)} quantified={token_summary.get('quantified_records', 0)} unquantified={token_summary.get('unquantified_records', 0)}",
            "",
            "Research-only. No live trading. No real orders.",
        ]
    )
    content = ["BT", "/F1 10 Tf", "56 760 Td", "12 TL"]
    for line in lines[:58]:
        content.append(f"({_pdf_escape(_pdf_ascii(line))}) Tj")
        content.append("T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    _write_pdf_objects(path, objects)


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(content)


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
