from __future__ import annotations

import json
import re
import sqlite3
import ssl
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .daily_boards import current_matches_board
from .io import atomic_write_json, atomic_write_text
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


FIXTURE_SANITY_JSON_LATEST = "fixture_sanity_latest.json"
FIXTURE_SANITY_MD_LATEST = "fixture_sanity_latest.md"
FIXTURE_SANITY_PDF_LATEST = "fixture_sanity_latest.pdf"
OPENFOOTBALL_RAW_LATEST = "openfootball_worldcup_2026_raw_latest.json"
OPENFOOTBALL_2026_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")

TEAM_ALIASES = {
    "czech republic": "czechia",
    "czech rep": "czechia",
    "korea republic": "south korea",
    "republic of korea": "south korea",
    "usa": "united states",
    "u s a": "united states",
    "united states of america": "united states",
    "bosnia herzegovina": "bosnia and herzegovina",
    "bosn herzegovina": "bosnia and herzegovina",
    "bosn herzeg": "bosnia and herzegovina",
    "bosn herzeg...": "bosnia and herzegovina",
    "cote d ivoire": "ivory coast",
    "côte d ivoire": "ivory coast",
}


def write_fixture_sanity_bundle(
    output_dir: Path,
    db_path: Path | None = None,
    *,
    openfootball_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_fixture_sanity(output_dir, db_path, openfootball_payload=openfootball_payload)
    json_path = output_dir / FIXTURE_SANITY_JSON_LATEST
    md_path = output_dir / FIXTURE_SANITY_MD_LATEST
    pdf_path = output_dir / FIXTURE_SANITY_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_fixture_sanity_markdown(payload))
    pdf_summary = write_fixture_sanity_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_fixture_sanity(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_fixture_sanity(
    output_dir: Path,
    db_path: Path,
    *,
    openfootball_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    source_payload, fetch_status = load_openfootball_payload(output_dir, openfootball_payload=openfootball_payload)
    if source_payload:
        atomic_write_json(output_dir / OPENFOOTBALL_RAW_LATEST, source_payload)
    openfootball_rows = openfootball_fixture_rows(source_payload)
    tab_rows = tab_match_rows(output_dir)
    comparison_rows = compare_fixtures(tab_rows, openfootball_rows)
    summary = summarize_fixture_sanity(openfootball_rows, tab_rows, comparison_rows, fetch_status)
    status = executive_status(summary)
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "fixture_sanity_dashboard",
        "purpose": "使用 openfootball/worldcup.json 的 2026 World Cup 公开赛程，对 TAB matches raw 中的比赛名称、日期、分组、场地和赛果字段做公开校验；只做赛程 sanity-check，不替代 TAB 赔率。",
        "executive_status": {
            "status": status,
            "fixture_sanity_ready": status.startswith("ready"),
            "source_fetch_ready": bool(fetch_status.get("ready")),
            "current_action": "用作公开赛程交叉校验" if status.startswith("ready") else "等待公开赛程源或 TAB raw 恢复",
            "primary_gap": primary_gap(summary),
            "recommended_next_action": recommended_next_action(summary),
        },
        "summary": summary,
        "source_fetch_status": fetch_status,
        "source_caveat": {
            "source": "openfootball/worldcup.json",
            "url": OPENFOOTBALL_2026_URL,
            "freshness": "delayed_public_source_not_live",
            "license": "public domain / CC0",
            "limitation": "openfootball 不是 TAB 官方盘口源，也不是 live odds feed；只能校验赛程、队名、分组、场地和公开赛果，不能用于替代赔率抓取。",
        },
        "comparison_rows": comparison_rows,
        "tab_rows": tab_rows,
        "openfootball_rows": openfootball_rows,
        "old_new_compare": old_new_compare(db_path, comparison_rows, summary),
        "evidence_layers": [
            {"layer": "FACT", "text": "openfootball/worldcup.json 公开 2026 World Cup 赛程 JSON。"},
            {"layer": "FACT", "text": "TAB matches raw 只读取本地公开 raw 快照中的 match/title 文本。"},
            {"layer": "INFERENCE", "text": "队名 alias、无序主客匹配、缺失/仅 TAB/仅公开源状态由本地代码计算。"},
        ],
        "truthfulness_note": "该报告是公开赛程校验，不是赔率源、不是 live 数据源、不是下注执行指令；openfootball 源可能滞后。",
        "safety_note": "不读取账户、不点击赔率、不添加 Bet Slip、不自动下注；即使校验 ready，也不会解除 raw/private/preflight 门禁。",
    }
    return sanitize_public_payload(payload)


def load_openfootball_payload(
    output_dir: Path,
    *,
    openfootball_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(openfootball_payload, dict):
        return openfootball_payload, {
            "ready": True,
            "status": "injected_fixture",
            "method": "test_or_caller_supplied_payload",
            "url": OPENFOOTBALL_2026_URL,
        }
    payload, status = fetch_openfootball_payload()
    if payload:
        return payload, status
    cached = load_json(Path(output_dir) / OPENFOOTBALL_RAW_LATEST)
    if cached:
        return cached, {
            **status,
            "ready": True,
            "status": "using_cached_public_source",
            "method": f"{status.get('method', 'unknown')} -> cached",
            "cache_artifact": OPENFOOTBALL_RAW_LATEST,
        }
    return {}, status


def fetch_openfootball_payload(timeout: int = 12) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    attempts = [
        ("urllib_default_ssl", None),
        ("urllib_certifi_ssl", "certifi"),
    ]
    for method, ssl_mode in attempts:
        try:
            context = None
            if ssl_mode == "certifi":
                try:
                    import certifi  # type: ignore

                    context = ssl.create_default_context(cafile=certifi.where())
                except Exception as exc:
                    errors.append(f"{method}: certifi unavailable: {exc}")
                    continue
            with urllib.request.urlopen(OPENFOOTBALL_2026_URL, timeout=timeout, context=context) as response:
                return parse_json_bytes(response.read()), {"ready": True, "status": "fetched", "method": method, "url": OPENFOOTBALL_2026_URL}
        except Exception as exc:
            errors.append(f"{method}: {type(exc).__name__}: {exc}")
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout), OPENFOOTBALL_2026_URL],
            text=True,
            capture_output=True,
            timeout=timeout + 3,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout), {"ready": True, "status": "fetched", "method": "curl", "url": OPENFOOTBALL_2026_URL}
        errors.append(f"curl: exit {result.returncode}: {result.stderr.strip()[:240]}")
    except Exception as exc:
        errors.append(f"curl: {type(exc).__name__}: {exc}")
    return {}, {"ready": False, "status": "fetch_failed", "method": "urllib+curl", "url": OPENFOOTBALL_2026_URL, "errors": errors[-4:]}


def parse_json_bytes(data: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def openfootball_fixture_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    matches = payload.get("matches") or []
    rows = []
    for item in matches:
        if not isinstance(item, dict):
            continue
        team1 = str(item.get("team1") or "")
        team2 = str(item.get("team2") or "")
        if not team1 or not team2:
            continue
        score = item.get("score") or {}
        ft = score.get("ft") if isinstance(score, dict) else None
        score_ft = ""
        if isinstance(ft, list) and len(ft) >= 2:
            score_ft = f"{ft[0]}-{ft[1]}"
        row = {
            "source": "openfootball/worldcup.json",
            "match": f"{team1} v {team2}",
            "team1": team1,
            "team2": team2,
            "team_key": team_key(team1, team2),
            "date": str(item.get("date") or ""),
            "time": str(item.get("time") or ""),
            "round": str(item.get("round") or item.get("stage") or ""),
            "group": str(item.get("group") or ""),
            "ground": str(item.get("ground") or ""),
            "city": str(item.get("city") or ""),
            "score_ft": score_ft,
        }
        rows.append(row)
    return rows


def tab_match_rows(output_dir: Path) -> list[dict[str, Any]]:
    raw_path = Path(output_dir) / current_matches_board().raw_snapshot
    payload = load_json(raw_path)
    rows = []
    for item in payload.get("matches") or []:
        if not isinstance(item, dict):
            continue
        match = str(item.get("match") or item.get("title") or "").strip()
        teams = split_match_teams(match)
        if not match or not teams:
            continue
        rows.append(
            {
                "source": current_matches_board().raw_snapshot,
                "match": match,
                "team1": teams[0],
                "team2": teams[1],
                "team_key": team_key(teams[0], teams[1]),
                "href_present": bool(item.get("href")),
                "market_count": len(item.get("markets") or {}),
            }
        )
    return rows


def compare_fixtures(tab_rows: list[dict[str, Any]], openfootball_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    open_by_key = {str(row.get("team_key")): row for row in openfootball_rows}
    tab_by_key = {str(row.get("team_key")): row for row in tab_rows}
    rows: list[dict[str, Any]] = []
    for tab in tab_rows:
        fixture = open_by_key.get(str(tab.get("team_key"))) or {}
        if fixture:
            status = "matched"
            reason = "TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。"
        else:
            status = "tab_only_missing_openfootball"
            reason = "TAB raw 中出现，但 openfootball 当前公开源未匹配；需人工确认是否队名 alias、赛程源滞后或 TAB 板块扩展。"
        rows.append(
            {
                "status": status,
                "tab_match": tab.get("match", ""),
                "openfootball_match": fixture.get("match", ""),
                "date": fixture.get("date", ""),
                "time": fixture.get("time", ""),
                "round": fixture.get("round", ""),
                "group": fixture.get("group", ""),
                "ground": fixture.get("ground", ""),
                "score_ft": fixture.get("score_ft", ""),
                "tab_market_count": tab.get("market_count", 0),
                "reason": reason,
            }
        )
    for fixture in openfootball_rows:
        if str(fixture.get("team_key")) in tab_by_key:
            continue
        rows.append(
            {
                "status": "openfootball_only_not_in_tab_raw",
                "tab_match": "",
                "openfootball_match": fixture.get("match", ""),
                "date": fixture.get("date", ""),
                "time": fixture.get("time", ""),
                "round": fixture.get("round", ""),
                "group": fixture.get("group", ""),
                "ground": fixture.get("ground", ""),
                "score_ft": fixture.get("score_ft", ""),
                "tab_market_count": 0,
                "reason": "openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。",
            }
        )
    return rows


def summarize_fixture_sanity(
    openfootball_rows: list[dict[str, Any]],
    tab_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    fetch_status: dict[str, Any],
) -> dict[str, Any]:
    status_counts = counter(row.get("status") for row in comparison_rows)
    matched_count = int(status_counts.get("matched", 0))
    tab_only_count = int(status_counts.get("tab_only_missing_openfootball", 0))
    open_only_count = int(status_counts.get("openfootball_only_not_in_tab_raw", 0))
    score_available = sum(1 for row in openfootball_rows if row.get("score_ft"))
    return {
        "source_fetch_ready": bool(fetch_status.get("ready")),
        "source_fetch_status": str(fetch_status.get("status") or ""),
        "source_freshness": "delayed_public_source_not_live",
        "openfootball_match_count": len(openfootball_rows),
        "tab_match_count": len(tab_rows),
        "comparison_row_count": len(comparison_rows),
        "matched_count": matched_count,
        "tab_only_count": tab_only_count,
        "openfootball_only_count": open_only_count,
        "date_available_count": sum(1 for row in openfootball_rows if row.get("date")),
        "score_available_count": score_available,
        "status_distribution": status_counts,
        "sanity_ready": bool(openfootball_rows) and bool(tab_rows) and matched_count > 0,
        "mismatch_review_count": tab_only_count + open_only_count,
    }


def executive_status(summary: dict[str, Any]) -> str:
    if summary.get("sanity_ready"):
        return "ready_with_delayed_public_source"
    if summary.get("openfootball_match_count") and not summary.get("tab_match_count"):
        return "partial_no_tab_raw"
    if summary.get("tab_match_count") and not summary.get("openfootball_match_count"):
        return "partial_public_source_missing"
    return "source_fetch_failed"


def old_new_compare(db_path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "matched_count_delta": 0, "mismatch_review_delta": 0}
    try:
        with connect_report_db(db_path) as conn:
            previous = conn.execute(
                """
                SELECT generated_at, matched_count, tab_only_count, openfootball_only_count, payload_json
                FROM fixture_sanity_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "matched_count_delta": 0, "mismatch_review_delta": 0}
    if not previous:
        return {"status": "no_previous_snapshot", "matched_count_delta": 0, "mismatch_review_delta": 0}
    previous_payload = parse_json_text(previous["payload_json"])
    previous_keys = {
        f"{item.get('status')}::{item.get('tab_match') or item.get('openfootball_match')}"
        for item in previous_payload.get("comparison_rows") or []
        if isinstance(item, dict)
    }
    current_keys = {f"{item.get('status')}::{item.get('tab_match') or item.get('openfootball_match')}" for item in rows}
    previous_mismatch = int(previous["tab_only_count"] or 0) + int(previous["openfootball_only_count"] or 0)
    current_mismatch = int(summary.get("mismatch_review_count") or 0)
    return {
        "status": "compared",
        "previous_generated_at": previous["generated_at"],
        "matched_count_delta": int(summary.get("matched_count") or 0) - int(previous["matched_count"] or 0),
        "tab_only_delta": int(summary.get("tab_only_count") or 0) - int(previous["tab_only_count"] or 0),
        "openfootball_only_delta": int(summary.get("openfootball_only_count") or 0) - int(previous["openfootball_only_count"] or 0),
        "mismatch_review_delta": current_mismatch - previous_mismatch,
        "new_fixture_status_rows": sorted(current_keys - previous_keys)[:8],
        "removed_fixture_status_rows": sorted(previous_keys - current_keys)[:8],
    }


def render_fixture_sanity_markdown(payload: dict[str, Any]) -> str:
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    source = payload.get("source_caveat") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 公开赛程校验 Dashboard",
        "",
        "本报告使用 openfootball/worldcup.json 公开赛程对 TAB World Cup Matches raw 做 sanity-check。它不读取账户、不替代 TAB 赔率，也不是下注执行指令。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- fixture_sanity_ready: `{executive.get('fixture_sanity_ready', False)}`",
        f"- openfootball_match_count: `{summary.get('openfootball_match_count', 0)}`",
        f"- tab_match_count: `{summary.get('tab_match_count', 0)}`",
        f"- matched_count: `{summary.get('matched_count', 0)}`",
        f"- mismatch_review_count: `{summary.get('mismatch_review_count', 0)}`",
        f"- source_freshness: `{summary.get('source_freshness', '')}`",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## 公开源说明",
        "",
        f"- source: `{source.get('source', '')}`",
        f"- url: `{source.get('url', '')}`",
        f"- license: `{source.get('license', '')}`",
        f"- limitation: {md(source.get('limitation'))}",
        "",
        "## 新旧变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- matched_count_delta: `{compare.get('matched_count_delta', 0)}`",
        f"- mismatch_review_delta: `{compare.get('mismatch_review_delta', 0)}`",
        "",
        "## 赛程校验明细",
        "",
        "| 状态 | TAB比赛 | 公开赛程 | 日期 | 分组/轮次 | 场地 | 赛果 | 原因 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("comparison_rows") or []:
        lines.append(
            "| {status} | {tab} | {fixture} | {date} {time} | {group} {round} | {ground} | {score} | {reason} |".format(
                status=md(row.get("status")),
                tab=md(row.get("tab_match")),
                fixture=md(row.get("openfootball_match")),
                date=md(row.get("date")),
                time=md(row.get("time")),
                group=md(row.get("group")),
                round=md(row.get("round")),
                ground=md(row.get("ground")),
                score=md(row.get("score_ft")),
                reason=md(row.get("reason")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_fixture_sanity_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    rows = payload.get("comparison_rows") or []
    compare = payload.get("old_new_compare") or {}
    source = payload.get("source_caveat") or {}
    distribution = summary.get("status_distribution") or {}
    charts = [
        chart_from_items(
            "公开源 / TAB / 匹配",
            [
                ("openfootball", summary.get("openfootball_match_count", 0)),
                ("TAB raw", summary.get("tab_match_count", 0)),
                ("matched", summary.get("matched_count", 0)),
                ("review", summary.get("mismatch_review_count", 0)),
            ],
            "#1F4E79",
        ),
        chart_from_items("状态分布", [(key, value) for key, value in distribution.items()], "#247A5A"),
        chart_from_items(
            "公开赛程字段覆盖",
            [
                ("date", summary.get("date_available_count", 0)),
                ("score", summary.get("score_available_count", 0)),
                ("source ready", 1 if summary.get("source_fetch_ready") else 0),
                ("sanity ready", 1 if summary.get("sanity_ready") else 0),
            ],
            "#6A4C93",
        ),
        chart_from_items(
            "新旧变化",
            [
                ("matched Δ", abs(float(compare.get("matched_count_delta") or 0))),
                ("review Δ", abs(float(compare.get("mismatch_review_delta") or 0))),
                ("tab-only Δ", abs(float(compare.get("tab_only_delta") or 0))),
                ("public-only Δ", abs(float(compare.get("openfootball_only_delta") or 0))),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 公开赛程校验 Dashboard",
        subtitle="openfootball 公开赛程 vs TAB World Cup Matches raw；用于赛程 sanity-check，不是 live odds，不替代 TAB 盘口。",
        summary_rows=[
            ("status", str((payload.get("executive_status") or {}).get("status", ""))),
            ("source_fetch", str(summary.get("source_fetch_status", ""))),
            ("openfootball matches", str(summary.get("openfootball_match_count", 0))),
            ("TAB matches", str(summary.get("tab_match_count", 0))),
            ("matched", str(summary.get("matched_count", 0))),
            ("review queue", str(summary.get("mismatch_review_count", 0))),
            ("source freshness", str(summary.get("source_freshness", ""))),
        ],
        charts=charts,
        table_headers=["状态", "TAB比赛", "公开赛程", "日期", "分组", "场地"],
        table_rows=[
            [
                str(row.get("status", "")),
                str(row.get("tab_match", "")),
                str(row.get("openfootball_match", "")),
                f"{row.get('date', '')} {row.get('time', '')}".strip(),
                f"{row.get('group', '')} {row.get('round', '')}".strip(),
                str(row.get("ground", "")),
            ]
            for row in rows[:24]
        ],
        extra_tables=[
            {
                "title": "公开源限制",
                "headers": ["项目", "说明"],
                "rows": [
                    ["source", str(source.get("source", ""))],
                    ["url", str(source.get("url", ""))],
                    ["license", str(source.get("license", ""))],
                    ["limitation", str(source.get("limitation", ""))],
                ],
            },
            {
                "title": "新旧赛程校验变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["matched_count_delta", str(compare.get("matched_count_delta", 0))],
                    ["mismatch_review_delta", str(compare.get("mismatch_review_delta", 0))],
                    ["new_fixture_status_rows", "；".join(compare.get("new_fixture_status_rows") or [])],
                ],
            },
            {
                "title": "Review Queue",
                "headers": ["状态", "比赛", "原因"],
                "rows": [
                    [
                        str(row.get("status", "")),
                        str(row.get("tab_match") or row.get("openfootball_match") or ""),
                        str(row.get("reason", "")),
                    ]
                    for row in rows
                    if row.get("status") != "matched"
                ][:18],
            },
        ],
    )


def persist_fixture_sanity(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fixture_sanity_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    openfootball_match_count INTEGER NOT NULL DEFAULT 0,
                    tab_match_count INTEGER NOT NULL DEFAULT 0,
                    matched_count INTEGER NOT NULL DEFAULT 0,
                    tab_only_count INTEGER NOT NULL DEFAULT 0,
                    openfootball_only_count INTEGER NOT NULL DEFAULT 0,
                    source_fetch_ready INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO fixture_sanity_snapshots(
                    snapshot_id, generated_at, status, openfootball_match_count, tab_match_count,
                    matched_count, tab_only_count, openfootball_only_count, source_fetch_ready, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    int(summary.get("openfootball_match_count") or 0),
                    int(summary.get("tab_match_count") or 0),
                    int(summary.get("matched_count") or 0),
                    int(summary.get("tab_only_count") or 0),
                    int(summary.get("openfootball_only_count") or 0),
                    int(bool(summary.get("source_fetch_ready"))),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "fixture_sanity_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def split_match_teams(match: str) -> tuple[str, str] | None:
    cleaned = re.sub(r"\s+", " ", match.replace(" vs ", " v ")).strip()
    parts = re.split(r"\s+v\s+|\s+V\s+", cleaned, maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = parts[0].strip(), parts[1].strip()
    return (left, right) if left and right else None


def normalize_team(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return TEAM_ALIASES.get(text, text)


def team_key(team1: str, team2: str) -> str:
    return "::".join(sorted([normalize_team(team1), normalize_team(team2)]))


def counter(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "")
        counts[key] = counts.get(key, 0) + 1
    return counts


def recommended_next_action(summary: dict[str, Any]) -> str:
    if summary.get("sanity_ready") and not summary.get("mismatch_review_count"):
        return "保持作为公开赛程 sanity-check；下注建议仍以 TAB raw 和日报门禁为准。"
    if summary.get("sanity_ready"):
        return "优先人工复核 tab_only/openfootball_only 队名和日期差异；不要用公开源替代 TAB 赔率。"
    if not summary.get("openfootball_match_count"):
        return "公开赛程源未取回；等待网络或使用缓存后重跑。"
    return "TAB matches raw 缺失或未匹配；先接入授权 raw 或导入用户导出快照，再重跑赛程校验。"


def primary_gap(summary: dict[str, Any]) -> str:
    if not summary.get("openfootball_match_count"):
        return "公开赛程源未就绪"
    if not summary.get("tab_match_count"):
        return "TAB matches raw 未就绪"
    if summary.get("mismatch_review_count"):
        return "存在赛程匹配差异待复核"
    return "无关键赛程缺口"


def snapshot_id(generated_at: str) -> str:
    return "fixture-sanity-" + str(generated_at or "").replace(":", "").replace("+", "-").replace(".", "-")


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_json_text(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
