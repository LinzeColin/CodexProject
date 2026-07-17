#!/usr/bin/env python3
"""Executable public-safe cross-Phase binding contract for KMFA v1.5 S04.

The contract joins the S04-P1 catalog/import, S04-P2 lineage/version, and
S04-P3 audit/recovery kernels with one synthetic trace.  Private import hashes
exist only inside the in-memory fixture and are never returned by the public
verification projection.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from KMFA.tools import v015_s04_p1_data_catalog as catalog
from KMFA.tools import v015_s04_p2_lineage_version_impact as lineage
from KMFA.tools import v015_s04_p3_audit_recovery as audit


RUN_PHASE_ID = "V015_S04_STAGE_REVIEW"
TRACE_ID = "TRACE::S04-STAGE-REVIEW-SYNTHETIC-001"
CHECK_IDS = (
    "CATALOG_SOURCE_BINDING",
    "IMPORT_SOURCE_VERSION_BINDING",
    "LINEAGE_FACT_VERSION_BINDING",
    "DERIVED_CHAIN_CLOSURE",
    "AUDIT_ACTION_LINKAGE",
    "EVENT_CHAIN_CLOSURE",
    "SNAPSHOT_REPORT_VERSION_BINDING",
    "SNAPSHOT_DEPENDENCY_RESTORE",
)


class StageReviewContractError(ValueError):
    """Raised when a Stage-level cross-Phase binding fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StageReviewContractError(message)


def _private_digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _registration(source_id: str, index: int) -> dict[str, Any]:
    candidate = {
        "source_id": source_id,
        "file_id": f"FILE-stage-review-synthetic-{index:02d}-a1b2c3d{index}",
        "import_run_id": f"IMP-20260714-14000{index}-stage-review-synthetic-a1b2c3d{index}",
        "file_hash": _private_digest(f"S04-STAGE-REVIEW-PRIVATE-SYNTHETIC-{index}"),
        "period": "2026-06",
        "parser_version": "1.0.0",
    }
    result = catalog.register_import(candidate, [])
    _require(result["outcome"] == "REGISTERED", "synthetic import registration failed")
    return result["record"]


def build_synthetic_stage_binding() -> dict[str, Any]:
    """Build one in-memory trace spanning the three accepted S04 Phases."""

    catalog_records = catalog.build_catalog_records()
    selected = catalog_records[:2]
    registrations = [_registration(str(row["source_id"]), index) for index, row in enumerate(selected, 1)]
    source_versions = [f"SOURCE-VERSION::{row['source_id']}::1.0.0" for row in registrations]

    field_lineage = lineage.synthetic_field_lineage_records()
    version_chain = lineage.synthetic_version_chain()
    version_chain["source_versions"] = source_versions
    version_chain["nodes"][0]["input_version_refs"] = [source_versions[0]]
    version_chain["nodes"][1]["input_version_refs"] = [source_versions[1]]
    lineage.validate_version_chain(version_chain)

    event_log = audit.AppendOnlyEventLog()
    common = {
        "actor_role": "ROLE::SYNTHETIC-CONTROL-OPERATOR",
        "subject_ref": "SUBJECT::SYNTHETIC-MANAGEMENT-REPORT",
    }
    events = []
    event_specs = (
        ("IMPORT", "PAYLOAD::SOURCE-VERSIONS-BOUND", False, None),
        ("MAPPING", "PAYLOAD::FACT-VERSIONS-BOUND", False, None),
        ("RECALCULATION", "PAYLOAD::METRIC-VERSION-BOUND", True, None),
        ("PUBLICATION", "PAYLOAD::REPORT-VERSION-BOUND", False, "RECALCULATION"),
    )
    recalculation_id = None
    for index, (action_type, payload_ref, requires_closure, closes_marker) in enumerate(event_specs, 1):
        event = event_log.append(
            action_type=action_type,
            occurred_at=f"2026-07-14T14:0{index}:00+10:00",
            payload_ref=payload_ref,
            reason_code=f"S04_STAGE_REVIEW_{action_type}",
            requires_closure=requires_closure,
            closes_event_id=recalculation_id if closes_marker else None,
            **common,
        )
        events.append(event)
        if action_type == "RECALCULATION":
            recalculation_id = event["event_id"]

    report_node = version_chain["nodes"][-1]
    all_dependencies = [
        *source_versions,
        *(str(node["version_id"]) for node in version_chain["nodes"][:-1]),
    ]
    payload = {"report_ref": str(report_node["output_ref"]), "trace_ref": TRACE_ID}
    snapshot = audit.build_snapshot(
        snapshot_id="SNAP-S04-REVIEW-REPORT-V1",
        subject_ref="SUBJECT::SYNTHETIC-MANAGEMENT-REPORT",
        subject_type="PUBLISHED_REPORT",
        version_ref=str(report_node["version_id"]),
        approval_status="APPROVED",
        dependency_version_refs=all_dependencies,
        payload=payload,
        captured_at="2026-07-14T14:05:00+10:00",
    )
    return {
        "trace_id": TRACE_ID,
        "catalog_records": selected,
        "registrations": registrations,
        "source_version_refs": source_versions,
        "field_lineage": field_lineage,
        "version_chain": version_chain,
        "events": events,
        "event_version_bindings": {
            events[0]["event_id"]: source_versions,
            events[1]["event_id"]: [str(node["version_id"]) for node in version_chain["nodes"][:2]],
            events[2]["event_id"]: [str(version_chain["nodes"][2]["version_id"])],
            events[3]["event_id"]: [str(report_node["version_id"])],
        },
        "snapshot": snapshot,
        "snapshot_payload": payload,
        "requested_restore_version_ref": str(report_node["version_id"]),
    }


def validate_stage_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    """Validate all cross-Phase joins and return a public-safe projection."""

    _require(binding.get("trace_id") == TRACE_ID, "trace identity drift")
    checks: list[dict[str, str]] = []

    catalog_records = list(binding.get("catalog_records") or [])
    registrations = list(binding.get("registrations") or [])
    _require(len(catalog_records) == len(registrations) == 2, "catalog/import cardinality drift")
    catalog_sources = [str(row.get("source_id")) for row in catalog_records]
    registration_sources = [str(row.get("source_id")) for row in registrations]
    _require(catalog_sources == registration_sources, "registration source is not present in catalog")
    checks.append({"check_id": CHECK_IDS[0], "status": "PASS"})

    source_versions = list(map(str, binding.get("source_version_refs") or []))
    expected_source_versions = [f"SOURCE-VERSION::{source_id}::1.0.0" for source_id in registration_sources]
    _require(source_versions == expected_source_versions, "import/source-version binding drift")
    checks.append({"check_id": CHECK_IDS[1], "status": "PASS"})

    field_lineage = list(binding.get("field_lineage") or [])
    lineage.validate_field_lineage(field_lineage)
    chain = dict(binding.get("version_chain") or {})
    nodes = list(chain.get("nodes") or [])
    _require(len(nodes) == 4, "derived version node count drift")
    fact_versions = [str(node.get("version_id")) for node in nodes if node.get("node_type") == "FACT"]
    lineage_fact_versions = {str(row.get("fact_version_ref")) for row in field_lineage}
    _require(set(fact_versions).issubset(lineage_fact_versions), "fact version is not bound to field lineage")
    checks.append({"check_id": CHECK_IDS[2], "status": "PASS"})

    chain_summary = lineage.validate_version_chain(chain)
    report_version = str(nodes[-1].get("version_id"))
    reconstruction = lineage.reconstruct_historical_report(chain, report_version)
    _require(chain_summary["chain_complete"] is True and reconstruction["status"] == "REBUILDABLE", "derived chain is not closed")
    _require(list(map(str, chain.get("source_versions") or [])) == source_versions, "chain source versions drift")
    checks.append({"check_id": CHECK_IDS[3], "status": "PASS"})

    events = list(binding.get("events") or [])
    action_order = [str(event.get("action_type")) for event in events]
    _require(action_order == ["IMPORT", "MAPPING", "RECALCULATION", "PUBLICATION"], "audit action linkage order drift")
    event_bindings = dict(binding.get("event_version_bindings") or {})
    expected_bindings = [source_versions, fact_versions, [str(nodes[2]["version_id"])], [report_version]]
    _require([list(map(str, event_bindings.get(str(event["event_id"]), []))) for event in events] == expected_bindings, "audit/version linkage drift")
    checks.append({"check_id": CHECK_IDS[4], "status": "PASS"})

    event_summary = audit.validate_event_chain(events)
    _require(event_summary["chain_valid"] is True and event_summary["unclosed_event_ids"] == [], "event chain is invalid or unclosed")
    checks.append({"check_id": CHECK_IDS[5], "status": "PASS"})

    snapshot = dict(binding.get("snapshot") or {})
    _require(snapshot.get("version_ref") == report_version, "snapshot is not bound to report version")
    _require(snapshot.get("subject_ref") == events[-1].get("subject_ref"), "snapshot subject is not bound to publication event")
    _require(event_bindings.get(str(events[-1]["event_id"])) == [report_version], "publication event report version drift")
    checks.append({"check_id": CHECK_IDS[6], "status": "PASS"})

    dependencies = set(map(str, snapshot.get("dependency_version_refs") or []))
    expected_dependencies = set(source_versions) | {str(node["version_id"]) for node in nodes[:-1]}
    _require(dependencies == expected_dependencies, "snapshot dependency closure drift")
    restored = audit.restore_snapshot(
        snapshot,
        payload=dict(binding.get("snapshot_payload") or {}),
        expected_version_ref=str(binding.get("requested_restore_version_ref") or ""),
        available_version_refs=expected_dependencies,
    )
    _require(restored["status"] == "RESTORED_VERIFIED" and restored["restored_version_ref"] == report_version, "snapshot restore verification failed")
    checks.append({"check_id": CHECK_IDS[7], "status": "PASS"})

    return {
        "schema_version": "kmfa.v015.s04_stage_review.binding_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "trace_id": TRACE_ID,
        "public_safe": True,
        "synthetic_fixture": True,
        "catalog_source_count": len(catalog_sources),
        "registered_source_version_count": len(source_versions),
        "lineage_fact_version_count": len(fact_versions),
        "derived_version_node_count": len(nodes),
        "audit_event_count": len(events),
        "approved_snapshot_count": 1,
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks), "failed": 0},
        "raw_root_access_count": 0,
        "actual_business_lineage_record_count": 0,
        "formal_report_allowed": False,
        "production_restore_performed": False,
        "private_import_metadata_exposed": False,
    }


def public_verification() -> dict[str, Any]:
    return validate_stage_binding(build_synthetic_stage_binding())
