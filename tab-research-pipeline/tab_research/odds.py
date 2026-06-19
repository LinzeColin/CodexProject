from __future__ import annotations

import math
import re
from typing import Iterable, List


DECIMAL_ODDS_RE = re.compile(r"^\d+(?:\.\d+)?$")
PRICE_LIKE_RE = re.compile(r"^(?:\d+(?:\.\d+)?|nan|inf|infinity|susp)$", re.IGNORECASE)


def parse_decimal_odds(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        if isinstance(value, str):
            text = value.strip()
            if not DECIMAL_ODDS_RE.match(text):
                return None
            odds = float(text)
        else:
            odds = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(odds) or odds <= 1.0:
        return None
    return odds


def valid_decimal_odds(value) -> bool:
    return parse_decimal_odds(value) is not None


def is_suspended_price(value) -> bool:
    return isinstance(value, str) and value.strip().upper() == "SUSP"


def is_decimal_price_text(value: str) -> bool:
    return parse_decimal_odds(value) is not None


def is_price_like_text(value: str) -> bool:
    return bool(PRICE_LIKE_RE.match(str(value).strip()))


def require_decimal_odds(value, context: str = "odds") -> float:
    odds = parse_decimal_odds(value)
    if odds is None:
        raise ValueError(f"{context} has invalid decimal odds: {value!r}")
    return odds


def validate_rows_decimal_odds(rows: Iterable[dict], label_key: str = "selection", odds_key: str = "odds") -> List[str]:
    errors = []
    for index, row in enumerate(rows):
        label = str(row.get(label_key) or row.get("team") or f"row {index + 1}").strip() or f"row {index + 1}"
        if not valid_decimal_odds(row.get(odds_key)):
            errors.append(label)
    return errors


def no_vig_from_decimal_odds(odds: Iterable[float], context: str = "market") -> List[float]:
    parsed = [require_decimal_odds(value, f"{context}[{index}]") for index, value in enumerate(odds)]
    inv = [1 / value for value in parsed]
    total = sum(inv)
    if total <= 0 or not math.isfinite(total):
        raise ValueError(f"{context} has invalid implied probability total")
    return [value / total for value in inv]

