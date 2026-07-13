#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.domain_repository import _report_period_bounds  # noqa: E402

OUTPUT = ROOT / "artifacts/tests/a104/t704_source_freshness_contract.json"
SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"
REQUIRED_SOURCE_FIELDS = [
    "last_attempt_at",
    "last_attempt_status",
    "last_success_at",
    "last_failure_at",
    "last_error_class",
    "latest_document_date",
    "latest_report_period_start",
    "latest_report_period_end",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


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


def companyfacts_period_values(payload: dict[str, Any]) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    for concepts in payload.get("facts", {}).values():
        for concept in concepts.values():
            for entries in concept.get("units", {}).values():
                for fact in entries:
                    periods.append(dict(fact))
    return periods


def build_contract() -> dict[str, Any]:
    openapi = yaml.safe_load((ROOT / "specs/api_contract.yaml").read_text(encoding="utf-8"))
    response_schema = (
        openapi["paths"]["/v1/sources/freshness"]["get"]["responses"]["200"]["content"]
        ["application/json"]["schema"]
    )
    require(
        response_schema == {"$ref": "#/components/schemas/SourceFreshnessResponse"},
        "source freshness response schema drift",
    )
    item_schema = openapi["components"]["schemas"]["SourceFreshnessItem"]
    required_fields = item_schema.get("required") or []
    for field in REQUIRED_SOURCE_FIELDS:
        require(field in required_fields, f"A104 source field missing: {field}")

    submissions = read_json(SUBMISSIONS_FIXTURE)
    companyfacts = read_json(COMPANYFACTS_FIXTURE)
    report_dates = submissions["filings"]["recent"]["reportDate"]
    fact_periods = companyfacts_period_values(companyfacts)
    report_start, report_end = _report_period_bounds(report_dates, fact_periods)
    require(report_start and report_start.isoformat() == "2024-01-01", "report start drift")
    require(report_end and report_end.isoformat() == "2024-12-31", "report end drift")

    return {
        "schema_version": "eei-a104-source-freshness-contract-v1",
        "task_id": "T704",
        "acceptance_ids": ["A104"],
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "contract": {
            "api_path": "/v1/sources/freshness",
            "response_schema": "SourceFreshnessResponse",
            "source_required_fields": REQUIRED_SOURCE_FIELDS,
            "status_precedence": [
                "latest_failure",
                "running",
                "never_attempted",
                "missing_documents",
                "fixture",
                "available",
            ],
            "attempt_time_is_document_time": False,
            "attempt_time_is_report_period": False,
            "document_date_source": "source_documents.document_date",
            "report_period_source": "validated_raw_source_snapshot_payload",
            "fixture_report_period_start": report_start.isoformat(),
            "fixture_report_period_end": report_end.isoformat(),
            "frontend_api_binding": "apps/web/src/app/production-data-client.ts",
            "frontend_surface": "home-freshness",
            "server_error_falls_back_to_fixture_success": False,
        },
        "test_evidence": [
            "tests/unit/test_source_freshness.py",
            "tests/integration/test_database_migrations.py",
            "tests/e2e/home.spec.ts",
            "tests/e2e/saved-view-live.spec.ts",
        ],
        "release_scope": {
            "fixture_and_database_freshness_only": True,
            "live_sec_request_performed": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }


def validate_contract(payload: dict[str, Any]) -> None:
    require(payload.get("status") == "PASS", "A104 contract status must be PASS")
    require(payload.get("task_id") == "T704", "A104 task mapping drift")
    require(payload.get("acceptance_ids") == ["A104"], "A104 acceptance mapping drift")
    contract = payload.get("contract") or {}
    require(contract.get("api_path") == "/v1/sources/freshness", "A104 API path drift")
    require(
        contract.get("source_required_fields") == REQUIRED_SOURCE_FIELDS,
        "A104 required source fields drift",
    )
    require(contract.get("attempt_time_is_document_time") is False, "time conflation")
    require(contract.get("attempt_time_is_report_period") is False, "period conflation")
    require(contract.get("fixture_report_period_start") == "2024-01-01", "start drift")
    require(contract.get("fixture_report_period_end") == "2024-12-31", "end drift")
    require(
        contract.get("server_error_falls_back_to_fixture_success") is False,
        "server errors must remain visible",
    )
    release_scope = payload.get("release_scope") or {}
    require(release_scope.get("live_sec_request_performed") is False, "live request claim")
    require(release_scope.get("mvp_release_ready") is False, "release-ready claim")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T704/A104 source freshness contract.")
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    if args.command == "generate":
        payload = build_contract()
        write_json(OUTPUT, payload)
    else:
        payload = read_json(OUTPUT)
    validate_contract(payload)
    print(json.dumps({"valid": True, "artifact": OUTPUT.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        raise SystemExit(1) from exc
