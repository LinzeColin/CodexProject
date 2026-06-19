from __future__ import annotations

import importlib.util
import json
import socket
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.cache import write_ohlcv_cache
from qbvs.backtest import normalize_ohlcv


@dataclass(frozen=True)
class MoomooProbeResult:
    host: str
    port: int
    socket_reachable: bool
    futu_sdk_available: bool
    moomoo_sdk_available: bool
    ready_for_fetch: bool
    checked_at: str
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def probe_moomoo_opend(host: str = "127.0.0.1", port: int = 11111, timeout: float = 2.0) -> MoomooProbeResult:
    errors: list[str] = []
    socket_reachable = False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            socket_reachable = True
    except Exception as exc:
        errors.append(f"opend_socket_unreachable: {exc}")
    futu_available = importlib.util.find_spec("futu") is not None
    moomoo_available = importlib.util.find_spec("moomoo") is not None
    if not futu_available and not moomoo_available:
        errors.append("moomoo_or_futu_sdk_not_installed")
    return MoomooProbeResult(
        host=host,
        port=port,
        socket_reachable=socket_reachable,
        futu_sdk_available=futu_available,
        moomoo_sdk_available=moomoo_available,
        ready_for_fetch=socket_reachable and (futu_available or moomoo_available),
        checked_at=datetime.now().isoformat(timespec="seconds"),
        errors=errors,
    )


def write_probe_report(result: MoomooProbeResult, output: Path | str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def cache_alipay_fund_nav(
    csv_path: Path | str,
    cache_dir: Path | str,
    symbol: str,
    fund_name: str = "",
    date_col: str = "date",
    nav_col: str = "nav",
    market: str = "ALIPAY_FUND",
    currency: str = "CNY",
    timezone: str = "Asia/Shanghai",
) -> dict[str, object]:
    frame = normalize_alipay_fund_nav_csv(csv_path, symbol=symbol, market=market, date_col=date_col, nav_col=nav_col)
    metadata = write_ohlcv_cache(
        frame,
        cache_dir,
        symbol=symbol,
        market=market,
        source="alipay_fund_nav_csv",
        source_path=str(Path(csv_path).resolve()),
        asset_class="FUND",
        tradability="CONFIRMED_SOURCE_NEEDS_ORDER_RULE_CHECK",
        currency=currency,
        timezone=timezone,
    )
    if fund_name:
        meta_path = Path(str(metadata["metadata_path"]))
        enriched = json.loads(meta_path.read_text(encoding="utf-8"))
        enriched["fund_name"] = fund_name
        meta_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
        metadata["fund_name"] = fund_name
    return metadata


def normalize_alipay_fund_nav_csv(
    csv_path: Path | str,
    symbol: str,
    market: str = "ALIPAY_FUND",
    date_col: str = "date",
    nav_col: str = "nav",
) -> pd.DataFrame:
    raw = pd.read_csv(csv_path)
    missing = [col for col in [date_col, nav_col] if col not in raw.columns]
    if missing:
        raise ValueError(f"Alipay NAV CSV missing columns: {missing}")
    close = pd.to_numeric(raw[nav_col], errors="coerce")
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(raw[date_col], errors="coerce"),
            "symbol": symbol,
            "market": market,
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 0.0,
        }
    )
    frame = frame.dropna(subset=["datetime", "close"])
    return normalize_ohlcv(frame, symbol=symbol, market=market)


def cache_moomoo_history(
    symbol: str,
    market: str,
    cache_dir: Path | str,
    start: str,
    end: str,
    host: str = "127.0.0.1",
    port: int = 11111,
    ktype: str = "K_DAY",
    autype: str = "QFQ",
    asset_class: str = "",
    tradability: str = "CONFIRMED_SOURCE_NEEDS_ACCOUNT_PERMISSION_CHECK",
    currency: str = "",
    timezone: str = "",
) -> dict[str, object]:
    probe = probe_moomoo_opend(host=host, port=port)
    if not probe.ready_for_fetch:
        raise RuntimeError(f"Moomoo/OpenD not ready: {probe.errors}")
    futu = _load_futu_module()
    quote_ctx = futu.OpenQuoteContext(host=host, port=port)
    try:
        ret, data, page_req_key = quote_ctx.request_history_kline(
            symbol,
            start=start,
            end=end,
            ktype=getattr(futu.KLType, ktype, ktype),
            autype=getattr(futu.AuType, autype, autype),
            max_count=1000,
        )
        frames = []
        if ret != futu.RET_OK:
            raise RuntimeError(f"request_history_kline failed: {data}")
        frames.append(data)
        while page_req_key:
            ret, data, page_req_key = quote_ctx.request_history_kline(
                symbol,
                start=start,
                end=end,
                ktype=getattr(futu.KLType, ktype, ktype),
                autype=getattr(futu.AuType, autype, autype),
                max_count=1000,
                page_req_key=page_req_key,
            )
            if ret != futu.RET_OK:
                raise RuntimeError(f"request_history_kline pagination failed: {data}")
            frames.append(data)
    finally:
        quote_ctx.close()
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if raw.empty:
        raise RuntimeError(f"Moomoo/OpenD returned empty history for {symbol}")
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(raw["time_key"]),
            "symbol": symbol,
            "market": market,
            "open": raw["open"],
            "high": raw["high"],
            "low": raw["low"],
            "close": raw["close"],
            "volume": raw.get("volume", 0.0),
        }
    )
    return write_ohlcv_cache(
        frame,
        cache_dir,
        symbol=symbol,
        market=market,
        source="moomoo_opend",
        source_path=f"{host}:{port}",
        asset_class=asset_class,
        tradability=tradability,
        currency=currency,
        timezone=timezone,
    )


def write_tradable_universe_template(output: Path | str, kind: str = "mixed") -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _template_rows(kind)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _template_rows(kind: str) -> list[dict[str, str]]:
    base_cols = {
        "symbol": "",
        "market": "",
        "asset_class": "",
        "tradability": "",
        "currency": "",
        "timezone": "",
        "source": "",
        "source_symbol": "",
        "notes": "",
    }
    if kind == "moomoo":
        rows = [
            {
                **base_cols,
                "symbol": "US.SPY",
                "market": "US",
                "asset_class": "ETF",
                "tradability": "LIKELY_TRADABLE_NEEDS_ACCOUNT_PERMISSION_CHECK",
                "currency": "USD",
                "timezone": "America/New_York",
                "source": "moomoo_opend",
                "source_symbol": "US.SPY",
                "notes": "example only; replace with your tradable symbol",
            }
        ]
    elif kind == "alipay":
        rows = [
            {
                **base_cols,
                "symbol": "ALIPAY_FUND_CODE",
                "market": "ALIPAY_FUND",
                "asset_class": "FUND",
                "tradability": "CONFIRMED_SOURCE_NEEDS_ORDER_RULE_CHECK",
                "currency": "CNY",
                "timezone": "Asia/Shanghai",
                "source": "alipay_fund_nav_csv",
                "source_symbol": "fund code from Alipay",
                "notes": "CSV needs date and nav columns",
            }
        ]
    else:
        rows = _template_rows("moomoo") + _template_rows("alipay")
    return rows


def _load_futu_module():
    try:
        import futu  # type: ignore

        return futu
    except Exception:
        import moomoo as futu  # type: ignore

        return futu
