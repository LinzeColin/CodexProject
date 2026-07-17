#!/usr/bin/env python3
"""Deterministic, public-safe lineage, version, and impact kernel for S04-P2.

The module intentionally contains no filesystem or raw-inbox access.  Public
fixtures use opaque references and synthetic identities only.  They prove the
runtime contracts without claiming that private business lineage has already
been materialized.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping, Sequence


RUN_PHASE_ID = "V015_S04_P2_LINEAGE_VERSION"
TASK_ID = "KMFA-V015-S04-P2-LINEAGE-VERSION-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S04-P2-LINEAGE-VERSION"
VERSION = "1.5.0-dev-s04p2"

CRITICAL_FIELD_CLASSES = ("CRITICAL_AMOUNT", "CRITICAL_STATUS")
REQUIRED_LINEAGE_FIELDS = (
    "lineage_record_id",
    "page_ref",
    "table_ref",
    "cell_ref",
    "raw_text_private_ref",
    "canonical_field_id",
    "critical_field_class",
    "mapping_version",
    "processing_steps",
    "fact_version_ref",
)
DERIVED_NODE_TYPES = ("FACT", "METRIC", "REPORT")
REQUIRED_VERSION_BINDINGS = (
    "input_version_refs",
    "rule_version",
    "formula_version",
)


class LineageVersionError(ValueError):
    """Raised when a lineage, version, or impact contract fails closed."""


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise LineageVersionError(f"{field} is required")
    return text


def synthetic_field_lineage_records() -> list[dict[str, Any]]:
    """Return four public-safe fixtures spanning critical amount and status."""

    definitions = (
        ("revenue_amount", "CRITICAL_AMOUNT", "A1"),
        ("collection_amount", "CRITICAL_AMOUNT", "B1"),
        ("project_status", "CRITICAL_STATUS", "C1"),
        ("invoice_status", "CRITICAL_STATUS", "D1"),
    )
    records: list[dict[str, Any]] = []
    for index, (field_id, field_class, cell_ref) in enumerate(definitions, start=1):
        records.append(
            {
                "lineage_record_id": f"LIN-S04P2-SYN-{index:03d}",
                "page_ref": "PAGE::SYNTHETIC-MANAGEMENT-OVERVIEW",
                "table_ref": "TABLE::SYNTHETIC-CRITICAL-FIELDS",
                "cell_ref": f"CELL::{cell_ref}",
                "raw_text_private_ref": f"PRIVATE::RAW-TEXT::SYNTHETIC-{index:03d}",
                "canonical_field_id": field_id,
                "critical_field_class": field_class,
                "mapping_version": "MAP::S04P2-SYNTHETIC::1.0.0",
                "processing_steps": [
                    "EXTRACT_PRIVATE_TEXT",
                    "NORMALIZE_CANONICAL_FIELD",
                    "APPEND_IMMUTABLE_FACT_VERSION",
                ],
                "fact_version_ref": f"FACT-VERSION::{field_id}::1.0.0",
                "public_safe_projection": True,
                "synthetic_fixture": True,
                "contains_raw_business_value": False,
            }
        )
    validate_field_lineage(records)
    return records


def validate_field_lineage(
    records: Sequence[Mapping[str, Any]],
    *,
    declared_critical_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate field paths and require 100% coverage for declared critical fields."""

    declared = tuple(
        declared_critical_fields
        or ("revenue_amount", "collection_amount", "project_status", "invoice_status")
    )
    if not declared or len(declared) != len(set(declared)):
        raise LineageVersionError("declared critical fields must be non-empty and unique")
    seen_ids: set[str] = set()
    covered: set[str] = set()
    classes: set[str] = set()
    for record in records:
        missing = [field for field in REQUIRED_LINEAGE_FIELDS if field not in record]
        if missing:
            raise LineageVersionError("lineage fields missing: " + ",".join(missing))
        record_id = _required_text(record.get("lineage_record_id"), "lineage_record_id")
        if record_id in seen_ids:
            raise LineageVersionError("lineage_record_id must be unique")
        seen_ids.add(record_id)
        for ref_field, prefix in (
            ("page_ref", "PAGE::"),
            ("table_ref", "TABLE::"),
            ("cell_ref", "CELL::"),
            ("raw_text_private_ref", "PRIVATE::RAW-TEXT::"),
            ("fact_version_ref", "FACT-VERSION::"),
        ):
            if not _required_text(record.get(ref_field), ref_field).startswith(prefix):
                raise LineageVersionError(f"{ref_field} must be an opaque {prefix} reference")
        field_id = _required_text(record.get("canonical_field_id"), "canonical_field_id")
        field_class = _required_text(record.get("critical_field_class"), "critical_field_class")
        if field_class not in CRITICAL_FIELD_CLASSES:
            raise LineageVersionError(f"unsupported critical field class: {field_class}")
        classes.add(field_class)
        if not _required_text(record.get("mapping_version"), "mapping_version").startswith("MAP::"):
            raise LineageVersionError("mapping_version must be an opaque version reference")
        steps = record.get("processing_steps")
        if not isinstance(steps, list) or len(steps) < 2 or not all(str(step).strip() for step in steps):
            raise LineageVersionError("processing_steps must contain an ordered non-empty chain")
        if record.get("public_safe_projection") is not True:
            raise LineageVersionError("lineage record must be a public-safe projection")
        if record.get("contains_raw_business_value") is not False:
            raise LineageVersionError("raw business values are forbidden from public lineage")
        if field_id in declared:
            covered.add(field_id)
    missing_fields = sorted(set(declared) - covered)
    coverage_bps = len(covered) * 10_000 // len(declared)
    if missing_fields or coverage_bps != 10_000:
        raise LineageVersionError(
            "critical lineage coverage gate failed: " + ",".join(missing_fields)
        )
    if classes != set(CRITICAL_FIELD_CLASSES):
        raise LineageVersionError("both critical amount and status classes are required")
    return {
        "declared_critical_field_count": len(declared),
        "covered_critical_field_count": len(covered),
        "critical_field_class_count": len(classes),
        "lineage_record_count": len(records),
        "required_lineage_field_count": len(REQUIRED_LINEAGE_FIELDS),
        "lineage_coverage_bps": coverage_bps,
        "lineage_gate_passed": True,
        "actual_business_lineage_record_count": 0,
        "synthetic_lineage_record_count": len(records),
        "formal_report_allowed": False,
        "formal_report_stop_reason": "ACTUAL_BUSINESS_LINEAGE_NOT_MATERIALIZED",
    }


def synthetic_version_chain() -> dict[str, Any]:
    """Build an immutable FACT -> METRIC -> REPORT historical version chain."""

    nodes = [
        {
            "version_id": "FACT-VERSION::revenue_amount::1.0.0",
            "node_type": "FACT",
            "input_version_refs": ["SOURCE-VERSION::SYNTHETIC-LEDGER::1.0.0"],
            "rule_version": "RULE::FIELD-MAPPING::1.0.0",
            "formula_version": "FORMULA::IDENTITY::1.0.0",
            "output_ref": "FACT::SYNTHETIC-REVENUE",
            "immutable": True,
        },
        {
            "version_id": "FACT-VERSION::collection_amount::1.0.0",
            "node_type": "FACT",
            "input_version_refs": ["SOURCE-VERSION::SYNTHETIC-BANK::1.0.0"],
            "rule_version": "RULE::FIELD-MAPPING::1.0.0",
            "formula_version": "FORMULA::IDENTITY::1.0.0",
            "output_ref": "FACT::SYNTHETIC-COLLECTION",
            "immutable": True,
        },
        {
            "version_id": "METRIC-VERSION::collection_ratio::1.0.0",
            "node_type": "METRIC",
            "input_version_refs": [
                "FACT-VERSION::revenue_amount::1.0.0",
                "FACT-VERSION::collection_amount::1.0.0",
            ],
            "rule_version": "RULE::METRIC-ELIGIBILITY::1.0.0",
            "formula_version": "FORMULA::COLLECTION-RATIO::1.0.0",
            "output_ref": "METRIC::SYNTHETIC-COLLECTION-RATIO",
            "immutable": True,
        },
        {
            "version_id": "REPORT-VERSION::management_overview::1.0.0",
            "node_type": "REPORT",
            "input_version_refs": ["METRIC-VERSION::collection_ratio::1.0.0"],
            "rule_version": "RULE::REPORT-VISIBILITY::1.0.0",
            "formula_version": "FORMULA::REPORT-ASSEMBLY::1.0.0",
            "output_ref": "REPORT::SYNTHETIC-MANAGEMENT-OVERVIEW",
            "immutable": True,
        },
    ]
    chain = {
        "schema_version": "kmfa.v015.s04p2.derived_version_chain.v1",
        "source_versions": [
            "SOURCE-VERSION::SYNTHETIC-LEDGER::1.0.0",
            "SOURCE-VERSION::SYNTHETIC-BANK::1.0.0",
        ],
        "nodes": nodes,
    }
    validate_version_chain(chain)
    return chain


def validate_version_chain(chain: Mapping[str, Any]) -> dict[str, Any]:
    nodes = chain.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise LineageVersionError("version chain nodes are required")
    known_sources = {_required_text(value, "source_version") for value in chain.get("source_versions", [])}
    node_by_id: dict[str, Mapping[str, Any]] = {}
    node_types: set[str] = set()
    for node in nodes:
        version_id = _required_text(node.get("version_id"), "version_id")
        if version_id in node_by_id:
            raise LineageVersionError("version_id must be unique")
        node_type = _required_text(node.get("node_type"), "node_type")
        if node_type not in DERIVED_NODE_TYPES:
            raise LineageVersionError(f"unsupported derived node type: {node_type}")
        for binding in REQUIRED_VERSION_BINDINGS:
            if binding not in node:
                raise LineageVersionError(f"missing version binding: {binding}")
        inputs = node.get("input_version_refs")
        if not isinstance(inputs, list) or not inputs:
            raise LineageVersionError("input_version_refs must be non-empty")
        _required_text(node.get("rule_version"), "rule_version")
        _required_text(node.get("formula_version"), "formula_version")
        _required_text(node.get("output_ref"), "output_ref")
        if node.get("immutable") is not True:
            raise LineageVersionError("derived versions must be immutable")
        node_by_id[version_id] = node
        node_types.add(node_type)
    if node_types != set(DERIVED_NODE_TYPES):
        raise LineageVersionError("FACT, METRIC, and REPORT versions are all required")
    known = set(node_by_id) | known_sources
    missing = sorted(
        {
            str(ref)
            for node in nodes
            for ref in node["input_version_refs"]
            if str(ref) not in known
        }
    )
    return {
        "derived_version_node_count": len(nodes),
        "derived_version_node_type_count": len(node_types),
        "required_version_binding_count": len(REQUIRED_VERSION_BINDINGS),
        "missing_input_version_refs": missing,
        "chain_complete": not missing,
    }


def reconstruct_historical_report(chain: Mapping[str, Any], report_version_id: str) -> dict[str, Any]:
    """Return deterministic rebuild order or a truthful NOT_REBUILDABLE result."""

    summary = validate_version_chain(chain)
    nodes = {str(node["version_id"]): node for node in chain["nodes"]}
    sources = {str(value) for value in chain.get("source_versions", [])}
    target = nodes.get(report_version_id)
    if target is None or target.get("node_type") != "REPORT":
        return {
            "status": "NOT_REBUILDABLE",
            "report_version_id": report_version_id,
            "missing_input_version_refs": [report_version_id],
            "rebuild_order": [],
            "formal_report_allowed": False,
        }
    missing = set(summary["missing_input_version_refs"])
    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(version_id: str) -> None:
        if version_id in sources or version_id in visited:
            return
        node = nodes.get(version_id)
        if node is None:
            missing.add(version_id)
            return
        if version_id in visiting:
            raise LineageVersionError("derived version chain contains a cycle")
        visiting.add(version_id)
        for input_ref in node["input_version_refs"]:
            visit(str(input_ref))
        visiting.remove(version_id)
        visited.add(version_id)
        order.append(version_id)

    visit(report_version_id)
    if missing:
        return {
            "status": "NOT_REBUILDABLE",
            "report_version_id": report_version_id,
            "missing_input_version_refs": sorted(missing),
            "rebuild_order": [],
            "formal_report_allowed": False,
        }
    return {
        "status": "REBUILDABLE",
        "report_version_id": report_version_id,
        "missing_input_version_refs": [],
        "rebuild_order": order,
        "formal_report_allowed": False,
        "synthetic_time_travel_test": True,
    }


def synthetic_impact_graph() -> dict[str, Any]:
    """Build a graph where only transitive dependants are recalculated."""

    return {
        "schema_version": "kmfa.v015.s04p2.impact_graph.v1",
        "nodes": {
            "SOURCE::LEDGER": "SOURCE",
            "SOURCE::BANK": "SOURCE",
            "RULE::FIELD-MAPPING": "RULE",
            "FORMULA::COLLECTION-RATIO": "FORMULA",
            "FACT::REVENUE": "FACT",
            "FACT::COLLECTION": "FACT",
            "FACT::UNRELATED-STATUS": "FACT",
            "METRIC::COLLECTION-RATIO": "METRIC",
            "PAGE::MANAGEMENT-OVERVIEW": "PAGE",
            "REPORT::MANAGEMENT-OVERVIEW": "REPORT",
        },
        "edges": [
            ["SOURCE::LEDGER", "FACT::REVENUE"],
            ["SOURCE::BANK", "FACT::COLLECTION"],
            ["RULE::FIELD-MAPPING", "FACT::REVENUE"],
            ["RULE::FIELD-MAPPING", "FACT::COLLECTION"],
            ["FACT::REVENUE", "METRIC::COLLECTION-RATIO"],
            ["FACT::COLLECTION", "METRIC::COLLECTION-RATIO"],
            ["FORMULA::COLLECTION-RATIO", "METRIC::COLLECTION-RATIO"],
            ["METRIC::COLLECTION-RATIO", "PAGE::MANAGEMENT-OVERVIEW"],
            ["METRIC::COLLECTION-RATIO", "REPORT::MANAGEMENT-OVERVIEW"],
        ],
    }


def analyze_impact(graph: Mapping[str, Any], changed_refs: Iterable[str]) -> dict[str, Any]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, Mapping) or not nodes or not isinstance(edges, list):
        raise LineageVersionError("impact graph nodes and edges are required")
    node_ids = {str(node_id) for node_id in nodes}
    changed = {_required_text(value, "changed_ref") for value in changed_refs}
    unknown_changes = sorted(changed - node_ids)
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise LineageVersionError("impact edge must contain source and target")
        source, target = map(str, edge)
        if source not in node_ids or target not in node_ids:
            raise LineageVersionError("impact edge references an unknown node")
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1
    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited_count = 0
    while queue:
        node_id = queue.popleft()
        visited_count += 1
        for target in sorted(adjacency[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    cyclic = visited_count != len(node_ids)
    if unknown_changes or cyclic:
        return {
            "scope_known": False,
            "unknown_changed_refs": unknown_changes,
            "cycle_detected": cyclic,
            "affected_refs": [],
            "affected_by_type": {},
            "automatic_publication_allowed": False,
            "stop_reason": "IMPACT_SCOPE_UNKNOWN",
        }
    affected: set[str] = set()
    frontier = deque(sorted(changed))
    while frontier:
        source = frontier.popleft()
        for target in sorted(adjacency[source]):
            if target not in affected and target not in changed:
                affected.add(target)
                frontier.append(target)
    by_type: dict[str, list[str]] = defaultdict(list)
    for ref in sorted(affected):
        by_type[str(nodes[ref])].append(ref)
    return {
        "scope_known": True,
        "unknown_changed_refs": [],
        "cycle_detected": False,
        "affected_refs": sorted(affected),
        "affected_by_type": dict(sorted(by_type.items())),
        "automatic_publication_allowed": False,
        "stop_reason": "FORMAL_REPORT_GATE_REMAINS_CLOSED",
    }
