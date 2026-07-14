"""交付通道（R3）—— 邮件=同一讲义的幂等镜像；无授权凭证一律失败关闭.

不变量落点：
- 1: 发送事件不得改变学习状态（delivery 事件与学习事件分账，且不写 review/learned）。
- 5: 无 Owner 签发授权凭证，真实发送失败关闭（只落 .eml 预览与 BLOCKED 回执）。
- 6: 同一防重号（idempotency key）永不产生第二次发送。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from . import config, store
from .render import env as _template_env

AUTH_PATH_NAME = "send_authorization.json"
REQUIRED_AUTH_FIELDS = ("issued_by", "issued_at", "expires_at", "recipient", "authorization_text", "revoked")


def authorization_path() -> Path:
    return config.data_dir() / "authorization" / AUTH_PATH_NAME


def authorization_state(*, now: datetime | None = None) -> dict[str, Any]:
    """授权凭证状态：限定接收者、可过期、可撤销；缺失/无效/过期/撤销都= 未授权."""
    now = now or datetime.now(timezone.utc)
    path = authorization_path()
    state: dict[str, Any] = {"side_effects_authorized": False}
    if not path.exists():
        state["explanation"] = "无 Owner 签发的授权凭证：真实发送/常驻一律失败关闭（不变量 5）。"
        return state
    try:
        credential = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        state["explanation"] = f"授权凭证不可读（{type(exc).__name__}），按未授权处理。"
        return state
    missing = [field for field in REQUIRED_AUTH_FIELDS if field not in credential]
    if missing:
        state["explanation"] = f"授权凭证缺少字段 {missing}，无效。"
        return state
    expires = _parse_dt(credential.get("expires_at"))
    status = "valid"
    if credential.get("revoked"):
        status = "revoked"
    elif expires is None or expires <= now:
        status = "expired"
    state["credential"] = {
        "recipient": credential.get("recipient"),
        "expires_at": credential.get("expires_at"),
        "status": status,
    }
    if status == "valid":
        state["side_effects_authorized"] = True
        state["explanation"] = "Owner 授权凭证有效（限定接收者、可过期、可撤销）。"
    else:
        state["explanation"] = f"授权凭证状态 {status}，按未授权失败关闭。"
    return state


def _parse_dt(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def render_lesson_email(conn: sqlite3.Connection, lesson_id: str) -> tuple[str, str]:
    """与网页同源的单模板渲染（成熟项目替代决策 #7：模板层单文件 Jinja2）；返回 (subject, html)."""
    row = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    if row is None:
        raise ValueError(f"lesson not found: {lesson_id}")
    doc = conn.execute(
        """SELECT d.title, d.canonical_url FROM doc_versions v
           JOIN documents d ON d.id = v.doc_id WHERE v.id=?""",
        (row["doc_version_id"],),
    ).fetchone()
    # 复审修复：与网页共用同一 Jinja 环境（render.env），消除双环境配置漂移
    html = _template_env.get_template("email_lesson.html").render(
        lesson_id=lesson_id, as_of_date=row["as_of_date"],
        doc_title=doc["title"], canonical_url=doc["canonical_url"],
        sections=json.loads(row["sections_json"]),
        generator=row["generator"],
    )
    subject = f"[ADP 学习镜像] {row['as_of_date']} · {doc['title'][:60]}"
    return subject, html


def deliver_lesson(conn: sqlite3.Connection, lesson_id: str, *, channel: str = "email",
                   now: datetime | None = None) -> dict[str, Any]:
    """幂等镜像交付。返回回执 dict；真实发送只在授权有效时发生（本版本恒为预览）.

    发送不改学习状态：本函数只写 deliveries 表和 delivery 事件，绝不触碰
    review_state / self_grade / lessons.status（不变量 1 的实现面）。
    """
    now = now or datetime.now(timezone.utc)
    as_of = now.strftime("%Y-%m-%d")
    key = f"{channel}:{lesson_id}:{as_of}"

    existing = conn.execute("SELECT * FROM deliveries WHERE idempotency_key=?", (key,)).fetchone()
    if existing:
        return {
            "delivered": False, "duplicate": True, "idempotency_key": key,
            "reason": f"同日重发被拒：防重号 {key} 已存在（{existing['result']} @ {existing['at']}），同一防重号永不二发（不变量 6）。",
        }

    subject, html = render_lesson_email(conn, lesson_id)
    auth = authorization_state(now=now)
    outbox = config.data_dir() / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = "adp@localhost"
    message["To"] = (auth.get("credential") or {}).get("recipient") or "OWNER (未授权，未寻址)"
    message.set_content("此邮件为讲义镜像的 HTML 版本。发送状态 ≠ 学习状态。")
    message.add_alternative(html, subtype="html")
    preview_path = outbox / f"{key.replace(':', '_')}.eml"
    preview_path.write_bytes(bytes(message))

    if auth["side_effects_authorized"]:
        # 真实发送通道保留给授权后的受控运行；本次交付合同全程零生产副作用。
        result = "AUTHORIZED_BUT_SEND_DISABLED_THIS_BUILD"
        delivered = False
    else:
        result = "BLOCKED_AUTH"
        delivered = False

    conn.execute(
        "INSERT INTO deliveries (idempotency_key, item_id, channel, rendered_path, authorized, result, at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (key, lesson_id, channel, str(preview_path), int(auth["side_effects_authorized"]),
         result, now.isoformat(timespec="seconds")),
    )
    store.append_event(conn, item_id=lesson_id, kind="delivery",
                       payload={"idempotency_key": key, "result": result, "channel": channel},
                       actor="system", at=now.isoformat(timespec="seconds"))
    conn.commit()
    return {
        "delivered": delivered, "duplicate": False, "idempotency_key": key, "result": result,
        "preview": str(preview_path), "subject": subject,
        "note": "发送状态 ≠ 学习状态：本次交付未产生任何学习事件（不变量 1）。",
    }


def weekly_radar(conn: sqlite3.Connection, *, now: datetime | None = None) -> dict[str, Any]:
    """每周雷达 + 知识债务账本（与网页/邮件同数据聚合渲染）."""
    from datetime import timedelta

    now = now or datetime.now(timezone.utc)
    week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    selections = []
    selected_count = abstain_count = 0
    # 每日取最新一次决策（失败重跑后同日可能有多行；run_id 为悉尼 ISO，字典序即时间序）
    for row in conn.execute(
        """SELECT s.* FROM selections s
           JOIN (SELECT as_of_date, MAX(run_id) AS max_run FROM selections GROUP BY as_of_date) latest
             ON latest.as_of_date = s.as_of_date AND latest.max_run = s.run_id
           WHERE s.as_of_date >= ? ORDER BY s.as_of_date""",
        (week_start,),
    ):
        if row["abstain"]:
            abstain_count += 1
            selections.append({"date": row["as_of_date"], "abstain": True,
                               "title": "", "reason": row["abstain_reason"] or ""})
        else:
            selected_count += 1
            title_row = conn.execute(
                """SELECT d.title FROM candidates c JOIN documents d ON d.id = c.doc_id WHERE c.id=?""",
                (row["candidate_id"],),
            ).fetchone()
            selections.append({"date": row["as_of_date"], "abstain": False,
                               "title": (title_row["title"][:60] if title_row else row["candidate_id"]),
                               "reason": row["why"] or ""})

    grades = [int(r["grade"]) for r in conn.execute(
        "SELECT grade FROM learning_events WHERE kind='self_grade' AND undone_by IS NULL AND at >= ?",
        (week_start,),
    ) if r["grade"]]
    debts = [dict(r) for r in conn.execute(
        "SELECT kind, note, opened_at FROM debts WHERE status='open' ORDER BY opened_at DESC LIMIT 20"
    )]
    boards = [
        {"name": "板块一 · 研究前沿 (arXiv)", "enabled": True,
         "note": f"本周入选 {selected_count} 篇、弃权 {abstain_count} 天"},
        {"name": "板块二 · 顶级期刊", "enabled": False, "note": "走 R5 启用提案（两周影子后上板）"},
        {"name": "板块三 · 中国政策法规", "enabled": False, "note": "维度已保留在阈值注册表扩展区"},
        {"name": "板块四 · 美国科技金融", "enabled": False, "note": "维度已保留在阈值注册表扩展区"},
        {"name": "板块五 · 跨板块总览", "enabled": False, "note": "多板块上线后自动聚合"},
    ]
    return {
        "week_start": week_start, "week_end": week_end,
        "selected_count": selected_count, "abstain_count": abstain_count,
        "recall_count": len(grades),
        "avg_grade": round(sum(grades) / len(grades), 2) if grades else None,
        "debt_count": len(debts), "debts": debts,
        "selections": selections, "boards": boards,
    }
