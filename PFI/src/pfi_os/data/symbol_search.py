from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import requests


@dataclass(frozen=True)
class SymbolSearchResult:
    symbol: str
    name: str
    market: str
    provider: str

    def label(self) -> str:
        return f"{self.symbol} - {self.name}" if self.name else self.symbol


US_FALLBACK = (
    SymbolSearchResult("AAPL", "Apple Inc.", "US", "fallback"),
    SymbolSearchResult("AMD", "Advanced Micro Devices, Inc.", "US", "fallback"),
    SymbolSearchResult("AMZN", "Amazon.com, Inc.", "US", "fallback"),
    SymbolSearchResult("AVGO", "Broadcom Inc.", "US", "fallback"),
    SymbolSearchResult("AXP", "American Express Company", "US", "fallback"),
)

CN_FALLBACK = (
    SymbolSearchResult("000001", "平安银行", "CN", "fallback"),
    SymbolSearchResult("000100", "TCL科技", "CN", "fallback"),
    SymbolSearchResult("000333", "美的集团", "CN", "fallback"),
    SymbolSearchResult("600000", "浦发银行", "CN", "fallback"),
    SymbolSearchResult("600519", "贵州茅台", "CN", "fallback"),
)

HK_FALLBACK = (
    SymbolSearchResult("0700.HK", "Tencent Holdings Limited", "HK", "fallback"),
    SymbolSearchResult("9988.HK", "Alibaba Group Holding Limited", "HK", "fallback"),
    SymbolSearchResult("0005.HK", "HSBC Holdings plc", "HK", "fallback"),
)


def search_symbols(query: str, market: str, limit: int = 10) -> list[SymbolSearchResult]:
    normalized = query.strip()
    if not normalized:
        return []
    market = market.upper()
    try:
        if market == "CN":
            return _search_cn(normalized, limit)
        if market == "HK":
            return _search_yahoo(normalized, "HK", limit)
        return _search_yahoo(normalized, "US", limit)
    except Exception:
        return _fallback_search(normalized, market, limit)


def _search_yahoo(query: str, market: str, limit: int) -> list[SymbolSearchResult]:
    response = requests.get(
        "https://query1.finance.yahoo.com/v1/finance/search",
        params={"q": query, "quotesCount": limit, "newsCount": 0, "listsCount": 0},
        timeout=10,
        headers={"User-Agent": "PFIOS/1.0"},
    )
    response.raise_for_status()
    rows = []
    for item in response.json().get("quotes", []):
        symbol = str(item.get("symbol", "")).strip()
        if not symbol:
            continue
        if market == "HK" and not symbol.endswith(".HK"):
            continue
        if market == "US" and "." in symbol:
            continue
        rows.append(
            SymbolSearchResult(
                symbol=symbol,
                name=str(item.get("shortname") or item.get("longname") or ""),
                market=market,
                provider="Yahoo Finance",
            )
        )
    return rows[:limit] or _fallback_search(query, market, limit)


def _search_cn(query: str, limit: int) -> list[SymbolSearchResult]:
    import akshare as ak

    frame = ak.stock_info_a_code_name()
    code_col = "code" if "code" in frame.columns else "证券代码"
    name_col = "name" if "name" in frame.columns else "证券简称"
    data = frame[[code_col, name_col]].astype(str)
    mask = data[code_col].str.contains(query, case=False, regex=False) | data[name_col].str.contains(query, case=False, regex=False)
    matches = data[mask].head(limit)
    return [
        SymbolSearchResult(symbol=row[code_col], name=row[name_col], market="CN", provider="AKShare")
        for _, row in matches.iterrows()
    ] or _fallback_search(query, "CN", limit)


def _fallback_search(query: str, market: str, limit: int) -> list[SymbolSearchResult]:
    source = {"CN": CN_FALLBACK, "HK": HK_FALLBACK}.get(market, US_FALLBACK)
    q = query.lower()
    rows = [item for item in source if q in item.symbol.lower() or q in item.name.lower()]
    return rows[:limit]
