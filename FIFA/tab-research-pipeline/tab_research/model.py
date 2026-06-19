import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .odds import no_vig_from_decimal_odds, require_decimal_odds


@dataclass(frozen=True)
class Candidate:
    match: str
    market: str
    selection: str
    odds: float
    model_probability: float
    breakeven_probability: float
    edge: float
    expected_value: float
    stake_unit: float
    stake_aud: float
    decision: str
    rationale: str
    risk: str


QUALITY_OVERLAYS = {
    "Mexico v South Africa": (0.08, -0.05, "Mexico host/travel edge"),
    "Canada v Bosn-Herzegovina": (0.06, -0.02, "Canada host edge"),
    "USA v Paraguay": (0.05, -0.02, "USA host edge"),
    "Brazil v Morocco": (-0.05, 0.10, "Morocco quality / Brazil premium fade"),
    "Netherlands v Japan": (-0.04, 0.10, "Japan quality upgrade"),
    "France v Senegal": (-0.03, 0.06, "Senegal quality upgrade"),
    "England v Croatia": (-0.05, 0.08, "England premium fade / Croatia tournament profile"),
    "Australia v Turkiye": (0.04, 0.00, "Australia support/market watch"),
}

MODEL_QUALITY_NOTES = {
    "Brazil v Morocco|Morocco": (
        "Morocco is treated as a live underdog rather than a generic long shot; Brazil name premium may compress the favourite price.",
        "High-variance underdog; reduce or cancel if Morocco lineup weakens.",
    ),
    "Netherlands v Japan|Japan": (
        "Japan's tactical discipline and recent cycle justify a probability above generic underdog pricing.",
        "Netherlands physicality and set-piece edge remain material.",
    ),
    "France v Senegal|Senegal": (
        "Senegal has enough tournament-quality profile to make a long price worth monitoring.",
        "France attacking depth can overwhelm the edge; lineup risk is high.",
    ),
    "England v Croatia|Croatia": (
        "Croatia has tournament pedigree and England can carry market premium in pre-tournament pricing.",
        "England squad depth is materially stronger; this remains a high-variance underdog.",
    ),
    "Belgium v Egypt|Under 2.5 Goals": (
        "Projected tempo and price support a low-total candidate.",
        "Early goal, penalty, or red card can break the under structure.",
    ),
    "South Korea v Czechia|Only One or Neither to score": (
        "Balanced match with low-total profile supports BTTS No at a usable price.",
        "Transition chances for either side make this only a marginal edge.",
    ),
}

CURATED_TOTALS = {
    "Belgium v Egypt|Under 2.5 Goals",
    "South Korea v Czechia|Only One or Neither to score",
    "Mexico v South Africa|Only One or Neither to score",
    "Brazil v Morocco|Under 2.5 Goals",
    "Netherlands v Japan|Only One or Neither to score",
}


def novig_probabilities(odds: Iterable[float]) -> List[float]:
    return no_vig_from_decimal_odds(odds, "novig_probabilities")


def implied_probability(odds: float) -> float:
    return 1 / require_decimal_odds(odds, "implied_probability")


def poisson_distribution(home_xg: float, away_xg: float, max_goals: int = 12) -> Dict[tuple, float]:
    return {
        (home, away): _poisson(home, home_xg) * _poisson(away, away_xg)
        for home in range(max_goals + 1)
        for away in range(max_goals + 1)
    }


def probability_of(distribution: Dict[tuple, float], predicate) -> float:
    return sum(probability for score, probability in distribution.items() if predicate(*score))


def estimate_xg(home_market_probability: float, away_market_probability: float, under_25_probability: float) -> tuple:
    total_goals = max(1.1, min(3.6, 0.7 + 3.4 * (1 - under_25_probability)))
    ratio = max(0.15, min(6.0, home_market_probability / max(away_market_probability, 0.01)))
    home_share = 1 / (1 + math.exp(-0.55 * math.log(ratio)))
    return max(0.2, total_goals * home_share), max(0.2, total_goals * (1 - home_share))


def apply_quality_overlay(match: str, home_xg: float, away_xg: float) -> tuple:
    home_delta, away_delta, note = QUALITY_OVERLAYS.get(match, (0.0, 0.0, "market baseline"))
    return max(0.1, home_xg + home_delta), max(0.1, away_xg + away_delta), note


def score_candidate(
    match: str,
    market: str,
    selection: str,
    odds: float,
    model_probability: float,
    bankroll_aud: float,
    unit_aud: float,
) -> Candidate:
    odds = require_decimal_odds(odds, f"{match}/{market}/{selection}")
    breakeven = implied_probability(odds)
    edge = model_probability - breakeven
    expected_value = (model_probability * odds) - 1
    decision, stake_unit = stake_policy(match, market, selection, odds, edge, expected_value)
    stake_aud = round(stake_unit * unit_aud, 2)
    rationale, risk = MODEL_QUALITY_NOTES.get(
        f"{match}|{selection}",
        (
            "Model edge is based on TAB market fit plus conservative quality overlay.",
            "Model uncertainty remains high until lineups, injuries, and closing prices are known.",
        ),
    )
    return Candidate(
        match=match,
        market=market,
        selection=selection,
        odds=odds,
        model_probability=model_probability,
        breakeven_probability=breakeven,
        edge=edge,
        expected_value=expected_value,
        stake_unit=stake_unit,
        stake_aud=stake_aud,
        decision=decision,
        rationale=rationale,
        risk=risk,
    )


def stake_policy(match: str, market: str, selection: str, odds: float, edge: float, expected_value: float) -> tuple:
    if not passes_quality_gate(match, market, selection, odds):
        return "reject_quality_gate", 0.0
    if not has_curated_support(match, market, selection):
        return "watch_or_no_bet", 0.0
    if expected_value >= 0.08 and edge >= 0.025:
        return "small_stake", 0.5 if odds <= 4.0 else 0.25
    if expected_value >= 0.02 and edge >= 0.01:
        return "marginal_small_stake", 0.25
    return "watch_or_no_bet", 0.0


def passes_quality_gate(match: str, market: str, selection: str, odds: float) -> bool:
    if odds < 1.30:
        return False
    if match in {"Germany v Curacao", "Spain v Cabo Verde", "Iraq v Norway", "Portugal v DR Congo", "Qatar v Switzerland"}:
        if market != "Result":
            return False
    if market == "Result" and odds > 15.0:
        return False
    if selection in {"Curacao", "Cabo Verde"}:
        return False
    if market == "Result" and odds >= 5.0:
        return f"{match}|{selection}" in MODEL_QUALITY_NOTES
    return True


def has_curated_support(match: str, market: str, selection: str) -> bool:
    key = f"{match}|{selection}"
    if market == "Team Total Goals Over/Under":
        return True
    if key in MODEL_QUALITY_NOTES:
        return True
    if key in CURATED_TOTALS:
        return True
    if market == "Result" and key in MODEL_QUALITY_NOTES:
        return True
    return False


def _poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)
