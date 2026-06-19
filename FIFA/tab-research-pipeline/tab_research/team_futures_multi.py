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
from .world_cup_2026 import GROUP_CODE_TO_TEAM


MARKETS = [
    "Win World Cup",
    "Reach Final",
    "Reach Semi Final",
    "Reach Quarter Final",
]
MARKET_SLOTS = {
    "Win World Cup": 1,
    "Reach Final": 2,
    "Reach Semi Final": 4,
    "Reach Quarter Final": 8,
}
EXPECTED_TEAM_COUNT = 14
EXPECTED_CODES = [
    "ARG",
    "AUS",
    "BEL",
    "BRA",
    "CRO",
    "ENG",
    "ESP",
    "FRA",
    "GER",
    "JPN",
    "NED",
    "NOR",
    "POR",
    "USA",
]
EXPECTED_CODE_SET = set(EXPECTED_CODES)


def load_team_multi_raw(path: Path) -> Dict:
    return json.loads(path.read_text())


def parse_team_futures_multi(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rows = []
    i = 0
    while i < len(lines):
        header = re.match(r"^2026 SWC Futures Multi ([A-Z]{3})$", lines[i])
        if not header:
            i += 1
            continue
        code = header.group(1)
        i += 1
        if i < len(lines) and lines[i] == "1 Market":
            i += 1
        if i < len(lines) and lines[i].startswith(f"2026 SWC Futures Multi {code}"):
            i += 1
        markets = {}
        for market in MARKETS:
            if i + 1 >= len(lines):
                break
            expected_label = f"{code} {market}"
            if lines[i] != expected_label or not is_price(lines[i + 1]):
                break
            markets[market] = parse_decimal_odds(lines[i + 1])
            i += 2
        if len(markets) == len(MARKETS):
            rows.append({"code": code, "team": code_to_team(code), "markets": markets})
    return rows


def is_price(value: str) -> bool:
    return parse_decimal_odds(value) is not None


def code_to_team(code: str) -> str:
    return GROUP_CODE_TO_TEAM.get(code, code)


def no_vig_market_probabilities(rows: List[Dict], market: str) -> Dict[str, float]:
    market_rows = [row for row in rows if market in row["markets"]]
    if not market_rows:
        return {}
    teams = [row["team"] for row in market_rows]
    probabilities = no_vig_from_decimal_odds([row["markets"][market] for row in market_rows], f"team futures multi/{market}")
    slots = MARKET_SLOTS[market]
    return {team: probability * slots for team, probability in zip(teams, probabilities)}


def generate_team_multi_report(raw_path: Path, output_dir: Path, version: str = "v0_16") -> Dict:
    raw = load_team_multi_raw(raw_path)
    rows = parse_team_futures_multi(raw.get("text", ""))
    probabilities = {market: no_vig_market_probabilities(rows, market) for market in MARKETS}
    gate = team_multi_gate(rows)
    recommendations = team_multi_candidates(rows, probabilities)
    result = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_raw": public_artifact_ref(raw_path),
        "board": raw.get("board"),
        "url": raw.get("url"),
        "team_count": len(rows),
        "markets": MARKETS,
        "market_slots": MARKET_SLOTS,
        "rows": rows,
        "probabilities": probabilities,
        "recommendations": recommendations,
        "automation_gate": gate,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / f"tab_fifa_world_cup_team_futures_multi_recommendations_{version}.json", result)
    atomic_write_json(output_dir / f"automation_gate_team_futures_multi_{version}.json", gate)
    atomic_write_text(output_dir / f"tab_fifa_world_cup_team_futures_multi_{version}_report.md", render_team_multi_markdown(result))
    return result


def team_multi_gate(rows: List[Dict]) -> Dict:
    complete_rows = sum(1 for row in rows if len(row["markets"]) == len(MARKETS))
    codes = [row["code"] for row in rows]
    duplicate_codes = sorted({code for code in codes if codes.count(code) > 1})
    code_set = set(codes)
    missing_codes = [code for code in EXPECTED_CODES if code not in code_set]
    unknown_codes = sorted(code for code in code_set if code not in EXPECTED_CODE_SET)
    invalid_odds = team_multi_integrity_errors(rows)
    ready = (
        len(rows) == EXPECTED_TEAM_COUNT
        and complete_rows == EXPECTED_TEAM_COUNT
        and not duplicate_codes
        and not missing_codes
        and not unknown_codes
        and not invalid_odds
    )
    return {
        "automation_ready": ready,
        "manual_report_ready": len(rows) >= 10 and complete_rows >= 10,
        "coverage": {
            "teams": {"covered": len(rows), "total": EXPECTED_TEAM_COUNT, "rate": round(len(rows) / EXPECTED_TEAM_COUNT, 3)},
            "complete_team_markets": {"covered": complete_rows, "total": EXPECTED_TEAM_COUNT},
            "expected_codes": {"covered": EXPECTED_TEAM_COUNT - len(missing_codes), "total": EXPECTED_TEAM_COUNT},
            "market_integrity": {"failed_rows": len(invalid_odds), "total": EXPECTED_TEAM_COUNT},
        },
        "blocking_reasons": [] if ready else team_multi_blocking_reasons(
            rows, complete_rows, duplicate_codes, missing_codes, unknown_codes, invalid_odds
        ),
    }


def team_multi_integrity_errors(rows: List[Dict]) -> List[str]:
    errors = []
    for row in rows:
        invalid = [
            market
            for market in MARKETS
            if market not in row.get("markets", {}) or not valid_decimal_odds(row["markets"].get(market))
        ]
        if invalid:
            errors.append(f"{row.get('code', '?')} invalid odds in {', '.join(invalid)}")
    return errors


def team_multi_blocking_reasons(
    rows: List[Dict],
    complete_rows: int,
    duplicate_codes: List[str],
    missing_codes: List[str],
    unknown_codes: List[str],
    invalid_odds: List[str],
) -> List[str]:
    reasons = []
    if len(rows) != EXPECTED_TEAM_COUNT:
        reasons.append(f"Expected {EXPECTED_TEAM_COUNT} team futures multi rows, parsed {len(rows)}.")
    if complete_rows != EXPECTED_TEAM_COUNT:
        reasons.append(f"Expected {EXPECTED_TEAM_COUNT} complete 4-market rows, parsed {complete_rows}.")
    if duplicate_codes:
        reasons.append(f"Duplicate team futures multi codes parsed: {', '.join(duplicate_codes)}.")
    if missing_codes:
        reasons.append(f"Missing team futures multi codes: {', '.join(missing_codes)}.")
    if unknown_codes:
        reasons.append(f"Unknown team futures multi codes parsed: {', '.join(unknown_codes)}.")
    if invalid_odds:
        reasons.append(f"Invalid decimal odds in team futures multi table: {'; '.join(invalid_odds[:8])}.")
    return reasons


def team_multi_candidates(rows: List[Dict], probabilities: Dict[str, Dict[str, float]]) -> List[Dict]:
    watch = {
        "Japan": "Best fit is path-depth rather than outright; quarter-final/semi-final prices remain the usable watch markets.",
        "Croatia": "Long tournament profile with knockout experience, but age/squad risk keeps this as watch only.",
        "Belgium": "Quarter-final route is more plausible than outright; compare against 48-team futures board before staking.",
        "USA": "Host factor creates upside, but Group D strength and knockout path require simulation before exposure.",
        "Australia": "Prices are long across all outcomes; only useful if match-level model upgrades Group D materially.",
    }
    rows_by_team = {row["team"]: row for row in rows}
    candidates = []
    for team, rationale in watch.items():
        row = rows_by_team.get(team)
        if not row:
            continue
        market = best_watch_market(team, probabilities)
        if market not in row["markets"] or team not in probabilities.get(market, {}):
            continue
        candidates.append(
            {
                "team": team,
                "market": market,
                "odds": row["markets"][market],
                "no_vig_probability": probabilities[market][team],
                "stake_aud": 0,
                "stake_unit": 0,
                "decision": "watch_or_no_bet",
                "rationale": rationale,
                "risk": "Team Futures Multi combines long-duration bankroll lockup with path variance; wait for portfolio-level edge confirmation.",
            }
        )
    return sorted(candidates, key=lambda item: item["no_vig_probability"], reverse=True)


def best_watch_market(team: str, probabilities: Dict[str, Dict[str, float]]) -> str:
    preferred = ["Reach Quarter Final", "Reach Semi Final", "Reach Final", "Win World Cup"]
    return max(preferred, key=lambda market: probabilities[market].get(team, 0))


def render_team_multi_markdown(result: Dict) -> str:
    gate = result["automation_gate"]
    lines = [
        f"# TAB FIFA World Cup Team Futures Multi Report {result['version']}",
        "",
        "本报告由 TAB Team Futures Multi 页面只读抓取生成；不自动下注、不操作下注单。",
        "",
        "## Automation Gate",
        "",
        f"- automation_ready: `{gate['automation_ready']}`",
        f"- manual_report_ready: `{gate['manual_report_ready']}`",
        f"- team_coverage: `{gate['coverage']['teams']['covered']}/{gate['coverage']['teams']['total']}`",
        f"- complete_team_markets: `{gate['coverage']['complete_team_markets']['covered']}/{gate['coverage']['complete_team_markets']['total']}`",
        "",
        "## Visual Summary",
        "",
        "### Team Futures Multi 操作分布",
        "",
        mermaid_pie("Team Futures Multi 操作分布", decision_distribution(result["recommendations"])),
        "",
        "### Reach QF 子集概率 Top",
        "",
        mermaid_bar(
            "Team Multi Reach QF No-Vig Top",
            top_items(
                [
                    {"team": team, "qf_probability_pct": probability * 100}
                    for team, probability in result["probabilities"]["Reach Quarter Final"].items()
                ],
                "team",
                "qf_probability_pct",
            ),
            "Subset No-Vig %",
        ),
        "",
        "## Team Futures Multi Table",
        "",
        "注意：本板块只覆盖 TAB Team Futures Multi 页面列出的 14 支球队，概率是该子集内按席位归一化的 no-vig 概率，不等同于 48 队全市场真实概率。",
        "",
        "| Team | Win WC | Final | Semi | Quarter | Win Subset No-Vig P | QF Subset No-Vig P |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        team = row["team"]
        markets = row["markets"]
        lines.append(
            "| {team} | {win:.2f} | {final:.2f} | {semi:.2f} | {qf:.2f} | {wp:.1%} | {qp:.1%} |".format(
                team=team,
                win=markets["Win World Cup"],
                final=markets["Reach Final"],
                semi=markets["Reach Semi Final"],
                qf=markets["Reach Quarter Final"],
                wp=result["probabilities"]["Win World Cup"][team],
                qp=result["probabilities"]["Reach Quarter Final"][team],
            )
        )
    lines.extend(
        [
            "",
            "## Research Candidates",
            "",
            "| Team | Market | Odds | Subset No-Vig P | Action | Stake | Reason |",
            "|---|---|---:|---:|---|---:|---|",
        ]
    )
    for item in result["recommendations"]:
        lines.append(
            "| {team} | {market} | {odds:.2f} | {prob:.1%} | {decision} | AUD {stake:.2f} / {unit:.2f}u | {reason} |".format(
                team=item["team"],
                market=item["market"],
                odds=item["odds"],
                prob=item["no_vig_probability"],
                decision=item["decision"],
                stake=item["stake_aud"],
                unit=item["stake_unit"],
                reason=item["rationale"],
            )
        )
    lines.extend(["", "## Blocking Reasons", ""])
    if gate["blocking_reasons"]:
        lines.extend(f"- {reason}" for reason in gate["blocking_reasons"])
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
