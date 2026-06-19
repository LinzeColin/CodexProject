from __future__ import annotations

import importlib.util
import socket
from dataclasses import dataclass

from pfi_os.config import get_env_value


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    market_cn: str
    market_en: str
    credential_cn: str
    credential_en: str
    status: str
    note_cn: str
    note_en: str


def provider_status_rows() -> list[dict[str, str]]:
    return [status.__dict__ for status in provider_statuses()]


def provider_statuses() -> list[ProviderStatus]:
    return [
        ProviderStatus(
            "Sample",
            "美股样例",
            "US sample",
            "不需要",
            "Not required",
            "Ready",
            "离线样例数据，适合第一次跑通流程。",
            "Offline sample data, best for first-run workflow validation.",
        ),
        ProviderStatus(
            "CSV",
            "取决于文件",
            "Depends on file",
            "不需要",
            "Not required",
            "Ready",
            "上传 OHLCV CSV，适合复用你自己的数据。",
            "Upload an OHLCV CSV file to reuse your own data.",
        ),
        ProviderStatus(
            "Moomoo",
            "A 股 / 港股 / 美股优先",
            "CN / HK / US first",
            "需要 Moomoo OpenD",
            "Requires Moomoo OpenD",
            _moomoo_status(),
            "作为优先真实数据入口；需要本机启动 Moomoo OpenD，不接交易接口。",
            "Primary real-data entry; requires local Moomoo OpenD and does not connect to trading APIs.",
        ),
        ProviderStatus(
            "AKShare",
            "A 股优先",
            "A-share first",
            "不需要 API Key",
            "No API key",
            "Ready",
            "需要网络和 akshare 包；当前支持 A 股日/周/月线。",
            "Requires network and the akshare package; currently supports A-share daily, weekly, and monthly bars.",
        ),
        ProviderStatus(
            "TuShare",
            "A 股优先",
            "A-share first",
            "需要 TUSHARE_TOKEN",
            "Requires TUSHARE_TOKEN",
            _env_status("TUSHARE_TOKEN"),
            "当前支持 A 股日线；未配置 token 时不可用。",
            "Currently supports A-share daily bars; unavailable without token configuration.",
        ),
        ProviderStatus(
            "Yahoo Finance",
            "美股优先，可查部分港股",
            "US first, some HK symbols",
            "不需要 API Key",
            "No API key",
            "Ready",
            "需要网络和 yfinance 包；分钟线可能受数据源历史长度限制。",
            "Requires network and the yfinance package; intraday history may be limited by the provider.",
        ),
        ProviderStatus(
            "Alpha Vantage",
            "美股优先",
            "US first",
            "需要 ALPHA_VANTAGE_API_KEY",
            "Requires ALPHA_VANTAGE_API_KEY",
            _env_status("ALPHA_VANTAGE_API_KEY"),
            "适合美股补充校验；免费额度可能有限。",
            "Useful as a US-market validation source; free quota may be limited.",
        ),
        ProviderStatus(
            "Polygon",
            "美股优先",
            "US first",
            "需要 POLYGON_API_KEY",
            "Requires POLYGON_API_KEY",
            _env_status("POLYGON_API_KEY"),
            "已接入聚合行情接口；未配置 key 时不可用。",
            "Aggregate market data fetching is implemented; unavailable without key configuration.",
        ),
    ]


def market_symbol_examples() -> list[dict[str, str]]:
    return [
        {
            "市场 Market": "CN A 股",
            "输入 Input": "000001 / SZ000001 / 000001.SZ",
            "AKShare": "000001",
            "TuShare": "000001.SZ",
            "说明 Notes": "未写交易所时会按代码前缀推断。",
        },
        {
            "市场 Market": "US 美股",
            "输入 Input": "AAPL / MSFT / SPY",
            "AKShare": "不适用",
            "TuShare": "不适用",
            "说明 Notes": "Yahoo Finance 和 Alpha Vantage 通常直接使用英文 ticker。",
        },
        {
            "市场 Market": "HK 港股",
            "输入 Input": "0700.HK / 9988.HK",
            "AKShare": "待扩展",
            "TuShare": "不适用",
            "说明 Notes": "当前建议优先用 Yahoo Finance 测试港股。",
        },
    ]


def _env_status(key: str) -> str:
    return "Ready" if get_env_value(key) else "NeedsConfig"


def _moomoo_status() -> str:
    if not _package_available("futu"):
        return "NeedsPackage"
    host = get_env_value("MOOMOO_HOST", "127.0.0.1")
    try:
        port = int(get_env_value("MOOMOO_PORT", "11111"))
    except ValueError:
        return "NeedsConfig"
    if not _port_reachable(host, port, timeout=0.2):
        return "NeedsOpenD"
    return "Ready"


def _package_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _port_reachable(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
