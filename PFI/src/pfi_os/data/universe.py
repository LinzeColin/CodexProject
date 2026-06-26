from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    market: str
    name: str = ""
    currency: str = ""
    sector: str = ""


@dataclass(frozen=True)
class Universe:
    universe_id: str
    instruments: tuple[Instrument, ...]

    @classmethod
    def from_symbols(cls, universe_id: str, symbols: list[str], market: str = "US") -> "Universe":
        return cls(universe_id=universe_id, instruments=tuple(Instrument(symbol=s, market=market) for s in symbols))

    @property
    def symbols(self) -> list[str]:
        return [instrument.symbol for instrument in self.instruments]


DEFAULT_US_ETF_UNIVERSE = Universe.from_symbols("us_etf_core", ["SPY", "QQQ", "TLT", "GLD"], market="US")
