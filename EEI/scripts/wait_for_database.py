from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from time import monotonic, sleep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.db_health import check_database  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait until the EEI PostgreSQL database is ready.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("DATABASE_WAIT_TIMEOUT", "60")),
        help="Maximum seconds to wait.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("DATABASE_WAIT_INTERVAL", "1")),
        help="Seconds between readiness checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is required before waiting for PostgreSQL", file=sys.stderr)
        return 1
    if args.timeout <= 0:
        print("ERROR: --timeout must be greater than 0", file=sys.stderr)
        return 1
    if args.interval <= 0:
        print("ERROR: --interval must be greater than 0", file=sys.stderr)
        return 1

    deadline = monotonic() + args.timeout
    attempt = 0
    last_status = "unknown"
    last_detail = "not checked"

    while monotonic() < deadline:
        attempt += 1
        health = check_database(database_url)
        last_status = health.status
        last_detail = health.detail
        if health.ok:
            print(f"PostgreSQL ready after {attempt} attempt(s): {health.detail}")
            return 0
        sleep(min(args.interval, max(0.0, deadline - monotonic())))

    print(
        "ERROR: PostgreSQL was not ready "
        f"after {attempt} attempt(s): status={last_status} detail={last_detail}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
