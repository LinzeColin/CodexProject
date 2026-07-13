#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    "A105": ROOT / "artifacts/tests/a105/t705_transactional_failure_rollback_contract.json",
    "A106": ROOT / "artifacts/tests/a106/t705_change_type_coverage_contract.json",
    "A107": ROOT / "artifacts/tests/a107/t705_change_provenance_api_contract.json",
}
CHANGE_TYPES = [
    "created",
    "updated",
    "superseded",
    "revoked",
    "conflict_detected",
    "stale",
    "ingestion_failed",
]
TRIGGER_SOURCE_FIELDS = [
    "source_document_id",
    "source_id",
    "source_code",
    "source_document_url",
    "source_document_title",
    "ingestion_run_id",
    "connector_version",
    "record_mode",
    "ingestion_status",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def validate_source_contracts() -> None:
    pipeline_source = (
        ROOT / "apps/api/app/ingest/transactional_pipeline.py"
    ).read_text(encoding="utf-8")
    repository_source = (ROOT / "apps/api/app/domain_repository.py").read_text(
        encoding="utf-8"
    )
    integration_source = (
        ROOT / "tests/integration/test_database_migrations.py"
    ).read_text(encoding="utf-8")
    for token in (
        "with connection.transaction()",
        "InjectedPipelineFailure",
        "publication_rollback_verified",
        "active_data_snapshot_id = %s",
        "active_scoring_run_id = %s",
    ):
        require(token in pipeline_source, f"A105 pipeline contract missing: {token}")
    for change_type in CHANGE_TYPES:
        require(change_type in pipeline_source, f"A106 change type missing: {change_type}")
        require(change_type in integration_source, f"A106 integration probe missing: {change_type}")
    for field in TRIGGER_SOURCE_FIELDS:
        require(field in repository_source, f"A107 trigger source field missing: {field}")
    require(
        "after_failure == before_failure" in integration_source,
        "A105 rollback assertion drift",
    )

    openapi = yaml.safe_load((ROOT / "specs/api_contract.yaml").read_text(encoding="utf-8"))
    response_schema = (
        openapi["paths"]["/v1/changes"]["get"]["responses"]["200"]["content"]
        ["application/json"]["schema"]
    )
    require(response_schema.get("type") == "array", "A107 changes response must be an array")
    require(
        response_schema.get("items") == {"$ref": "#/components/schemas/ChangeEvent"},
        "A107 ChangeEvent response schema drift",
    )
    change_schema = openapi["components"]["schemas"]["ChangeEvent"]
    require(
        change_schema["properties"]["change_type"]["enum"] == CHANGE_TYPES,
        "A106 OpenAPI change type enum drift",
    )
    require("trigger_source" in change_schema["required"], "A107 trigger source not required")
    trigger_schema = openapi["components"]["schemas"]["ChangeTriggerSource"]
    require(trigger_schema["required"] == TRIGGER_SOURCE_FIELDS, "A107 trigger fields drift")


def base_contract(acceptance_id: str) -> dict[str, Any]:
    return {
        "task_id": "T705",
        "acceptance_ids": [acceptance_id],
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "implementation": [
            "apps/api/app/ingest/transactional_pipeline.py",
            "scripts/run_transactional_ingestion_pipeline.py",
            "apps/api/app/domain_repository.py",
            "specs/api_contract.yaml",
        ],
        "test_evidence": [
            "tests/unit/test_transactional_pipeline.py",
            "tests/integration/test_database_migrations.py",
        ],
        "required_validation_commands": [
            ".venv/bin/pytest -q tests/unit",
            "DATABASE_URL=<isolated-postgres-url> .venv/bin/pytest -q "
            "tests/integration/test_database_migrations.py",
            ".venv/bin/python scripts/validate_contracts.py",
        ],
        "release_scope": {
            "fixture_postgres_validation_only": True,
            "live_sec_request_performed": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }


def build_contracts() -> dict[str, dict[str, Any]]:
    validate_source_contracts()
    a105 = {
        **base_contract("A105"),
        "schema_version": "eei-a105-transactional-failure-rollback-contract-v1",
        "contract": {
            "transaction_boundary": [
                "data_snapshots",
                "fact_versions",
                "fact_version_evidence",
                "scoring_runs",
                "score_results",
                "changes",
                "active_analysis_contexts",
                "transactional_outbox",
            ],
            "failure_injection_stages": ["after_facts", "after_scores", "after_changes"],
            "publication_state_rollback_fields": [
                "fact_version_count",
                "scoring_run_count",
                "score_result_count",
                "active_data_snapshot_id",
                "active_scoring_run_id",
                "refresh_token",
                "refresh_generation",
            ],
            "failure_audit_change_type": "ingestion_failed",
            "failure_audit_is_separate_transaction": True,
            "partial_fact_or_score_publication_allowed": False,
        },
    }
    a106 = {
        **base_contract("A106"),
        "schema_version": "eei-a106-change-type-coverage-contract-v1",
        "contract": {
            "api_path": "/v1/changes",
            "change_types": CHANGE_TYPES,
            "idempotent_replay_emits_changes": False,
            "failed_publication_emits_only_failure_audit": True,
        },
    }
    a107 = {
        **base_contract("A107"),
        "schema_version": "eei-a107-change-provenance-api-contract-v1",
        "contract": {
            "api_path": "/v1/changes",
            "response_schema": "ChangeEvent[]",
            "value_fields": ["old_value", "new_value"],
            "trigger_source_fields": TRIGGER_SOURCE_FIELDS,
            "review_field": "review_required",
            "review_required_change_types": [
                "conflict_detected",
                "revoked",
                "stale",
                "ingestion_failed",
            ],
        },
    }
    return {"A105": a105, "A106": a106, "A107": a107}


def validate_contract(acceptance_id: str, payload: dict[str, Any]) -> None:
    require(payload.get("task_id") == "T705", f"{acceptance_id} task mapping drift")
    require(
        payload.get("acceptance_ids") == [acceptance_id],
        f"{acceptance_id} acceptance mapping drift",
    )
    require(payload.get("status") == "PASS", f"{acceptance_id} status must be PASS")
    release_scope = payload.get("release_scope") or {}
    require(release_scope.get("live_sec_request_performed") is False, "live request claim")
    require(release_scope.get("a209_closed_by_contract") is False, "A209 closure claim")
    require(release_scope.get("mvp_release_ready") is False, "release-ready claim")

    contract = payload.get("contract") or {}
    if acceptance_id == "A105":
        require(
            contract.get("partial_fact_or_score_publication_allowed") is False,
            "A105 partial publication must fail closed",
        )
        require(
            contract.get("failure_audit_is_separate_transaction") is True,
            "A105 failure audit boundary drift",
        )
    elif acceptance_id == "A106":
        require(contract.get("change_types") == CHANGE_TYPES, "A106 type coverage drift")
    else:
        require(
            contract.get("trigger_source_fields") == TRIGGER_SOURCE_FIELDS,
            "A107 trigger source drift",
        )
        require(contract.get("value_fields") == ["old_value", "new_value"], "value drift")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate T705/A105-A107 transactional ingestion contracts."
    )
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    validate_source_contracts()
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
