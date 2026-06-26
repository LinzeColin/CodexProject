from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AShareSymbol:
    raw: str
    code: str
    exchange: str

    @property
    def akshare(self) -> str:
        return self.code

    @property
    def tushare(self) -> str:
        return f"{self.code}.{self.exchange}"

    @property
    def display(self) -> str:
        return f"{self.exchange}{self.code}"


def normalize_a_share_symbol(symbol: str) -> AShareSymbol:
    raw = symbol.strip().upper().replace(" ", "")
    if not raw:
        raise ValueError("A-share symbol cannot be empty.")

    exchange = ""
    code = raw
    if "." in raw:
        code, exchange = raw.split(".", 1)
    elif raw.startswith(("SH", "SZ", "BJ")):
        exchange = raw[:2]
        code = raw[2:]
    elif raw.endswith(("SH", "SZ", "BJ")):
        exchange = raw[-2:]
        code = raw[:-2]

    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"Invalid A-share code: {symbol}")

    if not exchange:
        exchange = infer_a_share_exchange(code)
    if exchange not in {"SH", "SZ", "BJ"}:
        raise ValueError(f"Unsupported A-share exchange: {exchange}")

    return AShareSymbol(raw=symbol, code=code, exchange=exchange)


def infer_a_share_exchange(code: str) -> str:
    if code.startswith(("6", "9")):
        return "SH"
    if code.startswith(("0", "2", "3")):
        return "SZ"
    if code.startswith(("4", "8")):
        return "BJ"
    raise ValueError(f"Cannot infer A-share exchange for code: {code}")
