"""Stage 1 source registry and connector contract validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .arxiv_adapter import ARXIV_ACKNOWLEDGEMENT, ARXIV_API_BASE_URL, ArxivAdapterError, parse_atom_feed
from .contracts import validate_source_item
from .owner_controls import load_owner_controls
from .source_ingest import SOURCE_INGEST_MAX_RESULTS, SOURCE_INGEST_POLITE_DELAY_SECONDS


SOURCE_REGISTRY_MODEL_ID = "adp-source-registry-contract-v1"
SOURCE_REGISTRY_SCHEMA_VERSION = 1
CONNECTOR_CONTRACT_VERSION = "source-connector-contract-v1"
SOURCE_REGISTRY_CANONICAL_CONFIG = "config/owner_controls.yaml"
STAGE1_ACTIVE_SOURCE_ID = "SRC-ARXIV"
STAGE1_ACTIVE_ADAPTER_ID = "arxiv.atom.v1"
STAGE1_MAX_CANARY_RESULTS = 10
STAGE1_ALLOWED_ENABLED_SOURCE_IDS = ("SRC-ARXIV",)
STAGE2_PREPRINT_SOURCE_ADAPTERS = {
    "SRC-BIORXIV": ("preprint", "biorxiv.details.v1"),
    "SRC-MEDRXIV": ("preprint", "medrxiv.details.v1"),
}
CONNECTOR_REQUIRED_OUTPUT_CONTRACTS = ("SourceItem", "SourceBatch")
CONNECTOR_FAIL_CLOSED_REASONS = (
    "network_error",
    "tls_error",
    "api_error",
    "atom_parse_error",
    "source_item_validation_error",
    "duplicate_only",
    "rate_limit_or_timeout",
)


class SourceRegistryError(ValueError):
    """Raised when the source registry contract cannot be evaluated."""


def load_source_registry_controls(path: str | Path | None = None) -> dict[str, Any]:
    """Load the canonical owner-editable registry input."""

    return load_owner_controls(path)


def build_source_registry_report(
    controls: Mapping[str, Any],
    *,
    generated_at: str,
    fixture_atom: str | None = None,
) -> dict[str, Any]:
    """Build the Stage 1 source registry contract report from owner controls."""

    sources = [_source_descriptor(source) for source in _sequence_of_mappings(controls.get("sources"))]
    active_sources = [source for source in sources if source["enabled"]]
    arxiv_source = next((source for source in sources if source["source_id"] == STAGE1_ACTIVE_SOURCE_ID), None)
    fixture_report = _fixture_report(fixture_atom, generated_at=generated_at) if fixture_atom is not None else {
        "status": "not_run",
        "source_item_count": 0,
        "errors": [],
    }
    report = {
        "model_id": SOURCE_REGISTRY_MODEL_ID,
        "schema_version": SOURCE_REGISTRY_SCHEMA_VERSION,
        "contract_version": CONNECTOR_CONTRACT_VERSION,
        "generated_at": generated_at,
        "status": "pass",
        "source_registry_source": SOURCE_REGISTRY_CANONICAL_CONFIG,
        "stage": "S1-A",
        "task_id": "S1-05-ARXIV-CONNECTOR-CONTRACT-001",
        "acceptance_id": "ADP-ACC-S1-05-ARXIV-CONNECTOR-CONTRACT",
        "connector_contract": {
            "required_output_contracts": list(CONNECTOR_REQUIRED_OUTPUT_CONTRACTS),
            "required_fail_closed_reasons": list(CONNECTOR_FAIL_CLOSED_REASONS),
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "paid_api_allowed": False,
            "secret_required": False,
            "max_canary_results": STAGE1_MAX_CANARY_RESULTS,
            "fixture_required": True,
            "real_canary_status": "DEFERRED_OR_NOT_RUN_IN_LOCAL_VALIDATION",
        },
        "active_source_ids": [source["source_id"] for source in active_sources],
        "allowed_enabled_source_ids": list(STAGE1_ALLOWED_ENABLED_SOURCE_IDS),
        "sources": sources,
        "active_adapter": {
            "source_id": STAGE1_ACTIVE_SOURCE_ID,
            "source_adapter": STAGE1_ACTIVE_ADAPTER_ID,
            "source_type": "arxiv",
            "api_base_url": ARXIV_API_BASE_URL,
            "acknowledgement": ARXIV_ACKNOWLEDGEMENT,
            "max_results_per_call": SOURCE_INGEST_MAX_RESULTS,
            "polite_min_interval_seconds": SOURCE_INGEST_POLITE_DELAY_SECONDS,
            "code_refs": [
                "arxiv-daily-push/src/arxiv_daily_push/arxiv_adapter.py",
                "arxiv-daily-push/src/arxiv_daily_push/source_ingest.py",
            ],
        },
        "fixture_validation": fixture_report,
        "blocking_reasons": [],
    }
    report["blocking_reasons"] = validate_source_registry_report(report, controls=controls, arxiv_source=arxiv_source)
    if report["blocking_reasons"]:
        report["status"] = "blocked"
    return report


def validate_source_registry_report(
    report: Mapping[str, Any],
    *,
    controls: Mapping[str, Any] | None = None,
    arxiv_source: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate the report without performing network, PDF, or write side effects."""

    errors: list[str] = []
    if report.get("model_id") != SOURCE_REGISTRY_MODEL_ID:
        errors.append("source registry model_id must be adp-source-registry-contract-v1")
    if report.get("schema_version") != SOURCE_REGISTRY_SCHEMA_VERSION:
        errors.append(f"source registry schema_version must be {SOURCE_REGISTRY_SCHEMA_VERSION}")
    if report.get("contract_version") != CONNECTOR_CONTRACT_VERSION:
        errors.append(f"connector contract_version must be {CONNECTOR_CONTRACT_VERSION}")
    contract = report.get("connector_contract")
    if not isinstance(contract, Mapping):
        errors.append("connector_contract must be an object")
    else:
        if contract.get("pdf_download_enabled") is not False:
            errors.append("connector contract must keep pdf_download_enabled false")
        if contract.get("bulk_harvest_enabled") is not False:
            errors.append("connector contract must keep bulk_harvest_enabled false")
        if int(contract.get("max_canary_results") or 0) > STAGE1_MAX_CANARY_RESULTS:
            errors.append(f"connector contract canary max must be <= {STAGE1_MAX_CANARY_RESULTS}")
    active_ids = [str(item) for item in report.get("active_source_ids") or []]
    if active_ids != list(STAGE1_ALLOWED_ENABLED_SOURCE_IDS):
        errors.append("Stage 1 Window A may enable only SRC-ARXIV as the active source")
    if SOURCE_INGEST_MAX_RESULTS != STAGE1_MAX_CANARY_RESULTS:
        errors.append(f"SOURCE_INGEST_MAX_RESULTS must be {STAGE1_MAX_CANARY_RESULTS} for Review8 Window A")
    if arxiv_source is None:
        source_map = {str(source.get("source_id")): source for source in _sequence_of_mappings(report.get("sources"))}
        arxiv_source = source_map.get(STAGE1_ACTIVE_SOURCE_ID)
    if not isinstance(arxiv_source, Mapping):
        errors.append("SRC-ARXIV source definition is required")
    else:
        if arxiv_source.get("enabled") is not True:
            errors.append("SRC-ARXIV must be enabled in Stage 1")
        if arxiv_source.get("board_id") != "B1":
            errors.append("SRC-ARXIV must remain bound to B1")
        if arxiv_source.get("access_method") != "official_atom_api":
            errors.append("SRC-ARXIV access_method must be official_atom_api")
        if arxiv_source.get("source_adapter") != STAGE1_ACTIVE_ADAPTER_ID:
            errors.append(f"SRC-ARXIV source_adapter must be {STAGE1_ACTIVE_ADAPTER_ID}")
    fixture = report.get("fixture_validation")
    if not isinstance(fixture, Mapping):
        errors.append("fixture_validation must be an object")
    elif fixture.get("status") not in {"pass", "not_run"}:
        errors.append("fixture_validation must pass or be explicitly not_run")
    if controls is not None:
        project = _mapping(controls.get("project"))
        outputs = _mapping(controls.get("outputs"))
        if project.get("production_enabled") is not False:
            errors.append("source registry validation requires project.production_enabled false in Window A")
        if outputs.get("production_acceptance_claimed") is not False:
            errors.append("source registry validation requires production_acceptance_claimed false")
    return errors


def _source_descriptor(source: Mapping[str, Any]) -> dict[str, Any]:
    source_id = str(source.get("source_id") or "")
    is_arxiv = source_id == STAGE1_ACTIVE_SOURCE_ID
    is_stage2_preprint = source_id in STAGE2_PREPRINT_SOURCE_ADAPTERS
    source_type = "arxiv" if is_arxiv else STAGE2_PREPRINT_SOURCE_ADAPTERS[source_id][0] if is_stage2_preprint else "planned"
    source_adapter = (
        STAGE1_ACTIVE_ADAPTER_ID
        if is_arxiv
        else STAGE2_PREPRINT_SOURCE_ADAPTERS[source_id][1]
        if is_stage2_preprint
        else "DEFERRED_UNTIL_STAGE2_PROMOTION"
    )
    connector_status = (
        "active"
        if is_arxiv and source.get("enabled") is True
        else "stage2_test_ready"
        if is_stage2_preprint
        else "deferred"
    )
    return {
        "source_id": source_id,
        "board_id": str(source.get("board_id") or ""),
        "enabled": source.get("enabled") is True,
        "name": str(source.get("name") or ""),
        "access_method": str(source.get("access_method") or ""),
        "tier": str(source.get("tier") or ""),
        "frequency": str(source.get("frequency") or ""),
        "weight": int(source.get("weight") or 0),
        "health_status": str(source.get("health_status") or ""),
        "source_type": source_type,
        "source_adapter": source_adapter,
        "connector_status": connector_status,
    }


def _fixture_report(fixture_atom: str, *, generated_at: str) -> dict[str, Any]:
    try:
        items = parse_atom_feed(fixture_atom, retrieved_at=generated_at)
    except ArxivAdapterError as exc:
        return {"status": "blocked", "source_item_count": 0, "errors": [str(exc)]}
    errors: list[str] = []
    for item in items:
        errors.extend(validate_source_item(item))
    if len(items) > STAGE1_MAX_CANARY_RESULTS:
        errors.append(f"fixture source_item_count must be <= {STAGE1_MAX_CANARY_RESULTS}")
    return {
        "status": "pass" if not errors else "blocked",
        "source_item_count": len(items),
        "source_ids": [str(item.get("source_id") or "") for item in items],
        "errors": errors,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]
