from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.business import build_cashflow_command
from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.consumption import build_consumption_guard
from pfi_os.policy import build_policy_radar
from pfi_os.reports.catalog import latest_report_artifact, report_artifacts_frame
from pfi_os.storage import atomic_write_json, atomic_write_text
from pfi_os.system import MASTER_DISPLAY_NAME, MASTER_SYSTEM_ID, build_daily_readiness, build_pfi_os_integration_audit

COMMAND_CENTER_COLUMN_LABELS = {
    "metric": "指标",
    "value": "数值",
    "status": "状态",
    "evidence": "证据",
    "gate": "闸门",
    "next_action": "下一步",
    "priority": "优先级",
    "owner": "负责人",
    "action": "行动",
    "source": "来源",
    "path": "路径",
    "schema": "契约",
    "subsystem": "子系统",
    "mode": "模式",
}

COMMAND_CENTER_DISPLAY_VALUES = {
    "Action Queue": "行动队列",
    "Blocked": "阻断",
    "CashFlow": "现金流",
    "Company CashFlow Command": "现金流指挥台",
    "Consumption Guard": "消费守卫",
    "Daily Readiness": "日常就绪",
    "Data Trust Audit": "数据边界审计",
    "DataTrust": "数据边界",
    "EntityRegistry": "标的注册表",
    "Evidence Sources": "证据来源",
    "Executive Command Center": "总控驾驶舱",
    "Fail": "失败",
    "Integration Audit": "集成审计",
    "IntegrationAudit": "集成审计",
    "Latest Report": "最新报告",
    "LatestReport": "最新报告",
    "LatestWordReport": "最新 Word 报告",
    "Missing": "缺失",
    "MissingBalance": "缺少余额",
    "MissingConsumptionEvidence": "缺少消费证据",
    "MissingPolicyEvidence": "缺少政策证据",
    "NeedsReview": "需复核",
    "NoLiveTradingBoundary": "禁止实盘边界",
    "Open": "待处理",
    "PFI_OS": "PFI OS",
    "PFIOS": "PFI OS",
    "Pass": "通过",
    "Policy Intelligence Radar": "政策雷达",
    "Present": "存在",
    "ReadyForResearch": "可用于研究",
    "Report Evidence": "报告证据",
    "ReportEvidence": "报告证据",
    "ResearchBusInterop": "研究总线互通",
    "Review": "需复核",
    "Risk Gates": "风控闸门",
    "Runtime": "运行摘要",
    "Runtime Summary Sources": "运行摘要来源",
    "Stable": "稳定",
    "Watch": "观察",
    "WorkflowInputs": "工作流输入",
    "runtime_summary": "运行摘要",
}

COMMAND_CENTER_TEXT_REPLACEMENTS = (
    ("Company CashFlow Command", "现金流指挥台"),
    ("Policy Intelligence Radar", "政策雷达"),
    ("Consumption Guard", "消费守卫"),
    ("Data Trust Audit", "数据边界审计"),
    ("Daily Readiness", "日常就绪"),
    ("Integration Audit", "集成审计"),
    ("Report Evidence", "报告证据"),
    ("DataTrust", "数据边界"),
    ("EntityRegistry", "标的注册表"),
    ("IntegrationAudit", "集成审计"),
    ("ReportEvidence", "报告证据"),
    ("LatestWordReport", "最新 Word 报告"),
    ("LatestReport", "最新报告"),
    ("NoLiveTradingBoundary", "禁止实盘边界"),
    ("ResearchBusInterop", "研究总线互通"),
    ("WorkflowInputs", "工作流输入"),
    ("ReadyForResearch", "可用于研究"),
    ("NeedsReview", "需复核"),
    ("Blocked", "阻断"),
    ("MissingBalance", "缺少余额"),
    ("MissingPolicyEvidence", "缺少政策证据"),
    ("MissingConsumptionEvidence", "缺少消费证据"),
    ("PFI_OS", "PFI OS"),
    ("PFIOS", "PFI OS"),
    ("Present", "存在"),
    ("Review/Fail", "复核或失败"),
    ("Keep evidence audit clean before using research outputs.", "使用研究输出前，先保持证据审计干净。"),
    ("Run scripts/auditPFIIntegration.sh --no-write if not Pass.", "如未通过，运行 scripts/auditPFIIntegration.sh --no-write。"),
    ("Run scripts/auditPFIIntegration.sh --no-write if not Pass", "如未通过，运行 scripts/auditPFIIntegration.sh --no-write"),
    ("Generate a report with RunMetadata before using results.", "使用结果前，先生成带 RunMetadata 的报告。"),
    ("Generate at least one Word report with current evidence metadata.", "至少生成一份带当前证据元数据的 Word 报告。"),
    ("Generate at least one Word report for the current research session.", "为当前研究会话至少生成一份 Word 报告。"),
    ("Open the latest report from Report Center and check data quality, cross-source validation, and risk gates before using it.", "在报告中心打开最新报告，先复核数据质量、多源校验和风控闸门。"),
    ("Remove or fail closed any real-order code path.", "发现真实下单路径时必须删除，或进入 fail-closed。"),
    ("Configure provider API keys only for the data sources you actually use; do not store keys in source code.", "只为实际使用的数据源配置 API key；不要把 key 写进源码。"),
    ("No live order path must remain enforced.", "禁止实盘下单边界必须持续生效。"),
    ("No workflow inputs have been recorded.", "尚未记录可追溯的工作流输入。"),
    ("ResearchBus interoperability status=Warn.", "研究总线互通状态为需关注。"),
    ("Policy Evidence", "政策证据"),
    ("Consumption Evidence", "消费证据"),
    ("BalanceSnapshot", "余额快照"),
    ("RunMetadata", "运行元数据"),
    ("Data Trust", "数据边界"),
    ("2/8 Pass", "2/8 通过"),
    ("=Review", "=需复核"),
    ("=Pass", "=通过"),
    ("=Fail", "=失败"),
    ("Warn/Fail", "需关注/失败"),
    ("Warn", "需关注"),
    ("Fail 项", "失败项"),
    ("audit_status=Review", "审计状态=需复核"),
    ("report_evidence_layer=Review", "报告证据层=需复核"),
    ("audit_status", "审计状态"),
    ("report_evidence_layer", "报告证据层"),
    ("run_metadata", "运行元数据"),
    ("review=", "需复核数="),
    ("rejected=", "拒绝数="),
    ("runtime_summary", "运行摘要"),
    ("cashflow_status", "现金流状态"),
    ("policy_status", "政策状态"),
    ("guard_status", "消费守卫状态"),
    ("balance=", "余额="),
    ("net=", "净现金流="),
    ("runway_days=", "Runway天数="),
    ("pending=", "待复核="),
    ("missing_evidence=", "缺证据="),
    ("opportunities=", "机会数="),
    ("actionable=", "可行动="),
    ("watch=", "观察="),
    ("spend=", "支出="),
    ("impulse=", "冲动支出="),
    ("fixed=", "固定成本="),
    ("pressure=", "现金流压力="),
    ("None", "缺失"),
    ("summary=", "摘要="),
    ("PFIOSEntityRegistryV1", "内部契约"),
    ("Entity Registry schema=", "标的注册表契约="),
    ("records=", "记录数="),
    ("'pass'", "'通过'"),
    ("'review'", "'复核'"),
    ("'fail'", "'失败'"),
    ("item_count", "检查项数"),
    ("CashFlow", "现金流"),
    ("Policy", "政策"),
    ("Consumption", "消费"),
    ("ResearchBus", "研究总线"),
    ("Research-only boundary remains active: no live trading, no real orders, no payments, no betting execution.", "研究专用边界持续生效：禁止实盘交易、真实订单、付款和自动下注。"),
    ("API key", "API 密钥"),
    ("fail-closed fallback", "失败即停止兜底"),
    ("fail-closed", "失败即停止"),
    ("fallback 到", "兜底读取"),
    ("compact runtime summary latest", "精简运行摘要 latest"),
    ("full latest", "完整 latest"),
)

COMMAND_CENTER_PDF_FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
)


def build_command_center(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    daily_readiness_payload: dict[str, Any] | None = None,
    integration_payload: dict[str, Any] | None = None,
    cashflow_payload: dict[str, Any] | None = None,
    policy_payload: dict[str, Any] | None = None,
    consumption_payload: dict[str, Any] | None = None,
    report_artifacts: pd.DataFrame | None = None,
    artifact_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    integration = integration_payload or build_pfi_os_integration_audit(
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
    scorecards = _scorecards(daily, integration, latest, risk_gates, business_systems)
    action_queue = _action_queue(daily, integration, latest, business_systems)
    status = _command_status(daily, integration, latest, business_systems)
    business_summary = _business_system_summary(cashflow, policy, consumption)
    return {
        "schema": "PFICommandCenterV1",
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
        "evidence_sources": _evidence_sources(root, latest, business_systems),
        "runtime_summary_sources": _runtime_summary_sources(root, business_systems),
        "business_system_summary": business_summary,
        "cashflow_summary": _cashflow_summary(cashflow),
        "policy_summary": _policy_summary(policy),
        "consumption_summary": _consumption_summary(consumption),
        "assumptions": [
            "总控驾驶舱只聚合本地证据，不刷新行情、不启动 Moomoo OpenD、不修改持仓、不连接实盘。",
            "所有输入必须进入证据层；没有证据的结论降级为观察或待复核。",
            "所有结论必须经过风控层；Blocked 或 NeedsReview 不应作为交易前参考。",
            "CashFlow、Policy、Consumption 只读取本地 latest 快照或 fail-closed fallback，不连接银行、支付、政府平台、支付宝、税务、工资或券商系统。",
            "总控优先读取 CashFlow、Policy、Consumption 的 compact runtime summary latest；缺失时才 fallback 到 full latest 或本地 fail-closed 构建。",
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
        cashflow_payload=cashflow_payload,
        policy_payload=policy_payload,
        consumption_payload=consumption_payload,
        report_artifacts=report_artifacts,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "commandCenter"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"PFICommandCenter_{stamp}"
    json_path = target / f"{stem}.json"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "PFICommandCenter_latest.json"
    latest_markdown = target / "PFICommandCenter_latest.md"
    latest_pdf = target / "PFICommandCenter_latest.pdf"
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
        f"# PFI OS 总控报告 {payload.get('as_of', '')}",
        "",
        "## 总览",
        f"- 系统：`{payload.get('display_name', MASTER_DISPLAY_NAME)}`",
        f"- 状态：`{_display_text(payload.get('command_status', ''))}`",
        f"- 原因：{_display_text(payload.get('status_reason', ''))}",
        f"- 生成时间：`{payload.get('generated_at', '')}`",
        "",
        "## 核心状态",
        _markdown_table(payload.get("scorecards", []), ["metric", "value", "status", "evidence"]),
        "",
        "## 风控闸门",
        _markdown_table(payload.get("risk_gates", []), ["gate", "status", "evidence", "next_action"]),
        "",
        "## 行动队列",
        _markdown_table(payload.get("action_queue", []), ["priority", "status", "owner", "action", "source"]),
        "",
        "## 证据来源",
        _markdown_table(payload.get("evidence_sources", []), ["source", "status", "path", "schema"]),
        "",
        "## 运行摘要来源",
        _markdown_table(payload.get("runtime_summary_sources", []), ["subsystem", "mode", "schema", "path"]),
        "",
        "## 业务子系统",
        _markdown_table(payload.get("business_system_summary", []), ["subsystem", "status", "metric", "value", "evidence"]),
        "",
        "## 约束与假设",
        *[f"- {_display_text(item)}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _command_status(
    daily: dict[str, Any],
    integration: dict[str, Any],
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
    latest: dict[str, Any],
    gates: list[dict[str, str]],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
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
    latest: dict[str, Any],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if integration.get("status") != "Pass":
        rows.append(
            {
                "priority": "P0",
                "status": "Open",
                "owner": "PFI_OS",
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
                "owner": "PFIOS",
                "action": str(item),
                "source": "Daily Readiness",
            }
        )
    if not latest.get("path"):
        rows.append(
            {
                "priority": "P1",
                "status": "Open",
                "owner": "PFIOS",
                "action": "生成一份带 RunMetadata、数据质量和风险闸门的正式 Word 研究报告。",
                "source": "Report Evidence",
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
                "owner": "PFI_OS",
                "action": "继续日常研究流程，所有结论保持证据化、风控化和研究用途。",
                "source": "Executive Command Center",
            }
        )
    return _dedupe_actions(rows)


def _evidence_sources(
    root: Path,
    latest: dict[str, Any],
    business_systems: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows = [
        _source_row("Daily Readiness", _latest_file(root / "data" / "systemAudit", "PFIOSDailyReadiness_*.json"), "PFIOSDailyReadinessV1"),
        _source_row("Integration Audit", _latest_file(root / "data" / "systemAudit", "PFIOSIntegrationAudit_*.json"), "PFIOSIntegrationAuditV1"),
        _source_row("Data Trust Audit", _latest_file(root / "data" / "systemAudit", "PFIOSDataTrustAudit_*.json"), "PFIOSDataTrustAuditV1"),
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
                _payload_schema(business_systems.get("cashflow", {}), "PFIOSCompanyCashFlowCommandV1"),
            ),
            _source_row(
                "Policy Intelligence Radar",
                _latest_payload_path(root, business_systems.get("policy", {}), "policy", "PolicyIntelligenceRuntimeSummary_latest.json", "PolicyIntelligenceRadar_latest.json"),
                _payload_schema(business_systems.get("policy", {}), "PFIOSPolicyIntelligenceRadarV1"),
            ),
            _source_row(
                "Consumption Guard",
                _latest_payload_path(root, business_systems.get("consumption", {}), "consumption", "ConsumptionGuardRuntimeSummary_latest.json", "ConsumptionGuard_latest.json"),
                _payload_schema(business_systems.get("consumption", {}), "PFIOSConsumptionGuardV1"),
            ),
        ]
    )
    return rows


def _runtime_summary_sources(root: Path, business_systems: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
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
    return _load_latest_schema(root / "data" / "cashflow" / "CompanyCashFlowRuntimeSummary_latest.json", "PFIOSCompanyCashFlowRuntimeSummaryV1") or _load_latest_schema(root / "data" / "cashflow" / "CompanyCashFlowCommand_latest.json", "PFIOSCompanyCashFlowCommandV1")


def _load_latest_policy(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "policy" / "PolicyIntelligenceRuntimeSummary_latest.json", "PFIOSPolicyIntelligenceRuntimeSummaryV1") or _load_latest_schema(root / "data" / "policy" / "PolicyIntelligenceRadar_latest.json", "PFIOSPolicyIntelligenceRadarV1")


def _load_latest_consumption(root: Path) -> dict[str, Any] | None:
    return _load_latest_schema(root / "data" / "consumption" / "ConsumptionGuardRuntimeSummary_latest.json", "PFIOSConsumptionGuardRuntimeSummaryV1") or _load_latest_schema(root / "data" / "consumption" / "ConsumptionGuard_latest.json", "PFIOSConsumptionGuardV1")


def _load_latest_schema(path: Path, schema: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) and payload.get("schema") == schema else None


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
    labels = [_column_label(column) for column in columns]
    if not rows:
        return "| " + " | ".join(labels) + " |\n| " + " | ".join("---" for _ in columns) + " |"
    header = "| " + " | ".join(labels) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_cell(row.get(column, ""), column) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def _cell(value: Any, column: str = "") -> str:
    text = str(value) if column == "path" else _display_text(value)
    return text.replace("\n", " ").replace("|", "/")


def _column_label(column: str) -> str:
    return COMMAND_CENTER_COLUMN_LABELS.get(column, column)


def _display_text(value: Any) -> str:
    text = str(value)
    if text.startswith(("PFIOS", "PFICommandCenter")) and text.endswith("V1"):
        return "内部契约"
    text = text.replace("PFIOSEntityRegistryV1", "内部契约")
    text = COMMAND_CENTER_DISPLAY_VALUES.get(text, text)
    for source, replacement in COMMAND_CENTER_TEXT_REPLACEMENTS:
        text = text.replace(source, replacement)
    return text


def _write_command_center_pdf(path: Path, payload: dict[str, Any]) -> None:
    if _write_command_center_image_pdf(path, payload):
        return
    markdown = command_center_markdown(payload)
    if _write_command_center_pdf_with_textutil(path, markdown):
        return
    _write_command_center_ascii_pdf(path, payload)


def _write_command_center_image_pdf(path: Path, payload: dict[str, Any]) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return False
    font_path = next((Path(candidate) for candidate in COMMAND_CENTER_PDF_FONT_CANDIDATES if Path(candidate).exists()), None)
    if font_path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 1240, 1754
        margin = 72
        line_gap = 12
        title_font = ImageFont.truetype(str(font_path), 34)
        body_font = ImageFont.truetype(str(font_path), 24)
        small_font = ImageFont.truetype(str(font_path), 20)
        pages: list[Any] = []
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        y = margin

        def new_page() -> None:
            nonlocal image, draw, y
            pages.append(image)
            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)
            y = margin

        for line, role in _command_center_pdf_lines(payload):
            font = title_font if role == "title" else small_font if role == "small" else body_font
            max_width = width - margin * 2
            wrapped = _wrap_pdf_line(draw, line, font, max_width) or [""]
            for wrapped_line in wrapped:
                line_height = int(font.getbbox(wrapped_line or "国")[3] - font.getbbox(wrapped_line or "国")[1]) + line_gap
                if y + line_height > height - margin:
                    new_page()
                draw.text((margin, y), wrapped_line, fill=(22, 28, 36), font=font)
                y += line_height
        pages.append(image)
        pages[0].save(path, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
        return path.exists() and path.stat().st_size > 1000
    except Exception:
        return False


def _wrap_pdf_line(draw: Any, line: str, font: Any, max_width: int) -> list[str]:
    if not line:
        return [""]
    chunks: list[str] = []
    current = ""
    for char in line:
        candidate = f"{current}{char}"
        if current and draw.textlength(candidate, font=font) > max_width:
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _command_center_pdf_lines(payload: dict[str, Any]) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = [
        (f"PFI OS 总控报告 {payload.get('as_of', '')}", "title"),
        (f"系统：{payload.get('display_name', MASTER_DISPLAY_NAME)}", "body"),
        (f"状态：{_display_text(payload.get('command_status', ''))}", "body"),
        (f"原因：{_display_text(payload.get('status_reason', ''))}", "body"),
        (f"生成时间：{payload.get('generated_at', '')}", "small"),
        ("", "body"),
        ("核心状态", "body"),
    ]
    for row in payload.get("scorecards", [])[:8]:
        lines.append((f"- {_display_text(row.get('metric', ''))}：{_display_text(row.get('value', ''))}｜{_display_text(row.get('status', ''))}", "small"))
    lines.extend([("", "body"), ("业务子系统", "body")])
    for row in payload.get("business_system_summary", [])[:6]:
        lines.append((f"- {_display_text(row.get('subsystem', ''))}：{_display_text(row.get('value', ''))}｜{_display_text(row.get('status', ''))}", "small"))
    lines.extend([("", "body"), ("行动队列", "body")])
    for row in payload.get("action_queue", [])[:12]:
        lines.append((f"- {_display_text(row.get('priority', ''))} {_display_text(row.get('action', ''))} [{_display_text(row.get('source', ''))}]", "small"))
    lines.extend([("", "body"), ("研究管理专用。禁止实盘自动下单、禁止真实订单、禁止付款、禁止自动下注。", "small")])
    return lines


def _write_command_center_pdf_with_textutil(path: Path, markdown: str) -> bool:
    textutil = shutil.which("textutil")
    if not textutil:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="pfi_command_center_pdf_") as tmp:
            source = Path(tmp) / "PFICommandCenter.md"
            source.write_text(markdown, encoding="utf-8")
            result = subprocess.run(
                [textutil, "-convert", "pdf", "-output", str(path), str(source)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=30,
            )
        if result.returncode != 0 or not path.exists() or path.stat().st_size <= 1000:
            return False
        if b"????" in path.read_bytes():
            path.unlink(missing_ok=True)
            return False
        return True
    except Exception:
        return False


def _write_command_center_ascii_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"PFI OS Command Center {payload.get('as_of', '')}",
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
    lines.extend(["", "Research-only. No live trading. No real orders."])
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
    normalized = (
        text.replace("需要复核：", "Needs review: ")
        .replace("已写入", "Written ")
        .replace("正式持仓", "canonical holdings")
        .replace("源文件", "source files")
    )
    return normalized.encode("latin-1", errors="ignore").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
