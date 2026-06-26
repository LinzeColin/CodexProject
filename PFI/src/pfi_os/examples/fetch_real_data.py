from __future__ import annotations

import argparse

from pfi_os.data import assess_bars, save_quality_report
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.factory import make_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch real market data and create a data quality report.")
    parser.add_argument("--provider", default="Yahoo Finance", help="Provider name, such as AKShare or Yahoo Finance.")
    parser.add_argument("--symbol", default="AAPL", help="Symbol, such as AAPL or 000001.")
    parser.add_argument("--market", default="US", help="Market, such as US or CN.")
    parser.add_argument("--interval", default="1d", help="Interval, such as 1d.")
    parser.add_argument("--start", default="2024-01-01", help="Start date.")
    parser.add_argument("--end", default="2024-03-31", help="End date.")
    parser.add_argument("--adjustment", default="none", help="Adjustment mode.")
    args = parser.parse_args()

    provider = make_provider(args.provider)
    request = BarDataRequest(
        symbol=args.symbol,
        market=args.market,
        interval=args.interval,
        start=args.start,
        end=args.end,
        adjustment=args.adjustment,
    )
    try:
        data = provider.get_bars(request)
    except Exception as exc:
        print(f"DataFetchFailed: {exc}")
        raise SystemExit(2) from exc
    report = assess_bars(data, provider=provider.name, symbol=args.symbol, market=args.market, interval=args.interval)
    path = save_quality_report(report)
    print(data.tail().to_string(index=False))
    print(f"Rows: {len(data)}")
    print(f"Quality: {report.quality_status}")
    print(f"QualityReport: {path}")


if __name__ == "__main__":
    main()
