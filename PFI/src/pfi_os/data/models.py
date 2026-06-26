from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BarDataRequest:
    symbol: str
    market: str = "US"
    interval: str = "1d"
    start: date | str | None = None
    end: date | str | None = None
    adjustment: str = "none"


REQUIRED_BAR_COLUMNS = ["datetime", "open", "high", "low", "close", "volume"]
