"""网页应用（R1-8/R1-9）—— 今天学什么 / 学习队列 / 前沿雷达 / 系统与来源.

FastAPI + Jinja2 + 原生 fetch（零构建链）；单用户绑定 127.0.0.1；
人读页面一律由机器记录渲染并带回执（不变量 9）。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config, store
from .claims import resolve_claim
from .manifest import read_manifests
from .review import (GRADES, MANUAL_STATES, due_items, grade_recall, learning_state,
                     manual_mark, manual_undo, preview_intervals)

TEMPLATES = Path(__file__).parent / "templates"
DEEP_DIVE_INSTRUCTION = (
    "请对这篇论文做：全网遍历、深度思考、深度搜索、给我 surprise、详细专业全面深度讲解。"
    "我已在自己的学习系统里读过八段讲义并完成主动回忆，以下是论文元数据与我已学要点。"
)

env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
env.filters["fromjson"] = json.loads
app = FastAPI(title="ADP 个人前沿学习系统", docs_url=None, redoc_url=None)


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
    sections = json.loads(row["sections_json"])
    bindings = json.loads(row["claim_bindings_json"])
    doc = conn.execute(
        """SELECT d.title, d.canonical_url, v.metadata_json FROM doc_versions v
           JOIN documents d ON d.id = v.doc_id WHERE v.id=?""",
        (row["doc_version_id"],),
    ).fetchone()
    meta = json.loads(doc["metadata_json"]) if doc else {}
    from .claims import split_sentences  # 句级 span 用与绑定一致的切分

    rendered_sections = []
    for section_index, section in enumerate(sections):
        sentences = []
        import re

        parts = [p.strip() for p in re.split(r"(?<=[。！？.!?])\s*", section["body"]) if p.strip()]
        for sent_index, sentence in enumerate(parts):
            claim_id = bindings.get(f"s{section_index}.{sent_index}", "__doc_meta__")
            sentences.append({"text": sentence, "claim_id": claim_id})
        rendered_sections.append({"title": section["title"], "sentences": sentences})
    deep_link = (
        "https://chatgpt.com/?q="
        + quote(f"{DEEP_DIVE_INSTRUCTION}\n\n论文: {doc['title'] if doc else ''}\n"
                f"链接: {doc['canonical_url'] if doc else ''}\n摘要: {meta.get('summary', '')[:800]}")
    )
    return {
        "lesson_id": row["id"], "as_of_date": row["as_of_date"], "generator": row["generator"],
        "template_ver": row["template_ver"], "status": row["status"],
        "doc_title": doc["title"] if doc else "", "canonical_url": doc["canonical_url"] if doc else "",
        "sections": rendered_sections, "deep_link": deep_link,
        "reveal_summary": sections[0]["body"] if sections else "",
    }


@app.get("/", response_class=HTMLResponse)
def today() -> HTMLResponse:
    conn = _conn()
    try:
        from .corrections import unresolved

        thresholds = config.load_thresholds()
        selection = conn.execute("SELECT * FROM selections ORDER BY as_of_date DESC LIMIT 1").fetchone()
        lesson_row = _latest_lesson(conn)
        lesson = _lesson_view(conn, lesson_row) if lesson_row else None
        state = learning_state(conn, lesson_row["id"]) if lesson_row else None
        intervals = preview_intervals(conn, lesson_row["id"], thresholds) if lesson_row else {}
        return _render(
            "today.html", page="today", selection=selection, lesson=lesson, state=state,
            intervals=intervals, grades=GRADES, manual_states=MANUAL_STATES,
            corrections=unresolved(conn),
        )
    finally:
        conn.close()


@app.get("/queue", response_class=HTMLResponse)
def queue() -> HTMLResponse:
    conn = _conn()
    try:
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
        due = due_items(conn)
        from .corrections import unresolved

        return _render("queue.html", page="queue", items=items, due=due,
                       manual_states=MANUAL_STATES, corrections=unresolved(conn))
    finally:
        conn.close()


@app.get("/corrections", response_class=HTMLResponse)
def corrections_page(q: str = "") -> HTMLResponse:
    """证据与纠错入口：声明检索（三步到原文）+ 纠错通知 + 矛盾/债务."""
    conn = _conn()
    try:
        from .corrections import unresolved

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
                       corrections=unresolved(conn), resolved_history=resolved_history)
    finally:
        conn.close()


@app.post("/api/corrections/{correction_id}/resolve")
def api_resolve_correction(correction_id: int) -> JSONResponse:
    conn = _conn()
    try:
        from .corrections import resolve

        return JSONResponse({"resolved": resolve(conn, correction_id)})
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
        auth_state = {
            "side_effects_authorized": False,
            "explanation": "无 Owner 签发的授权凭证：真实发送/常驻一律失败关闭（不变量 5）。",
        }
        from .delivery import authorization_state

        auth_state.update(authorization_state())
        return _render("system.html", page="system", manifests=manifests, sources=sources,
                       replay=replay, auth=auth_state, versions=config.config_versions())
    finally:
        conn.close()


@app.get("/radar", response_class=HTMLResponse)
def radar_page() -> HTMLResponse:
    conn = _conn()
    try:
        from .delivery import weekly_radar

        radar = weekly_radar(conn)
        return _render("radar.html", page="radar", radar=radar)
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
        store.append_event(conn, item_id=lesson_id, kind="recall_reveal", payload={})
        conn.commit()
        sections = json.loads(row["sections_json"])
        answer = " / ".join(s["body"][:160] for s in sections[:1] + sections[3:4])
        return JSONResponse({"answer": answer})
    finally:
        conn.close()


@app.post("/api/recall/{lesson_id}/grade/{grade}")
def api_grade(lesson_id: str, grade: int) -> JSONResponse:
    conn = _conn()
    try:
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
        ok = manual_undo(conn, event_id)
        return JSONResponse({"undone": ok})
    finally:
        conn.close()


@app.get("/pilot", response_class=HTMLResponse)
def pilot_page() -> HTMLResponse:
    conn = _conn()
    try:
        from .pilot import pilot_report, shadow_compare

        report = pilot_report(conn)
        shadow = shadow_compare(conn, config.load_thresholds(), days=14)
        decisions = conn.execute(
            "SELECT * FROM config_changes WHERE domain='pilot_decision' ORDER BY id DESC LIMIT 5"
        ).fetchall()
        return _render("pilot.html", page="pilot", report=report, shadow=shadow, decisions=decisions)
    finally:
        conn.close()


@app.post("/api/pilot/decision/{decision}")
def api_pilot_decision(decision: str, payload: dict[str, Any] | None = None) -> JSONResponse:
    conn = _conn()
    try:
        from .pilot import record_decision

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
