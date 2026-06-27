from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Iterable

from pfi_v02.stage3_read_mvp import STAGE3_FX_TO_AUD, build_stage3_read_model
from pfi_v02.stage4_analysis_mvp import build_stage4_analysis_model


RECOMMENDATION_DECISIONS = ("pending", "accept", "reject", "snooze", "review", "effect_measured")
EXPORT_FORMATS = ("markdown", "json", "csv")
ALPHA_CONTEXT_SCHEMA = "pfi_context_snapshot_v1"


@dataclass(frozen=True)
class Stage5Recommendation:
    recommendation_id: str
    domain: str
    evidence_refs: tuple[str, ...]
    expected_effect: str
    tradeoff_risk: str
    suggested_action: str
    owner_decision: str
    status: str
    priority: int
    target_entry: str
    recommendation_type: str
    savings_target_aud: float = 0.0
    review_after_days: int = 30

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_stage5_delivery_model(
    *,
    stage3_dashboard: dict[str, object] | None = None,
    stage4_dashboard: dict[str, object] | None = None,
    now: datetime | None = None,
    top_n: int = 3,
) -> dict[str, object]:
    stage3 = stage3_dashboard or build_stage3_read_model(now=now)
    stage4 = stage4_dashboard or build_stage4_analysis_model(stage3_dashboard=stage3, now=now)
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    recommendations = build_stage5_recommendations(stage4)
    lifecycle = build_recommendation_lifecycle(recommendations)
    top_recommendations = rank_top_recommendations(recommendations, top_n=top_n)
    reports = build_report_suite(stage3, stage4, recommendations, generated_at=generated_at)
    export_center = build_export_center(reports, generated_at=generated_at)
    alpha_context = build_alpha_context_snapshot(stage3, stage4, generated_at=generated_at)
    return {
        "schema": "PFIV02Stage5AdviceReportAlphaExportV1",
        "stage": "PFI V0.2 Stage 5",
        "generated_at": generated_at,
        "stage4_schema": stage4.get("schema", ""),
        "recommendations": [item.to_dict() for item in recommendations],
        "review_lifecycle": lifecycle,
        "top_recommendations": [item.to_dict() for item in top_recommendations],
        "reports": reports,
        "export_center": export_center,
        "alpha_context_export": alpha_context,
        "alpha_independence": {
            "alpha_repo_modified": False,
            "alpha_first_level_entry_added": False,
            "pfi_exports_context_only": True,
            "statement": "Alpha remains an independent system. PFI only exports a read-only context snapshot for Alpha to consume outside this repository task.",
        },
        "compatibility": {
            "primary_entry_count": 8,
            "alpha_first_level_entry_added": False,
            "ralpha_first_level_entry_added": False,
            "system_first_level_entry_added": False,
            "qbvs_runtime_moved": False,
        },
        "boundaries": (
            "recommendations_are_review_queue_items_not_orders",
            "reports_are_local_reproducible_exports",
            "alpha_context_is_read_only",
            "no_alpha_repository_modification",
            "no_trading_password",
            "no_broker_order_submission",
            "no_payment_submission",
            "live_trade_submission_authorized_false",
        ),
    }


def build_stage5_recommendations(stage4_dashboard: dict[str, object]) -> tuple[Stage5Recommendation, ...]:
    investment = stage4_dashboard["investment_analysis"]
    consumption = stage4_dashboard["consumption_analysis"]
    risk = investment["risk"]
    behavior = investment["behavior"]
    summary = investment["summary"]
    cashflow = consumption["cashflow_forecast"]
    recurring = consumption["recurring"]
    anomalies = consumption["anomalies"]
    con_summary = consumption["summary"]
    largest = risk["concentration"]
    trading_status = "有建议" if behavior.get("trade_count", 0) else "需要同步"
    return (
        Stage5Recommendation(
            "rec_inv_concentration",
            "investment",
            tuple(largest["evidence_refs"]),
            "降低单一持仓对净值波动的影响。",
            "过早降低集中度可能牺牲上涨弹性。",
            "复核最大持仓集中度，必要时设置人工减仓观察线。",
            "pending",
            str(largest["status"]),
            1,
            "投资管理",
            "concentration",
        ),
        Stage5Recommendation(
            "rec_inv_trading_frequency",
            "investment",
            tuple(behavior.get("evidence_refs", ())) or ("trades:missing",),
            "减少追涨、杀跌和短持有周期导致的摩擦成本。",
            "交易减少可能错过短线机会。",
            "把频繁交易标签进入 30 天复盘，暂停无证据短线操作。",
            "pending",
            trading_status,
            2,
            "建议与复盘",
            "trading_frequency",
        ),
        Stage5Recommendation(
            "rec_inv_cash_position",
            "investment",
            ("cashflow:stage4_fixture", "stage3:accounts"),
            f"维持生活 reserve 后，可投资现金约 AUD {cashflow['horizons'][0]['available_to_invest_aud']:,.2f}。",
            "现金过低会增加生活现金流压力。",
            "确认生活现金 reserve 后再决定是否把可投资现金转入策略观察池。",
            "pending",
            str(cashflow["horizons"][0]["cashflow_pressure"]),
            3,
            "投资管理",
            "cash_position",
        ),
        Stage5Recommendation(
            "rec_inv_strategy_control",
            "investment",
            ("PFI/modules/qbvs_lab/qbvs", "strategy:stage4_compatibility"),
            "把策略上线/暂停作为人工 gate，避免分析结果直接变成订单。",
            "过度保守会降低策略迭代速度。",
            "只允许策略实验室进入复核；上线/暂停由 owner 手动决定。",
            "pending",
            "有建议",
            4,
            "投资管理",
            "strategy_pause_or_launch",
        ),
        Stage5Recommendation(
            "rec_con_budget",
            "consumption",
            ("consumption:summary", "budget:stage4_fixture"),
            f"把剩余预算 AUD {con_summary['budget_remaining_aud']:,.2f} 作为本月弹性支出上限。",
            "预算过紧可能影响必要生活支出。",
            "设置本月剩余预算提醒，优先保护固定支出和生活 reserve。",
            "pending",
            "有建议",
            5,
            "消费管理",
            "budget",
            savings_target_aud=max(0.0, min(250.0, float(con_summary["flexible_spend_aud"]) * 0.08)),
        ),
        Stage5Recommendation(
            "rec_con_subscription",
            "consumption",
            tuple(item["evidence_ref"] for item in recurring["candidates"]),
            "取消或保留订阅前先确认使用价值。",
            "误删必要订阅会影响学习、工作或生活。",
            "复核所有周期扣费，标记保留、取消或暂缓。",
            "pending",
            "有建议" if recurring["candidate_count"] else "正常",
            6,
            "消费管理",
            "subscription",
            savings_target_aud=sum(float(item["amount_aud"]) for item in recurring["candidates"]),
        ),
        Stage5Recommendation(
            "rec_con_anomaly",
            "consumption",
            tuple(item["evidence_ref"] for item in anomalies["anomalies"]),
            "减少重复、大额、夜间和冲动型消费。",
            "异常不一定都是错误，必须人工复核。",
            "逐条处理异常消费，确认重复扣费或冲动消费是否需要退款/复盘。",
            "pending",
            "需要复核" if anomalies["anomaly_count"] else "正常",
            7,
            "消费管理",
            "anomaly",
            savings_target_aud=min(500.0, sum(float(item["amount_aud"]) for item in anomalies["anomalies"]) * 0.25),
        ),
        Stage5Recommendation(
            "rec_con_cost_saving",
            "consumption",
            ("consumption:classification", "consumption:cashflow"),
            "形成可量化降成本目标并在月末复盘。",
            "只追求节省可能压缩必要投入。",
            "设定 AUD 300.00 月度降成本目标，优先来自订阅和异常消费。",
            "pending",
            "有建议",
            8,
            "建议与复盘",
            "cost_saving",
            savings_target_aud=300.0,
        ),
    )


def build_recommendation_lifecycle(recommendations: Iterable[Stage5Recommendation]) -> dict[str, object]:
    rows = []
    for item in recommendations:
        rows.append(
            {
                "recommendation_id": item.recommendation_id,
                "supported_decisions": RECOMMENDATION_DECISIONS,
                "current_decision": item.owner_decision,
                "status": item.status,
                "review_after_days": item.review_after_days,
                "effect_measurement": {
                    "metric": "expected_effect_progress",
                    "baseline": 0.0,
                    "target": item.savings_target_aud if item.savings_target_aud else 1.0,
                    "actual": None,
                    "requires_follow_up": True,
                },
            }
        )
    return {
        "schema": "PFIRecommendationLifecycleV1",
        "rows": tuple(rows),
        "decision_record_supported": True,
        "manual_review_required": True,
    }


def apply_recommendation_decision(
    recommendation: Stage5Recommendation,
    decision: str,
    *,
    measured_effect: float | None = None,
    decided_at: str = "2026-06-27T12:30:00+10:00",
) -> dict[str, object]:
    if decision not in RECOMMENDATION_DECISIONS:
        raise ValueError("decision must be pending, accept, reject, snooze, review, or effect_measured")
    updated = replace(
        recommendation,
        owner_decision=decision,
        status="已复盘" if decision == "effect_measured" else ("已接受" if decision == "accept" else "需要复核"),
    )
    return {
        "recommendation": updated.to_dict(),
        "decision_record": {
            "recommendation_id": recommendation.recommendation_id,
            "decision": decision,
            "decided_at": decided_at,
            "measured_effect": measured_effect,
            "evidence_refs": recommendation.evidence_refs,
        },
        "effect_measurement": {
            "enabled": True,
            "target": recommendation.savings_target_aud if recommendation.savings_target_aud else 1.0,
            "actual": measured_effect,
            "status": "measured" if measured_effect is not None else "pending",
        },
    }


def rank_top_recommendations(
    recommendations: Iterable[Stage5Recommendation],
    *,
    top_n: int = 3,
) -> tuple[Stage5Recommendation, ...]:
    ranked = sorted(
        recommendations,
        key=lambda item: (
            _status_rank(item.status),
            item.priority,
            -item.savings_target_aud,
            item.recommendation_id,
        ),
    )
    return tuple(ranked[:top_n])


def build_report_suite(
    stage3_dashboard: dict[str, object],
    stage4_dashboard: dict[str, object],
    recommendations: tuple[Stage5Recommendation, ...],
    *,
    generated_at: str,
) -> dict[str, object]:
    stage3 = stage3_dashboard
    stage4 = stage4_dashboard
    recommendation_review = _recommendation_review_summary(recommendations)
    return {
        "monthly_report": _report(
            "monthly_report",
            "月度报告",
            ("净资产", "现金流", "消费", "投资", "建议复盘"),
            {
                "net_worth": _net_worth_aud(stage3),
                "cashflow": stage4["consumption_analysis"]["cashflow_forecast"],
                "consumption": stage4["consumption_analysis"]["summary"],
                "investment": stage4["investment_analysis"]["summary"],
                "recommendation_review": recommendation_review,
            },
            ("stage3:home", "stage4:analysis", "stage5:recommendations"),
            generated_at,
        ),
        "investment_report": _report(
            "investment_report",
            "投资报告",
            ("收益", "风险", "归因", "持仓", "行为复盘"),
            {
                "return": stage4["investment_analysis"]["summary"],
                "risk": stage4["investment_analysis"]["risk"],
                "attribution": stage4["investment_analysis"]["attribution"],
                "positions": stage4["investment_analysis"]["summary"]["asset_allocation_pct"],
                "behavior": stage4["investment_analysis"]["behavior"],
            },
            ("stage4:investment", "stage4:attribution", "stage4:risk"),
            generated_at,
        ),
        "consumption_report": _report(
            "consumption_report",
            "消费报告",
            ("分类", "预算", "订阅", "异常", "节省金额"),
            {
                "classification": stage4["consumption_analysis"]["classification"],
                "budget": stage4["consumption_analysis"]["summary"],
                "subscriptions": stage4["consumption_analysis"]["recurring"],
                "anomalies": stage4["consumption_analysis"]["anomalies"],
                "saving_target_aud": sum(item.savings_target_aud for item in recommendations if item.domain == "consumption"),
            },
            ("stage4:consumption", "stage5:consumption_recommendations"),
            generated_at,
        ),
        "data_quality_report": _report(
            "data_quality_report",
            "数据质量报告",
            ("同步状态", "缺失区间", "对账差异", "parser 错误"),
            {
                "sync_status": stage3.get("account_map", []),
                "missing_intervals": _missing_intervals(stage3),
                "reconciliation_differences": [row for row in stage3.get("reconciliation", []) if row.get("status") != "正常"],
                "parser_errors": _parser_errors(stage3),
            },
            ("stage3:account_map", "stage3:reconciliation", "stage3:ledger_source_trace"),
            generated_at,
        ),
    }


def build_export_center(reports: dict[str, object], *, generated_at: str) -> dict[str, object]:
    markdown_payload = _reports_to_markdown(reports)
    json_payload = json.dumps(reports, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    csv_payload = _reports_to_csv(reports)
    exports = (
        _export_item("stage5_reports_markdown", "markdown", "PFI_reports_stage5.md", markdown_payload, generated_at),
        _export_item("stage5_reports_json", "json", "PFI_reports_stage5.json", json_payload, generated_at),
        _export_item("stage5_reports_csv", "csv", "PFI_reports_stage5.csv", csv_payload, generated_at),
    )
    return {
        "schema": "PFIExportCenterV1",
        "preferred_formats": EXPORT_FORMATS,
        "exports": exports,
        "reproducible": True,
        "reproducibility_key": _sha256_text("|".join(item["content_sha256"] for item in exports)),
    }


def build_alpha_context_snapshot(
    stage3_dashboard: dict[str, object],
    stage4_dashboard: dict[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    cashflow = stage4_dashboard["consumption_analysis"]["cashflow_forecast"]
    behavior = stage4_dashboard["investment_analysis"]["behavior"]
    risk = stage4_dashboard["investment_analysis"]["risk"]
    return {
        "schema": ALPHA_CONTEXT_SCHEMA,
        "version": "1.0.0",
        "generated_at": generated_at,
        "source": {
            "project": "PFI",
            "source_schema": stage4_dashboard.get("schema", ""),
            "read_only": True,
        },
        "net_worth_aud": _net_worth_aud(stage3_dashboard),
        "investable_cash_aud": cashflow["horizons"][0]["available_to_invest_aud"],
        "portfolio_allocation": stage4_dashboard["investment_analysis"]["summary"]["asset_allocation_pct"],
        "risk_budget": {
            "max_single_position_weight_pct": 35.0,
            "current_largest_weight_pct": risk["concentration"]["largest_weight_pct"],
            "max_drawdown_watch_pct": 10.0,
            "reserve_floor_aud": cashflow["reserve_floor_aud"],
            "status": risk["concentration"]["status"],
        },
        "cashflow_pressure": cashflow["horizons"][0]["cashflow_pressure"],
        "behavior_tags": tuple(behavior.get("conclusions", ())),
        "data_freshness": {
            "account_statuses": tuple(row.get("status", "") for row in stage3_dashboard.get("account_map", [])),
            "ledger_rows": len(stage3_dashboard.get("ledger", [])),
            "review_queue_count": len(stage3_dashboard.get("review_queue", [])),
            "source": "stage3_read_model",
        },
        "constraints": {
            "trading_password_available": False,
            "live_trade_submission_authorized": False,
            "broker_order_submission_authorized": False,
            "payment_submission_authorized": False,
        },
    }


def _report(
    report_id: str,
    title: str,
    required_sections: tuple[str, ...],
    sections: dict[str, object],
    evidence_refs: tuple[str, ...],
    generated_at: str,
) -> dict[str, object]:
    return {
        "report_id": report_id,
        "title": title,
        "generated_at": generated_at,
        "required_sections": required_sections,
        "sections": sections,
        "evidence_refs": evidence_refs,
        "has_evidence_chain": bool(evidence_refs),
        "status": "ready",
    }


def _recommendation_review_summary(recommendations: tuple[Stage5Recommendation, ...]) -> dict[str, object]:
    return {
        "total": len(recommendations),
        "pending": sum(1 for item in recommendations if item.owner_decision == "pending"),
        "domains": sorted({item.domain for item in recommendations}),
        "evidence_refs": tuple(ref for item in recommendations for ref in item.evidence_refs[:1]),
    }


def _missing_intervals(stage3_dashboard: dict[str, object]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "source_id": str(row.get("source_id", "")),
            "status": str(row.get("status", "")),
            "missing_interval": "needs_owner_sync" if row.get("status") != "正常" else "none",
        }
        for row in stage3_dashboard.get("account_map", [])
    )


def _parser_errors(stage3_dashboard: dict[str, object]) -> tuple[dict[str, str], ...]:
    rows = []
    for row in stage3_dashboard.get("ledger", []):
        trace = row.get("source_trace", {}) if isinstance(row, dict) else {}
        if not trace.get("parser_version"):
            rows.append({"transaction_id": str(row.get("transaction_id", "")), "error": "missing_parser_version"})
    return tuple(rows)


def _reports_to_markdown(reports: dict[str, object]) -> str:
    lines = ["# PFI Stage 5 Reports", ""]
    for report in reports.values():
        lines.append(f"## {report['title']}")
        lines.append(f"- report_id: `{report['report_id']}`")
        lines.append(f"- evidence_refs: {', '.join(report['evidence_refs'])}")
        lines.append(f"- sections: {', '.join(report['required_sections'])}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _reports_to_csv(reports: dict[str, object]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=("report_id", "title", "section_count", "evidence_count", "status"))
    writer.writeheader()
    for report in reports.values():
        writer.writerow(
            {
                "report_id": report["report_id"],
                "title": report["title"],
                "section_count": len(report["required_sections"]),
                "evidence_count": len(report["evidence_refs"]),
                "status": report["status"],
            }
        )
    return buffer.getvalue()


def _export_item(export_id: str, export_format: str, filename: str, content: str, generated_at: str) -> dict[str, object]:
    return {
        "export_id": export_id,
        "format": export_format,
        "filename": filename,
        "generated_at": generated_at,
        "content_sha256": _sha256_text(content),
        "byte_length": len(content.encode("utf-8")),
        "reproducible": True,
    }


def _net_worth_aud(stage3_dashboard: dict[str, object]) -> float:
    total = 0.0
    for account in stage3_dashboard.get("accounts", []):
        if not isinstance(account, dict):
            continue
        currency = str(account.get("currency", "AUD"))
        total += float(account.get("ledger_balance", 0.0)) * STAGE3_FX_TO_AUD[currency]
    return round(total, 2)


def _status_rank(status: str) -> int:
    if status in {"需要复核", "有异常"}:
        return 0
    if status in {"有建议", "需要同步"}:
        return 1
    return 2


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
