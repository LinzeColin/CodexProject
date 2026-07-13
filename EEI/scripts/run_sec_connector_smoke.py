#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.sec_smoke import (  # noqa: E402
    SEC_SMOKE_REPORT_VERSION,
    run_fixture_smoke,
    run_live_smoke,
    validate_live_smoke_inputs,
)

SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def failed_report(
    args: argparse.Namespace,
    error: Exception,
    *,
    live_network_performed: bool,
) -> dict[str, Any]:
    return {
        "schema_version": SEC_SMOKE_REPORT_VERSION,
        "task_id": "T706",
        "acceptance_ids": ["A096", "A098", "A102"],
        "mode": args.mode,
        "status": "failed",
        "finished_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "error_class": type(error).__name__,
        "error_message": str(error),
        "release_scope": {
            "live_network_performed": live_network_performed,
            "database_write_performed": False,
            "production_publication_performed": False,
            "a202_closed_by_smoke": False,
            "a209_closed_by_smoke": False,
            "mvp_release_ready": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the T706 SEC fixture regression or explicit optional live smoke."
    )
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--allow-live-network", action="store_true")
    parser.add_argument("--cik")
    parser.add_argument("--user-agent-env", default="SEC_USER_AGENT")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    live_network_started = False
    try:
        if args.mode == "fixture":
            report = asyncio.run(
                run_fixture_smoke(
                    read_json(SUBMISSIONS_FIXTURE),
                    read_json(COMPANYFACTS_FIXTURE),
                )
            )
        else:
            user_agent = os.getenv(args.user_agent_env, "")
            normalized_cik = validate_live_smoke_inputs(
                cik=args.cik or "",
                user_agent=user_agent,
                allow_live_network=args.allow_live_network,
            )
            live_network_started = True
            report = asyncio.run(
                run_live_smoke(
                    cik=normalized_cik,
                    user_agent=user_agent,
                    allow_live_network=args.allow_live_network,
                )
            )
    except Exception as exc:  # noqa: BLE001 - structured smoke failure boundary.
        report = failed_report(
            args,
            exc,
            live_network_performed=live_network_started,
        )

    if args.output:
        write_report(Path(args.output), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
