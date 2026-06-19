from __future__ import annotations

import importlib.util
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from pfi_os.config import get_env_value
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.moomoo_provider import MoomooProvider
from pfi_os.data.quality import assess_bars, save_quality_report


@dataclass(frozen=True)
class MoomooDiagnosticResult:
    status: str
    status_cn: str
    status_en: str
    host: str
    port: int
    package_available: bool
    opend_reachable: bool
    quote_check: bool
    rows: int
    quality_status: str
    quality_report_path: str
    detail_cn: str
    detail_en: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def diagnose_moomoo_quote(
    symbol: str = "AAPL",
    market: str = "US",
    interval: str = "1d",
    start: str = "2024-01-01",
    end: str = "2024-01-31",
    host: str | None = None,
    port: int | None = None,
    fetch: bool = True,
    quality_output_dir: Path | str | None = None,
    package_checker: Callable[[str], bool] | None = None,
    connection_checker: Callable[[str, int, float], bool] | None = None,
    provider_factory: Callable[[str, int], MoomooProvider] | None = None,
) -> MoomooDiagnosticResult:
    resolved_host = host or get_env_value("MOOMOO_HOST", "127.0.0.1")
    raw_port = port if port is not None else get_env_value("MOOMOO_PORT", "11111")
    try:
        resolved_port = int(raw_port)
    except ValueError:
        return _result(
            status="NeedsConfig",
            status_cn="Moomoo 端口配置错误",
            status_en="Moomoo port configuration is invalid",
            host=resolved_host,
            port=0,
            package_available=False,
            opend_reachable=False,
            quote_check=False,
            detail_cn=f"MOOMOO_PORT 必须是数字，当前值为 {raw_port}。",
            detail_en=f"MOOMOO_PORT must be numeric. Current value: {raw_port}.",
        )
    package_checker = package_checker or _package_available
    connection_checker = connection_checker or _port_reachable

    package_ok = package_checker("futu")
    if not package_ok:
        return _result(
            status="NeedsPackage",
            status_cn="需要安装 futu-api",
            status_en="futu-api package is required",
            host=resolved_host,
            port=resolved_port,
            package_available=False,
            opend_reachable=False,
            quote_check=False,
            detail_cn="当前 Python 环境没有安装 futu-api，无法连接 Moomoo OpenD。",
            detail_en="The current Python environment does not have futu-api installed, so Moomoo OpenD cannot be used.",
        )

    reachable = connection_checker(resolved_host, resolved_port, 2.0)
    if not reachable:
        return _result(
            status="NeedsOpenD",
            status_cn="需要启动 Moomoo OpenD",
            status_en="Moomoo OpenD must be running",
            host=resolved_host,
            port=resolved_port,
            package_available=True,
            opend_reachable=False,
            quote_check=False,
            detail_cn=f"无法连接 {resolved_host}:{resolved_port}，请启动 Moomoo OpenD 并确认端口配置。",
            detail_en=f"Cannot reach {resolved_host}:{resolved_port}. Start Moomoo OpenD and confirm the configured port.",
        )

    if not fetch:
        return _result(
            status="Ready",
            status_cn="Moomoo OpenD 可连接",
            status_en="Moomoo OpenD is reachable",
            host=resolved_host,
            port=resolved_port,
            package_available=True,
            opend_reachable=True,
            quote_check=False,
            detail_cn="futu-api 已安装，Moomoo OpenD 端口可连接；未执行行情拉取。",
            detail_en="futu-api is installed and the Moomoo OpenD port is reachable; quote fetching was skipped.",
        )

    try:
        provider = provider_factory(resolved_host, resolved_port) if provider_factory else MoomooProvider(host=resolved_host, port=resolved_port)
        request = BarDataRequest(symbol=symbol, market=market, interval=interval, start=start, end=end)
        data = provider.get_bars(request)
    except Exception as exc:
        return _result(
            status="DataFetchFailed",
            status_cn="Moomoo 行情拉取失败",
            status_en="Moomoo quote fetch failed",
            host=resolved_host,
            port=resolved_port,
            package_available=True,
            opend_reachable=True,
            quote_check=False,
            detail_cn=f"已连接 OpenD，但行情请求失败：{exc}",
            detail_en=f"OpenD is reachable, but the quote request failed: {exc}",
        )

    report = assess_bars(
        data,
        provider="moomoo",
        symbol=symbol,
        market=market,
        interval=interval,
        notes="Moomoo quote-only diagnostic. No trading API was used.",
    )
    quality_path = save_quality_report(report, output_dir=quality_output_dir)
    if report.quality_status == "Pass":
        return _result(
            status="Ready",
            status_cn="Moomoo 行情可用",
            status_en="Moomoo quote data is ready",
            host=resolved_host,
            port=resolved_port,
            package_available=True,
            opend_reachable=True,
            quote_check=True,
            rows=report.row_count,
            quality_status=report.quality_status,
            quality_report_path=str(quality_path),
            detail_cn="Moomoo 只读行情拉取成功，并已生成数据质量报告。",
            detail_en="Moomoo quote-only data fetch succeeded and a data quality report was created.",
        )
    return _result(
        status="DataReview",
        status_cn="Moomoo 数据需要复核",
        status_en="Moomoo data needs review",
        host=resolved_host,
        port=resolved_port,
        package_available=True,
        opend_reachable=True,
        quote_check=True,
        rows=report.row_count,
        quality_status=report.quality_status,
        quality_report_path=str(quality_path),
        detail_cn="Moomoo 返回了行情数据，但数据质量状态不是 Pass，需要人工复核。",
        detail_en="Moomoo returned quote data, but the quality status is not Pass and needs manual review.",
    )


def _package_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _port_reachable(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _result(
    *,
    status: str,
    status_cn: str,
    status_en: str,
    host: str,
    port: int,
    package_available: bool,
    opend_reachable: bool,
    quote_check: bool,
    rows: int = 0,
    quality_status: str = "",
    quality_report_path: str = "",
    detail_cn: str,
    detail_en: str,
) -> MoomooDiagnosticResult:
    return MoomooDiagnosticResult(
        status=status,
        status_cn=status_cn,
        status_en=status_en,
        host=host,
        port=port,
        package_available=package_available,
        opend_reachable=opend_reachable,
        quote_check=quote_check,
        rows=rows,
        quality_status=quality_status,
        quality_report_path=quality_report_path,
        detail_cn=detail_cn,
        detail_en=detail_en,
    )
