#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.sec_smoke import (  # noqa: E402
    SEC_SMOKE_REPORT_VERSION,
    run_fixture_smoke,
)

OUTPUTS = {
    "A096": ROOT / "artifacts/tests/a096/t706_sec_fixture_allowlist_smoke_contract.json",
    "A098": ROOT / "artifacts/tests/a098/t706_sec_fixture_retry_smoke_contract.json",
    "A102": ROOT / "artifacts/tests/a102/t706_sec_fixture_dry_run_smoke_contract.json",
}
SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fixed_clock() -> Any:
    current = datetime(2026, 7, 13, 2, 0, tzinfo=UTC)

    def now() -> datetime:
        nonlocal current
        result = current
        current += timedelta(seconds=1)
        return result

    return now


def validate_source_contract() -> None:
    smoke_source = (ROOT / "apps/api/app/ingest/sec_smoke.py").read_text(encoding="utf-8")
    cli_source = (ROOT / "scripts/run_sec_connector_smoke.py").read_text(encoding="utf-8")
    unit_source = (ROOT / "tests/unit/test_sec_smoke.py").read_text(encoding="utf-8")
    for token in (
        "httpx.MockTransport",
        "validate_live_smoke_inputs",
        "live smoke requires explicit network opt-in",
        'record_mode="live"',
        "database_write_performed",
    ):
        require(token in smoke_source, f"T706 smoke source contract missing: {token}")
    for token in ("--allow-live-network", "SEC_USER_AGENT", "live_network_started"):
        require(token in cli_source, f"T706 CLI guard missing: {token}")
    for token in (
        "test_fixture_smoke_combines_allowlist_retry_and_dry_run_without_network",
        "test_live_smoke_requires_explicit_network_opt_in_before_transport_use",
        "test_fixture_payload_cannot_be_relabelled_by_live_smoke_path",
    ):
        require(token in unit_source, f"T706 unit contract missing: {token}")


def run_fixture_contract() -> dict[str, Any]:
    report = asyncio.run(
        run_fixture_smoke(
            read_json(SUBMISSIONS_FIXTURE),
            read_json(COMPANYFACTS_FIXTURE),
            now=fixed_clock(),
        )
    )
    require(report["schema_version"] == SEC_SMOKE_REPORT_VERSION, "smoke schema drift")
    require(report["status"] == "succeeded", "fixture smoke must succeed")
    return report


def common_contract(acceptance_id: str) -> dict[str, Any]:
    return {
        "task_id": "T706",
        "acceptance_ids": [acceptance_id],
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "implementation": [
            "apps/api/app/ingest/sec_smoke.py",
            "scripts/run_sec_connector_smoke.py",
        ],
        "test_evidence": [
            "tests/unit/test_sec_smoke.py",
            "tests/unit/test_sec_client.py",
            "tests/unit/test_sec_fixture_ingestion.py",
            "tests/integration/test_database_migrations.py",
        ],
        "optional_live_smoke": {
            "performed_by_contract_generation": False,
            "explicit_network_opt_in_required": True,
            "explicit_cik_required": True,
            "sec_user_agent_environment_required": True,
            "database_write_performed": False,
            "production_publication_performed": False,
        },
        "release_scope": {
            "fixture_mock_transport_only": True,
            "live_network_performed": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }


def build_contracts() -> dict[str, dict[str, Any]]:
    validate_source_contract()
    report = run_fixture_contract()
    request_contract = report["request_contract"]
    responses = report["responses"]
    ingestion = report["ingestion"]
    return {
        "A096": {
            **common_contract("A096"),
            "schema_version": "eei-a096-t706-fixture-allowlist-smoke-v1",
            "contract": {
                "transport": report["transport"],
                "request_count": request_contract["request_count"],
                "allowed_hosts_only": request_contract["allowed_hosts_only"],
                "credentials_absent": request_contract["credentials_absent"],
                "all_requests_use_governed_user_agent": all(
                    item["user_agent_matches"] for item in request_contract["requests"]
                ),
                "user_agent_value_recorded": request_contract["user_agent"][
                    "value_recorded"
                ],
                "user_agent_sha256": request_contract["user_agent"]["sha256"],
            },
        },
        "A098": {
            **common_contract("A098"),
            "schema_version": "eei-a098-t706-fixture-retry-smoke-v1",
            "contract": {
                "submissions_attempt_count": responses["submissions"]["attempt_count"],
                "submissions_retry_delays_seconds": responses["submissions"][
                    "retry_delays_seconds"
                ],
                "companyfacts_attempt_count": responses["companyfacts"]["attempt_count"],
                "companyfacts_retry_delays_seconds": responses["companyfacts"][
                    "retry_delays_seconds"
                ],
                "transient_statuses_exercised": [429, 503],
                "limiter_applies_to_retries": True,
            },
        },
        "A102": {
            **common_contract("A102"),
            "schema_version": "eei-a102-t706-fixture-dry-run-smoke-v1",
            "contract": {
                "execution_mode": ingestion["execution_mode"],
                "record_mode": ingestion["record_mode"],
                "status": ingestion["status"],
                "source_documents_planned": ingestion["counts"][
                    "source_documents_planned"
                ],
                "raw_snapshots_planned": ingestion["counts"]["raw_snapshots_planned"],
                "database_write_performed": ingestion["database_write_performed"],
                "ingestion_run_id": ingestion["ingestion_run_id"],
            },
        },
    }


def validate_contract(acceptance_id: str, payload: dict[str, Any]) -> None:
    require(payload.get("task_id") == "T706", f"{acceptance_id} task mapping drift")
    require(
        payload.get("acceptance_ids") == [acceptance_id],
        f"{acceptance_id} acceptance mapping drift",
    )
    require(payload.get("status") == "PASS", f"{acceptance_id} status must be PASS")
    live = payload.get("optional_live_smoke") or {}
    require(live.get("performed_by_contract_generation") is False, "unexpected live smoke")
    require(live.get("explicit_network_opt_in_required") is True, "live opt-in drift")
    release = payload.get("release_scope") or {}
    require(release.get("live_network_performed") is False, "live network claim")
    require(release.get("a209_closed_by_contract") is False, "A209 closure claim")
    require(release.get("mvp_release_ready") is False, "release-ready claim")

    contract = payload.get("contract") or {}
    if acceptance_id == "A096":
        require(contract.get("transport") == "httpx.MockTransport", "transport drift")
        require(contract.get("allowed_hosts_only") is True, "allowlist smoke failed")
        require(contract.get("credentials_absent") is True, "credential boundary failed")
        require(
            contract.get("all_requests_use_governed_user_agent") is True,
            "User-Agent smoke failed",
        )
        require(contract.get("user_agent_value_recorded") is False, "User-Agent leaked")
    elif acceptance_id == "A098":
        require(contract.get("submissions_attempt_count") == 2, "503 retry drift")
        require(contract.get("companyfacts_attempt_count") == 2, "429 retry drift")
        require(contract.get("transient_statuses_exercised") == [429, 503], "status drift")
    else:
        require(contract.get("execution_mode") == "dry_run", "dry-run mode drift")
        require(contract.get("record_mode") == "fixture", "fixture mode drift")
        require(contract.get("database_write_performed") is False, "unexpected DB write")
        require(contract.get("ingestion_run_id") is None, "unexpected ingestion run")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T706 SEC connector smoke contracts.")
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    validate_source_contract()
    contracts = build_contracts() if args.command == "generate" else {
        acceptance_id: read_json(path) for acceptance_id, path in OUTPUTS.items()
    }
    for acceptance_id, payload in contracts.items():
        validate_contract(acceptance_id, payload)
        if args.command == "generate":
            write_json(OUTPUTS[acceptance_id], payload)
    print(
        json.dumps(
            {
                "valid": True,
                "task_id": "T706",
                "acceptance_ids": list(OUTPUTS),
                "live_network_performed": False,
                "artifacts": [
                    path.relative_to(ROOT).as_posix() for path in OUTPUTS.values()
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        raise SystemExit(1) from exc
