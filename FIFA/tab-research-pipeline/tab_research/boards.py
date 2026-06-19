from __future__ import annotations

import json
from json import JSONDecodeError
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .markdown_visuals import mermaid_bar, mermaid_pie


@dataclass(frozen=True)
class BoardConfig:
    board_id: str
    refresh_board_id: str
    name: str
    tab_path: str
    priority: int
    version: str
    required_for_full_automation: bool
    parser_strategy: str
    refresh_method: str
    raw_snapshot: Optional[str]
    recommendations_artifact: Optional[str]
    gate_artifact: Optional[str]
    report_artifact: Optional[str]


BOARD_CONFIGS = [
    BoardConfig(
        board_id="world_cup_matches",
        refresh_board_id="matches",
        name="2026 World Cup Matches",
        tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches",
        priority=1,
        version="v0_11",
        required_for_full_automation=True,
        parser_strategy="match_detail_main_markets_merge",
        refresh_method="chrome_read_only_match_detail",
        raw_snapshot="tab_fifa_matches_main_markets_raw_v0_9.json",
        recommendations_artifact="tab_fifa_world_cup_matches_recommendations_v0_11.json",
        gate_artifact="automation_gate_v0_11.json",
        report_artifact="tab_fifa_world_cup_matches_v0_11_pipeline_report.md",
    ),
    BoardConfig(
        board_id="world_cup_futures",
        refresh_board_id="futures",
        name="2026 World Cup Futures",
        tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures",
        priority=2,
        version="v0_13",
        required_for_full_automation=True,
        parser_strategy="competition_page_text_parser",
        refresh_method="chrome_read_only_competition_page",
        raw_snapshot="tab_fifa_world_cup_futures_raw_v0_13.json",
        recommendations_artifact="tab_fifa_world_cup_futures_recommendations_v0_13.json",
        gate_artifact="automation_gate_futures_v0_13.json",
        report_artifact="tab_fifa_world_cup_futures_v0_13_report.md",
    ),
    BoardConfig(
        board_id="world_cup_group_betting",
        refresh_board_id="group_betting",
        name="2026 World Cup Group Betting",
        tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Group%20Betting",
        priority=3,
        version="v0_14",
        required_for_full_automation=True,
        parser_strategy="competition_page_text_parser",
        refresh_method="chrome_read_only_competition_page",
        raw_snapshot="tab_fifa_world_cup_group_betting_raw_v0_14.json",
        recommendations_artifact="tab_fifa_world_cup_group_betting_recommendations_v0_14.json",
        gate_artifact="automation_gate_group_betting_v0_14.json",
        report_artifact="tab_fifa_world_cup_group_betting_v0_14_report.md",
    ),
    BoardConfig(
        board_id="world_cup_australia_markets",
        refresh_board_id="australia_markets",
        name="2026 World Cup Australia Markets",
        tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Australia%20Markets",
        priority=4,
        version="v0_17",
        required_for_full_automation=True,
        parser_strategy="expanded_market_block_parser",
        refresh_method="chrome_read_only_header_expansion",
        raw_snapshot="tab_fifa_world_cup_australia_markets_expanded_raw_v0_17.json",
        recommendations_artifact="tab_fifa_world_cup_australia_markets_recommendations_v0_17.json",
        gate_artifact="automation_gate_australia_markets_v0_17.json",
        report_artifact="tab_fifa_world_cup_australia_markets_v0_17_report.md",
    ),
    BoardConfig(
        board_id="world_cup_team_futures_multi",
        refresh_board_id="team_futures_multi",
        name="2026 World Cup Team Futures Multi",
        tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Team%20Futures%20Multi",
        priority=5,
        version="v0_16",
        required_for_full_automation=True,
        parser_strategy="competition_page_text_parser",
        refresh_method="chrome_read_only_competition_page",
        raw_snapshot="tab_fifa_world_cup_team_futures_multi_raw_v0_16.json",
        recommendations_artifact="tab_fifa_world_cup_team_futures_multi_recommendations_v0_16.json",
        gate_artifact="automation_gate_team_futures_multi_v0_16.json",
        report_artifact="tab_fifa_world_cup_team_futures_multi_v0_16_report.md",
    ),
]
BOARD_BY_ID = {board.board_id: board for board in BOARD_CONFIGS}
BOARD_BY_REFRESH_ID = {board.refresh_board_id: board for board in BOARD_CONFIGS}


def board_registry() -> List[Dict]:
    return [asdict(board) for board in BOARD_CONFIGS]


def board_by_id(board_id: str) -> BoardConfig:
    return BOARD_BY_ID[board_id]


def board_by_refresh_id(refresh_board_id: str) -> BoardConfig:
    return BOARD_BY_REFRESH_ID[refresh_board_id]


def refresh_driver(board: BoardConfig) -> str:
    return f"scripts/refresh_tab_readonly.mjs --board {board.refresh_board_id}" if board.refresh_board_id else "not_configured"


def audit_portfolio(
    output_dir: Path,
    boards: List[BoardConfig] = BOARD_CONFIGS,
    max_raw_age_hours: float = 4.0,
    now: datetime | None = None,
) -> Dict:
    board_statuses = []
    now = now or datetime.now(timezone.utc)
    for board in boards:
        raw_path = output_dir / board.raw_snapshot if board.raw_snapshot else None
        gate_path = output_dir / board.gate_artifact if board.gate_artifact else None
        report_path = output_dir / board.report_artifact if board.report_artifact else None
        raw, raw_parse_error = read_json_with_error(raw_path)
        raw_validation = validate_current_raw(board, raw) if raw_parse_error is None else {"valid": False, "errors": [raw_parse_error]}
        gate, gate_parse_error = read_json_with_error(gate_path)
        automation_ready = bool(gate and gate.get("automation_ready"))
        raw_exists = bool(raw_path and raw_path.exists())
        gate_exists = bool(gate_path and gate_path.exists())
        raw_captured_at = raw_timestamp(raw) if raw else None
        raw_age_hours = raw_age(raw_captured_at, now)
        raw_fresh = raw_parse_error is None and raw_age_hours is not None and raw_age_hours <= max_raw_age_hours
        report_exists = bool(report_path and report_path.exists())
        raw_valid = bool(raw_validation.get("valid"))
        board_ready = raw_exists and raw_parse_error is None and raw_fresh and raw_valid and gate_parse_error is None and automation_ready and report_exists
        missing = []
        if not raw_exists:
            missing.append("raw_snapshot")
        if raw_exists and raw_parse_error:
            missing.append("raw_snapshot_parseable")
        elif raw_exists and not raw_fresh:
            missing.append("raw_snapshot_fresh")
        elif raw_exists and not raw_valid:
            missing.append("raw_snapshot_valid")
        if not gate_exists:
            missing.append("automation_gate")
        elif gate_parse_error:
            missing.append("automation_gate_parseable")
        elif not automation_ready:
            missing.append("automation_gate_ready")
        if not report_exists:
            missing.append("report_artifact")
        board_statuses.append(
            {
                "board_id": board.board_id,
                "name": board.name,
                "priority": board.priority,
                "required_for_full_automation": board.required_for_full_automation,
                "tab_path": board.tab_path,
                "ready": board_ready,
                "raw_snapshot": board.raw_snapshot,
                "raw_exists": raw_exists,
                "raw_fresh": raw_fresh,
                "raw_captured_at": raw_captured_at,
                "raw_age_hours": raw_age_hours,
                "raw_parse_error": raw_parse_error,
                "raw_valid": raw_valid,
                "raw_validation_errors": raw_validation.get("errors", []),
                "gate_artifact": board.gate_artifact,
                "gate_ready": automation_ready,
                "gate_parse_error": gate_parse_error,
                "report_artifact": board.report_artifact,
                "report_exists": report_exists,
                "missing": missing,
            }
        )
    required = [item for item in board_statuses if item["required_for_full_automation"]]
    ready_required = [item for item in required if item["ready"]]
    return {
        "generated_at": now.isoformat(),
        "max_raw_age_hours": max_raw_age_hours,
        "portfolio_automation_ready": len(ready_required) == len(required),
        "required_board_count": len(required),
        "ready_required_board_count": len(ready_required),
        "board_statuses": board_statuses,
        "blocking_reasons": portfolio_blocking_reasons(required),
    }


def portfolio_blocking_reasons(required_statuses: List[Dict]) -> List[str]:
    reasons = []
    for item in required_statuses:
        if not item["ready"]:
            reasons.append(f"{item['name']} is not ready: {', '.join(item['missing'])}.")
    return reasons


def render_portfolio_markdown(portfolio: Dict) -> str:
    lines = [
        "# TAB FIFA Portfolio Automation Readiness",
        "",
        "本报告检查多个 TAB FIFA 板块是否都达到每日自动生成研究报告的门槛；不自动下注、不操作下注单。",
        "",
        "## Summary",
        "",
        f"- portfolio_automation_ready: `{portfolio['portfolio_automation_ready']}`",
        f"- ready_required_boards: `{portfolio['ready_required_board_count']}/{portfolio['required_board_count']}`",
        f"- generated_at: `{portfolio['generated_at']}`",
        "",
        "## Visual Summary",
        "",
        "### Required Board Readiness",
        "",
        mermaid_pie(
            "Required Board Readiness",
            [
                ("ready", portfolio["ready_required_board_count"]),
                ("blocked", max(0, portfolio["required_board_count"] - portfolio["ready_required_board_count"])),
            ],
        ),
        "",
        "### Board Readiness Score",
        "",
        mermaid_bar(
            "Board Readiness Score",
            [
                (board["name"], readiness_score_for_markdown(board) * 100)
                for board in portfolio["board_statuses"]
            ],
            "Readiness %",
        ),
        "",
        "## Board Status",
        "",
        "| Priority | Board | Ready | Raw | Fresh | Gate | Report | Missing |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for board in portfolio["board_statuses"]:
        lines.append(
            "| {priority} | {name} | {ready} | {raw} | {fresh} | {gate} | {report} | {missing} |".format(
                priority=board["priority"],
                name=board["name"],
                ready=board["ready"],
                raw=board["raw_exists"],
                fresh=board["raw_fresh"],
                gate=board["gate_ready"],
                report=board["report_exists"],
                missing=", ".join(board["missing"]) or "none",
            )
        )
    lines.extend(["", "## Blocking Reasons", ""])
    if portfolio["blocking_reasons"]:
        for reason in portfolio["blocking_reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def readiness_score_for_markdown(board: Dict) -> float:
    checks = [board.get("raw_fresh"), board.get("raw_valid"), board.get("gate_ready"), board.get("report_exists")]
    return sum(1 for item in checks if item) / len(checks) if checks else 0.0


def validate_current_raw(board: BoardConfig, raw: Optional[Dict]) -> Dict:
    try:
        from .raw_refresh import validate_raw_snapshot
    except ImportError as exc:
        return {"valid": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    return validate_raw_snapshot(board.board_id, raw)


def read_json(path: Optional[Path]) -> Optional[Dict]:
    data, _error = read_json_with_error(path)
    return data


def read_json_with_error(path: Optional[Path]) -> tuple[Optional[Dict], Optional[str]]:
    if not path or not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text())
    except (OSError, JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return data, None


def raw_timestamp(raw: Dict) -> Optional[str]:
    return raw.get("captured_at") or raw.get("generated_at") or raw.get("created_at")


def raw_age(timestamp: Optional[str], now: datetime, max_future_skew_minutes: float = 5.0) -> Optional[float]:
    if not timestamp:
        return None
    normalized = timestamp.replace("Z", "+00:00")
    try:
        captured_at = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    age_hours = round((now - captured_at.astimezone(timezone.utc)).total_seconds() / 3600, 3)
    if age_hours < -(max_future_skew_minutes / 60):
        return None
    return age_hours
