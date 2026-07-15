"""网页应用（R1-8/R1-9）—— 今天学什么 / 学习队列 / 前沿雷达 / 证据与纠错 / 系统 / 试运行.

FastAPI + Jinja2 + 原生 fetch（零构建链）；单用户绑定 127.0.0.1；
人读页面一律由机器记录渲染并带回执（不变量 9）。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from . import config, store
from .claims import resolve_claim
from .corrections import resolve as resolve_correction
from .corrections import unresolved as unresolved_corrections
from .delivery import authorization_state, weekly_radar
from .manifest import read_manifests
from .pilot import pilot_report, record_decision, shadow_compare
from .render import env
from .review import (GRADES, MANUAL_STATES, due_items, grade_recall, learning_state,
                     manual_mark, manual_undo, preview_intervals)

DEEP_DIVE_INSTRUCTION = (
    "请对这篇论文做：全网遍历、深度思考、深度搜索、给我 surprise、详细专业全面深度讲解。"
    "我已在自己的学习系统里读过八段讲义并完成主动回忆，以下是论文元数据与我已学要点。"
)

app = FastAPI(title="ADP 个人前沿学习系统", docs_url=None, redoc_url=None)
_pilot_cache: dict[str, Any] = {}

# 公网直连守卫（R6·Tunnel）：经 Cloudflare 隧道来的请求必带 cf-connecting-ip
# （边缘强制覆写，本机浏览器不会有；外部流量无法绕过边缘直连 127.0.0.1）。
# 入口无登录（Owner 2026-07-15 指令），故远程只放行「浏览 + 主动回忆」，
# 其余写操作（上板/试点决策/状态编辑/纠错/撤销/迁移）仅限本机亲手执行。
# 边界（复审确认）：本守卫是前缀判断且只覆盖 http scope——新增 Owner 写路由
# 严禁放在 /api/recall/ 前缀下；若未来加 WebSocket 路由需另设 ws 守卫。
REMOTE_POST_ALLOWED = ("/api/recall/",)


@app.middleware("http")
async def remote_guard(request: Request, call_next):
    if ("cf-connecting-ip" in request.headers
            and request.method not in ("GET", "HEAD")
            and not request.url.path.startswith(REMOTE_POST_ALLOWED)):
        return JSONResponse(
            {"error": "该操作仅限本机执行；公网入口只开放浏览与主动回忆评分"},
            status_code=403)
    return await call_next(request)


def _conn() -> sqlite3.Connection:
    return store.connect()


def _render(template: str, **context: Any) -> HTMLResponse:
    context.setdefault("now", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    context.setdefault("receipt", f"render@{context['now']} source=run_manifests+sqlite")
    return HTMLResponse(env.get_template(template).render(**context))


def _latest_lesson(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM lessons WHERE archived_at IS NULL ORDER BY as_of_date DESC, created_at DESC LIMIT 1"
    ).fetchone()


def _lesson_view(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    """讲义视图：句子与绑定直接读自 sections_json（复审修复：渲染端零重切分）."""
    sections = json.loads(row["sections_json"])
    doc = conn.execute(
        """SELECT d.title, d.canonical_url, v.metadata_json FROM doc_versions v
           JOIN documents d ON d.id = v.doc_id WHERE v.id=?""",
        (row["doc_version_id"],),
    ).fetchone()
    meta = json.loads(doc["metadata_json"]) if doc else {}
    rendered_sections = [
        {"title": section["title"],
         "sentences": [{"text": s["text"], "claim_id": s["claim"]} for s in section.get("sentences") or []]}
        for section in sections
    ]
    deep_link = (
        "https://chatgpt.com/?q="
        + quote(f"{DEEP_DIVE_INSTRUCTION}\n\n论文: {doc['title'] if doc else ''}\n"
                f"链接: {doc['canonical_url'] if doc else ''}\n摘要: {meta.get('summary', '')[:800]}")
    )
    reveal_parts = [sections[0].get("body", "")] if sections else []
    if len(sections) > 3:
        reveal_parts.append(sections[3].get("body", ""))
    return {
        "lesson_id": row["id"], "as_of_date": row["as_of_date"], "generator": row["generator"],
        "template_ver": row["template_ver"], "status": row["status"],
        "doc_title": doc["title"] if doc else "", "canonical_url": doc["canonical_url"] if doc else "",
        "sections": rendered_sections, "deep_link": deep_link,
        "reveal_summary": " / ".join(p[:160] for p in reveal_parts if p),
    }


def _hero_metrics(conn: sqlite3.Connection, thresholds) -> dict[str, Any]:
    """首屏体征数据（v1.1 前端增补包）：全部读自真实运行记录与事件库."""
    from datetime import timedelta

    from .manifest import read_manifests

    latest = conn.execute(
        "SELECT * FROM selections ORDER BY as_of_date DESC, run_id DESC LIMIT 1"
    ).fetchone()
    top_title = ""
    if latest and not latest["abstain"] and latest["candidate_id"]:
        row = conn.execute(
            "SELECT d.title FROM candidates c JOIN documents d ON d.id=c.doc_id WHERE c.id=?",
            (latest["candidate_id"],),
        ).fetchone()
        top_title = row["title"] if row else ""

    # 近 7 日每日最新决策（run_id 悉尼 ISO，字典序即时间序）
    spark = []
    for row in conn.execute(
        """SELECT s.as_of_date, s.score, s.abstain FROM selections s
           JOIN (SELECT as_of_date, MAX(run_id) AS m FROM selections GROUP BY as_of_date) l
             ON l.as_of_date = s.as_of_date AND l.m = s.run_id
           ORDER BY s.as_of_date DESC LIMIT 7"""
    ):
        spark.append({"date": row["as_of_date"], "score": row["score"] or 0.0,
                      "abstain": bool(row["abstain"])})
    spark.reverse()

    # streak：以成功 manifest（正常/降级/弃权）的连续悉尼日期计
    ok_dates = sorted({m["run_id"][:10] for m in read_manifests(200)
                       if m.get("result") in {"正常", "降级", "弃权"}})
    streak = 0
    if ok_dates:
        from datetime import date

        cursor = date.fromisoformat(ok_dates[-1])
        dates = set(ok_dates)
        while cursor.isoformat() in dates:
            streak += 1
            cursor -= timedelta(days=1)

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
    grades = [int(r["grade"]) for r in conn.execute(
        "SELECT grade FROM learning_events WHERE kind='self_grade' AND undone_by IS NULL AND at >= ?",
        (week_ago,),
    ) if r["grade"]]
    retention = round(100 * sum(1 for g in grades if g >= 3) / len(grades)) if grades else None
    debt = conn.execute("SELECT COUNT(*) n FROM debts WHERE status='open'").fetchone()["n"]
    manifests = read_manifests(1)
    return {
        "date": latest["as_of_date"] if latest else "",
        "abstain": bool(latest["abstain"]) if latest else False,
        "abstain_reason": (latest["abstain_reason"] or "") if latest else "",
        "score": latest["score"] if latest else None,
        "top_title": top_title,
        "spark": spark, "streak": streak, "retention": retention,
        "review_debt": int(debt),
        "last_run_result": manifests[0]["result"] if manifests else "未运行",
        "abstain_line": thresholds.abstain_threshold,
    }


@app.get("/", response_class=HTMLResponse)
def today() -> HTMLResponse:
    conn = _conn()
    try:
        thresholds = config.load_thresholds()
        selection = conn.execute(
            "SELECT * FROM selections ORDER BY as_of_date DESC, run_id DESC LIMIT 1"
        ).fetchone()
        lesson_row = _latest_lesson(conn)
        lesson = _lesson_view(conn, lesson_row) if lesson_row else None
        state = learning_state(conn, lesson_row["id"]) if lesson_row else None
        intervals = preview_intervals(conn, lesson_row["id"], thresholds) if lesson_row else {}
        return _render(
            "today.html", page="today", selection=selection, lesson=lesson, state=state,
            intervals=intervals, grades=GRADES, manual_states=MANUAL_STATES,
            corrections=unresolved_corrections(conn),
            hero=_hero_metrics(conn, thresholds),
        )
    finally:
        conn.close()


@app.get("/queue", response_class=HTMLResponse)
def queue() -> HTMLResponse:
    conn = _conn()
    try:
        thresholds = config.load_thresholds()
        rows = conn.execute(
            "SELECT * FROM lessons WHERE archived_at IS NULL ORDER BY as_of_date DESC LIMIT 100"
        ).fetchall()
        items = []
        for row in rows:
            state = learning_state(conn, row["id"])
            doc = conn.execute(
                "SELECT d.title FROM doc_versions v JOIN documents d ON d.id=v.doc_id WHERE v.id=?",
                (row["doc_version_id"],),
            ).fetchone()
            items.append({"lesson_id": row["id"], "date": row["as_of_date"],
                          "title": doc["title"] if doc else row["id"], "state": state,
                          "reopened": row["status"] == "reopened"})
        due = due_items(conn, limit=thresholds.max_daily_reviews)
        return _render("queue.html", page="queue", items=items, due=due,
                       manual_states=MANUAL_STATES, corrections=unresolved_corrections(conn))
    finally:
        conn.close()


@app.get("/corrections", response_class=HTMLResponse)
def corrections_page(q: str = "") -> HTMLResponse:
    """证据与纠错入口：声明检索（三步到原文）+ 纠错通知 + 已处理历史."""
    conn = _conn()
    try:
        hits = []
        if q:
            for row in store.search(conn, "fts_claims", q, limit=20):
                resolved_claim = resolve_claim(conn, row["claim_id"])
                if resolved_claim:
                    hits.append(resolved_claim)
        resolved_history = conn.execute(
            "SELECT * FROM corrections WHERE resolved=1 ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        return _render("corrections.html", page="corrections", q=q, hits=hits,
                       corrections=unresolved_corrections(conn), resolved_history=resolved_history)
    finally:
        conn.close()


@app.get("/system", response_class=HTMLResponse)
def system() -> HTMLResponse:
    conn = _conn()
    try:
        manifests = read_manifests(limit=30)
        sources = conn.execute("SELECT * FROM sources").fetchall()
        replay_path = config.data_dir() / "replay_30d.json"
        replay = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path.exists() else None
        return _render("system.html", page="system", manifests=manifests, sources=sources,
                       replay=replay, auth=authorization_state(), versions=config.config_versions())
    finally:
        conn.close()


@app.get("/radar", response_class=HTMLResponse)
def radar_page() -> HTMLResponse:
    conn = _conn()
    try:
        from .boards import board_overview
        from .shadow_biorxiv import is_promoted, load_report

        return _render("radar.html", page="radar", radar=weekly_radar(conn),
                       boards=board_overview(conn),
                       shadow=load_report(), biorxiv_promoted=is_promoted(conn))
    finally:
        conn.close()


@app.post("/api/r5/promote")
def api_r5_promote() -> JSONResponse:
    """R5 上板/撤板——只由 Owner 在雷达页点击触发（自迭代边界：系统只能提案）."""
    conn = _conn()
    try:
        from .shadow_biorxiv import promote

        return JSONResponse(promote(conn))
    finally:
        conn.close()


@app.get("/pilot", response_class=HTMLResponse)
def pilot_page() -> HTMLResponse:
    conn = _conn()
    try:
        today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cached = _pilot_cache.get("shadow")
        if not cached or cached["date"] != today_key:
            shadow = shadow_compare(conn, config.load_thresholds(), days=14)
            _pilot_cache["shadow"] = {"date": today_key, "value": shadow}
        else:
            shadow = cached["value"]
        report = pilot_report(conn)
        decisions = conn.execute(
            "SELECT * FROM config_changes WHERE domain='pilot_decision' ORDER BY id DESC LIMIT 5"
        ).fetchall()
        return _render("pilot.html", page="pilot", report=report, shadow=shadow, decisions=decisions)
    finally:
        conn.close()


@app.get("/evidence/{claim_id}", response_class=HTMLResponse)
def evidence(claim_id: str) -> HTMLResponse:
    conn = _conn()
    try:
        if claim_id == "__doc_meta__":
            return _render("evidence.html", page="evidence", claim=None, meta_note=True)
        resolved = resolve_claim(conn, claim_id)
        if resolved is None:
            raise HTTPException(404, "claim not found")
        return _render("evidence.html", page="evidence", claim=resolved, meta_note=False)
    finally:
        conn.close()


@app.post("/api/recall/{lesson_id}/reveal")
def api_reveal(lesson_id: str) -> JSONResponse:
    conn = _conn()
    try:
        row = conn.execute("SELECT sections_json FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        if row is None:
            raise HTTPException(404)
        # 复审修复：reveal 事件同一 UTC 日只记一条——端点远程可达（无登录），
        # 不设上限会让外人无限制刷大事件表；重复 reveal 仍返回答案但不再记录。
        dup = conn.execute(
            "SELECT 1 FROM learning_events WHERE item_id=? AND kind='recall_reveal' "
            "AND substr(at, 1, 10) = substr(?, 1, 10)",
            (lesson_id, store.utcnow_iso())).fetchone()
        if dup is None:
            store.append_event(conn, item_id=lesson_id, kind="recall_reveal", payload={})
            conn.commit()
        sections = json.loads(row["sections_json"])
        answer = " / ".join(s.get("body", "")[:160] for s in sections[:1] + sections[3:4])
        return JSONResponse({"answer": answer})
    finally:
        conn.close()


@app.post("/api/recall/{lesson_id}/grade/{grade}")
def api_grade(lesson_id: str, grade: int) -> JSONResponse:
    conn = _conn()
    try:
        # 复审修复：讲义必须真实存在——公网入口下编造 ID 会往主库注入垃圾
        # review_state/事件行（review 层只校验档位，存在性由入口把关）。
        if conn.execute("SELECT 1 FROM lessons WHERE id=?", (lesson_id,)).fetchone() is None:
            raise HTTPException(404)
        thresholds = config.load_thresholds()
        outcome = grade_recall(conn, lesson_id, grade, thresholds)
        state = learning_state(conn, lesson_id)
        outcome["evidence_state"] = state["evidence_state"]
        return JSONResponse(outcome)
    finally:
        conn.close()


@app.post("/api/item/{item_id}/state/{state}")
def api_manual_state(item_id: str, state: str) -> JSONResponse:
    conn = _conn()
    try:
        event_id = manual_mark(conn, item_id, state)
        return JSONResponse({"event_id": event_id, "state": state, "subjective": True})
    finally:
        conn.close()


@app.post("/api/undo/{event_id}")
def api_undo(event_id: int) -> JSONResponse:
    conn = _conn()
    try:
        return JSONResponse({"undone": manual_undo(conn, event_id)})
    finally:
        conn.close()


@app.post("/api/corrections/{correction_id}/resolve")
def api_resolve_correction(correction_id: int) -> JSONResponse:
    conn = _conn()
    try:
        return JSONResponse({"resolved": resolve_correction(conn, correction_id)})
    finally:
        conn.close()


@app.post("/api/pilot/decision/{decision}")
def api_pilot_decision(decision: str, payload: dict[str, Any] | None = None) -> JSONResponse:
    conn = _conn()
    try:
        return JSONResponse(record_decision(conn, decision, (payload or {}).get("note", "")))
    finally:
        conn.close()


@app.post("/api/transfer/{item_id}")
def api_transfer(item_id: str, payload: dict[str, Any]) -> JSONResponse:
    """迁移练习与结果记录（应用域）——失败也记."""
    conn = _conn()
    try:
        kind = payload.get("kind", "outcome")
        if kind not in {"practice", "asset", "outcome"}:
            raise HTTPException(422, "kind must be practice/asset/outcome")
        conn.execute(
            "INSERT INTO applications (item_id, kind, payload_json, outcome, at) VALUES (?, ?, ?, ?, ?)",
            (item_id, kind, json.dumps(payload, ensure_ascii=False),
             payload.get("outcome"), store.utcnow_iso()),
        )
        store.append_event(conn, item_id=item_id, kind="transfer_result",
                           payload={"kind": kind, "outcome": payload.get("outcome")})
        conn.commit()
        return JSONResponse({"recorded": True})
    finally:
        conn.close()


def main(host: str = "127.0.0.1", port: int = 8787) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="warning")
