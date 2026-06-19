from __future__ import annotations

import argparse

from pfi_os.config import get_env_value
from pfi_os.data import BarDataRequest, save_cross_source_validation_result, validate_close_across_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real-data cross-source validation and save the result.")
    parser.add_argument("--market", default="US", choices=["US", "CN"], help="Market to validate.")
    parser.add_argument("--symbol", default="", help="Symbol. Defaults to AAPL for US and 600000 for CN.")
    parser.add_argument("--start", default="2024-01-01", help="Start date.")
    parser.add_argument("--end", default="2024-01-31", help="End date.")
    parser.add_argument("--tolerance", default=0.01, type=float, help="Maximum close-price difference tolerance.")
    args = parser.parse_args()

    providers = _providers_for_market(args.market)
    symbol = args.symbol or ("AAPL" if args.market == "US" else "600000")
    if len(providers) < 2:
        print(f"CrossSourceSkipped: market={args.market}, providers={providers}. Configure more real-data keys first.")
        raise SystemExit(3)

    request = BarDataRequest(symbol=symbol, market=args.market, interval="1d", start=args.start, end=args.end)
    result = validate_close_across_sources(providers, request, tolerance_pct=args.tolerance)
    path = save_cross_source_validation_result(result)
    print(f"Status: {result.status}")
    print(f"Providers: {', '.join(result.providers)}")
    print(f"OverlapRows: {result.overlap_rows}")
    print(f"MaxCloseDiff: {result.max_close_diff_pct:.2%}")
    print(f"MeanCloseDiff: {result.mean_close_diff_pct:.2%}")
    print(f"CrossValidationReport: {path}")
    if result.status not in {"Pass", "NoOverlap"}:
        raise SystemExit(2)


def _providers_for_market(market: str) -> list[str]:
    if market == "US":
        providers = ["Yahoo Finance"]
        if get_env_value("ALPHA_VANTAGE_API_KEY"):
            providers.append("Alpha Vantage")
        if get_env_value("POLYGON_API_KEY"):
            providers.append("Polygon")
        return providers
    providers = ["AKShare"]
    if get_env_value("TUSHARE_TOKEN"):
        providers.append("TuShare")
    return providers


if __name__ == "__main__":
    main()
