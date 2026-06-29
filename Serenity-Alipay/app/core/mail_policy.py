from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


MAINTAIN_ACTIONS = {"", "Maintain", "维持", "保持", "保持当前持仓"}
ACTION_PRIORITY = {
    "Block": 90,
    "清仓": 80,
    "暂停新增": 70,
    "Rebalance": 60,
    "增配": 50,
    "减配": 50,
    "Manual Review": 40,
    "维持": 0,
}


@dataclass(frozen=True)
class ActionSignature:
    payload: dict[str, object]
    text: str
    hash: str
    notification_kind: str
    beijing_date: str
    overall_action: str


@dataclass(frozen=True)
class MailSendDecision:
    should_send: bool
    notification_kind: str
    action_signature: str
    action_signature_hash: str
    beijing_date: str
    suppress_reason: str | None = None
    related_run_id: str | None = None


def _normalize_action(action: object) -> str:
    value = str(action or "").strip()
    if value in MAINTAIN_ACTIONS:
        return "维持"
    if value in {"Increase", "Buy", "买入", "加仓", "增配"}:
        return "增配"
    if value in {"Reduce", "Sell", "卖出", "减仓", "减配"}:
        return "减配"
    if value in {"Pause New", "No-New-Order", "暂停新增", "暂停申购"}:
        return "暂停新增"
    if value in {"Clear", "清仓"}:
        return "清仓"
    if value in {"Block", "Block/Clear"}:
        return "Block"
    if value in {"Manual Review", "人工复核"}:
        return "Manual Review"
    if value in {"Rebalance", "重平衡"}:
        return "Rebalance"
    return value


def _weight_pct(value: object) -> str:
    try:
        return f"{float(value or 0.0) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _beijing_date(run_time_bj: str | None) -> str:
    if run_time_bj:
        try:
            return datetime.fromisoformat(run_time_bj).date().isoformat()
        except ValueError:
            if "T" in run_time_bj:
                return run_time_bj.split("T", 1)[0]
            if " " in run_time_bj:
                return run_time_bj.split(" ", 1)[0]
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def _overall_action(actions: list[str], *, severity: str) -> str:
    if severity == "Urgent" and not any(action != "维持" for action in actions):
        return "Block"
    if not actions:
        return "维持"
    if "Block" in actions:
        return "Block"
    if "清仓" in actions:
        return "清仓"
    if "暂停新增" in actions:
        return "暂停新增"
    active = {action for action in actions if action != "维持"}
    if {"增配", "减配"}.issubset(active):
        return "Rebalance"
    if "Rebalance" in active:
        return "Rebalance"
    if "增配" in active:
        return "增配"
    if "减配" in active:
        return "减配"
    if "Manual Review" in active:
        return "Manual Review"
    return "维持"


def _key_actions(actions: list[str], *, severity: str) -> list[str]:
    keys = {action for action in actions if action != "维持"}
    if severity == "Urgent":
        keys.add("Block")
    return sorted(keys, key=lambda action: (-ACTION_PRIORITY.get(action, 10), action))


def build_action_signature(
    severity: str,
    recommendations: list[dict[str, object]],
    *,
    run_time_bj: str | None,
    data_quality_status: str = "pass",
    execution_locked: bool | None = None,
    limit: int = 5,
) -> ActionSignature:
    top = sorted(
        recommendations,
        key=lambda row: int(row.get("rank") or 999),
    )[:limit]
    normalized_rows: list[dict[str, object]] = []
    actions: list[str] = []
    for index, row in enumerate(top, start=1):
        action = _normalize_action(row.get("action_label"))
        if str(row.get("grade") or "") == "Block":
            action = "Block"
        actions.append(action)
        normalized_rows.append(
            {
                "rank": int(row.get("rank") or index),
                "asset_code": str(row.get("asset_code") or row.get("asset_id") or ""),
                "asset_name": str(row.get("asset_name") or ""),
                "action": action,
                "target_weight_pct": _weight_pct(row.get("target_weight")),
            }
        )
    overall = _overall_action(actions, severity=severity)
    key_actions = _key_actions(actions, severity=severity)
    notification_kind = "actionable" if overall != "维持" or bool(key_actions) else "info"
    payload: dict[str, object] = {
        "overall_action": overall,
        "top5": normalized_rows,
        "top5_order": [row["asset_code"] for row in normalized_rows],
        "key_actions": key_actions,
        "critical_flags": {
            "block": "Block" in key_actions,
            "clear": "清仓" in key_actions,
            "pause_new": "暂停新增" in key_actions,
            "rebalance": overall == "Rebalance" or "Rebalance" in key_actions,
        },
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return ActionSignature(
        payload=payload,
        text=text,
        hash=digest,
        notification_kind=notification_kind,
        beijing_date=_beijing_date(run_time_bj),
        overall_action=overall,
    )


def has_material_holding_change(recommendations: list[dict[str, object]], *, limit: int = 5) -> bool:
    signature = build_action_signature(
        "Info",
        recommendations[:limit],
        run_time_bj=None,
        data_quality_status="pass",
        execution_locked=False,
    )
    return signature.notification_kind == "actionable"


def should_send_mail_for_run(
    severity: str,
    recommendations: list[dict[str, object]],
    *,
    data_quality_status: str = "pass",
    execution_locked: bool | None = None,
) -> bool:
    signature = build_action_signature(
        severity,
        recommendations,
        run_time_bj=None,
        data_quality_status=data_quality_status,
        execution_locked=execution_locked,
    )
    return signature.notification_kind == "actionable"


def decide_mail_send_for_run(
    conn: sqlite3.Connection,
    *,
    severity: str,
    recommendations: list[dict[str, object]],
    run_time_bj: str | None,
    data_quality_status: str = "pass",
    execution_locked: bool | None = None,
) -> MailSendDecision:
    signature = build_action_signature(
        severity,
        recommendations,
        run_time_bj=run_time_bj,
        data_quality_status=data_quality_status,
        execution_locked=execution_locked,
    )
    if signature.notification_kind != "actionable":
        return MailSendDecision(
            should_send=False,
            notification_kind=signature.notification_kind,
            action_signature=signature.text,
            action_signature_hash=signature.hash,
            beijing_date=signature.beijing_date,
            suppress_reason="non_actionable",
        )

    previous = conn.execute(
        """
        SELECT run_id, action_signature_hash
        FROM notification_log
        WHERE notification_kind='actionable'
          AND send_status='sent'
          AND action_signature_hash IS NOT NULL
        ORDER BY COALESCE(sent_at, created_at) DESC, rowid DESC
        LIMIT 1
        """
    ).fetchone()
    if previous and previous["action_signature_hash"] == signature.hash:
        return MailSendDecision(
            should_send=False,
            notification_kind=signature.notification_kind,
            action_signature=signature.text,
            action_signature_hash=signature.hash,
            beijing_date=signature.beijing_date,
            suppress_reason="duplicate_action_signature",
            related_run_id=str(previous["run_id"]),
        )

    sent_today = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM notification_log
        WHERE notification_kind='actionable'
          AND send_status='sent'
          AND beijing_date=?
        """,
        (signature.beijing_date,),
    ).fetchone()["n"]
    if int(sent_today or 0) >= 2:
        return MailSendDecision(
            should_send=False,
            notification_kind=signature.notification_kind,
            action_signature=signature.text,
            action_signature_hash=signature.hash,
            beijing_date=signature.beijing_date,
            suppress_reason="daily_email_cap_reached",
        )

    return MailSendDecision(
        should_send=True,
        notification_kind=signature.notification_kind,
        action_signature=signature.text,
        action_signature_hash=signature.hash,
        beijing_date=signature.beijing_date,
    )


def suppressed_mail_message(reason: str | None) -> str:
    messages = {
        "duplicate_action_signature": "邮件已抑制：当前建议动作与上一封已发送 actionable 邮件一致。",
        "daily_email_cap_reached": "邮件已抑制：北京时间当日 actionable 邮件已达到 2 封上限。",
        "non_actionable": "邮件已抑制：本轮没有新增实质操作动作。",
    }
    return messages.get(reason or "", "邮件已按频率控制策略抑制。")


def suppressed_no_material_change_message() -> str:
    return suppressed_mail_message("non_actionable")
