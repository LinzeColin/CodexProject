from __future__ import annotations

from pathlib import Path

from pfi_os.data.providers import AlphaVantageProvider, CSVProvider, MoomooProvider, PolygonProvider, SampleDataProvider, TushareProvider


def make_provider(name: str, csv_path: Path | str | None = None):
    normalized = name.strip().lower().replace(" ", "_")
    if normalized == "sample":
        return SampleDataProvider()
    if normalized == "csv":
        if csv_path is None:
            raise ValueError("CSV provider requires a csv_path.")
        return CSVProvider(csv_path)
    if normalized in {"alpha_vantage", "alphavantage"}:
        if AlphaVantageProvider is None:
            raise RuntimeError("Alpha Vantage provider is unavailable.")
        return AlphaVantageProvider()
    if normalized == "tushare":
        if TushareProvider is None:
            raise RuntimeError("TuShare provider is unavailable.")
        return TushareProvider()
    if normalized == "polygon":
        if PolygonProvider is None:
            raise RuntimeError("Polygon provider is unavailable.")
        return PolygonProvider()
    if normalized in {"moomoo", "futu"}:
        if MoomooProvider is None:
            raise RuntimeError("Moomoo provider is unavailable. Install futu-api and run Moomoo OpenD.")
        return MoomooProvider()

    from pfi_os.data.providers import AKShareProvider, YahooFinanceProvider

    if normalized in {"akshare", "ak_share"}:
        if AKShareProvider is None:
            raise RuntimeError("AKShare provider is unavailable. Install pfi_os[data].")
        return AKShareProvider()
    if normalized in {"yahoo", "yahoo_finance", "yfinance"}:
        if YahooFinanceProvider is None:
            raise RuntimeError("Yahoo Finance provider is unavailable. Install pfi_os[data].")
        return YahooFinanceProvider()
    raise ValueError(f"Unknown provider: {name}")
