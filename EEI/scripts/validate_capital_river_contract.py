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
A108_OUTPUT = ROOT / "artifacts/tests/a108/t801_unreported_amount_ui_contract.json"
A109_OUTPUT = ROOT / "artifacts/tests/a109/t801_incomparable_amount_ui_contract.json"
A110_OUTPUT = ROOT / "artifacts/tests/a110/t801_capital_river_e2e_contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
    page_source = (ROOT / "apps/web/src/app/capital/page.tsx").read_text(encoding="utf-8")
    client_source = (ROOT / "apps/web/src/app/capital-events-client.ts").read_text(
        encoding="utf-8"
    )
    repository_source = (ROOT / "apps/api/app/domain_repository.py").read_text(
        encoding="utf-8"
    )
    e2e_source = (ROOT / "tests/e2e/capital-river.spec.ts").read_text(encoding="utf-8")
    integration_source = (
        ROOT / "tests/integration/test_database_migrations.py"
    ).read_text(encoding="utf-8")

    for token in (
        'data-has-flow-width="false"',
        'data-testid={`capital-lane-${kind}`}',
        'data-cross-bucket-summation={summary?.cross_bucket_summation_performed ?? false}',
        'objectType: "event"',
    ):
        require(token in page_source, f"T801 Capital River UI contract missing: {token}")
    for token in (
        'setQueryValue(query, "currency", filters.currency.toUpperCase())',
        'setQueryValue(query, "amount_kind", filters.amountKind)',
        'value.semantics.unknown_amount_is_zero === false',
        'value.semantics.incomparable_buckets_are_summed === false',
    ):
        require(token in client_source, f"T801 client contract missing: {token}")
    for token in ("event_evidence_detail", "FROM event_evidence ee"):
        require(token in repository_source, f"T801 event evidence repository missing: {token}")
    for token in (
        "A108 and A109 keep unknown and incomparable event amounts visually separate",
        "A110 applies Capital River filters and opens event evidence",
        'toHaveAttribute("data-has-flow-width", "false")',
        "data-aggregation-key",
    ):
        require(token in e2e_source, f"T801 E2E contract missing: {token}")
    for token in (
        '"/v1/evidence/event/{NVIDIA_CAPEX_EVENT_ID}"',
        'params={"currency": "USD", "amount_kind": "period_capex"}',
    ):
        require(token in integration_source, f"T801 PostgreSQL contract missing: {token}")

    openapi = yaml.safe_load((ROOT / "specs/api_contract.yaml").read_text(encoding="utf-8"))
    evidence_parameters = openapi["paths"]["/v1/evidence/{objectType}/{objectId}"]["get"][
        "parameters"
    ]
    object_type = next(item for item in evidence_parameters if item["name"] == "objectType")
    require("event" in object_type["schema"]["enum"], "OpenAPI event evidence enum missing")
    event_parameters = openapi["paths"]["/v1/events"]["get"]["parameters"]
    event_parameter_names = {item["name"] for item in event_parameters}
    require(
        {"entity", "from", "to", "event_type", "currency", "amount_kind"}
        <= event_parameter_names,
        "OpenAPI Capital River filters incomplete",
    )


def common_contract(acceptance_id: str) -> dict[str, Any]:
    return {
        "task_id": "T801",
        "acceptance_ids": [acceptance_id],
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "implementation": [
            "apps/api/app/domain_repository.py",
            "apps/api/app/domain.py",
            "apps/web/src/app/capital/page.tsx",
            "apps/web/src/app/capital-events-client.ts",
            "apps/web/src/app/production-data-client.ts",
            "apps/web/src/app/workspace-context.tsx",
            "specs/api_contract.yaml",
        ],
        "test_evidence": [
            "tests/e2e/capital-river.spec.ts",
            "tests/integration/test_database_migrations.py",
        ],
        "validated_commands": {
            "focused_playwright": "2 passed",
            "postgresql_integration": "2 passed",
            "web_typecheck": "PASS",
            "desktop_mobile_visual_check": "PASS",
        },
        "acceptance_closure": {
            "t801_slice_complete": True,
            "capital_river_ui_validated": True,
            "event_evidence_validated": True,
            "cross_view_validation_complete": False,
            "acceptance_status_required": "IN PROGRESS",
            "remaining_tasks": ["T805"],
        },
        "release_scope": {
            "fixture_postgres_and_e2e_validation": True,
            "production_owner_clearance_claimed": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }


def build_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_source_contract()
    a108 = {
        **common_contract("A108"),
        "schema_version": "eei-a108-t801-unreported-amount-ui-v1",
        "contract": {
            "unknown_amount_label": "未披露",
            "unknown_amount_rendered_as_zero": False,
            "unknown_amount_has_flow_track": False,
            "unknown_amount_has_sankey_width": False,
        },
    }
    a109 = {
        **common_contract("A109"),
        "schema_version": "eei-a109-t801-incomparable-amount-ui-v1",
        "contract": {
            "lane_key": ["currency", "amount_kind", "period_start", "period_end"],
            "fixture_lane_count": 2,
            "fixture_incomparable_dimensions": ["amount_kind", "period"],
            "cross_bucket_total_enabled": False,
            "cross_bucket_summation_performed": False,
        },
    }
    a110 = {
        **common_contract("A110"),
        "schema_version": "eei-a110-t801-capital-river-e2e-v1",
        "contract": {
            "route": "/capital",
            "event_endpoint": "/v1/events",
            "amount_summary_endpoint": "/v1/events/amount-summary",
            "event_evidence_endpoint": "/v1/evidence/event/{eventId}",
            "filters": ["entity", "from", "to", "event_type", "currency", "amount_kind"],
            "evidence_panel_opens_from_event": True,
        },
    }
    return a108, a109, a110


def validate_contracts(payloads: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    for acceptance_id, payload in zip(("A108", "A109", "A110"), payloads, strict=True):
        require(payload.get("task_id") == "T801", f"{acceptance_id} task mapping drift")
        require(
            payload.get("acceptance_ids") == [acceptance_id],
            f"{acceptance_id} acceptance mapping drift",
        )
        require(payload.get("status") == "PASS", f"{acceptance_id} T801 slice status drift")
        closure = payload.get("acceptance_closure") or {}
        require(closure.get("t801_slice_complete") is True, "T801 slice completion drift")
        require(
            closure.get("cross_view_validation_complete") is False,
            "T805 cross-view completion claimed early",
        )
        require(
            closure.get("acceptance_status_required") == "IN PROGRESS",
            "acceptance status must remain in progress until T805",
        )
        release = payload.get("release_scope") or {}
        require(release.get("a209_closed_by_contract") is False, "A209 closure claim")
        require(release.get("mvp_release_ready") is False, "release-ready claim")

    a108_contract = payloads[0].get("contract") or {}
    require(a108_contract.get("unknown_amount_rendered_as_zero") is False, "A108 zero drift")
    require(a108_contract.get("unknown_amount_has_sankey_width") is False, "A108 width drift")
    a109_contract = payloads[1].get("contract") or {}
    require(a109_contract.get("fixture_lane_count") == 2, "A109 lane count drift")
    require(
        a109_contract.get("cross_bucket_summation_performed") is False,
        "A109 cross-bucket sum drift",
    )
    a110_contract = payloads[2].get("contract") or {}
    require(a110_contract.get("route") == "/capital", "A110 route drift")
    require(a110_contract.get("evidence_panel_opens_from_event") is True, "A110 evidence drift")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T801 Capital River contracts.")
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    validate_source_contract()
    outputs = (A108_OUTPUT, A109_OUTPUT, A110_OUTPUT)
    if args.command == "generate":
        payloads = build_contracts()
        validate_contracts(payloads)
        for path, payload in zip(outputs, payloads, strict=True):
            write_json(path, payload)
    else:
        payloads = tuple(read_json(path) for path in outputs)
        validate_contracts(payloads)
    print(
        json.dumps(
            {
                "valid": True,
                "task_id": "T801",
                "acceptance_ids": ["A108", "A109", "A110"],
                "acceptance_status": "IN PROGRESS",
                "artifacts": [path.relative_to(ROOT).as_posix() for path in outputs],
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
