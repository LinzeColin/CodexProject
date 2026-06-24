import json
import math
import re
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .compare import compact_baseline, compare_recommendations, load_baseline
from .event_monitor import event_risk_for_match, load_event_audit
from .artifacts import public_artifact_ref
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import decision_distribution, mermaid_bar, mermaid_pie
from .model import (
    Candidate,
    apply_quality_overlay,
    estimate_xg,
    novig_probabilities,
    poisson_distribution,
    probability_of,
    score_candidate,
)
from .parser import invalid_market_price_rows, parse_market_pairs
from .public_sources import load_source_audit, source_baseline


EXPECTED_MATCHES = [
    "Mexico v South Africa",
    "South Korea v Czechia",
    "Canada v Bosn-Herzegovina",
    "USA v Paraguay",
    "Qatar v Switzerland",
    "Brazil v Morocco",
    "Haiti v Scotland",
    "Australia v Turkiye",
    "Germany v Curacao",
    "Netherlands v Japan",
    "Cote d Ivoire v Ecuador",
    "Sweden v Tunisia",
    "Spain v Cabo Verde",
    "Belgium v Egypt",
    "Saudi Arabia v Uruguay",
    "Iran v New Zealand",
    "France v Senegal",
    "Iraq v Norway",
    "Argentina v Algeria",
    "Austria v Jordan",
    "Portugal v DR Congo",
    "England v Croatia",
    "Ghana v Panama",
    "Uzbekistan v Colombia",
    "USA v Australia",
    "Paraguay v Australia",
]
CORE_MAIN_MARKETS = [
    "Result",
    "Double Chance",
    "Handicap",
    "Total Goals Over/Under",
    "Both Teams to Score",
    "Draw No Bet",
]

def load_raw(path: Path) -> Dict:
    return json.loads(path.read_text())


def generate_candidates(raw: Dict, bankroll_aud: float = 4000, unit_aud: float = 40) -> List[Candidate]:
    candidates: List[Candidate] = []
    for match in raw.get("matches", []):
        if match_is_in_play(match):
            continue
        markets = match.get("markets", {})
        result = list(parse_market_pairs(markets.get("Result", ""), "Result").items())[:3]
        if len(result) < 3:
            continue
        home_name, home_odds = result[0]
        draw_name, draw_odds = result[1]
        away_name, away_odds = result[2]
        home_market, draw_market, away_market = novig_probabilities([home_odds, draw_odds, away_odds])

        totals = parse_market_pairs(markets.get("Total Goals Over/Under", ""), "Total Goals Over/Under")
        if "Under 2.5 Goals" in totals and "Over 2.5 Goals" in totals:
            under_25_market, _ = novig_probabilities([totals["Under 2.5 Goals"], totals["Over 2.5 Goals"]])
        else:
            under_25_market = 0.54

        home_xg, away_xg = estimate_xg(home_market, away_market, under_25_market)
        home_xg, away_xg, _note = apply_quality_overlay(match["match"], home_xg, away_xg)
        distribution = poisson_distribution(home_xg, away_xg)
        probabilities = {
            home_name: probability_of(distribution, lambda h, a: h > a),
            "Draw": probability_of(distribution, lambda h, a: h == a),
            away_name: probability_of(distribution, lambda h, a: h < a),
            "Over 2.5 Goals": probability_of(distribution, lambda h, a: h + a >= 3),
            "Under 2.5 Goals": probability_of(distribution, lambda h, a: h + a <= 2),
            "Both Teams to Score": probability_of(distribution, lambda h, a: h >= 1 and a >= 1),
            "Only One or Neither to score": probability_of(distribution, lambda h, a: h == 0 or a == 0),
        }

        for market_name in ["Result", "Total Goals Over/Under", "Both Teams to Score"]:
            pairs = parse_market_pairs(markets.get(market_name, ""), market_name)
            for selection, odds in pairs.items():
                key = normalize_selection(selection)
                probability = probabilities.get(key)
                if probability is None:
                    continue
                candidates.append(
                    score_candidate(match["match"], market_name, selection, odds, probability, bankroll_aud, unit_aud)
                )
        team_total_pairs = parse_market_pairs(markets.get("Team Total Goals Over/Under", ""), "Team Total Goals Over/Under")
        for selection, odds in team_total_pairs.items():
            probability = team_total_probability(selection, home_name, away_name, home_xg, away_xg)
            if probability is None:
                continue
            candidates.append(
                score_candidate(
                    match["match"],
                    "Team Total Goals Over/Under",
                    selection,
                    odds,
                    probability,
                    bankroll_aud,
                    unit_aud,
                )
            )
    return sorted(candidates, key=lambda item: item.expected_value, reverse=True)


def normalize_selection(selection: str) -> str:
    if "Only One or Neither" in selection:
        return "Only One or Neither to score"
    if "Over 2.5" in selection:
        return "Over 2.5 Goals"
    if "Under 2.5" in selection:
        return "Under 2.5 Goals"
    return selection


def team_total_probability(selection: str, home_name: str, away_name: str, home_xg: float, away_xg: float) -> Optional[float]:
    match = re.match(r"(.+?)\s+(Over|Under)\s+([0-9]+(?:\.[0-9]+)?)\s+Goals?$", selection.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    team, side, line_text = match.groups()
    line = float(line_text)
    if not math.isclose(line % 1, 0.5, abs_tol=1e-9):
        return None
    team_key = team.strip().lower()
    if team_key == home_name.strip().lower():
        lam = home_xg
    elif team_key == away_name.strip().lower():
        lam = away_xg
    else:
        return None
    threshold = int(math.floor(line))
    under_probability = sum(_poisson_goals(goals, lam) for goals in range(threshold + 1))
    if side.lower() == "under":
        return under_probability
    return max(0.0, 1.0 - under_probability)


def _poisson_goals(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def automation_gate(
    raw: Dict,
    candidates: List[Candidate],
    public_source_audit: Optional[Dict] = None,
    event_audit: Optional[Dict] = None,
) -> Dict:
    expected_names, in_play_excluded = pre_match_expected_names(raw)
    total = len(expected_names)
    expected_matches = {match.get("match"): match for match in raw.get("matches", []) if match.get("match") in expected_names}
    detail_count = len(expected_matches)
    result_count = sum(1 for match in expected_matches.values() if market_has_prices(match, "Result"))
    full_count = sum(1 for match in expected_matches.values() if has_full_core_markets(match))
    market_errors = sum(len(match.get("errors", [])) for match in expected_matches.values())
    access_denied_count = sum(1 for match in expected_matches.values() if match_access_denied(match))
    quality = quality_audit(raw)
    market_integrity_errors = quality.get("market_integrity_errors", [])
    public_sources_ready = public_source_audit is not None and public_source_audit.get("all_sources_ok") is True
    event_monitor_ready = event_audit is not None and event_audit.get("all_feeds_ok") is True
    ready = (
        total > 0
        and detail_count / total >= 0.95
        and result_count == detail_count
        and full_count / total >= 0.90
        and market_errors == 0
        and access_denied_count == 0
        and not market_integrity_errors
        and public_sources_ready
        and event_monitor_ready
    )
    return {
        "automation_ready": ready,
        "manual_report_ready": total > 0 and detail_count >= min(20, total) and result_count == detail_count,
        "coverage": {
            "target_source": raw.get("target_source") or "configured_expected_matches",
            "pre_match_eligible_matches": total,
            "in_play_excluded_matches": len(in_play_excluded),
            "in_play_excluded_match_names": in_play_excluded,
            "result_market_matches": {"covered": result_count, "total": total, "rate": coverage_rate(result_count, total)},
            "detail_main_markets": {"covered": detail_count, "total": total, "rate": coverage_rate(detail_count, total)},
            "full_main_markets": {"covered": full_count, "total": total, "rate": coverage_rate(full_count, total)},
            "market_errors": market_errors,
            "access_denied_matches": access_denied_count,
            "market_integrity_errors": len(market_integrity_errors),
        },
        "quality_audit": quality,
        "public_sources": {
            "required": True,
            "ready": public_sources_ready,
            "ok_count": (public_source_audit or {}).get("ok_count", 0),
            "source_count": (public_source_audit or {}).get("source_count", 0),
        },
        "event_monitor": {
            "required": True,
            "ready": event_monitor_ready,
            "ok_count": (event_audit or {}).get("ok_count", 0),
            "feed_count": (event_audit or {}).get("feed_count", 0),
            "flagged_item_count": (event_audit or {}).get("flagged_item_count", 0),
        },
        "blocking_reasons": [] if ready else blocking_reasons(
            detail_count,
            result_count,
            full_count,
            market_errors,
            access_denied_count,
            market_integrity_errors,
            total,
            public_sources_ready,
            event_monitor_ready,
        ),
        "top_candidate_count": len([item for item in candidates if item.stake_unit > 0]),
    }


def expected_match_names(raw: Dict) -> List[str]:
    target_matches = raw.get("target_matches")
    if isinstance(target_matches, list):
        names = []
        seen = set()
        for item in target_matches:
            name = str(item or "").strip()
            if not name or " v " not in name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        if names:
            return names
    return list(EXPECTED_MATCHES)


def pre_match_expected_names(raw: Dict) -> tuple[List[str], List[str]]:
    expected_names = expected_match_names(raw)
    expected_rows = {
        match.get("match"): match
        for match in raw.get("matches", [])
        if match.get("match") in expected_names
    }
    in_play_excluded = [
        name for name in expected_names
        if name in expected_rows and match_is_in_play(expected_rows[name])
    ]
    excluded = set(in_play_excluded)
    return [name for name in expected_names if name not in excluded], in_play_excluded


def coverage_rate(covered: int, total: int) -> float:
    return round(covered / total, 3) if total else 0.0


def match_is_in_play(match: Dict) -> bool:
    status_fields = [
        match.get("status"),
        match.get("match_status"),
        match.get("state"),
        match.get("phase"),
    ]
    if str(match.get("in_play") or "").strip().lower() in {"1", "true", "yes"}:
        return True
    for value in status_fields:
        normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"in_play", "live", "started"}:
            return True
    values = [
        match.get("title"),
        match.get("text"),
        *(match.get("markets", {}) or {}).values(),
    ]
    combined = "\n".join(str(value or "") for value in values).lower()
    return "in-play" in combined or "in play" in combined


def market_has_prices(match: Dict, market_name: str) -> bool:
    market_text = match.get("markets", {}).get(market_name, "")
    try:
        return bool(parse_market_pairs(market_text, market_name))
    except Exception:
        return False


def match_access_denied(match: Dict) -> bool:
    if match.get("access_denied") or match.get("access_status") == "access_denied":
        return True
    title = str(match.get("title") or "")
    text = str(match.get("text") or "")
    return "access denied" in title.lower() or "access denied" in text.lower()


def has_full_core_markets(match: Dict) -> bool:
    return all(market_has_prices(match, market_name) for market_name in CORE_MAIN_MARKETS)


def quality_audit(raw: Dict) -> Dict:
    matches = raw.get("matches", [])
    all_expected_names = expected_match_names(raw)
    expected_names, in_play_excluded = pre_match_expected_names(raw)
    covered_names = {match.get("match") for match in matches}
    missing = [match for match in expected_names if match not in covered_names]
    partial = [
        match.get("match")
        for match in matches
        if match.get("match") in expected_names and not has_full_core_markets(match)
    ]
    errors = [
        {"match": match.get("match"), "errors": match.get("errors", [])}
        for match in matches
        if match.get("errors")
    ]
    access_denied = [
        match.get("match")
        for match in matches
        if match.get("match") in expected_names and match_access_denied(match)
    ]
    market_integrity = [
        {"match": match.get("match"), "errors": errors}
        for match in matches
        if match.get("match") in expected_names
        for errors in [market_integrity_errors(match)]
        if errors
    ]
    return {
        "total_expected_matches": len(all_expected_names),
        "pre_match_eligible_matches": expected_names,
        "in_play_excluded_matches": in_play_excluded,
        "missing_detail_matches": missing,
        "partial_core_only_matches": partial,
        "access_denied_matches": access_denied,
        "matches_with_errors": errors,
        "market_integrity_errors": market_integrity,
        "next_scrape_priority": missing + access_denied + partial + [item["match"] for item in errors],
    }


def market_integrity_errors(match: Dict) -> List[str]:
    errors = []
    markets = match.get("markets", {})
    for market_name in CORE_MAIN_MARKETS:
        invalid = invalid_market_price_rows(markets.get(market_name, ""), market_name)
        if invalid:
            errors.append(f"{market_name} has invalid decimal odds: {', '.join(invalid)}.")
    return errors


def blocking_reasons(
    detail_count: int,
    result_count: int,
    full_count: int,
    market_errors: int,
    access_denied_count: int,
    market_integrity_errors: List[Dict],
    total: int,
    public_sources_ready: bool,
    event_monitor_ready: bool,
) -> List[str]:
    reasons: List[str] = []
    if total <= 0:
        reasons.append("No pre-match eligible match details remain for new-bet automation.")
        if market_integrity_errors:
            reasons.append("Invalid decimal odds remain in raw market data.")
        if not public_sources_ready:
            reasons.append("Public source audit is missing or failed.")
        if not event_monitor_ready:
            reasons.append("Event/news monitor audit is missing or failed.")
        return reasons
    if detail_count / total < 0.95:
        reasons.append("Detail market coverage below 95% automation threshold.")
    if result_count != detail_count:
        reasons.append(f"Result market coverage {result_count}/{detail_count} does not match captured detail coverage.")
    if full_count / total < 0.90:
        reasons.append("Full Main Markets coverage below 90% automation threshold.")
    if access_denied_count:
        reasons.append(f"{access_denied_count} match detail page(s) returned Access Denied.")
    if market_errors:
        reasons.append("Market expansion errors remain in raw data.")
    if market_integrity_errors:
        detail = "; ".join(
            f"{item.get('match')}: {', '.join(item.get('errors', []))}" for item in market_integrity_errors[:5]
        )
        reasons.append(f"Invalid decimal odds remain in raw market data: {detail}.")
    if not public_sources_ready:
        reasons.append("Public source audit is missing or failed.")
    if not event_monitor_ready:
        reasons.append("Event/news monitor audit is missing or failed.")
    return reasons


def write_outputs(
    raw_path: Path,
    output_dir: Path,
    version: str = "v0.5",
    previous_baseline_path: Optional[Path] = None,
    public_source_audit_path: Optional[Path] = None,
    event_audit_path: Optional[Path] = None,
    allow_blocked_export: bool = False,
) -> Dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        raw = load_raw(raw_path)
    except Exception as exc:
        failure = failed_closed_export(
            raw_path=raw_path,
            version=version,
            gate={
                "automation_ready": False,
                "manual_report_ready": False,
                "blocking_reasons": [f"Raw parse failed: {type(exc).__name__}: {exc}"],
                "quality_audit": {},
            },
            candidates=[],
            failure_stage="parse",
        )
        atomic_write_json(output_dir / f"tab_fifa_world_cup_matches_failed_closed_{version}.json", failure)
        return failure
    public_source_audit = load_source_audit(public_source_audit_path)
    event_audit = load_event_audit(event_audit_path)
    candidates = generate_candidates(raw)
    gate = automation_gate(raw, candidates, public_source_audit, event_audit)
    if not gate.get("automation_ready") and not allow_blocked_export:
        failure = failed_closed_export(
            raw_path=raw_path,
            version=version,
            gate=gate,
            candidates=candidates,
            failure_stage="validation",
        )
        atomic_write_json(output_dir / f"automation_gate_{version}.json", gate)
        atomic_write_json(output_dir / f"tab_fifa_world_cup_matches_failed_closed_{version}.json", failure)
        return failure

    recommendations = {
        "version": version,
        "export_status": "ready" if gate.get("automation_ready") else "legacy_blocked_export",
        "source_raw": public_artifact_ref(raw_path),
        "bankroll_aud": 4000,
        "unit_aud": 40,
        "recommended_new_exposure_aud": round(sum(item.stake_aud for item in candidates if item.stake_unit > 0), 2),
        "public_source_baseline": source_baseline(),
        "public_source_audit": public_source_audit,
        "event_audit": event_audit,
        "recommendations": [
            enrich_candidate(asdict(item), event_audit) for item in candidates if item.stake_unit > 0
        ],
        "watchlist": [asdict(item) for item in candidates if item.decision == "watch_or_no_bet" and item.expected_value > -0.03][:20],
        "automation_gate": gate,
    }
    previous = load_baseline(previous_baseline_path)
    recommendations["daily_compare"] = compare_recommendations(recommendations, previous)
    report_markdown = render_markdown(recommendations)
    baseline = compact_baseline(recommendations)

    atomic_write_json(output_dir / f"tab_fifa_world_cup_matches_recommendations_{version}.json", recommendations)
    atomic_write_json(output_dir / f"automation_gate_{version}.json", gate)
    atomic_write_text(output_dir / f"tab_fifa_world_cup_matches_{version}_pipeline_report.md", report_markdown)
    atomic_write_json(output_dir / f"previous_report_baseline_{version}.json", baseline)
    return recommendations


def failed_closed_export(
    raw_path: Path,
    version: str,
    gate: Dict,
    candidates: List[Candidate],
    failure_stage: str,
) -> Dict:
    return {
        "version": version,
        "export_status": "failed_closed",
        "failure_stage": failure_stage,
        "source_raw": public_artifact_ref(raw_path),
        "recommended_new_exposure_aud": 0,
        "recommendations": [],
        "watchlist": [],
        "candidate_count": len(candidates),
        "top_candidate_count": gate.get("top_candidate_count", 0),
        "automation_gate": gate,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "message": "FIFA matches export failed closed; no recommendations, report, or baseline success deliverable was published.",
    }


def enrich_candidate(item: Dict, event_audit: Optional[Dict]) -> Dict:
    event_risk = event_risk_for_match(item["match"], event_audit)
    item["event_risk"] = event_risk
    if event_risk["flag_count"]:
        item["risk"] = item["risk"] + " Event monitor has recent flagged news; verify before staking."
    return item


def render_markdown(recommendations: Dict) -> str:
    rows = recommendations["recommendations"]
    compare = recommendations.get("daily_compare", {})
    compare_summary = compare.get("summary", {})
    source_audit = recommendations.get("public_source_audit") or {}
    event_audit = recommendations.get("event_audit") or {}
    unit_aud = recommendations["unit_aud"]
    exposure_units = recommendations["recommended_new_exposure_aud"] / unit_aud if unit_aud else 0
    lines = [
        f"# TAB FIFA World Cup Matches Pipeline Report {recommendations['version']}",
        "",
        "本报告由本地 pipeline 从 TAB 原始盘口 JSON 自动生成；不自动下注、不操作下注单。",
        "",
        "## Bankroll & Exposure",
        "",
        f"- bankroll_assumption: `AUD {recommendations['bankroll_aud']}`",
        f"- unit_size: `1u = AUD {unit_aud}`",
        f"- recommended_new_exposure: `AUD {recommendations['recommended_new_exposure_aud']} / {exposure_units:.2f}u`",
        f"- compare_exposure_change: `AUD {compare_summary.get('exposure_change_aud', 0)}`",
        "",
        "## Automation Gate",
        "",
        f"- automation_ready: `{recommendations['automation_gate']['automation_ready']}`",
        f"- manual_report_ready: `{recommendations['automation_gate']['manual_report_ready']}`",
        f"- recommended_new_exposure_aud: `AUD {recommendations['recommended_new_exposure_aud']}`",
        f"- pre_match_eligible_matches: `{recommendations['automation_gate']['coverage'].get('pre_match_eligible_matches', 0)}`",
        f"- in_play_excluded_matches: `{recommendations['automation_gate']['coverage'].get('in_play_excluded_matches', 0)}`",
        f"- detail_coverage: `{recommendations['automation_gate']['coverage']['detail_main_markets']['covered']}/{recommendations['automation_gate']['coverage']['detail_main_markets']['total']}`",
        f"- full_market_coverage: `{recommendations['automation_gate']['coverage']['full_main_markets']['covered']}/{recommendations['automation_gate']['coverage']['full_main_markets']['total']}`",
        f"- public_sources_ready: `{recommendations['automation_gate']['public_sources']['ready']}`",
        f"- event_monitor_ready: `{recommendations['automation_gate']['event_monitor']['ready']}`",
        "",
        "## Data Quality Audit",
        "",
        f"- missing_detail_matches: `{', '.join(recommendations['automation_gate']['quality_audit']['missing_detail_matches']) or 'none'}`",
        f"- partial_core_only_matches: `{', '.join(recommendations['automation_gate']['quality_audit']['partial_core_only_matches']) or 'none'}`",
        f"- in_play_excluded_matches: `{', '.join(recommendations['automation_gate']['quality_audit'].get('in_play_excluded_matches', [])) or 'none'}`",
        f"- matches_with_errors: `{len(recommendations['automation_gate']['quality_audit']['matches_with_errors'])}`",
        "",
        "## Public Source Baseline",
        "",
        "公开信息层当前用于赛程、晋级队伍、主客场/承办地和球队强度背景校验；伤停、首发、训练新闻会作为下一阶段自动抓取模块接入。",
        "",
        f"- source_audit_ready: `{source_audit.get('all_sources_ok')}`",
        f"- source_audit_coverage: `{source_audit.get('ok_count', 0)}/{source_audit.get('source_count', 0)}`",
        f"- source_audit_generated_at: `{source_audit.get('generated_at')}`",
        "",
        "| Source | Usage | URL |",
        "|---|---|---|",
    ]
    for source in recommendations["public_source_baseline"]:
        lines.append(f"| {source['name']} | {source['usage']} | {source['url']} |")
    failed_sources = [item for item in source_audit.get("sources", []) if not item.get("ok")]
    if failed_sources:
        lines.extend(["", "### Failed Public Sources", "", "| Source | Missing Terms | Error |", "|---|---|---|"])
        for item in failed_sources:
            lines.append(
                f"| {item['name']} | {', '.join(item.get('missing_terms', [])) or 'none'} | {item.get('error') or 'none'} |"
            )
    lines.extend(
        [
            "",
            "## Event Monitor",
            "",
            "事件监控用于发现推荐候选相关球队的伤停、阵容、停赛、适应性新闻。出现 flagged item 不自动取消下注，但会要求下注前人工复核。",
            "",
            f"- event_monitor_ready: `{event_audit.get('all_feeds_ok')}`",
            f"- event_feed_coverage: `{event_audit.get('ok_count', 0)}/{event_audit.get('feed_count', 0)}`",
            f"- flagged_item_count: `{event_audit.get('flagged_item_count', 0)}`",
            f"- event_monitor_generated_at: `{event_audit.get('generated_at')}`",
            "",
        ]
    )
    flagged_items = event_audit.get("flagged_items", [])[:10]
    if flagged_items:
        lines.extend(["| Team | Keywords | Title | Source |", "|---|---|---|---|"])
        for item in flagged_items:
            lines.append(
                f"| {item.get('team')} | {', '.join(item.get('matched_keywords', []))} | {item.get('title')} | {item.get('source')} |"
            )
    lines.extend(
        [
            "",
            "## Visual Summary",
            "",
            "### 操作分布",
            "",
            mermaid_pie("比赛盘口操作分布", decision_distribution(rows)),
            "",
            "### Top EV 候选",
            "",
            mermaid_bar(
                "比赛盘口 Top EV",
                [
                    (f"{item['match']} / {item['selection']}", max(0.0, item.get("expected_value", 0)) * 100)
                    for item in rows[:8]
                ],
                "EV %",
            ),
            "",
        "## Daily Compare",
        "",
        f"- previous_version: `{compare.get('previous_version')}`",
        f"- added: `{compare_summary.get('added_count', 0)}`",
        f"- removed: `{compare_summary.get('removed_count', 0)}`",
        f"- retained: `{compare_summary.get('retained_count', 0)}`",
        f"- changed: `{compare_summary.get('changed_count', 0)}`",
        "",
        "## Recommended Candidates",
        "",
        "| # | Match | Market | Selection | Odds | Model P | Breakeven | EV | Stake | Units | Event Flags | Decision |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    )
    for index, item in enumerate(rows, 1):
        lines.append(
            "| {idx} | {match} | {market} | {selection} | {odds:.2f} | {mp:.1%} | {bp:.1%} | {ev:+.1%} | AUD {stake:.2f} | {units:.2f}u | {flags} | {decision} |".format(
                idx=index,
                match=item["match"],
                market=item["market"],
                selection=item["selection"],
                odds=item["odds"],
                mp=item["model_probability"],
                bp=item["breakeven_probability"],
                ev=item["expected_value"],
                stake=item["stake_aud"],
                units=item["stake_unit"],
                flags=item.get("event_risk", {}).get("flag_count", 0),
                decision=item["decision"],
            )
        )
    if compare.get("changed"):
        lines.extend(
            [
                "",
                "## Changed Candidates",
                "",
                "| Match | Market | Selection | Odds | EV Change | Stake Change | Status |",
                "|---|---|---|---:|---:|---:|---|",
            ]
        )
        for item in compare["changed"][:20]:
            lines.append(
                "| {match} | {market} | {selection} | {old:.2f}->{new:.2f} | {ev:+.1%} | AUD {stake:+.2f} | {status} |".format(
                    match=item["match"],
                    market=item["market"],
                    selection=item["selection"],
                    old=item["old_odds"],
                    new=item["new_odds"],
                    ev=item["ev_change"],
                    stake=item["stake_change_aud"],
                    status=item["status"],
                )
            )
    lines.extend(
        [
            "",
            "## Blocking Reasons",
            "",
        ]
    )
    for reason in recommendations["automation_gate"]["blocking_reasons"]:
        lines.append(f"- {reason}")
    if not recommendations["automation_gate"]["blocking_reasons"]:
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
