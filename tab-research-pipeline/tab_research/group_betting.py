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
from .world_cup_2026 import GROUP_CODE_TO_TEAM, normalize_world_cup_team_name


GROUP_HEADER_RE = re.compile(r"^World Cup Group ([A-L]) \(([^)]+)\)$")
WINNER_RE = re.compile(r"^WC26 Group ([A-L]) Winner")


def load_group_raw(path: Path) -> Dict:
    return json.loads(path.read_text())


def parse_group_winners(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    groups = []
    i = 0
    while i < len(lines):
        header = GROUP_HEADER_RE.match(lines[i])
        if not header:
            i += 1
            continue
        group = header.group(1)
        label = lines[i]
        teams_hint = header.group(2)
        i += 1
        if i < len(lines) and lines[i].endswith("Markets"):
            i += 1
        if i < len(lines) and WINNER_RE.match(lines[i]):
            i += 1
        rows = []
        while i + 1 < len(lines):
            if GROUP_HEADER_RE.match(lines[i]) or lines[i] in GROUP_SECTION_TAILS:
                break
            team = normalize_team(lines[i])
            price = lines[i + 1]
            if is_price(price):
                rows.append({"team": team, "odds": parse_decimal_odds(price)})
                i += 2
            else:
                i += 1
            if len(rows) == 4:
                break
        groups.append(
            {
                "group": group,
                "label": label,
                "teams_hint": teams_hint,
                "market": "Group Winner",
                "rows": rows,
                "probabilities": no_vig_probabilities(rows),
            }
        )
    return groups


GROUP_SECTION_TAILS = {
    "To Qualify From Group",
    "Not To Qualify From Group",
    "Group Quinella",
    "Group Exacta",
    "Group Quadcast",
    "Finish Bottom Of Group",
    "Language:",
}


def normalize_team(team: str) -> str:
    return normalize_world_cup_team_name(team)


def is_price(value: str) -> bool:
    return parse_decimal_odds(value) is not None


def no_vig_probabilities(rows: List[Dict]) -> Dict[str, float]:
    teams = [row["team"] for row in rows]
    probabilities = no_vig_from_decimal_odds([row["odds"] for row in rows], "group winner")
    return dict(zip(teams, probabilities))


def generate_group_report(raw_path: Path, output_dir: Path, version: str = "v0_14") -> Dict:
    raw = load_group_raw(raw_path)
    groups = parse_group_winners(raw.get("text", ""))
    gate = group_gate(groups)
    recommendations = group_candidates(groups)
    result = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_raw": public_artifact_ref(raw_path),
        "board": raw.get("board"),
        "url": raw.get("url"),
        "group_count": len(groups),
        "groups": groups,
        "recommendations": recommendations,
        "automation_gate": gate,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / f"tab_fifa_world_cup_group_betting_recommendations_{version}.json", result)
    atomic_write_json(output_dir / f"automation_gate_group_betting_{version}.json", gate)
    atomic_write_text(output_dir / f"tab_fifa_world_cup_group_betting_{version}_report.md", render_group_markdown(result))
    return result


def group_gate(groups: List[Dict]) -> Dict:
    expected_groups = 12
    complete_groups = sum(1 for group in groups if len(group["rows"]) == 4)
    group_ids = [group["group"] for group in groups]
    expected_ids = set("ABCDEFGHIJKL")
    duplicate_groups = sorted({group for group in group_ids if group_ids.count(group) > 1})
    unknown_groups = sorted(set(group_ids) - expected_ids)
    missing_groups = sorted(expected_ids - set(group_ids))
    roster_errors = group_roster_errors(groups)
    invalid_odds = group_market_integrity_errors(groups)
    minimum_current_groups = 10
    ready = (
        len(groups) >= minimum_current_groups
        and complete_groups == len(groups)
        and not duplicate_groups
        and not unknown_groups
        and not roster_errors
        and not invalid_odds
    )
    return {
        "automation_ready": ready,
        "manual_report_ready": len(groups) >= 10,
        "coverage": {
            "groups": {"covered": len(groups), "total": expected_groups, "rate": round(len(groups) / expected_groups, 3)},
            "complete_group_winner_markets": {"covered": complete_groups, "total": expected_groups},
            "current_listed_group_winner_markets": {"covered": complete_groups, "total": len(groups)},
            "unavailable_groups": missing_groups,
            "roster_consistency": {"failed_groups": len(roster_errors), "total": expected_groups},
            "market_integrity": {"failed_groups": len(invalid_odds), "total": expected_groups},
        },
        "availability_notes": group_availability_notes(missing_groups),
        "blocking_reasons": [] if ready else group_blocking_reasons(
            groups, complete_groups, duplicate_groups, unknown_groups, roster_errors, invalid_odds, minimum_current_groups
        ),
    }


def group_roster_errors(groups: List[Dict]) -> List[str]:
    errors = []
    for group in groups:
        group_id = group.get("group", "?")
        teams = [row.get("team", "") for row in group.get("rows", [])]
        duplicate_teams = sorted({team for team in teams if team and teams.count(team) > 1})
        expected_teams = teams_from_hint(group.get("teams_hint", ""))
        missing_teams = [team for team in expected_teams if team not in teams]
        unknown_teams = sorted(team for team in teams if expected_teams and team not in expected_teams)
        if duplicate_teams:
            errors.append(f"Group {group_id} duplicate teams parsed: {', '.join(duplicate_teams)}.")
        if missing_teams or unknown_teams:
            parts = []
            if missing_teams:
                parts.append(f"missing {', '.join(missing_teams)}")
            if unknown_teams:
                parts.append(f"unknown {', '.join(unknown_teams)}")
            errors.append(f"Group {group_id} roster mismatch against TAB header: {'; '.join(parts)}.")
    return errors


def group_market_integrity_errors(groups: List[Dict]) -> List[str]:
    errors = []
    for group in groups:
        invalid = [
            str(row.get("team") or f"row {index + 1}")
            for index, row in enumerate(group.get("rows", []))
            if not valid_decimal_odds(row.get("odds"))
        ]
        if invalid:
            errors.append(f"Group {group.get('group', '?')} invalid decimal odds for: {', '.join(invalid)}.")
    return errors


def teams_from_hint(teams_hint: str) -> List[str]:
    teams = []
    for token in re.split(r"\s*[,/]\s*", teams_hint):
        token = token.strip()
        if not token:
            continue
        teams.append(normalize_team(GROUP_CODE_TO_TEAM.get(token, token)))
    return teams


def group_blocking_reasons(
    groups: List[Dict],
    complete_groups: int,
    duplicate_groups: List[str],
    unknown_groups: List[str],
    roster_errors: List[str],
    invalid_odds: List[str],
    minimum_current_groups: int,
) -> List[str]:
    reasons = []
    if len(groups) < minimum_current_groups:
        reasons.append(f"Listed group markets below minimum current coverage: {len(groups)}/{minimum_current_groups}.")
    if complete_groups != len(groups):
        reasons.append(f"Expected all listed Group Winner markets to be complete, parsed {complete_groups}/{len(groups)}.")
    if duplicate_groups:
        reasons.append(f"Duplicate groups parsed: {', '.join(duplicate_groups)}.")
    if unknown_groups:
        reasons.append(f"Unknown groups parsed: {', '.join(unknown_groups)}.")
    reasons.extend(roster_errors)
    reasons.extend(invalid_odds)
    return reasons


def group_availability_notes(missing_groups: List[str]) -> List[str]:
    if not missing_groups:
        return []
    return [
        f"Group {group_id} is not listed on the current TAB Group Betting page; treat it as unavailable for new Group Winner bets."
        for group_id in missing_groups
    ]


def group_candidates(groups: List[Dict]) -> List[Dict]:
    watch = {
        "Japan": "Match-market model already upgrades Japan; Group F winner price is a path-sensitive watch.",
        "Morocco": "Group C price depends on Brazil result; better treated as watch until group-path model is integrated.",
        "Croatia": "Group L winner price reflects England premium; useful monitoring candidate.",
        "Senegal": "Group I winner is hard with France/Norway, but price is worth tracking.",
        "Australia": "Group D has host-region dynamics and wide pricing; monitor rather than stake.",
        "Colombia": "Group K price is competitive behind Portugal; watch with group-path analysis.",
    }
    candidates = []
    for group in groups:
        for row in group["rows"]:
            team = row["team"]
            if team not in watch:
                continue
            candidates.append(
                {
                    "group": group["group"],
                    "team": team,
                    "market": "Group Winner",
                    "odds": row["odds"],
                    "no_vig_probability": group["probabilities"][team],
                    "stake_aud": 0,
                    "stake_unit": 0,
                    "decision": "watch_or_no_bet",
                    "rationale": watch[team],
                    "risk": "Group winner requires full match-path and qualification-market comparison before staking.",
                }
            )
    return sorted(candidates, key=lambda item: item["no_vig_probability"], reverse=True)


def render_group_markdown(result: Dict) -> str:
    gate = result["automation_gate"]
    lines = [
        f"# TAB FIFA World Cup Group Betting Report {result['version']}",
        "",
        "本报告由 TAB Group Betting 页面只读抓取生成；不自动下注、不操作下注单。",
        "",
        "## Automation Gate",
        "",
        f"- automation_ready: `{gate['automation_ready']}`",
        f"- manual_report_ready: `{gate['manual_report_ready']}`",
        f"- group_coverage: `{gate['coverage']['groups']['covered']}/{gate['coverage']['groups']['total']}`",
        f"- complete_group_winner_markets: `{gate['coverage']['complete_group_winner_markets']['covered']}/{gate['coverage']['complete_group_winner_markets']['total']}`",
        f"- unavailable_groups: `{', '.join(gate['coverage'].get('unavailable_groups', [])) or 'none'}`",
        "",
        "## Visual Summary",
        "",
        "### Group Betting 操作分布",
        "",
        mermaid_pie("Group Betting 操作分布", decision_distribution(result["recommendations"])),
        "",
        "### 小组第一概率 Top",
        "",
        mermaid_bar(
            "Group Winner No-Vig Top",
            top_items(
                [
                    {"team": row["team"], "probability_pct": group["probabilities"][row["team"]] * 100}
                    for group in result["groups"]
                    for row in group["rows"]
                ],
                "team",
                "probability_pct",
            ),
            "No-Vig %",
        ),
        "",
        "## Group Winner Markets",
        "",
        "| Group | Team | Odds | No-Vig P |",
        "|---|---|---:|---:|",
    ]
    for group in result["groups"]:
        for row in group["rows"]:
            team = row["team"]
            lines.append(
                f"| {group['group']} | {team} | {row['odds']:.2f} | {group['probabilities'][team]:.1%} |"
            )
    lines.extend(
        [
            "",
            "## Research Candidates",
            "",
            "| Group | Team | Odds | No-Vig P | Action | Stake | Reason |",
            "|---|---|---:|---:|---|---:|---|",
        ]
    )
    for item in result["recommendations"]:
        lines.append(
            "| {group} | {team} | {odds:.2f} | {prob:.1%} | {decision} | AUD {stake:.2f} | {reason} |".format(
                group=item["group"],
                team=item["team"],
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
