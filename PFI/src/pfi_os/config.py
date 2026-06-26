from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CACHE_DATA_DIR = DATA_DIR / "cache"
RESULTS_DIR = DATA_DIR / "results"
APPROVALS_DIR = DATA_DIR / "approvals"
DEFAULT_REPORT_ROOT_DIR = Path.home() / "Downloads" / "量化回测分析"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class MarketConfig:
    market: str
    timezone: str
    currency: str
    lot_size: int = 1


MARKETS = {
    "CN": MarketConfig(market="CN", timezone="Asia/Shanghai", currency="CNY", lot_size=100),
    "HK": MarketConfig(market="HK", timezone="Asia/Hong_Kong", currency="HKD", lot_size=100),
    "US": MarketConfig(market="US", timezone="America/New_York", currency="USD", lot_size=1),
}


SUPPORTED_INTERVALS = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "30min": "30min",
    "60min": "60min",
    "1d": "1D",
    "1w": "1W",
    "1m": "1ME",
    "1q": "1QE",
    "1y": "1YE",
}


def report_date_dir(day: date | None = None) -> Path:
    report_day = day or date.today()
    path = REPORT_ROOT_DIR / report_day.isoformat()
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_env_path() -> Path:
    override = os.getenv("PFI_ENV_FILE", "").strip()
    return Path(override).expanduser() if override else DEFAULT_ENV_FILE


def read_env_file(path: Path | str | None = None) -> dict[str, str]:
    env_path = Path(path).expanduser() if path is not None else local_env_path()
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def get_env_value(key: str, default: str = "") -> str:
    exported = os.getenv(key, "").strip()
    if exported:
        return exported
    return read_env_file().get(key, default).strip()


REPORT_ROOT_DIR = Path(get_env_value("PFI_REPORT_DIR", str(DEFAULT_REPORT_ROOT_DIR))).expanduser()
