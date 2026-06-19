import re
from typing import Dict, List, Tuple

from .odds import is_price_like_text, is_suspended_price, parse_decimal_odds

SKIP_LINES = {
    "|",
    "Tab.com.au",
    "Bet live",
    "Normal Time",
    "Show TAB Prop Number",
}
HEADER_LINES = {
    "Result",
    "Double Chance",
    "Handicap",
    "Correct Score",
    "Total Goals Over/Under",
    "Team Total Goals Over/Under",
    "Both Teams to Score",
    "Result Over/Under Double",
    "Draw No Bet",
    "Half/Full Double",
    "1st Half Result",
    "Team To Score",
}


def parse_market_pairs(section: str, market_name: str = "") -> Dict[str, float]:
    lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip()
        and line.strip() not in SKIP_LINES
        and not line.strip().startswith("|WC")
    ]
    pairs: List[Tuple[str, float]] = []
    i = 0
    while i < len(lines):
        if i + 2 < len(lines) and _is_price(lines[i + 1]) and lines[i + 1] == lines[i + 2]:
            _append_pair(pairs, lines[i], lines[i + 1])
            i += 3
        elif i + 1 < len(lines) and _is_price(lines[i + 1]):
            _append_pair(pairs, lines[i], lines[i + 1])
            i += 2
        else:
            i += 1

    result: Dict[str, float] = {}
    for name, odds in pairs:
        if name in HEADER_LINES and not (market_name == "Both Teams to Score" and name == "Both Teams to Score"):
            continue
        if _looks_like_metadata(name):
            continue
        result[name] = odds
    return result


def _append_pair(pairs: List[Tuple[str, float]], name: str, value: str) -> None:
    odds = parse_decimal_odds(value)
    if odds is None:
        return
    pairs.append((name, odds))


def _is_price(value: str) -> bool:
    return parse_decimal_odds(value) is not None or is_suspended_price(value)


def invalid_market_price_rows(section: str, market_name: str = "") -> List[str]:
    lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip()
        and line.strip() not in SKIP_LINES
        and not line.strip().startswith("|WC")
    ]
    invalid = []
    for index, value in enumerate(lines[1:], start=1):
        if not is_price_like_text(value):
            continue
        if is_suspended_price(value):
            continue
        selection = lines[index - 1]
        if selection in HEADER_LINES and not (market_name == "Both Teams to Score" and selection == "Both Teams to Score"):
            continue
        if _looks_like_metadata(selection):
            continue
        if parse_decimal_odds(value) is None:
            invalid.append(f"{selection}={value}")
    return invalid


def _looks_like_metadata(value: str) -> bool:
    return bool(re.search(r"\d{1,2}:\d{2}|Fri|Sat|Sun|Mon|Tue|Wed|Thu|Venue =|Normal Time", value))
