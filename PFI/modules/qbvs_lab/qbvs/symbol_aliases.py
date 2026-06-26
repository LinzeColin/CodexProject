from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolAliasDecision:
    symbol: str
    market: str
    original_source_symbol: str
    normalized_source_symbol: str
    provider: str
    rule_id: str
    requires_single_symbol_probe: bool
    evidence_note: str


def normalize_moomoo_source_symbol(symbol: str, market: str, source_symbol: str | None = None) -> SymbolAliasDecision:
    clean_symbol = str(symbol or "").strip()
    clean_market = str(market or "").strip()
    original_source = str(source_symbol or "").strip()
    if not original_source or original_source.lower() == "nan":
        original_source = _default_moomoo_source_symbol(clean_symbol, clean_market)
    elif clean_market in {"US_STOCK", "US_ETF"} and not original_source.startswith("US."):
        original_source = f"US.{original_source}"

    normalized = original_source
    rule_id = "no_change"
    requires_probe = False
    note = "No provider-specific alias normalization was required."

    if clean_market == "US_STOCK" and original_source.startswith("US.") and "-" in original_source.split("US.", 1)[1]:
        normalized = "US." + original_source.split("US.", 1)[1].replace("-", ".")
        rule_id = "us_class_share_dash_to_dot"
        requires_probe = True
        note = (
            "Moomoo public pages display class-share symbols such as BRK.B-US, while the OpenAPI "
            "uses US-prefixed codes such as US.AAPL. Use the dot-form candidate for OpenD and "
            "confirm with a single-symbol probe before batch retry."
        )

    return SymbolAliasDecision(
        symbol=clean_symbol,
        market=clean_market,
        original_source_symbol=original_source,
        normalized_source_symbol=normalized,
        provider="moomoo_opend",
        rule_id=rule_id,
        requires_single_symbol_probe=requires_probe,
        evidence_note=note,
    )


def _default_moomoo_source_symbol(symbol: str, market: str) -> str:
    if market in {"US_STOCK", "US_ETF"}:
        return f"US.{symbol}"
    if market == "HK":
        return f"HK.{symbol.split('.')[0]}"
    if market == "CN_ETF" and "." in symbol:
        code, suffix = symbol.split(".", 1)
        prefix = "SH" if suffix == "SS" else "SZ"
        return f"{prefix}.{code}"
    return symbol
