from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.backtest import BacktestConfig
from pfi_os.config import PROJECT_ROOT
from pfi_os.research.experiments import ExperimentRunner, analyze_parameter_stability, grid_parameters
from pfi_os.storage import atomic_write_json, atomic_write_text
from pfi_os.strategies import MovingAverageCrossoverStrategy


EVENT_REPLAY_SCHEMA = "PFIOSEventReplayBatchV1"
VECTORIZED_RESEARCH_SCHEMA = "PFIOSVectorizedResearchBatchV1"
OHLCV_COLUMNS = ["datetime", "symbol", "market", "interval", "source", "open", "high", "low", "close", "volume"]
SUPPORTED_STRATEGIES = {"ma_crossover": MovingAverageCrossoverStrategy}
DEFAULT_PARAM_GRID = {"short_window": [2, 3], "long_window": [4, 5]}


def load_event_replay_payload(path: Path | str | None = None, *, project_root: Path | str = PROJECT_ROOT) -> dict[str, Any]:
    replay_path = Path(path).expanduser() if path else Path(project_root).expanduser() / "data" / "replay" / "EventReplay_latest.json"
    if not replay_path.exists():
        return {
            "schema": EVENT_REPLAY_SCHEMA,
            "replay_status": "Empty",
            "records": [],
            "missing_data_log": [{"dataset": "event_replay", "status": "Missing", "message": f"Replay file not found: {replay_path}"}],
        }
    try:
        payload = json.loads(replay_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "schema": EVENT_REPLAY_SCHEMA,
            "replay_status": "Empty",
            "records": [],
            "missing_data_log": [{"dataset": "event_replay", "status": "Blocked", "message": f"Replay file is not valid JSON: {replay_path}"}],
        }
    if not isinstance(payload, dict) or payload.get("schema") != EVENT_REPLAY_SCHEMA:
        return {
            "schema": EVENT_REPLAY_SCHEMA,
            "replay_status": "Empty",
            "records": [],
            "missing_data_log": [{"dataset": "event_replay", "status": "Blocked", "message": f"Replay schema is not {EVENT_REPLAY_SCHEMA}: {replay_path}"}],
        }
    return payload


def event_replay_to_ohlcv(
    payload: dict[str, Any],
    *,
    symbol: str | None = None,
    market: str | None = None,
    interval: str | None = None,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    missing_data_log: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    for record in payload.get("records", []):
        if not isinstance(record, dict):
            continue
        if str(record.get("event_type", "")) != "BarClosed":
            continue
        record_symbol = str(record.get("symbol", "")).upper()
        record_market = str(record.get("market", "")).upper()
        record_interval = str(record.get("interval", ""))
        if symbol and record_symbol != symbol.upper():
            continue
        if market and record_market != market.upper():
            continue
        if interval and record_interval != interval:
            continue
        payload_json = str(record.get("payload_json", "") or "")
        try:
            bar = json.loads(payload_json)
        except json.JSONDecodeError:
            missing_data_log.append(_missing("bar_payload", "Blocked", f"Invalid payload_json for event_id={record.get('event_id', '')}"))
            continue
        required = {"open", "high", "low", "close", "volume"}
        if not isinstance(bar, dict) or required - set(bar):
            missing_data_log.append(_missing("bar_payload", "Blocked", f"Missing OHLCV fields for event_id={record.get('event_id', '')}"))
            continue
        rows.append(
            {
                "datetime": pd.to_datetime(record.get("event_time"), errors="coerce"),
                "symbol": record_symbol,
                "market": record_market,
                "interval": record_interval,
                "source": str(record.get("source", "")),
                "open": _float(bar.get("open")),
                "high": _float(bar.get("high")),
                "low": _float(bar.get("low")),
                "close": _float(bar.get("close")),
                "volume": _float(bar.get("volume")),
                "replay_index": int(record.get("replay_index", 0) or 0),
                "event_id": str(record.get("event_id", "")),
                "cursor_id": str(record.get("cursor_id", "")),
                "quality_status": str(record.get("quality_status", "")),
                "evidence_layer": str(record.get("evidence_layer", "")),
            }
        )
    if not rows:
        missing_data_log.append(_missing("ohlcv", "Missing", "No BarClosed replay records matched the requested filters."))
        return pd.DataFrame(columns=OHLCV_COLUMNS), missing_data_log
    frame = pd.DataFrame(rows)
    frame = frame.dropna(subset=["datetime", "open", "high", "low", "close", "volume"])
    if frame.empty:
        missing_data_log.append(_missing("ohlcv", "Blocked", "All matched replay records had invalid datetime or OHLCV values."))
        return pd.DataFrame(columns=OHLCV_COLUMNS), missing_data_log
    frame["datetime"] = frame["datetime"].dt.tz_localize(None)
    frame = frame.sort_values(["symbol", "datetime", "replay_index", "event_id"]).drop_duplicates(["symbol", "datetime"], keep="last")
    return frame.reset_index(drop=True), missing_data_log


def build_vectorized_research(
    *,
    project_root: Path | str = PROJECT_ROOT,
    replay_path: Path | str | None = None,
    symbol: str | None = None,
    market: str | None = None,
    interval: str | None = None,
    strategy_id: str = "ma_crossover",
    param_grid: dict[str, list[Any]] | None = None,
    initial_cash: float = 100_000.0,
    as_of: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    replay_file = Path(replay_path).expanduser() if replay_path else root / "data" / "replay" / "EventReplay_latest.json"
    payload = load_event_replay_payload(replay_file, project_root=root)
    ohlcv, missing_data_log = event_replay_to_ohlcv(payload, symbol=symbol, market=market, interval=interval)
    missing_data_log.extend([item for item in payload.get("missing_data_log", []) if isinstance(item, dict)])
    available_symbols = sorted(str(item) for item in ohlcv["symbol"].dropna().unique()) if not ohlcv.empty else []
    selected_symbol = (symbol or (available_symbols[0] if available_symbols else "")).upper()
    scan_data = ohlcv[ohlcv["symbol"] == selected_symbol].copy() if selected_symbol else ohlcv
    grid = param_grid or DEFAULT_PARAM_GRID
    strategy_factory = SUPPORTED_STRATEGIES.get(strategy_id)
    scan_summary = pd.DataFrame()
    best_run: dict[str, Any] = {}
    stability = analyze_parameter_stability(scan_summary)
    status = "Pass"
    if strategy_factory is None:
        status = "Blocked"
        missing_data_log.append(_missing("strategy", "Blocked", f"Unsupported vectorized strategy: {strategy_id}"))
    elif scan_data.empty:
        status = "Empty"
    else:
        try:
            with tempfile.TemporaryDirectory(prefix="eva-vectorized-") as tmp:
                summary, _ = ExperimentRunner(output_dir=tmp, config=BacktestConfig(initial_cash=initial_cash))._run_grid_without_persist(
                    scan_data,
                    strategy_factory,
                    grid,
                    experiment_name="vectorized_replay_scan",
                )
            scan_summary = summary.reset_index(drop=True)
            stability = analyze_parameter_stability(scan_summary)
            if not scan_summary.empty:
                best_run = _json_safe(scan_summary.iloc[0].to_dict())
        except Exception as exc:  # fail closed: invalid grids or strategy errors stay research-only.
            status = "Blocked"
            missing_data_log.append(_missing("parameter_scan", "Blocked", str(exc)))
    if status == "Pass" and scan_summary.empty:
        status = "Empty"
    return {
        "schema": VECTORIZED_RESEARCH_SCHEMA,
        "as_of": as_of or datetime.now().date().isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "Vectorized Research",
        "status": status,
        "project_root": "$PFI_HOME",
        "replay_path": _display_path(replay_file, root),
        "replay_status": str(payload.get("replay_status", "")),
        "row_count": int(len(ohlcv)),
        "symbol_count": int(len(available_symbols)),
        "available_symbols": available_symbols,
        "selected_symbol": selected_symbol,
        "first_datetime": _datetime_text(scan_data["datetime"].min()) if not scan_data.empty else "",
        "last_datetime": _datetime_text(scan_data["datetime"].max()) if not scan_data.empty else "",
        "strategy_id": strategy_id,
        "parameter_grid": grid,
        "parameter_run_count": len(grid_parameters(grid)),
        "scan_run_count": int(len(scan_summary)),
        "best_run": best_run,
        "stability": _json_safe(stability.__dict__),
        "missing_data_log": missing_data_log,
        "assumptions": [
            "Vectorized Research Mode reads local EventReplay output only and does not connect to live market data.",
            "Parameter scans are deterministic for the same replay file, strategy, costs, and grid.",
            "Outputs are research evidence only; they are not live trading instructions or broker actions.",
        ],
        "safety_boundary": "Read-only replay-to-DataFrame research adapter; no live orders, broker calls, or market refresh.",
        "summary_rows": [_json_safe(row) for row in scan_summary.head(20).to_dict("records")],
    }


def write_vectorized_research(
    *,
    project_root: Path | str = PROJECT_ROOT,
    output_dir: Path | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "vectorized"
    target.mkdir(parents=True, exist_ok=True)
    payload = build_vectorized_research(project_root=root, **kwargs)
    stamp = _date_stamp(str(payload["as_of"]))
    symbol = _path_part(payload.get("selected_symbol") or "ALL")
    stem = f"VectorizedResearch_{symbol}_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    latest_json = target / "VectorizedResearch_latest.json"
    latest_csv = target / "VectorizedResearch_latest.csv"
    latest_markdown = target / "VectorizedResearch_latest.md"
    outputs = {
        "json": _display_path(json_path, root),
        "csv": _display_path(csv_path, root),
        "markdown": _display_path(markdown_path, root),
        "latest_json": _display_path(latest_json, root),
        "latest_csv": _display_path(latest_csv, root),
        "latest_markdown": _display_path(latest_markdown, root),
    }
    payload["outputs"] = outputs
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    csv_text = pd.DataFrame(payload["summary_rows"]).to_csv(index=False)
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    markdown = vectorized_research_markdown(payload)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    return payload


def vectorized_research_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vectorized Research {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Status: `{payload.get('status', '')}`",
        f"- Replay Status: `{payload.get('replay_status', '')}`",
        f"- Rows: `{payload.get('row_count', 0)}`",
        f"- Symbols: `{', '.join(payload.get('available_symbols', []))}`",
        f"- Selected Symbol: `{payload.get('selected_symbol', '')}`",
        f"- Window: `{payload.get('first_datetime', '')}` -> `{payload.get('last_datetime', '')}`",
        f"- Strategy: `{payload.get('strategy_id', '')}`",
        f"- Parameter Runs: `{payload.get('parameter_run_count', 0)}`",
        f"- Scan Runs: `{payload.get('scan_run_count', 0)}`",
        "",
        "## Best Run",
        "```json",
        json.dumps(payload.get("best_run", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stability",
        "```json",
        json.dumps(payload.get("stability", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Safety Boundary",
        str(payload.get("safety_boundary", "")),
        "",
        "## Missing Data Log",
        _markdown_table(payload.get("missing_data_log", []), ["dataset", "status", "message"]),
    ]
    return "\n".join(lines) + "\n"


def _missing(dataset: str, status: str, message: str) -> dict[str, str]:
    return {"dataset": dataset, "status": status, "message": message}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _datetime_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return str(value)
    return value


def _date_stamp(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else datetime.now().strftime("%Y%m%d")


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _path_part(value: Any) -> str:
    text = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip())
    return text.strip("_") or "ALL"


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_None._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in columns) + " |")
    return "\n".join([header, sep, *body])
