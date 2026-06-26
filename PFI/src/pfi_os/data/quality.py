from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pfi_os.config import report_date_dir


@dataclass(frozen=True)
class DataQualityReport:
    provider: str
    symbol: str
    market: str
    interval: str
    request_time: str
    first_datetime: str | None
    last_datetime: str | None
    row_count: int
    missing_values: int
    duplicate_datetimes: int
    checksum: str
    quality_status: str
    notes: str = ""


def assess_bars(df: pd.DataFrame, provider: str, symbol: str, market: str, interval: str, notes: str = "") -> DataQualityReport:
    if df.empty:
        return DataQualityReport(
            provider=provider,
            symbol=symbol,
            market=market,
            interval=interval,
            request_time=_now(),
            first_datetime=None,
            last_datetime=None,
            row_count=0,
            missing_values=0,
            duplicate_datetimes=0,
            checksum="",
            quality_status="Empty",
            notes=notes or "No rows returned.",
        )

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])
    duplicate_datetimes = int(data["datetime"].duplicated().sum())
    required = ["datetime", "open", "high", "low", "close", "volume"]
    missing_values = int(data[required].isna().sum().sum())
    checksum = _checksum(data[required])
    status = "Pass" if missing_values == 0 and duplicate_datetimes == 0 else "Review"
    return DataQualityReport(
        provider=provider,
        symbol=symbol,
        market=market,
        interval=interval,
        request_time=_now(),
        first_datetime=str(data["datetime"].min()),
        last_datetime=str(data["datetime"].max()),
        row_count=int(len(data)),
        missing_values=missing_values,
        duplicate_datetimes=duplicate_datetimes,
        checksum=checksum,
        quality_status=status,
        notes=notes,
    )


def save_quality_report(report: DataQualityReport, output_dir: Path | str | None = None) -> Path:
    root = Path(output_dir) if output_dir is not None else report_date_dir() / "DataQuality"
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = root / f"DataQuality_{report.provider}_{report.market}_{report.symbol}_{timestamp}.json"
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _checksum(df: pd.DataFrame) -> str:
    canonical = df.sort_values("datetime").to_csv(index=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
