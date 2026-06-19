from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from zoneinfo import ZoneInfo

from .artifact_compare import build_artifact_old_new_compare
from .artifacts import sanitize_public_payload
from .boards import BOARD_CONFIGS
from .io import atomic_write_json, atomic_write_text
from .raw_refresh import looks_like_route_mismatch
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


LIVE_BOARD_DISCOVERY_RAW_LATEST = "tab_fifa_live_board_discovery_raw_latest.json"
LIVE_BOARD_DISCOVERY_JSON_LATEST = "live_board_discovery_latest.json"
LIVE_BOARD_DISCOVERY_MD_LATEST = "live_board_discovery_latest.md"
LIVE_BOARD_DISCOVERY_PDF_LATEST = "live_board_discovery_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_live_board_discovery_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_live_board_discovery(output_dir)
    json_path = output_dir / LIVE_BOARD_DISCOVERY_JSON_LATEST
    md_path = output_dir / LIVE_BOARD_DISCOVERY_MD_LATEST
    pdf_path = output_dir / LIVE_BOARD_DISCOVERY_PDF_LATEST
    payload["old_new_compare"] = build_artifact_old_new_compare(json_path, payload, live_board_compare_metrics())
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_live_board_discovery_markdown(payload))
    pdf_summary = write_live_board_discovery_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_live_board_discovery(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    raw = load_json(output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST)
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    diagnostics = load_json(output_dir / "raw_refresh_diagnostics_latest.json")
    route_mismatch = has_route_mismatch(raw_health, diagnostics)
    raw_summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
    raw_failed = discovery_raw_failed(raw)
    discovery_ready = (not raw_failed) and bool(raw_summary.get("discovery_ready", bool(raw)))
    expected_rows = normalize_expected_rows(raw)
    observed_rows = normalize_observed_rows(raw)
    missing_rows = [row for row in expected_rows if row["live_nav_status"] != "listed"]
    listed_rows = [row for row in expected_rows if row["live_nav_status"] == "listed"]
    unavailable_rows = [row for row in expected_rows if row["automation_decision"] == "temporarily_unavailable_review"]
    summary = {
        "discovery_raw_exists": bool(raw),
        "discovery_ready": discovery_ready,
        "quality_status": raw_summary.get("quality_status", "blocked_discovery_failed" if raw_failed else "ready" if discovery_ready else "missing"),
        "quality_issue_count": len(raw_summary.get("quality_issues") or []),
        "access_denied": bool(raw_summary.get("access_denied")),
        "discovery_failed": raw_failed,
        "expected_board_count": len(expected_rows),
        "listed_expected_count": len(listed_rows),
        "missing_expected_count": len(missing_rows),
        "observed_world_cup_link_count": len(observed_rows),
        "route_mismatch_active": route_mismatch,
        "temporarily_unavailable_count": len(unavailable_rows),
        "retry_required_count": len([row for row in expected_rows if row["automation_decision"] == "discovery_retry_required"]),
        "full_expected_nav_ready": discovery_ready and bool(expected_rows) and not missing_rows,
    }
    status = "ready" if summary["full_expected_nav_ready"] else "blocked"
    primary_gap = "无 live board 缺口" if status == "ready" else missing_gap_text(missing_rows, raw, summary)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "live_board_discovery_dashboard",
        "purpose": "TAB Soccer live board discovery：自动发现当前公开导航中实际列出的 FIFA/World Cup 板块，并把缺失板块放入 unavailable review queue；只读，不自动下注。",
        "executive_status": {
            "status": status,
            "primary_gap": primary_gap,
            "route_mismatch_active": route_mismatch,
            "recommended_next_action": recommended_next_action(status, missing_rows, summary),
        },
        "summary": summary,
        "expected_board_rows": expected_rows,
        "observed_world_cup_links": observed_rows,
        "unavailable_review_queue": unavailable_review_queue(unavailable_rows),
        "discovery_retry_queue": discovery_retry_queue(expected_rows, summary),
        "source_artifacts": {
            "raw_discovery": LIVE_BOARD_DISCOVERY_RAW_LATEST if raw else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "raw_refresh_diagnostics": "raw_refresh_diagnostics_latest.json" if diagnostics else "",
        },
        "truthfulness_note": "live 导航缺失的板块不得用旧 raw 或旧报告生成当前可执行下注建议；只能进入人工复核/重新发现队列。",
    }
    return sanitize_public_payload(payload)


def live_board_compare_metrics() -> list[tuple[str, str]]:
    return [
        ("status", "executive_status.status"),
        ("route_mismatch_active", "executive_status.route_mismatch_active"),
        ("discovery_ready", "summary.discovery_ready"),
        ("quality_status", "summary.quality_status"),
        ("access_denied", "summary.access_denied"),
        ("listed_expected_count", "summary.listed_expected_count"),
        ("missing_expected_count", "summary.missing_expected_count"),
        ("observed_world_cup_link_count", "summary.observed_world_cup_link_count"),
        ("retry_required_count", "summary.retry_required_count"),
    ]


def normalize_expected_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    raw_rows = raw.get("expected_boards") or []
    by_refresh = {row.get("refresh_board_id"): row for row in raw_rows if isinstance(row, dict)}
    raw_unusable = (not raw) or discovery_raw_failed(raw)
    rows = []
    for board in BOARD_CONFIGS:
        raw_row = by_refresh.get(board.refresh_board_id) or {}
        matched_links = raw_row.get("matched_links") or []
        live_status = raw_row.get("live_nav_status") or ("discovery_blocked" if raw_unusable else "discovery_missing")
        decision = raw_row.get("automation_decision") or (
            "refresh_allowed"
            if live_status == "listed"
            else "discovery_retry_required"
            if raw_unusable or live_status == "discovery_blocked"
            else "temporarily_unavailable_review"
        )
        rows.append(
            {
                "board_id": board.board_id,
                "refresh_board_id": board.refresh_board_id,
                "name": board.name,
                "priority": board.priority,
                "required_for_full_automation": bool(board.required_for_full_automation),
                "live_nav_status": live_status,
                "matched_link_count": int(raw_row.get("matched_link_count") or 0),
                "matched_text_marker": bool(raw_row.get("matched_text_marker")),
                "automation_decision": decision,
                "matched_links": [
                    {"text": str(item.get("text") or ""), "href": str(item.get("href") or "")}
                    for item in matched_links[:3]
                    if isinstance(item, dict)
                ],
                "next_action": row_next_action(decision),
            }
        )
    return rows


def discovery_raw_failed(raw: dict[str, Any]) -> bool:
    if not raw:
        return False
    status = str(raw.get("status") or "").lower()
    if status in {"failed", "blocked", "error"}:
        return True
    if raw.get("discovery_error") or raw.get("refresh_error"):
        return True
    summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
    quality = str(summary.get("quality_status") or "").lower()
    return quality.startswith("blocked") or summary.get("discovery_ready") is False


def normalize_observed_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(raw.get("observed_world_cup_links") or [], start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "rank": index,
                "text": str(item.get("text") or ""),
                "href": str(item.get("href") or ""),
                "mapped_expected_board": mapped_expected_board(item),
            }
        )
    return rows[:40]


def mapped_expected_board(item: dict[str, Any]) -> str:
    text = unquote(f"{item.get('text') or ''} {item.get('href') or ''}").lower()
    for board in BOARD_CONFIGS:
        if board.name.lower() in text:
            return board.name
        competition_marker = board_competition_marker(board.tab_path)
        if competition_marker and competition_marker in text:
            return board.name
    return ""


def board_competition_marker(tab_path: str) -> str:
    decoded = unquote(str(tab_path or "")).lower()
    marker = "/competitions/"
    if marker not in decoded:
        return ""
    competition = decoded.split(marker, 1)[1].split("/", 1)[0]
    return f"/competitions/{competition}" if competition else ""


def unavailable_review_queue(missing_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for rank, row in enumerate(missing_rows, start=1):
        queue.append(
            {
                "rank": rank,
                "board_id": row["board_id"],
                "name": row["name"],
                "reason": "TAB Soccer live nav 未列出该 expected board",
                "operation": "重新发现 TAB Soccer live board list；若仍缺失，保持 unavailable，不用旧盘口生成下注建议。",
                "success_gate": "live nav 出现该板块，且 deep link resolves to expected board",
            }
        )
    return queue


def discovery_retry_queue(expected_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[dict[str, Any]]:
    if summary.get("discovery_ready"):
        return []
    queue = []
    for rank, row in enumerate(
        [item for item in expected_rows if item.get("automation_decision") == "discovery_retry_required"],
        start=1,
    ):
        queue.append(
            {
                "rank": rank,
                "board_id": row["board_id"],
                "name": row["name"],
                "reason": str(summary.get("quality_status") or "discovery quality gate failed"),
                "operation": "TAB 拒绝 AI controlled access 时停止自动 discovery；等待官方/授权数据源或用户导出导入。",
                "success_gate": "导入或授权数据通过 Soccer board list freshness、coverage 和 public safety 门禁。",
            }
        )
    return queue


def has_route_mismatch(raw_health: dict[str, Any], diagnostics: dict[str, Any]) -> bool:
    if "route_mismatch" in (raw_health.get("blocker_codes") or []):
        return True
    if looks_like_route_mismatch(raw_health.get("refresh_error") or ""):
        return True
    for item in diagnostics.get("attempts") or []:
        if looks_like_route_mismatch(item.get("error") or item.get("stderr_tail") or ""):
            return True
    return False


def missing_gap_text(missing_rows: list[dict[str, Any]], raw: dict[str, Any], summary: dict[str, Any]) -> str:
    if not raw:
        return "尚未运行 TAB Soccer live board discovery"
    if not summary.get("discovery_ready"):
        quality = str(summary.get("quality_status") or "quality gate failed")
        return f"TAB live board discovery 未通过质量门禁：{quality}"
    names = "、".join(row["name"].replace("2026 World Cup ", "") for row in missing_rows[:4])
    return f"TAB live 导航缺失 {len(missing_rows)} 个 expected board：{names}"


def recommended_next_action(status: str, missing_rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if status == "ready":
        return "live board discovery 已覆盖全部 expected boards；继续执行只读 raw refresh。"
    if not summary.get("discovery_ready"):
        return "TAB 拒绝 AI controlled access 时自动 discovery 保持 fail-closed；等待官方/授权数据源或用户导出导入，成功前不把板块标记为下架。"
    if missing_rows:
        return "先按 unavailable review queue 复核缺失板块；缺失期间只允许生成研究/诊断视图，不发布当前可执行下注日报。"
    return "先运行只读 discovery 脚本，生成 live board list 证据。"


def row_next_action(decision: str) -> str:
    if decision == "refresh_allowed":
        return "允许进入只读 raw refresh。"
    if decision == "discovery_retry_required":
        return "Discovery 质量门禁失败；先重试只读发现，不判断板块下架。"
    return "标记 unavailable；重新发现或等待 TAB 重新列出该板块。"


def render_live_board_discovery_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA Live Board Discovery Dashboard",
        "",
        "本报告自动发现 TAB Soccer 当前公开导航中实际列出的 FIFA/World Cup 板块；只读，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- primary_gap: {md(executive.get('primary_gap'))}",
        f"- expected boards: `{summary.get('listed_expected_count', 0)}/{summary.get('expected_board_count', 0)}`",
        f"- missing expected boards: `{summary.get('missing_expected_count', 0)}`",
        f"- observed world cup links: `{summary.get('observed_world_cup_link_count', 0)}`",
        f"- route_mismatch_active: `{bool(summary.get('route_mismatch_active'))}`",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## Expected Board Status",
        "",
        "| 板块 | live nav | matched | automation decision | 下一步 |",
        "|---|---|---:|---|---|",
    ]
    for row in payload.get("expected_board_rows") or []:
        lines.append(
            f"| {md(row.get('name'))} | {md(row.get('live_nav_status'))} | {row.get('matched_link_count', 0)} | {md(row.get('automation_decision'))} | {md(row.get('next_action'))} |"
        )
    lines.extend(["", "## Unavailable Review Queue", "", "| 顺序 | 板块 | 原因 | 操作 | 成功门禁 |", "|---:|---|---|---|---|"])
    for row in payload.get("unavailable_review_queue") or []:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('name'))} | {md(row.get('reason'))} | {md(row.get('operation'))} | {md(row.get('success_gate'))} |"
        )
    lines.extend(["", "## Discovery Retry Queue", "", "| 顺序 | 板块 | 原因 | 操作 | 成功门禁 |", "|---:|---|---|---|---|"])
    for row in payload.get("discovery_retry_queue") or []:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('name'))} | {md(row.get('reason'))} | {md(row.get('operation'))} | {md(row.get('success_gate'))} |"
        )
    lines.extend(["", "## Observed World Cup Links", "", "| 顺序 | 链接文本 | mapped expected board |", "|---:|---|---|"])
    for row in (payload.get("observed_world_cup_links") or [])[:20]:
        lines.append(f"| {row.get('rank', '')} | {md(row.get('text'))} | {md(row.get('mapped_expected_board'))} |")
    lines.extend(
        [
            "",
            "## old_new_compare / 新旧发现变化",
            "",
            f"- compare_status: `{compare.get('status', '')}`",
            f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
            f"- changed_count: `{compare.get('changed_count', 0)}/{compare.get('metric_count', 0)}`",
            f"- summary: {md(compare.get('summary'))}",
            "",
            "| 指标 | 当前 | 上一版 | 变化 |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in compare.get("rows") or []:
        lines.append(f"| {md(row.get('metric'))} | {md(row.get('current'))} | {md(row.get('previous'))} | {md(row.get('delta'))} |")
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines)


def write_live_board_discovery_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("expected_board_rows") or []
    queue = payload.get("unavailable_review_queue") or []
    observed = payload.get("observed_world_cup_links") or []
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items(
            "Expected board coverage",
            [
                ("listed", summary.get("listed_expected_count", 0)),
                ("missing", summary.get("missing_expected_count", 0)),
            ],
            "#1F4E79",
        ),
        chart_from_items(
            "Automation decision",
            [
                ("refresh allowed", len([row for row in rows if row.get("automation_decision") == "refresh_allowed"])),
                ("unavailable", len([row for row in rows if row.get("automation_decision") != "refresh_allowed"])),
            ],
            "#A56710",
        ),
        chart_from_items("Observed links", [("World Cup links", summary.get("observed_world_cup_link_count", 0))], "#247A5A"),
        chart_from_items("Route mismatch", [("active", 1 if summary.get("route_mismatch_active") else 0)], "#C62828"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Live Board Discovery Dashboard",
        subtitle="自动发现 TAB Soccer live 导航中的 FIFA/World Cup 板块；缺失板块进入 unavailable review queue。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("primary gap", str(executive.get("primary_gap", ""))),
            ("expected boards", f"{summary.get('listed_expected_count', 0)}/{summary.get('expected_board_count', 0)}"),
            ("missing expected", str(summary.get("missing_expected_count", 0))),
            ("observed links", str(summary.get("observed_world_cup_link_count", 0))),
            ("route mismatch active", str(bool(summary.get("route_mismatch_active")))),
        ],
        charts=charts,
        table_headers=["板块", "live nav", "matched", "decision", "下一步"],
        table_rows=[
            [
                str(row.get("name", "")),
                str(row.get("live_nav_status", "")),
                str(row.get("matched_link_count", 0)),
                str(row.get("automation_decision", "")),
                str(row.get("next_action", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "Unavailable Review Queue",
                "headers": ["顺序", "板块", "原因", "成功门禁"],
                "rows": [
                    [str(row.get("rank", "")), str(row.get("name", "")), str(row.get("reason", "")), str(row.get("success_gate", ""))]
                    for row in queue
                ],
            },
            {
                "title": "Observed World Cup Links",
                "headers": ["顺序", "链接文本", "mapped board"],
                "rows": [
                    [str(row.get("rank", "")), str(row.get("text", "")), str(row.get("mapped_expected_board", ""))]
                    for row in observed[:12]
                ],
            },
            {
                "title": "新旧发现变化",
                "headers": ["指标", "当前", "上一版", "变化"],
                "rows": [
                    [str(row.get("metric", "")), str(row.get("current", "")), str(row.get("previous", "")), str(row.get("delta", ""))]
                    for row in (compare.get("rows") or [])
                ],
            },
        ],
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
