import argparse
import json
from typing import Any, Dict

from .bootstrap import seed_world_cup_2026
from .database import connect, init_db, row
from .scheduler import run_refresh_cycle
from .services import build_prediction, create_match_report, run_backtest


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def database_status() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        tables = [
            "teams",
            "competitions",
            "matches",
            "team_stats",
            "crawl_sources",
            "news_articles",
            "predictions",
            "reports",
            "refresh_runs",
        ]
        counts = {
            table: row(conn, f"SELECT COUNT(*) AS count FROM {table}")["count"]
            for table in tables
        }
        latest_refresh = row(conn, "SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 1")
    return {"status": "ok", "counts": counts, "latest_refresh": latest_refresh}


def bootstrap_world_cup() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        result = seed_world_cup_2026(conn)
    return {"status": "ok", "bootstrap": result}


def refresh_now() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return run_refresh_cycle(conn)


def predict_match(match_id: int) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return build_prediction(conn, match_id)


def report_match(match_id: int, include_prediction: bool) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return create_match_report(conn, match_id, include_prediction=include_prediction)


def backtest(model_version: str = "") -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return run_backtest(conn, model_version)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FIFA analysis batch CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show database counts and latest refresh")
    sub.add_parser("bootstrap-world-cup", help="Seed FIFA World Cup 2026 baseline data")
    sub.add_parser("refresh", help="Run one compliant refresh cycle")

    predict = sub.add_parser("predict", help="Generate prediction for one match")
    predict.add_argument("--match-id", type=int, required=True)

    report = sub.add_parser("report", help="Generate Markdown report for one match")
    report.add_argument("--match-id", type=int, required=True)
    report.add_argument("--no-prediction", action="store_true")

    bt = sub.add_parser("backtest", help="Run prediction backtest")
    bt.add_argument("--model-version", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "status":
            payload = database_status()
        elif args.command == "bootstrap-world-cup":
            payload = bootstrap_world_cup()
        elif args.command == "refresh":
            payload = refresh_now()
        elif args.command == "predict":
            payload = predict_match(args.match_id)
        elif args.command == "report":
            payload = report_match(args.match_id, include_prediction=not args.no_prediction)
        elif args.command == "backtest":
            payload = backtest(args.model_version)
        else:
            raise AssertionError(f"unhandled command {args.command}")
        _print_json(payload)
        return 0
    except Exception as exc:
        _print_json({"status": "error", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
