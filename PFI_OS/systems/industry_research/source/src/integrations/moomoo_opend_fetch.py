from __future__ import annotations

import argparse
import csv
import os
import re
import ssl
import tempfile
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import certifi


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch moomoo OpenD market snapshots")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--watchlist", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--diagnostics", default="")
    parser.add_argument("--skip-opend", action="store_true")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    watchlist = _read_csv(args.watchlist)
    quote_codes = ["" if args.skip_opend else _to_moomoo_code(row) for row in watchlist]
    quote_pairs = [(row, code) for row, code in zip(watchlist, quote_codes) if code]
    no_code_rows = [row for row, code in zip(watchlist, quote_codes) if not code]
    snapshot_by_code, errors_by_code = _fetch_snapshots(args.host, args.port, [code for _, code in quote_pairs])
    missing_rows = [
        row
        for row, code in quote_pairs
        if errors_by_code.get(code) or code not in snapshot_by_code or not _has_valid_snapshot(snapshot_by_code.get(code, {}))
    ]
    direct_fallback_rows = [row for row in no_code_rows if _has_fallback_mapping(row)]
    fallback_by_symbol = _fetch_preferred_fallbacks(missing_rows + direct_fallback_rows)

    rows = []
    for row, quote_code in quote_pairs:
        snapshot = snapshot_by_code.get(quote_code, {})
        error = errors_by_code.get(quote_code, "")
        if not error and quote_code not in snapshot_by_code:
            error = "OpenD returned OK but no snapshot row for this code"
        if not error and not _has_valid_snapshot(snapshot):
            error = "OpenD snapshot row does not contain a usable quote"
        fallback = fallback_by_symbol.get(row["symbol"], {})
        close = _first(snapshot, ["last_price", "price", "cur_price"])
        prev_close = _first(snapshot, ["prev_close_price", "prev_close"])
        change_pct = _first(snapshot, ["change_rate", "rate", "price_spread_rate"])
        if change_pct not in {"", None}:
            change_pct = float(change_pct) / 100
        elif close not in {"", None} and prev_close not in {"", None} and float(prev_close) != 0:
            change_pct = float(close) / float(prev_close) - 1
        if error and fallback:
            close = fallback.get("close", "")
            prev_close = fallback.get("prev_close", "")
            if close not in {"", None} and prev_close not in {"", None} and float(prev_close) != 0:
                change_pct = float(close) / float(prev_close) - 1

        rows.append(
            {
                "date": args.date,
                "symbol": row["symbol"],
                "quote_code": quote_code,
                "name": row["name"],
                "exchange": row["exchange"],
                "asset_class": row["asset_class"],
                "research_group": row["research_group"],
                "close": _clean(close),
                "daily_change_pct": _clean(change_pct),
                "open": _clean(fallback.get("open", _first(snapshot, ["open_price", "open"]))),
                "high": _clean(fallback.get("high", _first(snapshot, ["high_price", "high"]))),
                "low": _clean(fallback.get("low", _first(snapshot, ["low_price", "low"]))),
                "volume": _clean(fallback.get("volume", _first(snapshot, ["volume"]))),
                "turnover": _clean(fallback.get("turnover", _first(snapshot, ["turnover"]))),
                "snapshot_note": _snapshot_note(error, fallback),
                "source_name": "Moomoo OpenD" if not error else fallback.get("source_name", "行情补充未成功"),
                "source_url": "opend://127.0.0.1" if not error else fallback.get("source_url", "fallback://unavailable"),
            }
        )

    known_symbols = {row["symbol"] for row, _ in quote_pairs}
    for row in watchlist:
        if row["symbol"] in known_symbols:
            continue
        fallback = fallback_by_symbol.get(row["symbol"], {})
        if fallback:
            close = fallback.get("close", "")
            prev_close = fallback.get("prev_close", "")
            change_pct = ""
            if close not in {"", None} and prev_close not in {"", None} and float(prev_close) != 0:
                change_pct = float(close) / float(prev_close) - 1
            rows.append(
                {
                    "date": args.date,
                    "symbol": row["symbol"],
                    "quote_code": _display_quote_code(row),
                    "name": row["name"],
                    "exchange": row["exchange"],
                    "asset_class": row["asset_class"],
                    "research_group": row["research_group"],
                    "close": _clean(close),
                    "daily_change_pct": _clean(change_pct),
                    "open": _clean(fallback.get("open", "")),
                    "high": _clean(fallback.get("high", "")),
                    "low": _clean(fallback.get("low", "")),
                    "volume": _clean(fallback.get("volume", "")),
                    "turnover": _clean(fallback.get("turnover", "")),
                    "snapshot_note": f"{_opend_skip_reason(row)}，已用{fallback.get('source_name', '备用行情源')}补充（{fallback.get('source_time', '时间未标注')}）",
                    "source_name": fallback.get("source_name", "行情补充未成功"),
                    "source_url": fallback.get("source_url", "fallback://unavailable"),
                }
            )
            continue
        rows.append(
            {
                "date": args.date,
                "symbol": row["symbol"],
                "quote_code": "",
                "name": row["name"],
                "exchange": row["exchange"],
                "asset_class": row["asset_class"],
                "research_group": row["research_group"],
                "close": "",
                "daily_change_pct": "",
                "open": "",
                "high": "",
                "low": "",
                "volume": "",
                "turnover": "",
                "snapshot_note": "暂不支持该市场代码的 OpenD 快照映射",
                "source_name": "Moomoo Watchlist",
                "source_url": "local://moomoo-watchlist-db",
            }
        )

    _write_csv(args.output, rows)
    diagnostics_output = args.diagnostics or str(Path(args.output).with_name(f"opend_quote_diagnostics_{args.date}.csv"))
    _write_diagnostics_csv(
        diagnostics_output,
        _diagnostic_rows(args.date, quote_pairs, snapshot_by_code, errors_by_code, fallback_by_symbol, watchlist, known_symbols),
    )
    print(f"OK: saved {len(rows)} snapshot rows to {args.output}")


def _fetch_snapshots(host: str, port: int, codes: list[str]) -> tuple[dict[str, dict[str, object]], dict[str, str]]:
    if not codes:
        return {}, {}
    import moomoo as ft

    quote_ctx = ft.OpenQuoteContext(host=host, port=port)
    try:
        snapshots: dict[str, dict[str, object]] = {}
        errors: dict[str, str] = {}
        for group_codes in _group_quote_codes(codes):
            ret, data = quote_ctx.get_market_snapshot(group_codes)
            if ret != ft.RET_OK:
                for code in group_codes:
                    errors[code] = str(data)
                continue
            for row in data.to_dict("records"):
                row_code = row.get("code")
                if row_code:
                    snapshots[str(row_code)] = row
        return snapshots, errors
    finally:
        quote_ctx.close()


def _group_quote_codes(codes: list[str]) -> list[list[str]]:
    grouped: dict[str, list[str]] = {}
    for code in codes:
        prefix = code.split(".", 1)[0] if "." in code else ""
        grouped.setdefault(prefix, []).append(code)
    return [grouped[key] for key in sorted(grouped)]


def _to_moomoo_code(row: dict[str, str]) -> str:
    symbol = row["symbol"]
    exchange = row["exchange"]
    asset_class = row["asset_class"]
    if asset_class == "FX":
        return ""
    if exchange == "US":
        return f"US.{symbol}"
    if exchange in {"SSE", "SZSE"} and not _opend_cn_quotes_enabled():
        return ""
    if exchange == "SSE":
        return f"SH.{symbol}"
    if exchange == "SZSE":
        return f"SZ.{symbol}"
    if exchange == "SEHK":
        return f"HK.{symbol.zfill(5)}"
    return ""


def _display_quote_code(row: dict[str, str]) -> str:
    symbol = row["symbol"]
    exchange = row["exchange"]
    if exchange == "US":
        return f"US.{symbol}"
    if exchange == "SSE":
        return f"SH.{symbol}"
    if exchange == "SZSE":
        return f"SZ.{symbol}"
    if exchange == "SEHK":
        return f"HK.{symbol.zfill(5)}"
    return ""


def _opend_cn_quotes_enabled() -> bool:
    return os.environ.get("AI_RESEARCH_OPEND_CN_QUOTES", "").strip().lower() in {"1", "true", "yes"}


def _has_fallback_mapping(row: dict[str, str]) -> bool:
    return bool(_to_yahoo_symbol(row) or _to_tencent_code(row) or _to_sina_code(row))


def _opend_skip_reason(row: dict[str, str]) -> str:
    if row.get("exchange") in {"SSE", "SZSE"} and not _opend_cn_quotes_enabled():
        return "OpenD A股快照默认跳过以避免当前权限不足导致超时"
    return "暂不支持该市场代码的 OpenD 快照映射"


def _diagnostic_rows(
    as_of: str,
    quote_pairs: list[tuple[dict[str, str], str]],
    snapshot_by_code: dict[str, dict[str, object]],
    errors_by_code: dict[str, str],
    fallback_by_symbol: dict[str, dict[str, object]],
    watchlist: list[dict[str, str]],
    known_symbols: set[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row, quote_code in quote_pairs:
        snapshot = snapshot_by_code.get(quote_code, {})
        error = errors_by_code.get(quote_code, "")
        if not error and quote_code not in snapshot_by_code:
            error = "OpenD returned OK but no snapshot row for this code"
        if not error and not _has_valid_snapshot(snapshot):
            error = "OpenD snapshot row does not contain a usable quote"
        fallback = fallback_by_symbol.get(row["symbol"], {})
        rows.append(
            {
                "date": as_of,
                "symbol": row["symbol"],
                "quote_code": quote_code,
                "name": row["name"],
                "exchange": row["exchange"],
                "asset_class": row["asset_class"],
                "opend_status": "ok" if not error else "failed",
                "opend_error_category": _opend_error_category(error),
                "opend_error": error,
                "fallback_status": "used" if error and fallback else "not_needed" if not error else "unavailable",
                "fallback_source_name": fallback.get("source_name", ""),
                "fallback_source_time": fallback.get("source_time", ""),
                "diagnosis": _diagnosis_text(error, fallback),
            }
        )
    for row in watchlist:
        if row["symbol"] in known_symbols:
            continue
        fallback = fallback_by_symbol.get(row["symbol"], {})
        if fallback:
            rows.append(
                {
                    "date": as_of,
                    "symbol": row["symbol"],
                    "quote_code": _display_quote_code(row),
                    "name": row["name"],
                    "exchange": row["exchange"],
                    "asset_class": row["asset_class"],
                    "opend_status": "skipped",
                    "opend_error_category": "cn_opend_disabled",
                    "opend_error": _opend_skip_reason(row),
                    "fallback_status": "used",
                    "fallback_source_name": fallback.get("source_name", ""),
                    "fallback_source_time": fallback.get("source_time", ""),
                    "diagnosis": f"{_opend_skip_reason(row)}；已使用{fallback.get('source_name', '备用行情源')}补充。",
                }
            )
            continue
        rows.append(
            {
                "date": as_of,
                "symbol": row["symbol"],
                "quote_code": "",
                "name": row["name"],
                "exchange": row["exchange"],
                "asset_class": row["asset_class"],
                "opend_status": "unsupported",
                "opend_error_category": "unsupported_market_or_asset",
                "opend_error": "No OpenD quote code mapping for this row.",
                "fallback_status": "unavailable",
                "fallback_source_name": "",
                "fallback_source_time": "",
                "diagnosis": "当前市场或资产类型未配置 OpenD 快照映射；只用于自选池背景或另接专用数据源。",
            }
        )
    return rows


def _opend_error_category(error: str) -> str:
    text = error.lower()
    if not text:
        return "ok"
    if "no permission" in text or "permission" in text:
        return "quote_permission"
    if "no snapshot row" in text:
        return "empty_snapshot"
    if "does not contain a usable quote" in text:
        return "unusable_snapshot"
    if "unknown" in text or "invalid" in text:
        return "symbol_mapping_or_unavailable"
    return "opend_error"


def _diagnosis_text(error: str, fallback: dict[str, object]) -> str:
    category = _opend_error_category(error)
    if category == "ok":
        return "OpenD 返回可用行情。"
    if category == "quote_permission":
        base = "OpenD 行情权限不足；需要检查对应市场/指数/ETF权限。"
    elif category == "empty_snapshot":
        base = "OpenD 调用成功但未返回该代码快照；优先检查代码映射和该市场订阅范围。"
    elif category == "unusable_snapshot":
        base = "OpenD 返回行缺少可用价格；应保留 fallback 并复查该标的行情权限。"
    elif category == "symbol_mapping_or_unavailable":
        base = "OpenD 可能不支持该代码或代码映射不匹配。"
    else:
        base = "OpenD 返回异常；需要保留原始错误并复查连接、权限和代码。"
    if fallback:
        return f"{base} 已使用{fallback.get('source_name', '备用行情源')}补充。"
    return f"{base} 且备用行情源未返回可用数据。"


def _fetch_preferred_fallbacks(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    fallback: dict[str, dict[str, object]] = {}
    deadline = time.monotonic() + _fallback_budget_seconds()
    for fetcher in [_fetch_yahoo_fallback, _fetch_tencent_fallback, _fetch_sina_fallback]:
        missing = [row for row in rows if row["symbol"] not in fallback]
        if not missing or _deadline_expired(deadline):
            break
        fallback.update(fetcher(missing, deadline))
    return fallback


def _fetch_yahoo_fallback(rows: list[dict[str, str]], deadline: float | None = None) -> dict[str, dict[str, object]]:
    results = {}
    for row in rows:
        if deadline is not None and _deadline_expired(deadline):
            break
        yahoo_symbol = _to_yahoo_symbol(row)
        if not yahoo_symbol:
            continue
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=5d&interval=1d"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=_request_timeout(deadline, default=5), context=_verified_ssl_context()) as response:
                import json

                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            continue
        chart = payload.get("chart", {})
        if chart.get("error") or not chart.get("result"):
            continue
        result = chart["result"][0]
        meta = result.get("meta", {})
        quote = (result.get("indicators", {}).get("quote") or [{}])[0]
        close = meta.get("regularMarketPrice") or _last(quote.get("close", []))
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        if close in {"", None} or prev_close in {"", None}:
            continue
        volume = _last(quote.get("volume", []))
        timestamp = meta.get("regularMarketTime")
        source_time = ""
        if timestamp:
            source_time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        results[row["symbol"]] = {
            "open": _last(quote.get("open", [])),
            "prev_close": prev_close,
            "close": close,
            "high": _last(quote.get("high", [])),
            "low": _last(quote.get("low", [])),
            "volume": volume,
            "turnover": float(volume) * float(close) if volume not in {"", None} else "",
            "source_time": source_time,
            "source_name": "Yahoo Finance (US)",
            "source_url": "https://finance.yahoo.com",
        }
    return results


def _fetch_tencent_fallback(rows: list[dict[str, str]], deadline: float | None = None) -> dict[str, dict[str, object]]:
    if deadline is not None and _deadline_expired(deadline):
        return {}
    code_by_symbol = {}
    for row in rows:
        code = _to_tencent_code(row)
        if code:
            code_by_symbol[row["symbol"]] = code
    if not code_by_symbol:
        return {}
    url = "https://qt.gtimg.cn/q=" + ",".join(code_by_symbol.values())
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=_request_timeout(deadline, default=6), context=_verified_ssl_context()) as response:
            text = response.read().decode("gbk", errors="ignore")
    except Exception:
        return {}
    by_code = {}
    for match in re.finditer(r"v_([a-z]{2}\d+)=\"([^\"]*)\";", text):
        code, payload = match.groups()
        fields = payload.split("~")
        if len(fields) < 38 or not fields[1]:
            continue
        turnover = ""
        try:
            turnover = float(fields[37]) * 10000
        except (TypeError, ValueError):
            pass
        timestamp = fields[30] if len(fields) > 30 else ""
        source_time = ""
        if len(timestamp) == 14:
            source_time = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]} Beijing/Hong Kong"
        by_code[code] = {
            "name": fields[1],
            "open": fields[5],
            "prev_close": fields[4],
            "close": fields[3],
            "high": fields[33] if len(fields) > 33 else "",
            "low": fields[34] if len(fields) > 34 else "",
            "volume": fields[6],
            "turnover": turnover,
            "source_time": source_time,
            "source_name": "Tencent Finance Quote (HK-listed platform)",
            "source_url": "https://qt.gtimg.cn",
        }
    return {symbol: by_code[code] for symbol, code in code_by_symbol.items() if code in by_code}


def _fetch_sina_fallback(rows: list[dict[str, str]], deadline: float | None = None) -> dict[str, dict[str, object]]:
    if deadline is not None and _deadline_expired(deadline):
        return {}
    code_by_symbol = {}
    for row in rows:
        code = _to_sina_code(row)
        if code:
            code_by_symbol[row["symbol"]] = code
    if not code_by_symbol:
        return {}
    url = "https://hq.sinajs.cn/list=" + ",".join(code_by_symbol.values())
    request = urllib.request.Request(
        url,
        headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=_request_timeout(deadline, default=6), context=_verified_ssl_context()) as response:
            text = response.read().decode("gbk", errors="ignore")
    except Exception:
        return {}
    by_code = {}
    for match in re.finditer(r"var hq_str_([a-z]{2}\d+)=\"([^\"]*)\";", text):
        code, payload = match.groups()
        fields = payload.split(",")
        if len(fields) < 32 or not fields[0]:
            continue
        try:
            by_code[code] = {
                "name": fields[0],
                "open": fields[1],
                "prev_close": fields[2],
                "close": fields[3],
                "high": fields[4],
                "low": fields[5],
                "volume": fields[8],
                "turnover": fields[9],
                "source_time": f"{fields[30]} {fields[31]} Beijing",
                "source_name": "Sina Finance Realtime Quote (CN fallback)",
                "source_url": "https://finance.sina.com.cn",
            }
        except (IndexError, ValueError):
            continue
    return {symbol: by_code[code] for symbol, code in code_by_symbol.items() if code in by_code}


def _fallback_budget_seconds() -> float:
    raw = os.environ.get("AI_RESEARCH_QUOTE_FALLBACK_BUDGET_SECONDS", "55")
    try:
        return max(10.0, float(raw))
    except ValueError:
        return 55.0


def _deadline_expired(deadline: float) -> bool:
    return time.monotonic() >= deadline


def _request_timeout(deadline: float | None, *, default: int) -> float:
    if deadline is None:
        return float(default)
    remaining = max(1.0, deadline - time.monotonic())
    return min(float(default), remaining)


def _to_yahoo_symbol(row: dict[str, str]) -> str:
    symbol = row["symbol"]
    exchange = row["exchange"]
    if exchange == "US":
        return symbol
    if exchange == "SSE":
        return f"{symbol}.SS"
    if exchange == "SZSE":
        return f"{symbol}.SZ"
    if exchange == "SEHK":
        return f"{symbol.zfill(4)}.HK"
    return ""


def _to_tencent_code(row: dict[str, str]) -> str:
    symbol = row["symbol"]
    exchange = row["exchange"]
    if exchange == "SSE":
        return f"sh{symbol}"
    if exchange == "SZSE":
        return f"sz{symbol}"
    if exchange == "SEHK":
        return f"hk{symbol.zfill(5)}"
    return ""


def _to_sina_code(row: dict[str, str]) -> str:
    symbol = row["symbol"]
    exchange = row["exchange"]
    if exchange == "SSE":
        return f"sh{symbol}"
    if exchange == "SZSE":
        return f"sz{symbol}"
    return ""


def _snapshot_note(error: str, fallback: dict[str, object]) -> str:
    if not error:
        return "moomoo OpenD 行情快照"
    if fallback:
        return f"OpenD 未返回可用行情，已用{fallback.get('source_name', '备用行情源')}补充（{fallback.get('source_time', '时间未标注')}）"
    return f"OpenD 未返回可用行情，其他行情源暂未返回：{error}"


def _has_valid_snapshot(row: dict[str, object]) -> bool:
    return _first(row, ["last_price", "price", "cur_price"]) not in {"", None}


def _first(row: dict[str, object], keys: list[str]) -> object:
    for key in keys:
        value = row.get(key)
        if value not in {"", None, "--"}:
            return value
    return ""


def _last(values: object) -> object:
    if not isinstance(values, list):
        return ""
    for value in reversed(values):
        if value not in {"", None, "--"}:
            return value
    return ""


def _clean(value: object) -> str:
    if value in {"", None, "--"}:
        return ""
    try:
        return f"{float(value):.8f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _read_csv(path: str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: str, rows: list[dict[str, object]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not _has_actionable_output_rows(rows):
        raise RuntimeError("Refusing to overwrite quote snapshot because the refreshed output has no actionable prices.")
    _backup_existing_snapshot(output)
    fieldnames = [
        "date",
        "symbol",
        "quote_code",
        "name",
        "exchange",
        "asset_class",
        "research_group",
        "close",
        "daily_change_pct",
        "open",
        "high",
        "low",
        "volume",
        "turnover",
        "snapshot_note",
        "source_name",
        "source_url",
    ]
    fd, tmp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, output)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _has_actionable_output_rows(rows: list[dict[str, object]]) -> bool:
    return any(row.get("close") not in {"", None} and row.get("asset_class") in {"Stock", "ETF", "Index"} for row in rows)


def _backup_existing_snapshot(output: Path) -> None:
    if not output.exists():
        return
    backup = output.with_name(output.name + ".last_good")
    if not _snapshot_file_has_actionable_rows(output):
        return
    text = output.read_text(encoding="utf-8-sig")
    backup.write_text(text, encoding="utf-8")


def _snapshot_file_has_actionable_rows(output: Path) -> bool:
    try:
        return _has_actionable_output_rows(_read_csv(str(output)))
    except Exception:
        return False


def _write_diagnostics_csv(path: str, rows: list[dict[str, object]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "symbol",
        "quote_code",
        "name",
        "exchange",
        "asset_class",
        "opend_status",
        "opend_error_category",
        "opend_error",
        "fallback_status",
        "fallback_source_name",
        "fallback_source_time",
        "diagnosis",
    ]
    fd, tmp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, output)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _verified_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


if __name__ == "__main__":
    main()
