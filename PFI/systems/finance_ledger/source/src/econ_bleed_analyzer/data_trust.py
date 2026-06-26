from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from .classifier import ClassifiedTransaction
from .review import ReviewDecisions, review_key


TRUST_STATUSES = (
    "RAW_IMPORTED",
    "PARSED_CANDIDATE",
    "NEEDS_REVIEW",
    "USER_CONFIRMED",
    "RECONCILED",
    "ARCHIVED",
    "REJECTED",
)


def build_data_trust_transactions(
    rows: list[ClassifiedTransaction],
    *,
    review_decisions: ReviewDecisions | None = None,
    allocation_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    production_keys = {str(item.get("review_key", "")) for item in allocation_rows or [] if item.get("review_key")}
    output: list[dict[str, Any]] = []
    for row in rows:
        key = review_key(row)
        status, reason, ledger_effect, decision_grade = _transaction_status(row, key, production_keys, review_decisions)
        output.append(
            {
                "transaction_key": key,
                "data_trust_status": status,
                "evidence_classification": _evidence_classification(status),
                "decision_grade": decision_grade,
                "ledger_effect": ledger_effect,
                "review_required": status == "NEEDS_REVIEW",
                "review_key": key,
                "source_platform": row.source_platform,
                "source_file": row.source_file,
                "transaction_time": row.transaction_time,
                "date": row.date,
                "order_id": row.order_id,
                "counterparty": row.counterparty,
                "description": row.description,
                "direction": row.direction,
                "amount": row.amount,
                "amount_cents": row.amount_cents,
                "cash_flow_type": row.cash_flow_type,
                "primary_bucket": row.primary_bucket,
                "main_category": row.main_category,
                "sub_category": row.sub_category,
                "rule_name": row.rule_name,
                "classification_reason": row.classification_reason,
                "status_reason": reason,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return output


def build_data_trust_sources(source_archives: list[dict[str, object]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, item in enumerate(source_archives, start=1):
        extracted_path = str(item.get("extracted_path", "") or "")
        archive_hash = str(item.get("archive_sha256", "") or "")
        member_hash = str(item.get("member_sha256", "") or "")
        output.append(
            {
                "source_key": member_hash or archive_hash or f"source_{index}",
                "data_trust_status": "RAW_IMPORTED",
                "archive_status": "ARCHIVED" if extracted_path else "RAW_IMPORTED",
                "evidence_classification": "FACT",
                "decision_grade": "Observe",
                "source_type": item.get("source_type", ""),
                "bill_period": item.get("bill_period", ""),
                "archive_path": item.get("archive_path", ""),
                "archive_sha256": archive_hash,
                "member_name": item.get("member_name", ""),
                "member_sha256": member_hash,
                "extracted_path": extracted_path,
                "size_bytes": item.get("size_bytes", ""),
                "status_reason": "原始账单文件已入库并保留 hash / extracted path 作为溯源证据。",
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return output


def summarize_data_trust(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(item.get("data_trust_status", "")) for item in rows)
    total = sum(counts.values())
    return [
        {
            "data_trust_status": status,
            "count": counts.get(status, 0),
            "count_pct": _format_pct(counts.get(status, 0), total),
        }
        for status in TRUST_STATUSES
        if counts.get(status, 0) or status in {"NEEDS_REVIEW", "RECONCILED", "REJECTED"}
    ]


def data_trust_report_markdown(transaction_rows: list[dict[str, Any]]) -> str:
    summary = summarize_data_trust(transaction_rows)
    lines = [
        "# Data Trust Layer 审计报告",
        "",
        "本报告说明消费分析系统逐笔交易的可信度状态。该层只用于审计、复核、跨系统读取和下游决策降级，不改变既有分类、金额、复核和生产统计口径。",
        "",
        "## 状态定义",
        "",
        "| 状态 | 含义 | 下游动作 |",
        "|---|---|---|",
        "| RAW_IMPORTED | 原始账单文件已入库或归档 | 仅作为源文件证据，不直接进入统计 |",
        "| PARSED_CANDIDATE | 已解析和分类，但未进入生产分摊或不属于支出口径 | 可观察，不作为控制动作依据 |",
        "| NEEDS_REVIEW | 大额、默认规则或无法识别交易 | 必须人工复核，未确认前不入生产统计 |",
        "| USER_CONFIRMED | 用户复核文件已确认纳入或排除 | 按确认结果处理 |",
        "| RECONCILED | 已进入生产分摊并可和月度汇总对账 | 可供下游只读使用 |",
        "| ARCHIVED | 原始文件已稳定归档并保留 hash | 作为溯源证据 |",
        "| REJECTED | 失败、关闭或明确排除的交易 | 不进入生产统计 |",
        "",
        "## 当前分布",
        "",
        "| 状态 | 笔数 | 占比 |",
        "|---|---:|---:|",
    ]
    for item in summary:
        lines.append(f"| {item['data_trust_status']} | {item['count']} | {item['count_pct']} |")
    lines.extend(
        [
            "",
            "## 口径说明",
            "",
            "- 金额公式不变：生产支出仍以 `production_expense_allocations.allocated_amount_cents / 100` 为准。",
            "- 对账公式：`sum(production_expense_allocations.allocated_amount_cents) / 100` 应等于月度汇总支出合计，容差 0.05 元。",
            "- 大额复核公式不变：单笔支出 `amount_cents >= 1,000,000` 进入复核队列。",
            "- Data Trust 状态只决定证据等级和下游读取优先级，不自动执行支付、投资、转账或交易。",
        ]
    )
    return "\n".join(lines) + "\n"


def _transaction_status(
    row: ClassifiedTransaction,
    key: str,
    production_keys: set[str],
    review_decisions: ReviewDecisions | None,
) -> tuple[str, str, str, str]:
    if review_decisions and key in review_decisions.excluded:
        return "USER_CONFIRMED", "用户复核确认排除。", "excluded_by_user_review", "Reject"
    if review_decisions and key in review_decisions.included:
        if key in production_keys:
            return "RECONCILED", "用户复核确认纳入且已进入生产分摊。", "production_reconciled_after_user_review", "Actionable"
        return "USER_CONFIRMED", "用户复核确认纳入，但未在生产分摊表中找到对账记录。", "user_confirmed_not_reconciled", "Watch"
    if key in production_keys:
        return "RECONCILED", "交易已进入生产分摊表，可与汇总口径对账。", "production_reconciled", "Actionable"
    if row.needs_review:
        return "NEEDS_REVIEW", "大额支出未确认，按 fail-closed 原则隔离。", "blocked_until_manual_review", "Watch"
    if row.rule_name == "default" or row.mechanism == "未识别":
        return "NEEDS_REVIEW", "默认规则或未识别机制，需要人工复核。", "blocked_until_manual_review", "Watch"
    if row.cash_flow_type == "excluded" or row.primary_bucket == "excluded":
        return "REJECTED", "失败、关闭或明确排除交易。", "not_in_production", "Reject"
    return "PARSED_CANDIDATE", "交易已解析分类，但不属于当前生产支出分摊记录。", "not_current_production_expense", "Observe"


def _evidence_classification(status: str) -> str:
    if status in {"RAW_IMPORTED", "ARCHIVED", "USER_CONFIRMED", "RECONCILED", "REJECTED"}:
        return "FACT"
    if status == "NEEDS_REVIEW":
        return "OBSERVATION"
    return "INFERENCE"


def _format_pct(value: int, total: int) -> str:
    if total <= 0:
        return "0.00%"
    return f"{value / total * 100:.2f}%"
