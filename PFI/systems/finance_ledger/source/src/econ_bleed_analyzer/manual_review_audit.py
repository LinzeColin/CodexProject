from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "manual_review_queue_audit.v1"


def build_manual_review_audit_rows(
    *,
    review_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    data_trust_rows: list[dict[str, Any]],
    invalid_decision_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build a read-only audit layer for manual review queue operations."""
    generated_at = datetime.now().isoformat(timespec="seconds")
    candidate_by_key = {str(row.get("review_key", "")): row for row in candidate_rows}
    data_trust_by_key = {str(row.get("review_key", "")): row for row in data_trust_rows}
    invalid_rows = invalid_decision_rows or []
    rows: list[dict[str, Any]] = []
    for row in review_rows:
        key = str(row.get("review_key") or row.get("order_id") or _fallback_review_key(row))
        candidate = candidate_by_key.get(key, {})
        trust = data_trust_by_key.get(key, {})
        amount = _float(row.get("amount"))
        priority, reason = _priority_for_pending(amount, candidate, trust)
        rows.append(
            {
                "review_key": key,
                "queue_status": "PENDING_REVIEW",
                "priority": priority,
                "priority_reason": reason,
                "evidence_classification": "OBSERVATION",
                "decision_grade": "Watch",
                "ledger_effect": "blocked_until_manual_review",
                "next_action": _next_action_for_pending(candidate),
                "candidate_action": candidate.get("candidate_action", "manual_review"),
                "candidate_confidence": candidate.get("candidate_confidence", "low"),
                "candidate_main_category": candidate.get("candidate_main_category") or row.get("main_category", ""),
                "candidate_sub_category": candidate.get("candidate_sub_category") or row.get("sub_category", ""),
                "candidate_reason": candidate.get("candidate_reason", "缺少候选动作，保持人工复核。"),
                "data_trust_status": trust.get("data_trust_status", "NEEDS_REVIEW"),
                "data_trust_reason": trust.get("status_reason", ""),
                "amount": amount,
                "amount_cents": _int(row.get("amount_cents")),
                "transaction_time": row.get("transaction_time") or row.get("date", ""),
                "source_platform": row.get("source_platform", ""),
                "counterparty": row.get("counterparty", ""),
                "description": row.get("description", ""),
                "current_main_category": row.get("main_category", row.get("current_main_category", "")),
                "current_sub_category": row.get("sub_category", row.get("current_sub_category", "")),
                "current_risk_tags": row.get("risk_tags", row.get("current_risk_tags", "")),
                "source_table": "manual_review_queue",
                "generated_at": generated_at,
                "schema_version": SCHEMA_VERSION,
            }
        )
    for index, invalid in enumerate(invalid_rows, start=1):
        key = str(invalid.get("review_key") or invalid.get("order_id") or f"invalid_decision_{index}")
        rows.append(
            {
                "review_key": key,
                "queue_status": "INVALID_DECISION",
                "priority": "P0",
                "priority_reason": "复核确认文件存在无效行，必须修正后重建。",
                "evidence_classification": "FACT",
                "decision_grade": "Reject",
                "ledger_effect": "blocked_until_decision_file_fixed",
                "next_action": "修正 review_decisions CSV 的无效行，然后重跑 weekly_update.py。",
                "candidate_action": "fix_decision_file",
                "candidate_confidence": "high",
                "candidate_main_category": "",
                "candidate_sub_category": "",
                "candidate_reason": json.dumps(invalid, ensure_ascii=False, default=str),
                "data_trust_status": "NEEDS_REVIEW",
                "data_trust_reason": "invalid review decision row",
                "amount": _float(invalid.get("amount")),
                "amount_cents": _int(invalid.get("amount_cents")),
                "transaction_time": invalid.get("transaction_time", ""),
                "source_platform": invalid.get("source_platform", ""),
                "counterparty": invalid.get("counterparty", ""),
                "description": invalid.get("description", ""),
                "current_main_category": invalid.get("main_category", ""),
                "current_sub_category": invalid.get("sub_category", ""),
                "current_risk_tags": invalid.get("risk_tags", ""),
                "source_table": "manual_review_invalid_rows",
                "generated_at": generated_at,
                "schema_version": SCHEMA_VERSION,
            }
        )
    if not rows:
        for status in status_rows:
            if str(status.get("status", "")) == "pending_review":
                rows.append(
                    {
                        "review_key": "manual_review_queue_empty",
                        "queue_status": "EMPTY",
                        "priority": "P3",
                        "priority_reason": "当前没有仍待复核交易。",
                        "evidence_classification": "FACT",
                        "decision_grade": "Actionable",
                        "ledger_effect": "no_pending_review_blocker",
                        "next_action": "继续保持周更导入和输出校验。",
                        "candidate_action": "none",
                        "candidate_confidence": "high",
                        "candidate_main_category": "",
                        "candidate_sub_category": "",
                        "candidate_reason": str(status.get("next_action", "")),
                        "data_trust_status": "RECONCILED",
                        "data_trust_reason": "manual review queue empty",
                        "amount": 0.0,
                        "amount_cents": 0,
                        "transaction_time": "",
                        "source_platform": "",
                        "counterparty": "",
                        "description": "",
                        "current_main_category": "",
                        "current_sub_category": "",
                        "current_risk_tags": "",
                        "source_table": "manual_review_status_summary",
                        "generated_at": generated_at,
                        "schema_version": SCHEMA_VERSION,
                    }
                )
                break
    return rows


def summarize_manual_review_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_amount = sum(_float(row.get("amount")) for row in rows if str(row.get("queue_status")) != "EMPTY")
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("queue_status", "")), str(row.get("priority", "")))
        bucket = buckets.setdefault(
            key,
            {
                "queue_status": key[0],
                "priority": key[1],
                "count": 0,
                "amount": 0.0,
                "decision_grade": str(row.get("decision_grade", "")),
                "next_action": str(row.get("next_action", "")),
            },
        )
        bucket["count"] += 1
        bucket["amount"] += _float(row.get("amount"))
    output = []
    for item in sorted(buckets.values(), key=lambda value: (value["priority"], value["queue_status"])):
        amount = float(item["amount"])
        output.append(
            {
                **item,
                "amount": round(amount, 2),
                "amount_pct": f"{(amount / total_amount * 100 if total_amount else 0.0):.2f}%",
                "evidence_classification": "FACT",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return output


def manual_review_audit_report_markdown(rows: list[dict[str, Any]]) -> str:
    summary = summarize_manual_review_audit(rows)
    total_pending = sum(1 for row in rows if str(row.get("queue_status")) == "PENDING_REVIEW")
    total_invalid = sum(1 for row in rows if str(row.get("queue_status")) == "INVALID_DECISION")
    total_amount = sum(_float(row.get("amount")) for row in rows if str(row.get("queue_status")) == "PENDING_REVIEW")
    priorities = Counter(str(row.get("priority", "")) for row in rows)
    top_rows = sorted(
        [row for row in rows if str(row.get("queue_status")) != "EMPTY"],
        key=lambda item: (_priority_rank(str(item.get("priority", ""))), -_float(item.get("amount"))),
    )[:30]
    lines = [
        "# Manual Review Queue 人工复核队列审计报告",
        "",
        "口径：本报告只读取 `manual_review_queue`、复核候选、Data Trust 和无效复核确认行；不改变生产金额、分类、报告总支出或复核确认逻辑。",
        "",
        "## 审计总览",
        "",
        f"- 待复核笔数：{total_pending}",
        f"- 待复核金额：¥{total_amount:,.2f}",
        f"- 无效复核确认行：{total_invalid}",
        f"- P0：{priorities.get('P0', 0)}；P1：{priorities.get('P1', 0)}；P2：{priorities.get('P2', 0)}；P3：{priorities.get('P3', 0)}",
        "",
        "## 证据分层与决策等级",
        "",
        "| 字段 | 口径 |",
        "|---|---|",
        "| evidence_classification | `FACT` 表示来自确认文件或系统文件状态；`OBSERVATION` 表示待复核队列中的原始观察。 |",
        "| decision_grade | `Watch` 表示需要人工复核；`Reject` 表示确认文件有错误；`Actionable` 表示没有当前复核阻塞。 |",
        "| ledger_effect | 描述该复核项对生产账本的影响。未确认大额交易必须保持隔离。 |",
        "| next_action | 下一个可执行动作，通常是确认、修正或继续周更。 |",
        "",
        "## 队列摘要",
        "",
        "| 状态 | 优先级 | 笔数 | 金额 | 金额占比 | 决策等级 | 下一步 |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['queue_status']} | {item['priority']} | {item['count']} | ¥{float(item['amount']):,.2f} | "
            f"{item['amount_pct']} | {item['decision_grade']} | {item['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## 优先复核明细",
            "",
            "| 优先级 | 状态 | 时间 | 对方 | 金额 | 候选动作 | 置信度 | Data Trust | 下一步 |",
            "|---|---|---|---|---:|---|---|---|---|",
        ]
    )
    if not top_rows:
        lines.append("| P3 | EMPTY |  |  | ¥0.00 | none | high | RECONCILED | 继续周更。 |")
    for row in top_rows:
        lines.append(
            f"| {row.get('priority', '')} | {row.get('queue_status', '')} | {row.get('transaction_time', '')} | "
            f"{_safe_text(row.get('counterparty', ''), 24)} | ¥{_float(row.get('amount')):,.2f} | "
            f"{row.get('candidate_action', '')} | {row.get('candidate_confidence', '')} | "
            f"{row.get('data_trust_status', '')} | {_safe_text(row.get('next_action', ''), 38)} |"
        )
    lines.extend(
        [
            "",
            "## 机器可读产物",
            "",
            "- CSV：`audit/manual_review_queue_audit.csv`",
            "- JSON：`audit/manual_review_queue_audit.json`",
            "- SQLite 表：`manual_review_queue_audit`、`manual_review_queue_audit_summary`",
            "- SQLite 视图：`v_manual_review_queue_audit`、`v_manual_review_queue_blockers`、`v_manual_review_queue_summary`",
            "",
            "## 验证方式",
            "",
            "```bash",
            "python3 scripts/validate_outputs.py outputs/finance_ledger_20220605_20260603 data/finance_ledger/finance_ledger.sqlite --require-ledger",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_manual_review_audit_outputs(rows: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    audit_dir = output / "audit"
    reports_dir = output / "reports"
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = audit_dir / "manual_review_queue_audit.csv"
    json_path = audit_dir / "manual_review_queue_audit.json"
    md_path = reports_dir / "manual_review_queue_audit_report.md"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    markdown = manual_review_audit_report_markdown(rows)
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "manual_review_queue_audit_csv": csv_path,
        "manual_review_queue_audit_json": json_path,
        "manual_review_queue_audit_md": md_path,
    }


def _priority_for_pending(amount: float, candidate: dict[str, Any], trust: dict[str, Any]) -> tuple[str, str]:
    confidence = str(candidate.get("candidate_confidence", "")).lower()
    trust_status = str(trust.get("data_trust_status", ""))
    if trust_status == "NEEDS_REVIEW" and amount >= 100000:
        return "P0", "单笔金额 >= ¥100,000 且 Data Trust 为 NEEDS_REVIEW。"
    if amount >= 50000:
        return "P1", "单笔金额 >= ¥50,000，需要优先确认是否纳入生产统计。"
    if confidence == "low":
        return "P1", "候选置信度 low，疑似个人转账或责任归属不清。"
    if amount >= 10000:
        return "P2", "单笔金额 >= ¥10,000，按大额复核规则隔离。"
    return "P3", "金额较低或仅作观察。"


def _next_action_for_pending(candidate: dict[str, Any]) -> str:
    action = str(candidate.get("candidate_action", "manual_review"))
    confidence = str(candidate.get("candidate_confidence", "low"))
    if action == "include_suggested" and confidence in {"high", "medium"}:
        return "在复核工作台确认是否按候选分类纳入；确认前保持隔离。"
    return "人工判断是否 include、exclude 或 split；确认前保持隔离。"


def _fallback_review_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("transaction_time") or row.get("date") or ""),
            str(row.get("counterparty") or ""),
            str(row.get("amount_cents") or ""),
            str(row.get("description") or ""),
        ]
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").replace("|", "/").replace("\n", " ").strip()
    return text[:limit]
