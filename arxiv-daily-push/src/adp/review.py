"""学习与排程 —— 主动回忆 + 四档自评 + FSRS-6（py-fsrs 6.3.1，零自研）+ 手动状态编辑.

不变量落点：
- 2/3: 「已学会」必须引用不可变回忆事件；「已掌握」需两次间隔回忆+一次应用证据；手动标记单独记账。
- 6: 同 idempotency key 的学习完成事件永不重复。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from . import store
from .config import Thresholds

GRADES = {1: "忘了", 2: "困难", 3: "良好", 4: "轻松"}
MANUAL_STATES = ("未学习", "学习中", "已学会", "需复习", "已掌握")


def _scheduler(thresholds: Thresholds):
    from fsrs import Scheduler

    return Scheduler(desired_retention=thresholds.desired_retention)


def _load_card(row: sqlite3.Row | None):
    from fsrs import Card

    if row is None:
        return Card()
    return Card.from_dict(json.loads(row["card_json"]))


def grade_recall(conn: sqlite3.Connection, item_id: str, grade: int, thresholds: Thresholds,
                 *, at: datetime | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
    """一次主动回忆自评：落不可变事件 → FSRS 更新 → 返回下次复习时间.

    同一 idempotency_key 不产生第二次学习完成记录（不变量 6）。
    """
    from fsrs import Rating

    if grade not in GRADES:
        raise ValueError(f"grade must be 1-4, got {grade}")
    at = at or datetime.now(timezone.utc)
    key = idempotency_key or f"{item_id}:{at.date().isoformat()}:{grade}"
    duplicate = conn.execute(
        """SELECT id FROM learning_events WHERE kind='self_grade' AND undone_by IS NULL
           AND json_extract(payload_json, '$.idempotency_key') = ?""",
        (key,),
    ).fetchone()
    if duplicate:
        return {"duplicate": True, "event_id": int(duplicate["id"]), "idempotency_key": key}

    event_id = store.append_event(
        conn, item_id=item_id, kind="self_grade", grade=grade,
        payload={"idempotency_key": key, "grade_label": GRADES[grade]},
        at=at.isoformat(timespec="seconds"),
    )
    scheduler = _scheduler(thresholds)
    row = conn.execute("SELECT * FROM review_state WHERE item_id=?", (item_id,)).fetchone()
    card, _log = scheduler.review_card(_load_card(row), Rating(grade), at)
    conn.execute(
        """INSERT INTO review_state (item_id, card_json, stability, difficulty, due_at, fsrs_params_ver, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(item_id) DO UPDATE SET card_json=excluded.card_json, stability=excluded.stability,
             difficulty=excluded.difficulty, due_at=excluded.due_at, updated_at=excluded.updated_at""",
        (item_id, json.dumps(card.to_dict()), card.stability, card.difficulty,
         card.due.isoformat(timespec="seconds"), "fsrs-6-default-21", at.isoformat(timespec="seconds")),
    )
    conn.commit()
    return {
        "duplicate": False, "event_id": event_id, "idempotency_key": key,
        "grade": grade, "grade_label": GRADES[grade],
        "due_at": card.due.isoformat(timespec="seconds"),
        "stability": round(card.stability or 0, 3), "difficulty": round(card.difficulty or 0, 3),
    }


def preview_intervals(conn: sqlite3.Connection, item_id: str, thresholds: Thresholds,
                      *, at: datetime | None = None) -> dict[int, str]:
    """四档按钮上的下次间隔预览（对每档在卡片副本上试演一次）."""
    from fsrs import Rating

    at = at or datetime.now(timezone.utc)
    scheduler = _scheduler(thresholds)
    row = conn.execute("SELECT * FROM review_state WHERE item_id=?", (item_id,)).fetchone()
    previews: dict[int, str] = {}
    for grade in GRADES:
        card, _ = scheduler.review_card(_load_card(row), Rating(grade), at)
        delta = card.due - at
        if delta.days >= 1:
            previews[grade] = f"{delta.days} 天"
        else:
            minutes = max(1, int(delta.total_seconds() // 60))
            previews[grade] = f"{minutes} 分钟" if minutes < 60 else f"{minutes // 60} 小时"
    return previews


def due_items(conn: sqlite3.Connection, *, at: datetime | None = None, limit: int = 12) -> list[dict[str, Any]]:
    """到期复习队列（日上限 12，超出顺延并记知识债务——业务规则·复习保护）."""
    at = at or datetime.now(timezone.utc)
    rows = conn.execute(
        """SELECT r.item_id, r.due_at, l.sections_json FROM review_state r
           JOIN lessons l ON l.id = r.item_id
           WHERE r.due_at <= ? ORDER BY r.due_at LIMIT ?""",
        (at.isoformat(timespec="seconds"), limit + 50),
    ).fetchall()
    items = []
    for row in rows[:limit]:
        sections = json.loads(row["sections_json"])
        items.append({"item_id": row["item_id"], "due_at": row["due_at"],
                      "headline": sections[0]["body"][:120] if sections else row["item_id"]})
    overdue_beyond_cap = max(0, len(rows) - limit)
    if overdue_beyond_cap:
        store.append_event(conn, item_id="__system__", kind="skip",
                           payload={"overdue_beyond_cap": overdue_beyond_cap}, actor="system")
        conn.execute(
            "INSERT INTO debts (kind, ref_id, note, opened_at) VALUES ('overdue', '__review_queue__', ?, ?)",
            (f"到期未复习超上限 {overdue_beyond_cap} 项", store.utcnow_iso()),
        )
        conn.commit()
    return items


def manual_mark(conn: sqlite3.Connection, item_id: str, state: str) -> int:
    """手动状态编辑：主观标记单独记账、可撤销、不冒充回忆证据（不变量 3）."""
    if state not in MANUAL_STATES:
        raise ValueError(f"state must be one of {MANUAL_STATES}")
    event_id = store.append_event(conn, item_id=item_id, kind="manual_mark",
                                  payload={"state": state, "subjective": True})
    conn.commit()
    return event_id


def manual_undo(conn: sqlite3.Connection, event_id: int) -> bool:
    """撤销一条手动标记（事件不删除，只标 undone_by——事件只增不删）."""
    row = conn.execute(
        "SELECT id, kind FROM learning_events WHERE id=? AND undone_by IS NULL", (event_id,)
    ).fetchone()
    if row is None or row["kind"] != "manual_mark":
        return False
    undo_id = store.append_event(conn, item_id="__undo__", kind="manual_undo",
                                 payload={"undoes": event_id})
    conn.execute("UPDATE learning_events SET undone_by=? WHERE id=?", (undo_id, event_id))
    conn.commit()
    return True


def learning_state(conn: sqlite3.Connection, item_id: str, *, at: datetime | None = None) -> dict[str, Any]:
    """当前学习状态 = 事件折叠（未见→接触→投入→回忆→保留→应用→掌握 + 重开）.

    证据态与主观标记分开返回：manual_state 永远不覆盖 evidence_state 的证据判定。
    """
    events = store.events_for(conn, item_id)
    at = at or datetime.now(timezone.utc)

    grades = [e for e in events if e["kind"] == "self_grade" and e["undone_by"] is None]
    reveals = [e for e in events if e["kind"] == "recall_reveal" and e["undone_by"] is None]
    applications = conn.execute(
        "SELECT COUNT(*) AS n FROM applications WHERE item_id=? AND kind='outcome'", (item_id,)
    ).fetchone()["n"]
    reopened = any(e["kind"] == "correction_reopen" and e["undone_by"] is None for e in events)

    if reopened and not _graded_after_reopen(events):
        evidence_state = "重开待复习"
    elif grades:
        distinct_days = {e["at"][:10] for e in grades if (e["grade"] or 0) >= 3}
        if len(distinct_days) >= 2 and applications >= 1:
            evidence_state = "已掌握"
        elif any((e["grade"] or 0) >= 2 for e in grades):
            evidence_state = "已学会"
        else:
            evidence_state = "需复习"
    elif reveals:
        evidence_state = "投入"
    else:
        # delivery/skip 是系统事件，不构成 Owner 接触（不变量 1：发送不改学习状态）
        owner_events = [e for e in events if e["kind"] not in {"delivery", "skip"}]
        evidence_state = "接触" if owner_events else "未见"

    manual = [e for e in events if e["kind"] == "manual_mark" and e["undone_by"] is None]
    manual_state = json.loads(manual[-1]["payload_json"]).get("state") if manual else None
    due_row = conn.execute("SELECT due_at FROM review_state WHERE item_id=?", (item_id,)).fetchone()
    return {
        "item_id": item_id,
        "evidence_state": evidence_state,
        "manual_state": manual_state,
        "manual_event_id": int(manual[-1]["id"]) if manual else None,
        "recall_count": len(grades),
        "application_count": int(applications),
        "due_at": due_row["due_at"] if due_row else None,
        "reopened": reopened,
    }


def _graded_after_reopen(events: list[sqlite3.Row]) -> bool:
    last_reopen = max((e["id"] for e in events if e["kind"] == "correction_reopen"), default=None)
    if last_reopen is None:
        return True
    return any(e["kind"] == "self_grade" and e["id"] > last_reopen and e["undone_by"] is None for e in events)
