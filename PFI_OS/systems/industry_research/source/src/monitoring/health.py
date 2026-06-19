from __future__ import annotations


def run_health_checks(price_rows: list[dict[str, str]], as_of: str) -> list[str]:
    logs: list[str] = []
    latest_dates = {row["symbol"]: row["date"] for row in price_rows}
    stale = [symbol for symbol, date in latest_dates.items() if date < as_of]
    if stale:
        logs.append(f"行情未更新标的：{', '.join(sorted(stale))}")
    else:
        logs.append("行情数据已更新至报告日期。")

    missing_close = [row["symbol"] for row in price_rows if not row.get("close")]
    if missing_close:
        logs.append(f"存在收盘价缺失：{', '.join(sorted(set(missing_close)))}")
    else:
        logs.append("未发现收盘价缺失。")
    return logs
