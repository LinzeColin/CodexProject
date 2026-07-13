#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.amount_semantics import (  # noqa: E402
    aggregate_event_amounts,
    event_amount_semantics,
)

A108_OUTPUT = ROOT / "artifacts/tests/a108/t800_unreported_amount_semantics_contract.json"
A109_OUTPUT = ROOT / "artifacts/tests/a109/t800_incomparable_amount_aggregation_contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(item) for item in value]
    return value


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


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_source_contract() -> None:
    service_source = (ROOT / "apps/api/app/amount_semantics.py").read_text(encoding="utf-8")
    repository_source = (ROOT / "apps/api/app/domain_repository.py").read_text(
        encoding="utf-8"
    )
    integration_source = (
        ROOT / "tests/integration/test_database_migrations.py"
    ).read_text(encoding="utf-8")
    for token in (
        '"unknown_amount_is_zero": False',
        '"unknown_amount_has_visual_weight": False',
        '"cross_bucket_summation_performed": False',
        '"aggregation_key": ["currency", "amount_kind", "period_start", "period_end"]',
    ):
        require(token in service_source, f"T800 service contract missing: {token}")
    for token in ("list_events_for_connection", "event_amount_summary"):
        require(token in repository_source, f"T800 repository contract missing: {token}")
    for token in (
        "exercise_event_amount_semantics_contracts",
        'unknown["amount_semantics"]["visual_weight"] is None',
        'summary["comparable_reported_total"] is None',
    ):
        require(token in integration_source, f"T800 integration contract missing: {token}")

    openapi = yaml.safe_load((ROOT / "specs/api_contract.yaml").read_text(encoding="utf-8"))
    summary_schema = (
        openapi["paths"]["/v1/events/amount-summary"]["get"]["responses"]["200"]
        ["content"]["application/json"]["schema"]
    )
    require(
        summary_schema == {"$ref": "#/components/schemas/EventAmountSummary"},
        "T800 amount-summary response schema drift",
    )
    event_required = openapi["components"]["schemas"]["Event"]["required"]
    require("amount_semantics" in event_required, "Event amount semantics not required")


def common_contract(acceptance_id: str) -> dict[str, Any]:
    return {
        "task_id": "T800",
        "acceptance_ids": [acceptance_id],
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "implementation": [
            "apps/api/app/amount_semantics.py",
            "apps/api/app/domain_repository.py",
            "apps/api/app/domain.py",
            "specs/api_contract.yaml",
        ],
        "test_evidence": [
            "tests/unit/test_amount_semantics.py",
            "tests/integration/test_database_migrations.py",
        ],
        "acceptance_closure": {
            "backend_service_validated": True,
            "api_validated": True,
            "ui_validation_complete": False,
            "cross_view_validation_complete": False,
            "acceptance_status_required": "IN PROGRESS",
            "remaining_tasks": ["T801", "T805"],
        },
        "release_scope": {
            "fixture_postgres_validation_only": True,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }


def build_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_source_contract()
    unreported = event_amount_semantics(
        amount=None,
        currency=None,
        amount_kind=None,
        period_start=None,
        period_end=None,
    )
    aggregation = aggregate_event_amounts(
        [
            {
                "id": "period-capex",
                "amount": 1_000_000_000,
                "currency": "USD",
                "amount_kind": "period_capex",
                "period_start": "2026-01-01",
                "period_end": "2026-12-31",
            },
            {
                "id": "award-ceiling",
                "amount": 500_000_000,
                "currency": "USD",
                "amount_kind": "award_ceiling",
                "period_start": None,
                "period_end": None,
            },
            {
                "id": "unreported",
                "amount": None,
                "currency": None,
                "amount_kind": None,
                "period_start": None,
                "period_end": None,
            },
        ]
    )
    a108 = {
        **common_contract("A108"),
        "schema_version": "eei-a108-t800-unreported-amount-semantics-v1",
        "contract": jsonable(unreported),
    }
    a109 = {
        **common_contract("A109"),
        "schema_version": "eei-a109-t800-incomparable-amount-aggregation-v1",
        "contract": jsonable(aggregation),
    }
    return a108, a109


def validate_contracts(a108: dict[str, Any], a109: dict[str, Any]) -> None:
    for acceptance_id, payload in (("A108", a108), ("A109", a109)):
        require(payload.get("task_id") == "T800", f"{acceptance_id} task mapping drift")
        require(
            payload.get("acceptance_ids") == [acceptance_id],
            f"{acceptance_id} acceptance mapping drift",
        )
        require(payload.get("status") == "PASS", f"{acceptance_id} service status drift")
        closure = payload.get("acceptance_closure") or {}
        require(closure.get("backend_service_validated") is True, "backend status drift")
        require(closure.get("ui_validation_complete") is False, "UI completion claim")
        require(
            closure.get("acceptance_status_required") == "IN PROGRESS",
            "acceptance status must remain partial",
        )
        release = payload.get("release_scope") or {}
        require(release.get("a209_closed_by_contract") is False, "A209 closure claim")
        require(release.get("mvp_release_ready") is False, "release-ready claim")

    unknown = a108.get("contract") or {}
    require(unknown.get("state") == "unreported", "A108 unknown state drift")
    require(unknown.get("amount") is None, "A108 unknown amount must be null")
    require(unknown.get("display_amount") is None, "A108 display amount must be null")
    require(unknown.get("visual_weight") is None, "A108 visual weight must be null")
    require(unknown.get("width_eligible") is False, "A108 width must be disabled")

    aggregation = a109.get("contract") or {}
    require(aggregation.get("bucket_count") == 2, "A109 bucket count drift")
    require(
        aggregation.get("incomparable_dimensions") == ["amount_kind", "period"],
        "A109 incomparable dimensions drift",
    )
    require(
        aggregation.get("cross_bucket_summation_performed") is False,
        "A109 cross-bucket sum performed",
    )
    require(aggregation.get("comparable_reported_total") is None, "A109 silent sum")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T800 amount semantics contracts.")
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    validate_source_contract()
    if args.command == "generate":
        a108, a109 = build_contracts()
        validate_contracts(a108, a109)
        write_json(A108_OUTPUT, a108)
        write_json(A109_OUTPUT, a109)
    else:
        a108, a109 = read_json(A108_OUTPUT), read_json(A109_OUTPUT)
        validate_contracts(a108, a109)
    print(
        json.dumps(
            {
                "valid": True,
                "task_id": "T800",
                "acceptance_ids": ["A108", "A109"],
                "acceptance_status": "IN PROGRESS",
                "artifacts": [
                    A108_OUTPUT.relative_to(ROOT).as_posix(),
                    A109_OUTPUT.relative_to(ROOT).as_posix(),
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
