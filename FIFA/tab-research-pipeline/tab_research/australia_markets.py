from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .artifacts import public_artifact_ref
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import decision_distribution, mermaid_bar, mermaid_pie, top_items
from .odds import no_vig_from_decimal_odds, parse_decimal_odds, require_decimal_odds, valid_decimal_odds


EXPECTED_MARKETS = [
    "AUS Group Match Wins",
    "Team To Win A Group Match",
    "Team To Win All 3 Group Matches",
    "Team Total Group Goals Scored O/U",
    "Team Total Group Goals Scored Exact",
    "AUS Score In Every Group Match",
    "Team Total Group Goals Conceded O/U",
    "AUS Concede In Every Group Match",
    "AUS Group Exact Finishing Position",
    "AUS Group Point O/U",
    "AUS Exact Group Points",
    "To Score a Goal in Tournament",
    "Team Total Goals Scored Bands",
    "Top Australian Goalscorer",
]

KNOWN_TAIL_MARKETS = set(EXPECTED_MARKETS[1:])
MARKET_ID_TO_NAME = {
    "team_group_match_wins": "AUS Group Match Wins",
    "team_to_win_a_group_match": "Team To Win A Group Match",
    "team_to_win_all_3_group_matches": "Team To Win All 3 Group Matches",
    "team_total_group_goals_scored_o_u": "Team Total Group Goals Scored O/U",
    "team_total_group_goals_scored_exact": "Team Total Group Goals Scored Exact",
    "aus_score_in_every_group_match": "AUS Score In Every Group Match",
    "team_total_group_goals_conceded_o_u": "Team Total Group Goals Conceded O/U",
    "aus_concede_in_every_group_match": "AUS Concede In Every Group Match",
    "aus_group_exact_finishing_position": "AUS Group Exact Finishing Position",
    "aus_group_point_o_u": "AUS Group Point O/U",
    "aus_exact_group_points": "AUS Exact Group Points",
    "to_score_a_goal_in_tournament": "To Score a Goal in Tournament",
    "team_total_goals_scored_bands": "Team Total Goals Scored Bands",
    "top_australian_goalscorer": "Top Australian Goalscorer",
}
MUTUALLY_EXCLUSIVE_MARKETS = {
    "AUS Group Match Wins",
    "Team Total Group Goals Scored Exact",
    "AUS Group Exact Finishing Position",
    "AUS Exact Group Points",
    "Team Total Goals Scored Bands",
}
SINGLE_SELECTION_MARKETS = {
    "Team To Win A Group Match",
    "Team To Win All 3 Group Matches",
    "AUS Score In Every Group Match",
    "AUS Concede In Every Group Match",
    "To Score a Goal in Tournament",
}


def load_australia_raw(path: Path) -> Dict:
    return json.loads(path.read_text())


def parse_australia_raw(raw: Dict) -> List[Dict]:
    if raw.get("markets"):
        return parse_expanded_market_blocks(raw["markets"])
    return parse_australia_markets(raw.get("text", ""))


def parse_expanded_market_blocks(blocks: List[Dict]) -> List[Dict]:
    markets = []
    for block in blocks:
        market_name = MARKET_ID_TO_NAME.get(block.get("id"), block.get("id", "Unknown Market"))
        text = block.get("afterText") or block.get("text") or ""
        rows = parse_price_rows(text)
        probabilities, method = market_probabilities(market_name, rows)
        for row in rows:
            row["probability"] = probabilities.get(row["selection"], 0)
        markets.append(
            {
                "id": block.get("id"),
                "market": market_name,
                "status": "priced" if rows else "expanded_without_prices",
                "probability_method": method,
                "rows": rows,
                "probabilities": probabilities,
            }
        )
    return sort_markets(markets)


def sort_markets(markets: List[Dict]) -> List[Dict]:
    order = {name: i for i, name in enumerate(EXPECTED_MARKETS)}
    return sorted(markets, key=lambda market: order.get(market["market"], 999))


def parse_australia_markets(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    markets = []
    group_wins = parse_group_match_wins(lines)
    if group_wins:
        markets.append(group_wins)
    visible_names = {market["market"] for market in markets}
    for name in EXPECTED_MARKETS:
        if name not in visible_names and any(line == name for line in lines):
            markets.append({"market": name, "status": "collapsed_without_prices", "rows": []})
    return markets


def parse_price_rows(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rows = []
    for index, line in enumerate(lines):
        if not is_price(line) or index == 0:
            continue
        selection = normalize_selection(lines[index - 1])
        if selection in {"14 Markets", "World Cup Australia Markets"} or is_price(selection):
            continue
        rows.append({"selection": selection, "odds": parse_decimal_odds(line)})
    return rows


def parse_group_match_wins(lines: List[str]) -> Dict:
    start = next((i for i, line in enumerate(lines) if line.startswith("AUS Group Match Wins")), None)
    if start is None:
        return {}
    rows = []
    i = start + 1
    while i + 1 < len(lines):
        if lines[i] in KNOWN_TAIL_MARKETS:
            break
        selection = normalize_selection(lines[i])
        price = lines[i + 1]
        if is_price(price):
            rows.append({"selection": selection, "odds": parse_decimal_odds(price)})
            i += 2
        else:
            i += 1
    probabilities = no_vig_probabilities(rows)
    return {
        "market": "AUS Group Match Wins",
        "status": "priced",
        "probability_method": "market_no_vig",
        "probabilities": probabilities,
        "rows": rows_with_probabilities(rows, probabilities),
    }


def normalize_selection(selection: str) -> str:
    return (
        selection.replace("GrpMatches", "Grp Matches")
        .replace("Grp Matchs", "Grp Matches")
        .replace("ConcedeUnder", "Concede Under ")
        .replace("Concede Over", "Concede Over ")
    )


def is_price(value: str) -> bool:
    return parse_decimal_odds(value) is not None


def no_vig_probabilities(rows: List[Dict]) -> Dict[str, float]:
    if not rows:
        return {}
    selections = [row["selection"] for row in rows]
    probabilities = no_vig_from_decimal_odds([row["odds"] for row in rows], "australia market")
    return dict(zip(selections, probabilities))


def rows_with_probabilities(rows: List[Dict], probabilities: Dict[str, float]) -> List[Dict]:
    for row in rows:
        row["probability"] = probabilities.get(row["selection"], 0)
    return rows


def market_probabilities(market_name: str, rows: List[Dict]) -> tuple[Dict[str, float], str]:
    if not rows:
        return {}, "none"
    if market_name in MUTUALLY_EXCLUSIVE_MARKETS:
        return no_vig_probabilities(rows), "market_no_vig"
    if "O/U" in market_name:
        return over_under_probabilities(rows), "threshold_pair_no_vig"
    if market_name == "Top Australian Goalscorer":
        return no_vig_probabilities(rows), "displayed_subset_no_vig"
    if market_name in SINGLE_SELECTION_MARKETS:
        return {row["selection"]: 1 / require_decimal_odds(row["odds"], f"{market_name}/{row['selection']}") for row in rows}, "single_selection_implied"
    return no_vig_probabilities(rows), "market_no_vig"


def over_under_probabilities(rows: List[Dict]) -> Dict[str, float]:
    by_threshold: Dict[str, List[Dict]] = {}
    for row in rows:
        key = threshold_key(row["selection"])
        by_threshold.setdefault(key, []).append(row)
    probabilities = {}
    for grouped_rows in by_threshold.values():
        if len(grouped_rows) == 2:
            probabilities.update(no_vig_probabilities(grouped_rows))
        else:
            probabilities.update(
                {
                    row["selection"]: 1 / require_decimal_odds(row["odds"], f"Australia O/U/{row['selection']}")
                    for row in grouped_rows
                }
            )
    return probabilities


def threshold_key(selection: str) -> str:
    match = re.search(r"(Over|Under)\s*([0-9]+(?:\.[0-9]+)?)", selection)
    if match:
        return match.group(2)
    return selection


def generate_australia_report(raw_path: Path, output_dir: Path, version: str = "v0_17") -> Dict:
    raw = load_australia_raw(raw_path)
    markets = parse_australia_raw(raw)
    gate = australia_gate(markets)
    recommendations = australia_candidates(markets)
    result = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_raw": public_artifact_ref(raw_path),
        "board": raw.get("board"),
        "url": raw.get("url"),
        "expected_markets": EXPECTED_MARKETS,
        "market_count": len(markets),
        "priced_market_count": sum(1 for market in markets if market["status"] == "priced"),
        "markets": markets,
        "recommendations": recommendations,
        "automation_gate": gate,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / f"tab_fifa_world_cup_australia_markets_recommendations_{version}.json", result)
    atomic_write_json(output_dir / f"automation_gate_australia_markets_{version}.json", gate)
    atomic_write_text(output_dir / f"tab_fifa_world_cup_australia_markets_{version}_report.md", render_australia_markdown(result))
    return result


def australia_gate(markets: List[Dict]) -> Dict:
    priced = [market for market in markets if market["status"] == "priced"]
    complete_priced = [market for market in priced if market["rows"]]
    names = [market["market"] for market in markets]
    expected = set(EXPECTED_MARKETS)
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    unknown_names = sorted(set(names) - expected)
    missing_names = sorted(expected - set(names), key=EXPECTED_MARKETS.index)
    integrity_errors = australia_market_integrity_errors(markets)
    ready = (
        not duplicate_names
        and not unknown_names
        and not missing_names
        and not integrity_errors
        and len(markets) == len(EXPECTED_MARKETS)
        and len(complete_priced) == len(EXPECTED_MARKETS)
    )
    return {
        "automation_ready": ready,
        "manual_report_ready": bool(complete_priced),
        "coverage": {
            "markets": {"covered": len(markets), "total": len(EXPECTED_MARKETS), "rate": round(len(markets) / len(EXPECTED_MARKETS), 3)},
            "priced_markets": {"covered": len(complete_priced), "total": len(EXPECTED_MARKETS)},
            "unique_expected_markets": {"covered": len(set(names) & expected), "total": len(EXPECTED_MARKETS)},
            "market_integrity": {"failed_markets": len(integrity_errors), "total": len(EXPECTED_MARKETS)},
        },
        "blocking_reasons": [] if ready else australia_blocking_reasons(
            markets, missing_names, duplicate_names, unknown_names, integrity_errors
        ),
    }


def australia_market_integrity_errors(markets: List[Dict]) -> List[str]:
    errors = []
    for market in markets:
        if market.get("status") != "priced":
            continue
        market_name = market.get("market", "Unknown Market")
        rows = market.get("rows", [])
        selections = [str(row.get("selection", "")).strip() for row in rows]
        empty_count = sum(1 for selection in selections if not selection)
        duplicate_selections = sorted({selection for selection in selections if selection and selections.count(selection) > 1})
        invalid_odds = [selection for selection, row in zip(selections, rows) if not valid_decimal_odds(row.get("odds"))]
        if empty_count:
            errors.append(f"{market_name} has {empty_count} empty Australia selections.")
        if duplicate_selections:
            errors.append(f"{market_name} duplicate Australia selections parsed: {', '.join(duplicate_selections)}.")
        if invalid_odds:
            errors.append(f"{market_name} has invalid decimal odds for: {', '.join(invalid_odds)}.")
        if "O/U" in market_name:
            errors.extend(over_under_pair_errors(market_name, rows))
    return errors


def over_under_pair_errors(market_name: str, rows: List[Dict]) -> List[str]:
    by_threshold: Dict[str, set[str]] = {}
    for row in rows:
        selection = str(row.get("selection", ""))
        match = re.search(r"\b(Over|Under)\s*([0-9]+(?:\.[0-9]+)?)", selection)
        if match:
            by_threshold.setdefault(match.group(2), set()).add(match.group(1))
    if not by_threshold:
        return [f"{market_name} has no parsed Over/Under thresholds."]
    errors = []
    for threshold, sides in sorted(by_threshold.items(), key=lambda item: float(item[0])):
        missing_sides = sorted({"Over", "Under"} - sides)
        if missing_sides:
            errors.append(f"{market_name} threshold {threshold} missing {'/'.join(missing_sides)} side.")
    return errors


def australia_blocking_reasons(
    markets: List[Dict],
    missing_names: List[str] | None = None,
    duplicate_names: List[str] | None = None,
    unknown_names: List[str] | None = None,
    integrity_errors: List[str] | None = None,
) -> List[str]:
    status_by_name = {market["market"]: market["status"] for market in markets}
    missing = missing_names if missing_names is not None else [name for name in EXPECTED_MARKETS if name not in status_by_name]
    duplicate = duplicate_names or []
    unknown = unknown_names or []
    collapsed = [name for name, status in status_by_name.items() if status != "priced"]
    reasons = []
    if missing:
        reasons.append(f"Expected {len(EXPECTED_MARKETS)} Australia markets, missing {len(missing)}: {', '.join(missing)}.")
    if duplicate:
        reasons.append(f"Duplicate Australia markets parsed: {', '.join(duplicate)}.")
    if unknown:
        reasons.append(f"Unknown Australia markets parsed: {', '.join(unknown)}.")
    if collapsed:
        reasons.append(f"{len(collapsed)} Australia markets are visible but not expanded with prices: {', '.join(collapsed)}.")
    reasons.extend(integrity_errors or [])
    return reasons


def australia_candidates(markets: List[Dict]) -> List[Dict]:
    candidates = []
    for market in markets:
        if market["status"] != "priced" or not market["rows"]:
            continue
        best = max(market["rows"], key=lambda row: row.get("probability", 0))
        candidates.append(
            {
                "market": market["market"],
                "selection": best["selection"],
                "odds": best["odds"],
                "probability": best.get("probability", 0),
                "probability_method": market.get("probability_method"),
                "stake_aud": 0,
                "stake_unit": 0,
                "decision": "watch_or_no_bet",
                "rationale": australia_rationale(market["market"], best, market.get("probability_method", "")),
                "risk": "Australia is in Group D with USA, Turkiye and Paraguay; this market needs match-level simulations before staking.",
            }
        )
    return candidates


def australia_rationale(market: str, row: Dict, probability_method: str) -> str:
    selection = row["selection"]
    probability = row.get("probability", 0)
    if "Exactly 1" in selection:
        return "Highest no-vig probability among priced outcomes, but price is short and depends heavily on Paraguay/Turkiye matchups."
    if "0 Grp" in selection:
        return "Market implies a high chance Australia fails to win a group match; plausible in Group D, but downside price is too short without simulation edge."
    if market == "AUS Group Match Wins" and "Exactly 2" in selection:
        return "Upside outcome with meaningful payout, but requires Australia to outperform at least two of USA, Turkiye and Paraguay."
    if market == "AUS Group Match Wins" and "All 3" in selection:
        return "Very low-probability sweep outcome; monitor only unless match-level injuries or rotations materially shift the group."
    if probability_method == "single_selection_implied":
        return f"Single-sided TAB price implies {probability:.1%}; no opposite side is displayed, so this is not enough to justify staking."
    if probability_method == "threshold_pair_no_vig":
        return f"Highest probability option in this O/U threshold set is {probability:.1%}; compare with match-level goal model before staking."
    if probability_method == "displayed_subset_no_vig":
        return f"Displayed-subset probability is {probability:.1%}; 'quote others' means this is not a complete player universe."
    return f"Market no-vig probability is {probability:.1%}; keep as watch/no-bet until the group simulation shows edge."


def render_australia_markdown(result: Dict) -> str:
    gate = result["automation_gate"]
    lines = [
        f"# TAB FIFA World Cup Australia Markets Report {result['version']}",
        "",
        "本报告由 TAB Australia Markets 页面只读抓取生成；不自动下注、不操作下注单。",
        "",
        "## Automation Gate",
        "",
        f"- automation_ready: `{gate['automation_ready']}`",
        f"- manual_report_ready: `{gate['manual_report_ready']}`",
        f"- market_coverage: `{gate['coverage']['markets']['covered']}/{gate['coverage']['markets']['total']}`",
        f"- priced_market_coverage: `{gate['coverage']['priced_markets']['covered']}/{gate['coverage']['priced_markets']['total']}`",
        "",
        "## Visual Summary",
        "",
        "### Australia Markets 操作分布",
        "",
        mermaid_pie("Australia Markets 操作分布", decision_distribution(result["recommendations"])),
        "",
        "### 候选概率 Top",
        "",
        mermaid_bar(
            "Australia Candidate Probability Top",
            top_items(
                [
                    {**item, "label": f"{item['market']} / {item['selection']}", "probability_pct": item["probability"] * 100}
                    for item in result["recommendations"]
                ],
                "label",
                "probability_pct",
            ),
            "Probability %",
        ),
        "",
        "## Priced Markets",
        "",
        "| Market | Selection | Odds | Probability | Method |",
        "|---|---|---:|---:|---|",
    ]
    for market in result["markets"]:
        if market["status"] != "priced":
            continue
        for row in market["rows"]:
            selection = row["selection"]
            lines.append(
                f"| {market['market']} | {selection} | {row['odds']:.2f} | {row.get('probability', 0):.1%} | {market.get('probability_method', '')} |"
            )
    lines.extend(["", "## Collapsed Or Missing Markets", ""])
    incomplete = [market for market in result["markets"] if market["status"] != "priced"]
    if incomplete:
        for market in incomplete:
            lines.append(f"- {market['market']}: {market['status']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Research Candidates",
            "",
            "| Market | Selection | Odds | Probability | Action | Stake | Reason |",
            "|---|---|---:|---:|---|---:|---|",
        ]
    )
    for item in result["recommendations"]:
        lines.append(
            "| {market} | {selection} | {odds:.2f} | {prob:.1%} | {decision} | AUD {stake:.2f} / {unit:.2f}u | {reason} |".format(
                market=item["market"],
                selection=item["selection"],
                odds=item["odds"],
                prob=item["probability"],
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
