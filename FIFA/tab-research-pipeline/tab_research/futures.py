from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .artifacts import public_artifact_ref
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import decision_distribution, mermaid_bar, mermaid_pie, top_items
from .odds import no_vig_from_decimal_odds, parse_decimal_odds, valid_decimal_odds
from .world_cup_2026 import EXPECTED_TEAMS, EXPECTED_TEAM_SET, normalize_world_cup_team_name


CORE_MARKETS = [
    "Winner",
    "To Qualify for Final",
    "To Qualify For Semi Final",
    "To Qualify for Quarter Final",
]
MARKET_SLOTS = {
    "Winner": 1,
    "To Qualify for Final": 2,
    "To Qualify For Semi Final": 4,
    "To Qualify for Quarter Final": 8,
}
CURRENT_DETAIL_MARKETS = [
    "Winner",
    "Stage of Elimination",
    "Team Tournament Goals O/U",
    "Player Tournament Goals OU",
]
STAGE_OUTCOMES = [
    "Group Stage",
    "Round of 32",
    "Last 16",
    "Quarter Finals",
    "Semi Finals",
    "Runner Up",
    "Winner",
]
MIN_STAGE_TEAM_COUNT = 30
MIN_TEAM_GOALS_COUNT = 30
MIN_PLAYER_GOALS_COUNT = 10

KNOWN_NEXT_MARKET = "Top Goal Scorer"


def load_futures_raw(path: Path) -> Dict:
    return json.loads(path.read_text())


def parse_core_futures(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines()]
    compact_lines = [line for line in lines if line]
    legacy_rows = parse_legacy_core_futures(compact_lines)
    if legacy_rows:
        return legacy_rows
    winner_rows = parse_collapsed_winner_futures(compact_lines)
    if winner_rows:
        return winner_rows
    raise ValueError("Could not find futures core table header")


def parse_legacy_core_futures(lines: List[str]) -> List[Dict]:
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("Winner") and "Quarter" in line)
        end = lines.index(KNOWN_NEXT_MARKET, start + 1)
    except StopIteration as exc:
        return []
    except ValueError as exc:
        raise ValueError("Could not find end of futures core table") from exc

    tokens = [line for line in lines[start + 1 : end] if line]
    rows = []
    i = 0
    while i < len(tokens):
        team = tokens[i]
        values = tokens[i + 1 : i + 5]
        if len(values) < 4:
            break
        if all(is_price(value) for value in values):
            rows.append(
                {
                    "team": normalize_team(team),
                    "markets": {
                        market: parse_decimal_odds(value) for market, value in zip(CORE_MARKETS, values)
                    },
                }
            )
            i += 5
        else:
            i += 1
    return rows


def parse_collapsed_winner_futures(lines: List[str]) -> List[Dict]:
    start = next((i for i, line in enumerate(lines) if "2026 World Cup Winner" in line), -1)
    if start < 0:
        return []
    end_markers = {
        "Show All Selections",
        "Top Goal Scorer",
        "Reach Round of 16",
        "Stage of Elimination",
        "Team Tournament Goals O/U",
        "Player Tournament Goals OU",
        "Language:",
    }
    end = next((i for i in range(start + 1, len(lines)) if lines[i] in end_markers), len(lines))
    tokens = lines[start + 1 : end]
    rows = []
    i = 0
    while i < len(tokens) - 1:
        team = tokens[i]
        price = tokens[i + 1]
        if not is_price(team) and is_price(price):
            rows.append({"team": normalize_team(team), "markets": {"Winner": parse_decimal_odds(price)}})
            i += 2
        else:
            i += 1
    return rows


def parse_stage_of_elimination(text: str) -> List[Dict]:
    rows_by_team: Dict[str, Dict[str, float]] = {}
    tokens = section_tokens(text, "Stage of Elimination", {"Team Tournament Goals O/U", "Player Tournament Goals OU", "Language:"})
    i = 0
    while i < len(tokens) - 1:
        selection = tokens[i]
        price = tokens[i + 1]
        odds = parse_decimal_odds(price)
        if odds is not None:
            parsed = parse_stage_selection(selection)
            if parsed:
                team, outcome = parsed
                rows_by_team.setdefault(team, {})[outcome] = odds
            i += 2
        else:
            i += 1
    return [
        {"team": team, "outcomes": outcomes}
        for team, outcomes in sorted(rows_by_team.items(), key=lambda item: EXPECTED_TEAMS.index(item[0]) if item[0] in EXPECTED_TEAM_SET else 999)
    ]


def parse_team_tournament_goals(text: str) -> List[Dict]:
    return parse_goals_ou_section(
        text,
        "Team Tournament Goals O/U",
        {"Player Tournament Goals OU", "Language:"},
        entity_key="team",
        normalize_entity=normalize_team,
    )


def parse_player_tournament_goals(text: str) -> List[Dict]:
    return parse_goals_ou_section(
        text,
        "Player Tournament Goals OU",
        {"Bet Slip", "Pending Bets", "Language:"},
        entity_key="player",
        normalize_entity=lambda value: value.strip(),
    )


def parse_goals_ou_section(text: str, start_marker: str, end_markers: set[str], entity_key: str, normalize_entity) -> List[Dict]:
    rows_by_entity: Dict[str, Dict] = {}
    tokens = section_tokens(text, start_marker, end_markers)
    pattern = re.compile(r"^(.+?)\s+(Over|Under)\s+(\d+(?:\.\d+)?)\s+Goals$", re.IGNORECASE)
    i = 0
    while i < len(tokens) - 1:
        selection = tokens[i]
        price = tokens[i + 1]
        odds = parse_decimal_odds(price)
        match = pattern.match(selection)
        if match and odds is not None:
            entity = normalize_entity(match.group(1))
            side = match.group(2).title()
            line = float(match.group(3))
            row = rows_by_entity.setdefault(entity, {entity_key: entity, "line": line})
            row[side.lower()] = odds
            row["line"] = line
            i += 2
        else:
            i += 1
    return [
        row for row in rows_by_entity.values()
        if valid_decimal_odds(row.get("over")) and valid_decimal_odds(row.get("under"))
    ]


def section_tokens(text: str, start_marker: str, end_markers: set[str]) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    try:
        start = lines.index(start_marker)
    except ValueError:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i] in end_markers), len(lines))
    return lines[start + 1:end]


def parse_stage_selection(selection: str) -> tuple[str, str] | None:
    for outcome in STAGE_OUTCOMES:
        if selection.endswith(outcome):
            team = normalize_team(selection[: -len(outcome)].strip())
            return team, outcome
    return None


def normalize_team(team: str) -> str:
    return normalize_world_cup_team_name(team)


def is_price(value: str) -> bool:
    return parse_decimal_odds(value) is not None


def no_vig_market_probabilities(rows: List[Dict], market: str) -> Dict[str, float]:
    teams = [row["team"] for row in rows]
    probabilities = no_vig_from_decimal_odds([row["markets"][market] for row in rows], f"futures/{market}")
    slots = MARKET_SLOTS[market]
    return {team: probability * slots for team, probability in zip(teams, probabilities)}


def generate_futures_report(raw_path: Path, output_dir: Path, version: str = "v0_13") -> Dict:
    raw = load_futures_raw(raw_path)
    rows = parse_core_futures(raw.get("text", ""))
    current_markets = parse_current_detail_markets(raw.get("text", ""))
    probabilities = {
        market: no_vig_market_probabilities(market_rows(rows, market), market)
        if market_rows(rows, market)
        else {}
        for market in CORE_MARKETS
    }
    gate = futures_gate(rows, raw)
    recommendations = futures_candidates(rows, probabilities)
    result = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_raw": public_artifact_ref(raw_path),
        "board": raw.get("board"),
        "url": raw.get("url"),
        "core_markets": CORE_MARKETS,
        "market_slots": MARKET_SLOTS,
        "team_count": len(rows),
        "rows": rows,
        "current_markets": current_markets,
        "probabilities": probabilities,
        "recommendations": recommendations,
        "automation_gate": gate,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / f"tab_fifa_world_cup_futures_recommendations_{version}.json", result)
    atomic_write_json(output_dir / f"automation_gate_futures_{version}.json", gate)
    atomic_write_text(output_dir / f"tab_fifa_world_cup_futures_{version}_report.md", render_futures_markdown(result))
    return result


def futures_gate(rows: List[Dict], raw: Dict) -> Dict:
    expected_teams = len(EXPECTED_TEAMS)
    market_count = len(CORE_MARKETS)
    teams = [row["team"] for row in rows]
    duplicate_teams = sorted({team for team in teams if teams.count(team) > 1})
    team_set = set(teams)
    missing_teams = [team for team in EXPECTED_TEAMS if team not in team_set]
    unknown_teams = sorted(team for team in team_set if team not in EXPECTED_TEAM_SET)
    complete_rows = sum(1 for row in rows if len(row["markets"]) == market_count)
    invalid_odds = futures_invalid_odds(rows)
    covered_core_markets = len({market for row in rows for market in row.get("markets", {}) if market in CORE_MARKETS})
    current_markets = parse_current_detail_markets(raw.get("text", "")) if isinstance(raw, dict) else empty_current_detail_markets()
    current_gate = current_detail_market_gate(rows, current_markets, duplicate_teams, missing_teams, unknown_teams, invalid_odds)
    legacy_ready = (
        len(rows) == expected_teams
        and complete_rows == expected_teams
        and not duplicate_teams
        and not missing_teams
        and not unknown_teams
        and not invalid_odds
    )
    ready = legacy_ready or current_gate["ready"]
    return {
        "automation_ready": ready,
        "manual_report_ready": len(rows) >= 40 or current_gate["manual_ready"],
        "coverage": {
            "teams": {"covered": len(rows), "total": expected_teams, "rate": round(len(rows) / expected_teams, 3)},
            "complete_team_markets": {"covered": complete_rows, "total": expected_teams},
            "core_markets": {"covered": covered_core_markets, "total": market_count},
            "current_detail_markets": current_gate["coverage"],
            "expected_team_names": {"covered": expected_teams - len(missing_teams), "total": expected_teams},
            "market_integrity": {"failed_rows": len(invalid_odds), "total": expected_teams},
        },
        "availability_notes": current_gate["availability_notes"],
        "blocking_reasons": [] if ready else futures_blocking_reasons(
            rows, complete_rows, duplicate_teams, missing_teams, unknown_teams, invalid_odds, current_gate
        ),
    }


def parse_current_detail_markets(text: str) -> Dict:
    return {
        "stage_of_elimination": parse_stage_of_elimination(text),
        "team_tournament_goals_ou": parse_team_tournament_goals(text),
        "player_tournament_goals_ou": parse_player_tournament_goals(text),
    }


def empty_current_detail_markets() -> Dict:
    return {
        "stage_of_elimination": [],
        "team_tournament_goals_ou": [],
        "player_tournament_goals_ou": [],
    }


def current_detail_market_gate(
    rows: List[Dict],
    current_markets: Dict,
    duplicate_teams: List[str],
    missing_teams: List[str],
    unknown_teams: List[str],
    invalid_odds: List[str],
) -> Dict:
    stage_rows = current_markets.get("stage_of_elimination", [])
    team_goals = current_markets.get("team_tournament_goals_ou", [])
    player_goals = current_markets.get("player_tournament_goals_ou", [])
    stage_complete = sum(1 for row in stage_rows if len(row.get("outcomes", {})) == len(STAGE_OUTCOMES))
    team_goals_complete = len(team_goals)
    player_goals_complete = len(player_goals)
    winner_complete = len(rows) == len(EXPECTED_TEAMS) and not missing_teams and not unknown_teams
    ready = (
        winner_complete
        and stage_complete >= MIN_STAGE_TEAM_COUNT
        and team_goals_complete >= MIN_TEAM_GOALS_COUNT
        and player_goals_complete >= MIN_PLAYER_GOALS_COUNT
        and not duplicate_teams
        and not invalid_odds
    )
    coverage = {
        "winner": {"covered": len(rows), "total": len(EXPECTED_TEAMS), "rate": round(len(rows) / len(EXPECTED_TEAMS), 3)},
        "stage_of_elimination": {"covered": stage_complete, "minimum": MIN_STAGE_TEAM_COUNT, "listed": len(stage_rows)},
        "team_tournament_goals_ou": {"covered": team_goals_complete, "minimum": MIN_TEAM_GOALS_COUNT},
        "player_tournament_goals_ou": {"covered": player_goals_complete, "minimum": MIN_PLAYER_GOALS_COUNT},
        "parsed_market_names": [
            market for market, covered in [
                ("Winner", bool(rows)),
                ("Stage of Elimination", bool(stage_rows)),
                ("Team Tournament Goals O/U", bool(team_goals)),
                ("Player Tournament Goals OU", bool(player_goals)),
            ] if covered
        ],
    }
    stage_teams = {row.get("team") for row in stage_rows}
    missing_stage_teams = [team for team in EXPECTED_TEAMS if team not in stage_teams]
    availability_notes = []
    if missing_stage_teams:
        availability_notes.append(
            "Stage of Elimination is not currently listed for: " + ", ".join(missing_stage_teams) + "."
        )
    return {
        "ready": ready,
        "manual_ready": winner_complete and stage_complete >= MIN_STAGE_TEAM_COUNT,
        "coverage": coverage,
        "availability_notes": availability_notes,
    }


def futures_invalid_odds(rows: List[Dict]) -> List[str]:
    errors = []
    for row in rows:
        invalid = [
            market
            for market in CORE_MARKETS
            if market in row.get("markets", {}) and not valid_decimal_odds(row["markets"].get(market))
        ]
        if invalid:
            errors.append(f"{row.get('team', 'Unknown Team')} invalid odds in {', '.join(invalid)}")
    return errors


def futures_blocking_reasons(
    rows: List[Dict],
    complete_rows: int,
    duplicate_teams: List[str],
    missing_teams: List[str],
    unknown_teams: List[str],
    invalid_odds: List[str],
    current_gate: Dict | None = None,
) -> List[str]:
    reasons = []
    expected_teams = len(EXPECTED_TEAMS)
    current_coverage = (current_gate or {}).get("coverage", {})
    parsed_current = set(current_coverage.get("parsed_market_names", []))
    current_detail_detected = bool(parsed_current - {"Winner"})
    if len(rows) != expected_teams:
        reasons.append(f"Expected {expected_teams} teams in futures core table, parsed {len(rows)}.")
    if complete_rows != expected_teams and not current_detail_detected:
        reasons.append(f"Expected {expected_teams} complete futures rows, parsed {complete_rows}.")
    if current_detail_detected:
        stage = current_coverage.get("stage_of_elimination", {})
        team_goals = current_coverage.get("team_tournament_goals_ou", {})
        player_goals = current_coverage.get("player_tournament_goals_ou", {})
        if stage.get("covered", 0) < stage.get("minimum", MIN_STAGE_TEAM_COUNT):
            reasons.append(
                f"Stage of Elimination coverage below current-market threshold: {stage.get('covered', 0)}/{stage.get('minimum', MIN_STAGE_TEAM_COUNT)}."
            )
        if team_goals.get("covered", 0) < team_goals.get("minimum", MIN_TEAM_GOALS_COUNT):
            reasons.append(
                f"Team Tournament Goals O/U coverage below current-market threshold: {team_goals.get('covered', 0)}/{team_goals.get('minimum', MIN_TEAM_GOALS_COUNT)}."
            )
        if player_goals.get("covered", 0) < player_goals.get("minimum", MIN_PLAYER_GOALS_COUNT):
            reasons.append(
                f"Player Tournament Goals OU coverage below current-market threshold: {player_goals.get('covered', 0)}/{player_goals.get('minimum', MIN_PLAYER_GOALS_COUNT)}."
            )
    if duplicate_teams:
        reasons.append(f"Duplicate futures teams parsed: {', '.join(duplicate_teams)}.")
    if missing_teams:
        reasons.append(f"Missing futures teams: {', '.join(missing_teams)}.")
    if unknown_teams:
        reasons.append(f"Unknown futures teams parsed: {', '.join(unknown_teams)}.")
    if invalid_odds:
        reasons.append(f"Invalid decimal odds in futures core table: {'; '.join(invalid_odds[:8])}.")
    return reasons


def futures_candidates(rows: List[Dict], probabilities: Dict[str, Dict[str, float]]) -> List[Dict]:
    watch_teams = {
        "Japan": "Model already likes Japan in match market; futures price is worth monitoring, not automatic staking.",
        "Morocco": "Strong underdog profile; outright price is long but quarter-final path price may be more usable.",
        "Croatia": "Tournament profile is stronger than outright price implies, but age/squad risk must be checked.",
        "Senegal": "Long-shot quality profile; requires squad/news validation before staking.",
        "Belgium": "Better suited to quarter/semi qualification than outright winner.",
        "Colombia": "Potentially live in qualification-stage futures if draw path supports it.",
    }
    candidates = []
    rows_by_team = {row["team"]: row for row in rows}
    for team, rationale in watch_teams.items():
        row = rows_by_team.get(team)
        if not row:
            continue
        best_market = best_relative_market(team, row, probabilities)
        if best_market not in row.get("markets", {}) or team not in probabilities.get(best_market, {}):
            continue
        candidates.append(
            {
                "team": team,
                "market": best_market,
                "odds": row["markets"][best_market],
                "no_vig_probability": probabilities[best_market][team],
                "stake_aud": 0,
                "stake_unit": 0,
                "decision": "watch_or_no_bet",
                "rationale": rationale,
                "risk": "Futures exposure ties up bankroll and has path/draw variance; wait for full multi-source validation.",
            }
        )
    return sorted(candidates, key=lambda item: item["no_vig_probability"], reverse=True)


def best_relative_market(team: str, row: Dict, probabilities: Dict[str, Dict[str, float]]) -> str:
    preferred = ["To Qualify for Quarter Final", "To Qualify For Semi Final", "To Qualify for Final", "Winner"]
    return max(preferred, key=lambda market: probabilities[market].get(team, 0))


def market_rows(rows: List[Dict], market: str) -> List[Dict]:
    return [
        row
        for row in rows
        if market in row.get("markets", {}) and valid_decimal_odds(row.get("markets", {}).get(market))
    ]


def render_futures_markdown(result: Dict) -> str:
    gate = result["automation_gate"]
    coverage = gate.get("coverage", {})
    team_coverage = coverage.get("teams", {"covered": len(result.get("rows", [])), "total": len(EXPECTED_TEAMS)})
    current_detail = coverage.get("current_detail_markets") or {
        "parsed_market_names": [],
        "stage_of_elimination": {"covered": 0, "minimum": MIN_STAGE_TEAM_COUNT},
        "team_tournament_goals_ou": {"covered": 0, "minimum": MIN_TEAM_GOALS_COUNT},
        "player_tournament_goals_ou": {"covered": 0, "minimum": MIN_PLAYER_GOALS_COUNT},
    }
    lines = [
        f"# TAB FIFA World Cup Futures Report {result['version']}",
        "",
        "本报告由 TAB Futures 页面只读抓取生成；不自动下注、不操作下注单。",
        "",
        "## Automation Gate",
        "",
        f"- automation_ready: `{gate['automation_ready']}`",
        f"- manual_report_ready: `{gate['manual_report_ready']}`",
        f"- team_coverage: `{team_coverage['covered']}/{team_coverage['total']}`",
        f"- current_detail_markets: `{', '.join(current_detail.get('parsed_market_names', [])) or 'none'}`",
        f"- stage_of_elimination_coverage: `{current_detail['stage_of_elimination']['covered']}/{current_detail['stage_of_elimination']['minimum']}`",
        f"- team_goals_ou_coverage: `{current_detail['team_tournament_goals_ou']['covered']}/{current_detail['team_tournament_goals_ou']['minimum']}`",
        f"- player_goals_ou_coverage: `{current_detail['player_tournament_goals_ou']['covered']}/{current_detail['player_tournament_goals_ou']['minimum']}`",
        "",
        "## Visual Summary",
        "",
        "### Futures 操作分布",
        "",
        mermaid_pie("Futures 操作分布", decision_distribution(result["recommendations"])),
        "",
        "### Winner 概率 Top",
        "",
        mermaid_bar(
            "Futures Winner No-Vig Top",
            top_items(
                [
                    {"team": team, "winner_probability_pct": probability * 100}
                    for team, probability in result["probabilities"]["Winner"].items()
                ],
                "team",
                "winner_probability_pct",
            ),
            "No-Vig %",
        ),
        "",
        "## Core Futures Table",
        "",
        "| Team | Winner | Final | Semi Final | Quarter Final | Winner No-Vig P | QF No-Vig P |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        team = row["team"]
        markets = row["markets"]
        lines.append(
            "| {team} | {winner} | {final} | {semi} | {qf} | {wp} | {qp} |".format(
                team=team,
                winner=format_optional_odds(markets.get("Winner")),
                final=format_optional_odds(markets.get("To Qualify for Final")),
                semi=format_optional_odds(markets.get("To Qualify For Semi Final")),
                qf=format_optional_odds(markets.get("To Qualify for Quarter Final")),
                wp=format_optional_pct(result["probabilities"].get("Winner", {}).get(team)),
                qp=format_optional_pct(result["probabilities"].get("To Qualify for Quarter Final", {}).get(team)),
            )
        )
    current = result.get("current_markets", {})
    lines.extend(
        [
            "",
            "## Current TAB Futures Detail Markets",
            "",
            "| Market | Parsed Rows | Minimum | Status |",
            "|---|---:|---:|---|",
            current_market_row("Stage of Elimination", len(current.get("stage_of_elimination", [])), MIN_STAGE_TEAM_COUNT),
            current_market_row("Team Tournament Goals O/U", len(current.get("team_tournament_goals_ou", [])), MIN_TEAM_GOALS_COUNT),
            current_market_row("Player Tournament Goals OU", len(current.get("player_tournament_goals_ou", [])), MIN_PLAYER_GOALS_COUNT),
            "",
            "### Stage of Elimination Sample",
            "",
            "| Team | Group Stage | Round of 32 | Last 16 | Quarter | Semi | Runner Up | Winner |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in current.get("stage_of_elimination", [])[:12]:
        outcomes = row.get("outcomes", {})
        lines.append(
            "| {team} | {group_stage} | {round32} | {last16} | {quarter} | {semi} | {runner_up} | {winner} |".format(
                team=row.get("team"),
                group_stage=format_optional_odds(outcomes.get("Group Stage")),
                round32=format_optional_odds(outcomes.get("Round of 32")),
                last16=format_optional_odds(outcomes.get("Last 16")),
                quarter=format_optional_odds(outcomes.get("Quarter Finals")),
                semi=format_optional_odds(outcomes.get("Semi Finals")),
                runner_up=format_optional_odds(outcomes.get("Runner Up")),
                winner=format_optional_odds(outcomes.get("Winner")),
            )
        )
    lines.extend(
        [
            "",
            "## Research Candidates",
            "",
            "| Team | Market | Odds | No-Vig P | Action | Stake | Reason |",
            "|---|---|---:|---:|---|---:|---|",
        ]
    )
    for item in result["recommendations"]:
        lines.append(
            "| {team} | {market} | {odds:.2f} | {prob:.1%} | {decision} | AUD {stake:.2f} | {reason} |".format(
                team=item["team"],
                market=item["market"],
                odds=item["odds"],
                prob=item["no_vig_probability"],
                decision=item["decision"],
                stake=item["stake_aud"],
                reason=item["rationale"],
            )
        )
    lines.extend(["", "## Blocking Reasons", ""])
    if gate["blocking_reasons"]:
        lines.extend(f"- {reason}" for reason in gate["blocking_reasons"])
    else:
        lines.append("- none")
    lines.extend(["", "## Availability Notes", ""])
    if gate.get("availability_notes"):
        lines.extend(f"- {note}" for note in gate["availability_notes"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Disclaimer",
            "",
            "本报告是下注前研究与资金管理参考，不构成财务建议、投注建议或保证收益判断。",
        ]
    )
    return "\n".join(lines)


def format_optional_odds(value: object) -> str:
    return f"{float(value):.2f}" if valid_decimal_odds(value) else "n/a"


def current_market_row(label: str, covered: int, minimum: int) -> str:
    status = "ready" if covered >= minimum else "blocked"
    return f"| {label} | {covered} | {minimum} | {status} |"


def format_optional_pct(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{number:.1%}"
