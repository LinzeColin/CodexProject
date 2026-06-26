from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.symbol_aliases import normalize_moomoo_source_symbol


SEED_SCHEMA_VERSION = "qbvs-tradable-universe-seed-v1"


US_ETFS = """
SPY QQQ DIA IWM VTI VOO IVV RSP SCHD VIG VYM IWB IWF IWD IVE IVW MDY IJH IJR IJS
EFA EEM VEA VWO ACWI VT IEFA IEMG HYG LQD TLT IEF SHY BIL TIP MUB BND AGG VCIT VCSH
VNQ XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH SOXX XBI IBB ARKK BOTZ ROBO HACK
ICLN TAN PBW XME GDX GDXJ SLV GLD IAU USO UNG DBA DBC PDBC UUP FXE FXY FXI KWEB MCHI ASHR CQQQ
"""

US_STOCKS = """
AAPL MSFT NVDA AMZN META GOOGL GOOG TSLA BRK-B JPM V MA UNH HD PG COST NFLX ADBE CRM ORCL
CSCO AVGO AMD INTC QCOM TXN AMAT MU IBM NOW PANW SHOP PLTR SNOW UBER ABNB BKNG DIS CMCSA PEP
KO MCD NKE SBUX WMT TGT LOW CAT DE BA GE RTX LMT XOM CVX COP SLB NEE ENPH FSLR BAC GS MS C WFC SCHW PYPL SQ COIN
"""

HK_SYMBOLS = """
0700.HK 9988.HK 3690.HK 9618.HK 1810.HK 9999.HK 1024.HK 1299.HK 2318.HK 0939.HK
1398.HK 3988.HK 0005.HK 0388.HK 0883.HK 0857.HK 0941.HK 0762.HK 2020.HK 1211.HK
2015.HK 0175.HK 2333.HK 2382.HK 2269.HK 6618.HK 9888.HK 0968.HK 2800.HK 2822.HK
"""

CN_ETFS = """
510300.SS 510500.SS 512100.SS 159915.SZ 159949.SZ 588000.SS 588080.SS 512760.SS 512480.SS 512880.SS
512660.SS 515790.SS 515030.SS 516160.SS 515050.SS 515220.SS 159995.SZ 159869.SZ 159920.SZ 513100.SS
513500.SS 513030.SS 513050.SS 513180.SS 513330.SS 518880.SS 511010.SS 511220.SS 510880.SS 510050.SS
510180.SS 159919.SZ 159901.SZ 159922.SZ 159928.SZ 159934.SZ 512690.SS 512800.SS 515700.SS 516950.SS
"""


def build_seed_universe(output: Path | str, limit: int = 220) -> tuple[Path, Path]:
    rows = _seed_rows()[:limit]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    summary = validate_seed_universe(path, min_symbols=min(200, len(rows)))
    summary_path = path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, summary_path


def validate_seed_universe(path: Path | str, min_symbols: int = 200) -> dict[str, Any]:
    frame = pd.read_csv(path)
    errors: list[str] = []
    warnings: list[str] = []
    required = {
        "symbol",
        "market",
        "asset_class",
        "tradability",
        "currency",
        "timezone",
        "source",
        "source_symbol",
        "yahoo_symbol",
        "notes",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        errors.append(f"missing columns: {missing}")
    if len(frame) < min_symbols:
        errors.append(f"symbol_count {len(frame)} below minimum {min_symbols}")
    if "symbol" in frame.columns:
        duplicates = frame["symbol"][frame["symbol"].duplicated()].tolist()
        if duplicates:
            errors.append(f"duplicate symbols: {duplicates[:10]}")
    market_count = int(frame["market"].nunique()) if "market" in frame.columns else 0
    asset_count = int(frame["asset_class"].nunique()) if "asset_class" in frame.columns else 0
    if market_count < 4:
        warnings.append("market_coverage_below_4")
    if asset_count < 5:
        warnings.append("asset_class_coverage_below_5")
    source_counts = frame["source"].value_counts().to_dict() if "source" in frame.columns else {}
    return {
        "schema_version": SEED_SCHEMA_VERSION,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "path": str(path),
        "symbols": int(len(frame)),
        "markets": market_count,
        "asset_classes": asset_count,
        "source_counts": {str(k): int(v) for k, v in source_counts.items()},
        "market_counts": {str(k): int(v) for k, v in frame["market"].value_counts().to_dict().items()} if "market" in frame.columns else {},
        "asset_class_counts": {str(k): int(v) for k, v in frame["asset_class"].value_counts().to_dict().items()} if "asset_class" in frame.columns else {},
    }


def build_seed_cache_plan(
    universe_path: Path | str,
    output_dir: Path | str,
    start: str = "2000-01-01",
    end: str = "2026-06-05",
    cache_dir: str = "data_cache_seed",
    python_executable: str = "python3",
    limit: int | None = None,
) -> dict[str, Path]:
    frame = pd.read_csv(universe_path)
    selected = frame.head(limit) if limit else frame
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    commands = []
    for _, row in selected.iterrows():
        symbol = str(row["symbol"])
        source_symbol = str(row.get("source_symbol") or symbol)
        market = str(row.get("market") or "")
        command = (
            f"PYTHONPATH=. {python_executable} -m qbvs.cli cache-moomoo-history "
            f"--symbol {source_symbol} --market {market} --start {start} --end {end} --cache-dir {cache_dir}"
        )
        commands.append(command)
        rows.append(
            {
                "symbol": symbol,
                "source_symbol": source_symbol,
                "yahoo_symbol": str(row.get("yahoo_symbol") or symbol),
                "market": market,
                "asset_class": str(row.get("asset_class") or ""),
                "tradability": str(row.get("tradability") or ""),
                "command": command,
                "status": "pending",
            }
        )
    plan_path = output / "seed_cache_plan.csv"
    command_path = output / "seed_cache_commands.sh"
    summary_path = output / "seed_cache_plan.summary.json"
    pd.DataFrame(rows).to_csv(plan_path, index=False)
    command_path.write_text("\n".join(commands) + ("\n" if commands else ""), encoding="utf-8")
    summary = {
        "schema_version": SEED_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "universe_path": str(universe_path),
        "output_dir": str(output),
        "provider": "moomoo_opend",
        "starts_background_processes": False,
        "commands": len(commands),
        "start": start,
        "end": end,
        "cache_dir": cache_dir,
        "warning": "Commands require Moomoo/OpenD readiness and account/data permissions; this builder does not fetch data.",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"plan": plan_path, "commands": command_path, "summary": summary_path}


def build_seed_yahoo_universe(
    universe_path: Path | str,
    output: Path | str,
    limit: int | None = None,
) -> tuple[Path, Path]:
    frame = pd.read_csv(universe_path)
    rows = []
    for _, row in frame.iterrows():
        yahoo_symbol = str(row.get("yahoo_symbol") or "").strip()
        if not yahoo_symbol or yahoo_symbol.lower() == "nan":
            continue
        rows.append(
            {
                "symbol": yahoo_symbol,
                "market": str(row.get("market") or "YAHOO"),
                "source_symbol": str(row.get("source_symbol") or row.get("symbol") or yahoo_symbol),
                "original_symbol": str(row.get("symbol") or yahoo_symbol),
                "asset_class": str(row.get("asset_class") or ""),
                "tradability": str(row.get("tradability") or ""),
                "currency": str(row.get("currency") or ""),
                "timezone": str(row.get("timezone") or ""),
                "source": "yahoo_public_chart",
                "notes": "Public historical data fallback for validation only; not proof of account tradability.",
            }
        )
    if limit is not None:
        rows = rows[:limit]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    summary = {
        "schema_version": SEED_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_universe_path": str(universe_path),
        "path": str(path),
        "symbols": len(rows),
        "provider": "yahoo_public_chart",
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "starts_background_processes": False,
        "boundary": "public historical data fallback; use Moomoo/OpenD or Alipay fund NAV for final tradability checks",
    }
    summary_path = path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, summary_path


def build_seed_yahoo_cache_plan(
    yahoo_universe_path: Path | str,
    output_dir: Path | str,
    cache_dir: str = "data_cache_seed_yahoo",
    python_executable: str = "python3",
    limit: int | None = None,
    allow_insecure_ssl: bool = False,
) -> dict[str, Path]:
    frame = pd.read_csv(yahoo_universe_path)
    selected = frame.head(limit) if limit else frame
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "yahoo_seed_cache_plan.csv"
    command_path = output / "yahoo_seed_cache_commands.sh"
    summary_path = output / "yahoo_seed_cache_plan.summary.json"
    plan = []
    command = (
        f"PYTHONPATH=. {python_executable} -m qbvs.cli cache-yahoo "
        f"--universe {yahoo_universe_path} --cache-dir {cache_dir}"
    )
    if limit is not None:
        command += f" --limit {limit}"
    if allow_insecure_ssl:
        command += " --allow-insecure-ssl"
    for _, row in selected.iterrows():
        plan.append(
            {
                "symbol": str(row["symbol"]),
                "market": str(row.get("market") or "YAHOO"),
                "asset_class": str(row.get("asset_class") or ""),
                "tradability": str(row.get("tradability") or ""),
                "cache_dir": cache_dir,
                "provider": "yahoo_public_chart",
                "status": "pending",
            }
        )
    pd.DataFrame(plan).to_csv(plan_path, index=False)
    command_path.write_text(command + "\n", encoding="utf-8")
    summary = {
        "schema_version": SEED_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "universe_path": str(yahoo_universe_path),
        "output_dir": str(output),
        "provider": "yahoo_public_chart",
        "starts_background_processes": False,
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "commands": 1,
        "symbols": int(len(plan)),
        "cache_dir": cache_dir,
        "warning": "Yahoo public data is a fallback validation source, not account-level tradability confirmation.",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"plan": plan_path, "commands": command_path, "summary": summary_path}


def sample_universe_stratified(
    universe_path: Path | str,
    output: Path | str,
    max_symbols: int,
    seed: int = 42,
    group_cols: tuple[str, ...] = ("market", "asset_class"),
) -> tuple[Path, Path]:
    if max_symbols <= 0:
        raise ValueError("max_symbols must be positive")
    frame = pd.read_csv(universe_path)
    available_group_cols = [col for col in group_cols if col in frame.columns]
    if not available_group_cols:
        sampled = frame.sample(n=min(max_symbols, len(frame)), random_state=seed).reset_index(drop=True)
    else:
        groups = list(frame.groupby(available_group_cols, dropna=False, sort=True))
        per_group = max(1, int((max_symbols + max(1, len(groups)) - 1) / max(1, len(groups))))
        chunks = []
        for idx, (_, group) in enumerate(groups):
            chunks.append(group.sample(n=min(per_group, len(group)), random_state=seed + idx))
        sampled = pd.concat(chunks, ignore_index=True) if chunks else frame.head(0).copy()
        if len(sampled) > max_symbols:
            sampled = sampled.sample(n=max_symbols, random_state=seed + 10_000).reset_index(drop=True)
        elif len(sampled) < max_symbols:
            existing = set(sampled["symbol"]) if "symbol" in sampled.columns else set()
            remainder = frame[~frame["symbol"].isin(existing)] if "symbol" in frame.columns else frame.drop(sampled.index, errors="ignore")
            needed = min(max_symbols - len(sampled), len(remainder))
            if needed > 0:
                sampled = pd.concat([sampled, remainder.sample(n=needed, random_state=seed + 20_000)], ignore_index=True)
        sort_cols = [col for col in ["market", "asset_class", "symbol"] if col in sampled.columns]
        if sort_cols:
            sampled = sampled.sort_values(sort_cols).reset_index(drop=True)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_csv(path, index=False)
    summary = {
        "schema_version": SEED_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_universe_path": str(universe_path),
        "path": str(path),
        "source_symbols": int(len(frame)),
        "sampled_symbols": int(len(sampled)),
        "seed": int(seed),
        "group_cols": list(group_cols),
        "market_counts": {str(k): int(v) for k, v in sampled["market"].value_counts().to_dict().items()} if "market" in sampled.columns else {},
        "asset_class_counts": {str(k): int(v) for k, v in sampled["asset_class"].value_counts().to_dict().items()} if "asset_class" in sampled.columns else {},
        "starts_background_processes": False,
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
    }
    summary_path = path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, summary_path


def _seed_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for symbol in _tokens(US_ETFS):
        asset_class = _us_etf_asset_class(symbol)
        rows.append(_row(symbol, "US_ETF", asset_class, "USD", "America/New_York", "moomoo_opend", _moomoo_us(symbol, "US_ETF"), symbol))
    for symbol in _tokens(US_STOCKS):
        rows.append(_row(symbol, "US_STOCK", "STOCK", "USD", "America/New_York", "moomoo_opend", _moomoo_us(symbol, "US_STOCK"), symbol))
    for symbol in _tokens(HK_SYMBOLS):
        rows.append(_row(symbol, "HK", "STOCK" if symbol not in {"2800.HK", "2822.HK"} else "ETF", "HKD", "Asia/Hong_Kong", "moomoo_opend", _moomoo_hk(symbol), symbol))
    for symbol in _tokens(CN_ETFS):
        rows.append(_row(symbol, "CN_ETF", _cn_asset_class(symbol), "CNY", "Asia/Shanghai", "moomoo_opend", _moomoo_cn(symbol), symbol))
    deduped = []
    seen = set()
    for row in rows:
        if row["symbol"] in seen:
            continue
        seen.add(row["symbol"])
        deduped.append(row)
    return deduped


def _row(
    symbol: str,
    market: str,
    asset_class: str,
    currency: str,
    timezone: str,
    source: str,
    source_symbol: str,
    yahoo_symbol: str,
) -> dict[str, str]:
    return {
        "symbol": symbol,
        "market": market,
        "asset_class": asset_class,
        "tradability": "LIKELY_TRADABLE_NEEDS_ACCOUNT_PERMISSION_CHECK",
        "currency": currency,
        "timezone": timezone,
        "source": source,
        "source_symbol": source_symbol,
        "yahoo_symbol": yahoo_symbol,
        "notes": "Seed candidate for validation; confirm account permission, liquidity, fees, and data availability before final use.",
    }


def _tokens(text: str) -> list[str]:
    return [item.strip() for item in text.split() if item.strip()]


def _moomoo_hk(symbol: str) -> str:
    return f"HK.{symbol.split('.')[0]}"


def _moomoo_cn(symbol: str) -> str:
    code, suffix = symbol.split(".")
    prefix = "SH" if suffix == "SS" else "SZ"
    return f"{prefix}.{code}"


def _moomoo_us(symbol: str, market: str) -> str:
    return normalize_moomoo_source_symbol(symbol=symbol, market=market, source_symbol=f"US.{symbol}").normalized_source_symbol


def _us_etf_asset_class(symbol: str) -> str:
    if symbol in {"GLD", "IAU", "SLV", "GDX", "GDXJ", "USO", "UNG", "DBA", "DBC", "PDBC"}:
        return "COMMODITY"
    if symbol in {"TLT", "IEF", "SHY", "BIL", "TIP", "MUB", "BND", "AGG", "VCIT", "VCSH", "HYG", "LQD"}:
        return "BOND"
    if symbol in {"UUP", "FXE", "FXY"}:
        return "FX"
    return "ETF"


def _cn_asset_class(symbol: str) -> str:
    if symbol.startswith("511"):
        return "BOND"
    if symbol == "518880.SS":
        return "COMMODITY"
    return "ETF"
