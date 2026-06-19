from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PROVIDER_FALLBACK_VERIFICATION_JSON_LATEST = "provider_fallback_verification_latest.json"
PROVIDER_FALLBACK_VERIFICATION_MD_LATEST = "provider_fallback_verification_latest.md"
PROVIDER_FALLBACK_VERIFICATION_PDF_LATEST = "provider_fallback_verification_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")
TEAM_TOTAL_LABEL = "Team Total Goals Over/Under"
TOTAL_OU_LABEL = "Total Goals Over/Under"


def write_provider_fallback_verification_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_provider_fallback_verification(output_dir)
    json_path = output_dir / PROVIDER_FALLBACK_VERIFICATION_JSON_LATEST
    md_path = output_dir / PROVIDER_FALLBACK_VERIFICATION_MD_LATEST
    pdf_path = output_dir / PROVIDER_FALLBACK_VERIFICATION_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_provider_fallback_verification_markdown(payload))
    pdf_summary = write_provider_fallback_verification_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_provider_fallback_verification(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    plan = load_json(output_dir / "provider_alternate_plan_latest.json")
    blocked = load_json(output_dir / "odds_provider_blocked_latest.json")
    target = first_matches_target(coverage)
    raw = load_staged_matches_raw(output_dir, target)
    matches = [item for item in raw.get("matches") or [] if isinstance(item, Mapping)]
    queue = build_verification_queue(matches)
    blocker = str(blocked.get("blocker_code") or "")
    status = "manual_verification_required" if queue else "ready"
    if blocker:
        status = "provider_blocked_manual_verification_required" if queue else "provider_blocked_no_queue"
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_fallback_verification",
        "status": status,
        "scope": coverage.get("scope") or plan.get("scope") or "matches",
        "refresh_id": coverage.get("refresh_id") or plan.get("refresh_id") or "",
        "source_provider_status": plan.get("status", "missing"),
        "provider_blocker_code": blocker,
        "queue_count": len(queue),
        "top_priority_count": len([row for row in queue if row["priority_tier"] == "high"]),
        "manual_verification_queue": queue[:30],
        "manual_verification_contract": manual_verification_contract(),
        "recommended_next_action": recommended_next_action(queue, blocker),
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "truthfulness_note": (
            "该队列只把 provider 无法覆盖的盘口转成人工校验任务；不自动登录 TAB、不点击赔率、不加入 Bet Slip、"
            "不发布 formal raw，也不生成新增可执行下注金额。"
        ),
    }
    return sanitize_public_payload(payload)


def first_matches_target(coverage: Mapping[str, Any]) -> Mapping[str, Any]:
    for row in coverage.get("targets") or []:
        if isinstance(row, Mapping) and row.get("board_id") == "world_cup_matches":
            return row
    targets = coverage.get("targets") or []
    return targets[0] if targets and isinstance(targets[0], Mapping) else {}


def load_staged_matches_raw(output_dir: Path, target: Mapping[str, Any]) -> dict[str, Any]:
    staged = str(target.get("provider_staged_path") or "")
    if staged:
        path = output_dir / staged
        if path.exists():
            return load_json(path)
    return {}


def build_verification_queue(matches: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for match in matches:
        markets = match.get("markets") or {}
        if TEAM_TOTAL_LABEL in markets:
            continue
        covered_markets = sorted(str(key) for key in markets.keys())
        has_total = TOTAL_OU_LABEL in markets
        has_result = "Result" in markets
        has_handicap = "Handicap" in markets
        priority_score = (40 if has_total else 0) + (30 if has_result else 0) + (15 if has_handicap else 0)
        priority_tier = "high" if has_total and has_result else ("medium" if has_result else "watch")
        rows.append(
            {
                "event_id": str(match.get("provider_event_id") or ""),
                "match": str(match.get("match") or ""),
                "commence_time": str(match.get("commence_time") or ""),
                "missing_market": TEAM_TOTAL_LABEL,
                "covered_markets": covered_markets,
                "priority_score": priority_score,
                "priority_tier": priority_tier,
                "verification_scope": "只校验 Team Total O/U；如果该场 Total O/U 也缺失，则同步记录 Total O/U 是否存在。",
                "rank_reason": rank_reason(has_total=has_total, has_result=has_result, has_handicap=has_handicap),
                "required_manual_fields": [
                    "tab_match_name",
                    "tab_market_name",
                    "selection_name",
                    "line",
                    "decimal_odds",
                    "observed_at_aest",
                    "operator_initials",
                    "evidence_note_or_screenshot_ref",
                ],
                "post_verification_gate": "人工记录后只进入 provider_tab_final_verification hash gate；未通过前 stake 仍为 AUD 0。",
            }
        )
    rows.sort(key=lambda row: (tier_rank(row["priority_tier"]), row.get("commence_time") or "", row.get("match") or ""))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def rank_reason(*, has_total: bool, has_result: bool, has_handicap: bool) -> str:
    parts = []
    if has_result:
        parts.append("Result 已由 provider 覆盖")
    if has_total:
        parts.append("Total O/U 已由 provider 覆盖")
    if has_handicap:
        parts.append("Handicap 已由 provider 覆盖")
    if not parts:
        return "核心盘口覆盖不足，只作为低优先级人工校验候选。"
    return "；".join(parts) + "；Team Total 是当前主要缺口。"


def tier_rank(tier: str) -> int:
    return {"high": 0, "medium": 1, "watch": 2}.get(str(tier), 3)


def manual_verification_contract() -> dict[str, Any]:
    return {
        "allowed_actions": [
            "用户或人工操作员打开 TAB 页面读取盘口",
            "只记录候选比赛的 Team Total O/U 盘口、选择、line、decimal odds、观察时间和证据备注",
            "将人工记录写入后续 verification/import 文件，再走 hash gate",
        ],
        "forbidden_actions": [
            "自动登录 TAB",
            "自动点击赔率",
            "自动加入 Bet Slip",
            "自动下注",
            "绕过 CAPTCHA、Cloudflare、browser signature 或访问控制",
        ],
        "publish_gate": "provider_tab_final_verification refresh_id + board_id + sha256 匹配后才允许进入 formal raw publish；否则只作为研究证据。",
    }


def recommended_next_action(queue: list[Mapping[str, Any]], blocker: str) -> str:
    if not queue:
        return "当前没有 Team Total fallback 队列；进入 formal publish gate 和日报门禁复核。"
    if blocker == "opticodds_access_denied_1010":
        return "OpticOdds 当前被 1010 阻断；优先对高优先级候选做 TAB 人工 Team Total 校验，或向 OpticOdds 申请官方允许访问/白名单。"
    return "优先校验 high tier 候选；只记录盘口数据，不执行下注。"


def render_provider_fallback_verification_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Provider Fallback Verification Queue",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- queue_count: `{payload.get('queue_count', 0)}`",
        f"- top_priority_count: `{payload.get('top_priority_count', 0)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Manual Verification Queue",
        "",
        "| Rank | Match | Time | Priority | Missing | Reason |",
        "|---:|---|---|---|---|---|",
    ]
    for row in payload.get("manual_verification_queue") or []:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('match'))} | `{row.get('commence_time', '')}` | "
            f"`{row.get('priority_tier', '')}` | {md(row.get('missing_market'))} | {md(row.get('rank_reason'))} |"
        )
    contract = payload.get("manual_verification_contract") or {}
    lines.extend(["", "## Allowed Actions", ""])
    lines.extend(f"- {md(item)}" for item in contract.get("allowed_actions") or [])
    lines.extend(["", "## Forbidden Actions", ""])
    lines.extend(f"- {md(item)}" for item in contract.get("forbidden_actions") or [])
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_provider_fallback_verification_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    rows = [
        [
            str(row.get("rank", "")),
            str(row.get("match", "")),
            str(row.get("commence_time", "")),
            str(row.get("priority_tier", "")),
            str(row.get("rank_reason", "")),
        ]
        for row in (payload.get("manual_verification_queue") or [])[:18]
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Fallback Verification Queue",
        subtitle="Candidate-level Team Total manual verification queue. Research only, no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Queue", str(payload.get("queue_count", 0))),
            ("High Priority", str(payload.get("top_priority_count", 0))),
            ("Provider Blocker", str(payload.get("provider_blocker_code") or "none")),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Queue Priority",
                priority_chart_items(payload.get("manual_verification_queue") or []),
                "#C62828",
            )
        ],
        table_headers=["Rank", "Match", "Time", "Tier", "Reason"],
        table_rows=rows,
    )


def priority_chart_items(rows: list[Mapping[str, Any]]) -> list[tuple[str, float]]:
    counts = {"high": 0, "medium": 0, "watch": 0}
    for row in rows:
        tier = str(row.get("priority_tier") or "watch")
        counts[tier if tier in counts else "watch"] += 1
    return [(label, value) for label, value in counts.items()]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
