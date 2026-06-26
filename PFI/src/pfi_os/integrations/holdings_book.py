from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR, PROJECT_ROOT
from pfi_os.integrations.external_systems import (
    DEFAULT_CONSUMER_HOLDINGS_DIRS,
    DEFAULT_INDUSTRY_REPORT_DIR,
    DEFAULT_PFI_HOLDINGS_DIRS,
    IGNORED_HOLDING_FILENAME_PREFIXES,
    IGNORED_HOLDING_FILENAMES,
    holding_columns,
    holdings_summary,
    load_holding_sources_from_dirs,
)


HOLDINGS_DIR = DATA_DIR / "holdings"
HOLDINGS_IMPORT_DIR = HOLDINGS_DIR / "imports"
HOLDINGS_BOOK_PATH = HOLDINGS_DIR / "HoldingsBook.json"
HOLDINGS_HISTORY_PATH = HOLDINGS_DIR / "HoldingsImportHistory.json"
HOLDINGS_EXPORT_PATH = HOLDINGS_DIR / "HoldingsBook.csv"
HOLDINGS_LOCK_PATH = HOLDINGS_DIR / "HoldingsBook.lock"
LOCAL_ALIPAY_LEDGER_DIR = PROJECT_ROOT / "data" / "private" / "alipay"
SUPPORTED_HOLDING_SUFFIXES = {".csv", ".xlsx", ".xls", ".json"}
MAX_HOLDING_SOURCE_FILE_SIZE_BYTES = 20 * 1024 * 1024
HOLDINGS_HISTORY_SCHEMA = "PFIOSHoldingsImportHistoryV1"
HOLDINGS_HISTORY_COLUMNS = ["synced_at", "raw_row_count", "canonical_row_count", "source_file_count", "book_path", "history_path", "warnings"]


@dataclass(frozen=True)
class HoldingSourceSpec:
    source_system: str
    paths: tuple[Path, ...]
    description: str

    def existing_files(self) -> list[Path]:
        files: list[Path] = []
        seen: set[str] = set()
        for path in self.paths:
            for file_path in _supported_holding_files(path):
                key = str(file_path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                files.append(file_path)
        return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)


@dataclass(frozen=True)
class HoldingSyncResult:
    synced_at: str
    raw_row_count: int
    canonical_row_count: int
    source_file_count: int
    book_path: str
    history_path: str
    warnings: tuple[str, ...]

    def to_row(self) -> dict[str, object]:
        return {
            "synced_at": self.synced_at,
            "raw_row_count": self.raw_row_count,
            "canonical_row_count": self.canonical_row_count,
            "source_file_count": self.source_file_count,
            "book_path": self.book_path,
            "history_path": self.history_path,
            "warnings": "；".join(self.warnings),
        }


def default_holding_source_specs() -> list[HoldingSourceSpec]:
    alipay_current_files = tuple(path / "current_positions.csv" for path in default_alipay_ledger_dirs())
    return [
        HoldingSourceSpec(
            source_system="支付宝持仓账本",
            paths=alipay_current_files,
            description="行研报告自动化生成的支付宝确认持仓文件，只读取 current_positions.csv。",
        ),
        HoldingSourceSpec(
            source_system="行研报告系统上传",
            paths=tuple(_configured_paths("PFI_INDUSTRY_HOLDINGS_DIR", (DEFAULT_INDUSTRY_REPORT_DIR, DATA_DIR / "external" / "industryHoldings"))),
            description="行研报告对话或目录中上传的 CSV/XLSX/JSON 持仓文件。",
        ),
        HoldingSourceSpec(
            source_system="消费行为分析系统",
            paths=tuple(_configured_paths("PFI_CONSUMER_HOLDINGS_DIR", DEFAULT_CONSUMER_HOLDINGS_DIRS)),
            description="消费行为分析系统同步的持仓文件。",
        ),
        HoldingSourceSpec(
            source_system="量化回测系统导入",
            paths=tuple(_configured_paths("PFI_HOLDINGS_DIR", (HOLDINGS_IMPORT_DIR, *DEFAULT_PFI_HOLDINGS_DIRS))),
            description="PFI OS 本地导入目录中的持仓文件。",
        ),
    ]


def default_alipay_ledger_dirs() -> tuple[Path, ...]:
    configured = os.getenv("PFI_ALIPAY_LEDGER_DIR", "").strip()
    if configured:
        return tuple(Path(item).expanduser() for item in configured.split(":") if item.strip())
    return (LOCAL_ALIPAY_LEDGER_DIR,)


def load_holdings_book(path: Path | str = HOLDINGS_BOOK_PATH, missing_ok: bool = True) -> pd.DataFrame:
    book_path = Path(path)
    if not book_path.exists():
        if missing_ok:
            return pd.DataFrame(columns=holding_columns())
        raise FileNotFoundError(book_path)
    payload = _read_json_file(book_path)
    if not isinstance(payload, (dict, list)):
        raise ValueError(f"持仓状态文件格式不正确，已阻止覆盖：{book_path}")
    rows = payload.get("holdings", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"持仓状态文件 holdings 字段格式不正确，已阻止覆盖：{book_path}")
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=holding_columns())
    for column in holding_columns():
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[holding_columns()].copy()
    return _coerce_holding_numbers(frame)


def load_current_holdings() -> pd.DataFrame:
    book = load_holdings_book()
    if not book.empty:
        return book
    return pd.DataFrame(columns=holding_columns())


def scan_holding_sources(specs: list[HoldingSourceSpec] | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in specs or default_holding_source_specs():
        files = spec.existing_files()
        latest = max((file.stat().st_mtime for file in files), default=0)
        rows.append(
            {
                "source_system": spec.source_system,
                "status": "Ready" if files else "NeedsData",
                "file_count": len(files),
                "latest_modified_time": datetime.fromtimestamp(latest).isoformat(timespec="seconds") if latest else "",
                "paths": "\n".join(str(path) for path in spec.paths),
                "description": spec.description,
            }
        )
    return pd.DataFrame(rows)


def sync_holdings_book(
    specs: list[HoldingSourceSpec] | None = None,
    book_path: Path | str = HOLDINGS_BOOK_PATH,
    history_path: Path | str | None = None,
) -> HoldingSyncResult:
    sync_specs = specs or default_holding_source_specs()
    target_book_path = Path(book_path)
    target_history_path = Path(history_path) if history_path is not None else _history_path_for_book(target_book_path)
    lock_path = _lock_path_for_book(target_book_path)
    frames = []
    source_file_count = 0
    warnings: list[str] = []
    for spec in sync_specs:
        source_file_count += len(spec.existing_files())
        frame = load_holding_sources_from_dirs(spec.source_system, list(spec.paths))
        if not frame.empty:
            frames.append(frame)
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=holding_columns())
    if raw.empty:
        warnings.append("未读取到外部确认持仓文件；已保留现有正式持仓，不生成模拟持仓。")
    result = HoldingSyncResult(
        synced_at=datetime.now().isoformat(timespec="seconds"),
        raw_row_count=int(len(raw)),
        canonical_row_count=0,
        source_file_count=int(source_file_count),
        book_path=str(target_book_path),
        history_path=str(target_history_path),
        warnings=tuple(warnings),
    )
    with _file_lock(lock_path):
        existing_locked = load_holdings_book(target_book_path, missing_ok=True)
        manual_locked = existing_locked[existing_locked["source_system"].astype(str).eq("手动录入")].copy() if not existing_locked.empty else pd.DataFrame(columns=holding_columns())
        if raw.empty:
            canonical_locked = canonical_holdings_frame(existing_locked)
            saved_book_path = target_book_path
        else:
            canonical_locked = canonical_holdings_frame(pd.concat([raw, manual_locked], ignore_index=True))
            if canonical_locked.empty:
                warnings.append("读取到源文件，但没有满足正式持仓条件的记录；请检查市值、份额或权重字段。")
            saved_book_path = _save_holdings_book_unlocked(canonical_locked, target_book_path)
        result = HoldingSyncResult(
            synced_at=result.synced_at,
            raw_row_count=result.raw_row_count,
            canonical_row_count=int(len(canonical_locked)),
            source_file_count=result.source_file_count,
            book_path=str(saved_book_path),
            history_path=result.history_path,
            warnings=tuple(warnings),
        )
        _append_holdings_sync_history_unlocked(result, target_history_path)
    return result


def canonical_holdings_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=holding_columns())
    data = frame.copy()
    for column in holding_columns():
        if column not in data.columns:
            data[column] = ""
    data = data[holding_columns()].copy()
    data = _coerce_holding_numbers(data)
    for column in ["symbol", "name", "market", "source_system", "source_file", "updated_at", "source_modified_time"]:
        data[column] = data[column].fillna("").astype(str).str.strip()
    valid_identity = data["symbol"].ne("") | data["name"].ne("")
    valid_amount = data["position_value"].abs().gt(0) | data["quantity"].abs().gt(0) | data["weight"].abs().gt(0)
    data = data[valid_identity & valid_amount].copy()
    if data.empty:
        return pd.DataFrame(columns=holding_columns())
    data["_key"] = data.apply(_holding_key, axis=1)
    data["_updated_ts"] = pd.to_datetime(data["updated_at"], errors="coerce")
    data["_source_ts"] = pd.to_datetime(data["source_modified_time"], errors="coerce")
    data["_latest_ts"] = data["_updated_ts"].fillna(data["_source_ts"]).fillna(pd.Timestamp.min)
    data["_source_priority"] = data["source_system"].map(_source_priority).fillna(50)
    data = data.sort_values(["_key", "_latest_ts", "_source_priority"], ascending=[True, True, True])
    canonical = data.groupby("_key", as_index=False).tail(1).copy()
    canonical = canonical.drop(columns=[column for column in canonical.columns if column.startswith("_")])
    canonical = canonical[holding_columns()].sort_values(["weight", "position_value"], ascending=[False, False]).reset_index(drop=True)
    total = canonical["position_value"].abs().sum()
    if total > 0:
        canonical["weight"] = canonical["position_value"].abs() / total
    return canonical


def upsert_manual_holding(payload: dict[str, Any], book_path: Path | str = HOLDINGS_BOOK_PATH) -> pd.DataFrame:
    now = datetime.now().isoformat(timespec="seconds")
    row = {
        "source_system": "手动录入",
        "source_file": "ManualEntry",
        "symbol": str(payload.get("symbol", "")).strip(),
        "name": str(payload.get("name", "")).strip(),
        "market": str(payload.get("market", "")).strip(),
        "quantity": payload.get("quantity", 0.0),
        "cost_basis": payload.get("cost_basis", 0.0),
        "position_value": payload.get("position_value", 0.0),
        "unrealized_pnl": payload.get("unrealized_pnl", 0.0),
        "weight": payload.get("weight", 0.0),
        "updated_at": str(payload.get("updated_at", now)).strip() or now,
        "source_modified_time": now,
    }
    target_book_path = Path(book_path)
    with _file_lock(_lock_path_for_book(target_book_path)):
        existing = load_holdings_book(target_book_path, missing_ok=True)
        frame = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        canonical = _save_holdings_book_unlocked(canonical_holdings_frame(frame), target_book_path)
    return load_holdings_book(canonical, missing_ok=True)


def save_holdings_book(frame: pd.DataFrame, path: Path | str = HOLDINGS_BOOK_PATH) -> Path:
    book_path = Path(path)
    with _file_lock(_lock_path_for_book(book_path)):
        return _save_holdings_book_unlocked(frame, book_path)


def _save_holdings_book_unlocked(frame: pd.DataFrame, path: Path | str = HOLDINGS_BOOK_PATH) -> Path:
    book_path = Path(path)
    book_path.parent.mkdir(parents=True, exist_ok=True)
    canonical = canonical_holdings_frame(frame)
    payload = {
        "schema": "PFIOSHoldingsBookV1",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "holdings": canonical.to_dict("records"),
        "summary": holdings_summary(canonical),
    }
    _atomic_write_json(book_path, payload)
    return book_path


def append_holdings_sync_history(result: HoldingSyncResult, path: Path | str = HOLDINGS_HISTORY_PATH) -> Path:
    history_path = Path(path)
    with _file_lock(_lock_path_for_book(history_path.with_name(HOLDINGS_BOOK_PATH.name))):
        return _append_holdings_sync_history_unlocked(result, history_path)


def _append_holdings_sync_history_unlocked(result: HoldingSyncResult, path: Path | str = HOLDINGS_HISTORY_PATH) -> Path:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if history_path.exists():
        history = _holdings_sync_history_rows(_read_json_file(history_path), history_path)
    else:
        history = []
    history.append(result.to_row())
    _atomic_write_json(history_path, {"schema": HOLDINGS_HISTORY_SCHEMA, "history": history[-200:]})
    return history_path


def export_holdings_csv(frame: pd.DataFrame | None = None, path: Path | str = HOLDINGS_EXPORT_PATH) -> Path:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    data = frame if isinstance(frame, pd.DataFrame) else load_holdings_book()
    canonical = canonical_holdings_frame(data)
    _atomic_write_text(export_path, canonical.to_csv(index=False))
    return export_path


def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"持仓状态文件损坏，已阻止覆盖：{path}") from exc


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


@contextmanager
def _file_lock(path: Path):
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _lock_path_for_book(book_path: Path) -> Path:
    if book_path.resolve() == HOLDINGS_BOOK_PATH.resolve():
        return HOLDINGS_LOCK_PATH
    return book_path.with_suffix(".lock")


def holdings_sync_history_frame(path: Path | str = HOLDINGS_HISTORY_PATH) -> pd.DataFrame:
    history_path = Path(path)
    if not history_path.exists():
        return pd.DataFrame(columns=HOLDINGS_HISTORY_COLUMNS)
    history = _holdings_sync_history_rows(_read_json_file(history_path), history_path)
    frame = pd.DataFrame(history)
    if frame.empty:
        return pd.DataFrame(columns=HOLDINGS_HISTORY_COLUMNS)
    for column in HOLDINGS_HISTORY_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[HOLDINGS_HISTORY_COLUMNS].copy()
    return frame.sort_values("synced_at", ascending=False).reset_index(drop=True)


def _holdings_sync_history_rows(payload: Any, history_path: Path) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("history"), list):
        return [row for row in payload["history"] if isinstance(row, dict)]
    raise ValueError(f"Holdings sync history must be a JSON list or schema/history object: {history_path}")


def holdings_quality_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if frame.empty:
        return pd.DataFrame([{"检查项": "持仓数据", "状态": "NeedsData", "说明": "未读取到正式持仓。"}])
    rows.append({"检查项": "持仓数量", "状态": "Pass" if len(frame) > 0 else "NeedsData", "说明": f"当前正式持仓 {len(frame)} 条。"})
    missing_value = int((pd.to_numeric(frame["position_value"], errors="coerce").fillna(0.0).abs() <= 0).sum())
    rows.append({"检查项": "市值字段", "状态": "Review" if missing_value else "Pass", "说明": f"{missing_value} 条记录缺少有效市值。"})
    missing_market = int(frame["market"].fillna("").astype(str).str.strip().eq("").sum())
    rows.append({"检查项": "市场字段", "状态": "Review" if missing_market else "Pass", "说明": f"{missing_market} 条记录缺少市场。"})
    updated = pd.to_datetime(frame["updated_at"], errors="coerce", utc=True).dropna()
    if updated.empty:
        rows.append({"检查项": "更新时间", "状态": "Review", "说明": "未找到可解析更新时间。"})
    else:
        latest_updated = updated.max().tz_convert(None).normalize()
        days = (pd.Timestamp.today().normalize() - latest_updated).days
        rows.append({"检查项": "更新时间", "状态": "Review" if days > 10 else "Pass", "说明": f"最新持仓更新时间距今约 {days} 天。"})
    weights = pd.to_numeric(frame["weight"], errors="coerce").fillna(0.0).abs().sort_values(ascending=False)
    top1 = float(weights.iloc[0]) if not weights.empty else 0.0
    top3 = float(weights.head(3).sum()) if not weights.empty else 0.0
    rows.append({"检查项": "集中度", "状态": "Review" if top1 >= 0.35 or top3 >= 0.65 else "Pass", "说明": f"最大单一权重 {top1:.2%}，前三权重 {top3:.2%}。"})
    return pd.DataFrame(rows)


def holdings_exposure_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["维度", "类别", "市值", "权重"])
    data = frame.copy()
    data["position_value"] = pd.to_numeric(data["position_value"], errors="coerce").fillna(0.0)
    data["weight"] = pd.to_numeric(data["weight"], errors="coerce").fillna(0.0)
    value_total = data["position_value"].abs().sum()
    if value_total > 0:
        exposure_column = "position_value"
        total = value_total
    else:
        exposure_column = "weight"
        total = data["weight"].abs().sum()
    rows: list[dict[str, object]] = []
    for dimension, column in [("市场", "market"), ("来源", "source_system")]:
        grouped = data.groupby(column, dropna=False)[exposure_column].sum().reset_index()
        for _, row in grouped.iterrows():
            value = float(row[exposure_column])
            display_value = value if exposure_column == "position_value" else 0.0
            rows.append({"维度": dimension, "类别": row[column] or "未标记", "市值": display_value, "权重": abs(value) / total if total else 0.0})
    return pd.DataFrame(rows).sort_values(["维度", "权重"], ascending=[True, False]).reset_index(drop=True)


def load_pending_orders_frame(alipay_dirs: tuple[Path, ...] | None = None) -> pd.DataFrame:
    frames = []
    for root in alipay_dirs or default_alipay_ledger_dirs():
        path = root / "pending_orders.csv"
        if path.exists():
            try:
                frame = pd.read_csv(path)
            except Exception:
                continue
            frame["source_file"] = _source_file_label(path)
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_candidate_holdings_frame(alipay_dirs: tuple[Path, ...] | None = None) -> pd.DataFrame:
    files: list[Path] = []
    for root in alipay_dirs or default_alipay_ledger_dirs():
        if root.exists():
            files.extend(sorted(root.glob("video_position_candidates_*.csv"), key=lambda item: item.stat().st_mtime, reverse=True))
    if not files:
        return pd.DataFrame(columns=holding_columns())
    frames = [load_holding_sources_from_dirs("截图候选持仓", [file]) for file in files]
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=holding_columns())
    return data[holding_columns()].copy()


def _holding_key(row: pd.Series) -> str:
    market = str(row.get("market", "")).strip().upper()
    symbol = str(row.get("symbol", "")).strip().upper()
    name = str(row.get("name", "")).strip()
    if symbol:
        return f"{market}|{symbol}"
    return f"{market}|NAME|{name}"


def _source_priority(source_system: str) -> int:
    priorities = {
        "量化回测系统导入": 10,
        "消费行为分析系统": 20,
        "行研报告系统上传": 30,
        "支付宝持仓账本": 40,
        "手动录入": 50,
    }
    return priorities.get(str(source_system), 0)


def _coerce_holding_numbers(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    for column in ["quantity", "cost_basis", "position_value", "unrealized_pnl", "weight"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0.0)
    return data


def _configured_paths(env_name: str, defaults: tuple[Path | str, ...]) -> list[Path]:
    configured = os.getenv(env_name, "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(":") if item.strip()]
    return [Path(item).expanduser() for item in defaults]


def _history_path_for_book(book_path: Path) -> Path:
    if book_path.resolve() == HOLDINGS_BOOK_PATH.resolve():
        return HOLDINGS_HISTORY_PATH
    return book_path.with_name(HOLDINGS_HISTORY_PATH.name)


def _supported_holding_files(path: Path) -> list[Path]:
    expanded = path.expanduser()
    if expanded.name in IGNORED_HOLDING_FILENAMES or expanded.is_symlink():
        return []
    if expanded.is_file():
        return [expanded] if _is_supported_holding_file(expanded) else []
    if not expanded.exists() or not expanded.is_dir():
        return []
    files: list[Path] = []
    for item in expanded.rglob("*"):
        if _is_supported_holding_file(item):
            files.append(item)
    return files


def _is_supported_holding_file(path: Path) -> bool:
    if path.is_symlink() or path.name in IGNORED_HOLDING_FILENAMES:
        return False
    if any(path.name.startswith(prefix) for prefix in IGNORED_HOLDING_FILENAME_PREFIXES):
        return False
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_HOLDING_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_HOLDING_SOURCE_FILE_SIZE_BYTES
    except OSError:
        return False


def _source_file_label(path: Path) -> str:
    try:
        parent = path.parent.name
        return f"{parent}/{path.name}" if parent else path.name
    except Exception:
        return path.name
