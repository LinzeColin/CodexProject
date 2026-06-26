from __future__ import annotations

import argparse
import json

from pfi_os.data.moomoo_diagnostics import diagnose_moomoo_quote


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Moomoo quote-only connectivity and data quality.")
    parser.add_argument("--symbol", default="AAPL", help="Symbol, such as AAPL, 0700.HK, or 000001.")
    parser.add_argument("--market", default="US", help="Market: US, HK, or CN.")
    parser.add_argument("--interval", default="1d", help="Interval, such as 1d.")
    parser.add_argument("--start", default="2024-01-01", help="Start date.")
    parser.add_argument("--end", default="2024-01-31", help="End date.")
    parser.add_argument("--host", default=None, help="Moomoo OpenD host. Defaults to MOOMOO_HOST or 127.0.0.1.")
    parser.add_argument("--port", type=int, default=None, help="Moomoo OpenD port. Defaults to MOOMOO_PORT or 11111.")
    parser.add_argument("--no-fetch", action="store_true", help="Only check futu-api and OpenD connectivity.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--strict", action="store_true", help="Return a non-zero exit code unless status is Ready.")
    args = parser.parse_args()

    result = diagnose_moomoo_quote(
        symbol=args.symbol,
        market=args.market,
        interval=args.interval,
        start=args.start,
        end=args.end,
        host=args.host,
        port=args.port,
        fetch=not args.no_fetch,
    )
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Moomoo Quote Diagnostic")
        print("=======================")
        print(f"Status: {result.status}")
        print(f"中文状态: {result.status_cn}")
        print(f"English Status: {result.status_en}")
        print(f"Host: {result.host}")
        print(f"Port: {result.port}")
        print(f"futu-api: {'Ready' if result.package_available else 'Missing'}")
        print(f"OpenD: {'Reachable' if result.opend_reachable else 'Not Reachable'}")
        print(f"Quote Fetch: {'Pass' if result.quote_check else 'Not Verified'}")
        print(f"Rows: {result.rows}")
        if result.quality_status:
            print(f"DataQuality: {result.quality_status}")
        if result.quality_report_path:
            print(f"QualityReport: {result.quality_report_path}")
        print("")
        print(result.detail_cn)
        print(result.detail_en)
        print("")
        print("Safety: quote-only check; no trading API, no order submission, no account password storage.")

    if args.strict and result.status != "Ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
