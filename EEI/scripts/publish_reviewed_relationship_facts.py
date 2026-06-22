#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from psycopg.types.json import Jsonb

try:
    from db_tools import connect_database
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts package.
    from scripts.db_tools import connect_database

try:
    from validate_release_decision_bundle import (
        read_json as read_release_bundle_json,
    )
    from validate_release_decision_bundle import (
        validate_signed_decision_bundle,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts package.
    from scripts.validate_release_decision_bundle import (
        read_json as read_release_bundle_json,
    )
    from scripts.validate_release_decision_bundle import (
        validate_signed_decision_bundle,
    )

PUBLISHER_VERSION = "a202-reviewed-publication-v1"
DEFAULT_SCOPE = "golden-vertical:nvidia"
DEFAULT_RECORD_MODE = "curated_official_fixture"
REQUIRED_DECISION = "approved_for_publication"
FIXTURE_REVIEW_CONTEXT = "integration_contract_fixture"
PRODUCTION_OWNER_SIGNOFF_CONTEXT = "production_owner_signoff_contract"


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def read_decision_file(
    path: Path,
    *,
    allow_fixture_review: bool,
    allow_production_owner_signoff: bool,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise RuntimeError("review decision schema_version must be 1")
    if payload.get("record_mode") != DEFAULT_RECORD_MODE:
        raise RuntimeError("review decision record_mode must be curated_official_fixture")
    review_context = require_text(payload, "review_context")
    fixture_review = bool(payload.get("fixture_review_only_not_production_clearance"))
    production_owner_signoff = bool(payload.get("production_owner_signoff"))
    if fixture_review and review_context != FIXTURE_REVIEW_CONTEXT:
        raise RuntimeError("fixture review decisions must use integration_contract_fixture context")
    if production_owner_signoff and review_context != PRODUCTION_OWNER_SIGNOFF_CONTEXT:
        raise RuntimeError(
            "production owner sign-off decisions must use "
            "production_owner_signoff_contract context"
        )
    if fixture_review and production_owner_signoff:
        raise RuntimeError(
            "review decision cannot be both fixture review and production owner sign-off"
        )
    if fixture_review and not allow_fixture_review:
        raise RuntimeError(
            "fixture review decisions require --allow-fixture-review and are not "
            "production clearance"
        )
    if production_owner_signoff and not allow_production_owner_signoff:
        raise RuntimeError(
            "production owner sign-off decisions require --allow-production-owner-signoff"
        )
    if not fixture_review and not production_owner_signoff:
        raise RuntimeError("review decision must declare an explicit review clearance mode")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise RuntimeError("review decision file must contain at least one decision")
    for decision in decisions:
        require_text(decision, "candidate_key")
        require_text(decision, "reviewer")
        require_text(decision, "reviewed_at")
        require_text(decision, "attestation")
        if decision.get("decision") != REQUIRED_DECISION:
            raise RuntimeError(f"{decision['candidate_key']} decision must be {REQUIRED_DECISION}")
        if production_owner_signoff:
            require_text(decision, "owner_actor")
            require_text(decision, "owner_role")
            require_text(decision, "authority_scope")
            require_text(decision, "signature")
    return payload


def signed_entry_hash(entry: dict[str, Any], fields: list[str]) -> str:
    return sha256_text(canonical_json({field: entry[field] for field in fields}))


def validate_release_decision_bundle_for_publication(
    bundle_path: Path,
    *,
    decision_payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        bundle = read_release_bundle_json(bundle_path)
        summary = validate_signed_decision_bundle(bundle)
    except ValueError as exc:
        raise RuntimeError(f"invalid release decision bundle: {exc}") from exc

    decision_keys = {
        str(decision["candidate_key"]) for decision in decision_payload["decisions"]
    }
    passage_reviews = {
        str(entry["candidate_key"]): entry
        for entry in bundle["passage_level_relationship_reviews"]
    }
    owner_signoffs = {
        str(entry["candidate_key"]): entry for entry in bundle["production_owner_signoffs"]
    }
    missing_passage = sorted(decision_keys - set(passage_reviews))
    missing_owner = sorted(decision_keys - set(owner_signoffs))
    if missing_passage:
        raise RuntimeError(
            "release decision bundle missing passage reviews for: "
            + ", ".join(missing_passage)
        )
    if missing_owner:
        raise RuntimeError(
            "release decision bundle missing owner signoffs for: " + ", ".join(missing_owner)
        )

    approved_source_anchors = {
        str(entry["anchor_id"]) for entry in bundle["source_license_reviews"]
    }
    candidate_reviews: dict[str, dict[str, Any]] = {}
    for candidate_key in sorted(decision_keys):
        passage = passage_reviews[candidate_key]
        owner = owner_signoffs[candidate_key]
        supporting_anchor_ids = [str(anchor_id) for anchor_id in passage["supporting_anchor_ids"]]
        missing_source_licenses = sorted(set(supporting_anchor_ids) - approved_source_anchors)
        if missing_source_licenses:
            raise RuntimeError(
                f"{candidate_key} references anchors without source-license review: "
                + ", ".join(missing_source_licenses)
            )
        candidate_reviews[candidate_key] = {
            "supporting_anchor_ids": supporting_anchor_ids,
            "supporting_passage_locator": passage["supporting_passage_locator"],
            "passage_review_signature_hash": signed_entry_hash(
                passage,
                [
                    "candidate_key",
                    "supporting_passage_locator",
                    "reviewer",
                    "reviewed_at",
                    "signature",
                ],
            ),
            "owner_signoff_signature_hash": signed_entry_hash(
                owner,
                [
                    "candidate_key",
                    "owner_actor",
                    "owner_role",
                    "authority_scope",
                    "signed_at",
                    "signature",
                ],
            ),
        }

    bundle_text = bundle_path.read_text(encoding="utf-8")
    legal = bundle["legal_release_clearance"]
    brand = bundle["brand_clearance_or_risk_waiver"]
    attestation = bundle["attestation"]
    return {
        "bundle_id": bundle["bundle_id"],
        "bundle_status": bundle["bundle_status"],
        "bundle_sha256": sha256_text(bundle_text),
        "bundle_path": str(bundle_path),
        "signed_decision_complete": True,
        "release_gate_closure_allowed": bool(bundle["release_gate_closure_allowed"]),
        "source_license_reviews": summary["source_license_reviews"],
        "passage_reviews": summary["passage_reviews"],
        "owner_signoffs": summary["owner_signoffs"],
        "legal_clearance_status": summary["legal_clearance_status"],
        "legal_clearance_signature_hash": signed_entry_hash(
            legal,
            [
                "legal_reviewer",
                "clearance_status",
                "clearance_scope",
                "risk_waiver_id_or_opinion_ref",
                "signed_at",
                "signature",
            ],
        ),
        "brand_decision": summary["brand_decision"],
        "brand_decision_signature_hash": signed_entry_hash(
            brand,
            ["decision", "scope", "evidence_uri", "signed_by", "signed_at", "signature"],
        ),
        "attestation_signature_hash": signed_entry_hash(
            attestation,
            ["signed_by", "signed_at", "signature"],
        ),
        "candidate_reviews": candidate_reviews,
    }


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"review decision missing {key}")
    return value.strip()


def reviewed_relationship_id(candidate_key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"https://eei.local/a202/reviewed/{candidate_key}/v1"))


def candidate_row(connection: object, candidate_key: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
          rfc.id,
          rfc.candidate_key,
          rfc.relationship_type,
          rfc.relationship_family,
          rfc.record_mode,
          rfc.fact_status::text,
          rfc.publication_status,
          rfc.confidence,
          rfc.independent_source_count,
          rfc.source_threshold_met,
          rfc.review_status,
          rfc.parser_version,
          rfc.structured_fact,
          rfc.counter_evidence,
          rfc.subject_resolution_id,
          subject.candidate_name AS subject_candidate_name,
          subject.matched_research_id AS subject_research_id,
          subject.matched_entity_id AS subject_entity_id,
          rfc.object_resolution_id,
          object.candidate_name AS object_candidate_name,
          object.matched_research_id AS object_research_id,
          object.matched_entity_id AS object_entity_id
        FROM relationship_fact_candidates rfc
        JOIN entity_resolution_candidates subject ON subject.id = rfc.subject_resolution_id
        JOIN entity_resolution_candidates object ON object.id = rfc.object_resolution_id
        WHERE rfc.candidate_key = %s
        """,
        (candidate_key,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"candidate not found: {candidate_key}")
    return {
        "id": str(row[0]),
        "candidate_key": row[1],
        "relationship_type": row[2],
        "relationship_family": row[3],
        "record_mode": row[4],
        "fact_status": row[5],
        "publication_status": row[6],
        "confidence": float(row[7]),
        "independent_source_count": int(row[8]),
        "source_threshold_met": bool(row[9]),
        "review_status": row[10],
        "parser_version": row[11],
        "structured_fact": row[12] or {},
        "counter_evidence": row[13] or [],
        "subject_resolution_id": str(row[14]),
        "subject_candidate_name": row[15],
        "subject_research_id": row[16],
        "subject_entity_id": str(row[17]) if row[17] else None,
        "object_resolution_id": str(row[18]),
        "object_candidate_name": row[19],
        "object_research_id": row[20],
        "object_entity_id": str(row[21]) if row[21] else None,
    }


def candidate_evidence(connection: object, candidate_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
          rfce.ingestion_evidence_chain_id,
          rfce.source_document_id,
          rfce.role::text,
          rfce.locator,
          rfce.support_excerpt,
          iec.structured_fact,
          rss.ingestion_run_id,
          sd.observed_at
        FROM relationship_fact_candidate_evidence rfce
        JOIN ingestion_evidence_chain iec ON iec.id = rfce.ingestion_evidence_chain_id
        JOIN raw_source_snapshots rss ON rss.id = iec.raw_snapshot_id
        JOIN source_documents sd ON sd.id = rfce.source_document_id
        WHERE rfce.candidate_id = %s
        ORDER BY rfce.role, rfce.source_document_id
        """,
        (candidate_id,),
    ).fetchall()
    return [
        {
            "ingestion_evidence_chain_id": str(row[0]),
            "source_document_id": str(row[1]),
            "role": row[2],
            "locator": row[3],
            "support_excerpt": row[4],
            "structured_fact": row[5] or {},
            "ingestion_run_id": str(row[6]) if row[6] else None,
            "observed_at": row[7],
        }
        for row in rows
    ]


def validate_publishable(
    candidate: dict[str, Any],
    evidence: list[dict[str, Any]],
    decision: dict[str, Any],
) -> None:
    if candidate["record_mode"] != DEFAULT_RECORD_MODE:
        raise RuntimeError(f"{candidate['candidate_key']} has unsupported record_mode")
    if candidate["publication_status"] not in {
        "candidate",
        "ready_for_review",
        "approved_for_publication",
        "published",
    }:
        raise RuntimeError(f"{candidate['candidate_key']} is not publishable")
    if candidate["review_status"] == "disputed":
        raise RuntimeError(f"{candidate['candidate_key']} is disputed")
    if candidate["subject_entity_id"] is None or candidate["object_entity_id"] is None:
        raise RuntimeError(f"{candidate['candidate_key']} has unresolved endpoints")
    if not evidence:
        raise RuntimeError(f"{candidate['candidate_key']} has no evidence chain")
    if candidate["counter_evidence"] and not decision.get("counter_evidence_reviewed"):
        raise RuntimeError(f"{candidate['candidate_key']} has unreviewed counter evidence")
    source_min = int(candidate["structured_fact"].get("source_threshold_min", 2))
    if candidate["independent_source_count"] < source_min:
        if decision.get("source_threshold_override") is not True:
            raise RuntimeError(f"{candidate['candidate_key']} requires source threshold override")
        require_text(decision, "source_threshold_override_reason")


def deterministic_research_entity_id(research_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"https://eei.local/a202/research-entity/{research_id}"))


def ensure_research_entity(
    connection: object,
    *,
    resolution_id: str,
    candidate_name: str,
    research_id: str | None,
    existing_entity_id: str | None,
) -> str | None:
    if existing_entity_id:
        return existing_entity_id
    if not research_id:
        return None
    research = connection.execute(
        """
        SELECT canonical_name, tier, power_system, research_focus, verification_status,
               entity_id
        FROM company_research_universe
        WHERE research_id = %s
        """,
        (research_id,),
    ).fetchone()
    if research is None:
        return None
    if research[5]:
        entity_id = str(research[5])
    else:
        entity_id = deterministic_research_entity_id(research_id)
        connection.execute(
            """
            INSERT INTO entities(id, canonical_name, entity_type, status, description)
            VALUES (%s, %s, 'legal_entity', 'research_target', %s)
            ON CONFLICT (id) DO UPDATE SET
              canonical_name = EXCLUDED.canonical_name,
              entity_type = EXCLUDED.entity_type,
              status = EXCLUDED.status,
              description = EXCLUDED.description,
              updated_at = now()
            """,
            (
                entity_id,
                research[0],
                (
                    "Research-universe entity materialized for reviewed A202 publication; "
                    "live facts still require production source approval."
                ),
            ),
        )
        connection.execute(
            """
            UPDATE company_research_universe
            SET entity_id = %s
            WHERE research_id = %s
            """,
            (entity_id, research_id),
        )
    connection.execute(
        """
        INSERT INTO entity_aliases(entity_id, alias, alias_type)
        VALUES (%s, %s, 'curated_candidate_name')
        ON CONFLICT (entity_id, alias, alias_type) DO NOTHING
        """,
        (entity_id, candidate_name),
    )
    connection.execute(
        """
        UPDATE entity_resolution_candidates
        SET matched_entity_id = %s
        WHERE id = %s
        """,
        (entity_id, resolution_id),
    )
    return entity_id


def ensure_candidate_endpoint_entities(connection: object, candidate: dict[str, Any]) -> None:
    candidate["subject_entity_id"] = ensure_research_entity(
        connection,
        resolution_id=candidate["subject_resolution_id"],
        candidate_name=candidate["subject_candidate_name"],
        research_id=candidate["subject_research_id"],
        existing_entity_id=candidate["subject_entity_id"],
    )
    candidate["object_entity_id"] = ensure_research_entity(
        connection,
        resolution_id=candidate["object_resolution_id"],
        candidate_name=candidate["object_candidate_name"],
        research_id=candidate["object_research_id"],
        existing_entity_id=candidate["object_entity_id"],
    )


def activate_snapshot(
    connection: object,
    *,
    snapshot_key: str,
    decision_payload: dict[str, Any],
    source_hash: str,
    as_of: datetime,
    release_decision_context: dict[str, Any] | None = None,
) -> str:
    previous = connection.execute(
        """
        SELECT id
        FROM data_snapshots
        WHERE scope = %s
          AND record_mode = %s
          AND status = 'active'
          AND snapshot_key <> %s
        ORDER BY activated_at DESC
        LIMIT 1
        """,
        (DEFAULT_SCOPE, DEFAULT_RECORD_MODE, snapshot_key),
    ).fetchone()
    previous_id = str(previous[0]) if previous else None
    if previous_id:
        connection.execute(
            """
            UPDATE data_snapshots
            SET status = 'superseded'
            WHERE id = %s
            """,
            (previous_id,),
        )
    metadata = {
        "acceptance_id": "A202",
        "task_id": "T1301",
        "publisher_version": PUBLISHER_VERSION,
        "decision_set_key": decision_payload["decision_set_key"],
        "review_context": decision_payload["review_context"],
        "fixture_review_only_not_production_clearance": bool(
            decision_payload.get("fixture_review_only_not_production_clearance")
        ),
        "production_owner_signoff": bool(decision_payload.get("production_owner_signoff")),
    }
    if release_decision_context:
        metadata.update(
            {
                "release_decision_bundle_id": release_decision_context["bundle_id"],
                "release_decision_bundle_sha256": release_decision_context[
                    "bundle_sha256"
                ],
                "signed_decision_complete": release_decision_context[
                    "signed_decision_complete"
                ],
                "legal_clearance_status": release_decision_context[
                    "legal_clearance_status"
                ],
                "brand_decision": release_decision_context["brand_decision"],
                "source_license_reviews": release_decision_context[
                    "source_license_reviews"
                ],
                "passage_reviews": release_decision_context["passage_reviews"],
                "owner_signoffs": release_decision_context["owner_signoffs"],
            }
        )
    row = connection.execute(
        """
        INSERT INTO data_snapshots(
          snapshot_key, scope, record_mode, status, source_hash, as_of, activated_at,
          supersedes_snapshot_id, metadata
        )
        VALUES (%s, %s, %s, 'active', %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_key) DO UPDATE SET
          scope = EXCLUDED.scope,
          record_mode = EXCLUDED.record_mode,
          status = 'active',
          source_hash = EXCLUDED.source_hash,
          as_of = EXCLUDED.as_of,
          activated_at = EXCLUDED.activated_at,
          supersedes_snapshot_id = EXCLUDED.supersedes_snapshot_id,
          metadata = EXCLUDED.metadata
        RETURNING id
        """,
        (
            snapshot_key,
            DEFAULT_SCOPE,
            DEFAULT_RECORD_MODE,
            source_hash,
            as_of,
            as_of,
            previous_id,
            Jsonb(metadata),
        ),
    ).fetchone()
    return str(row[0])


def owner_signature_hash(decision: dict[str, Any]) -> str | None:
    signature = decision.get("signature")
    if not isinstance(signature, str) or not signature.strip():
        return None
    payload = {
        "candidate_key": decision["candidate_key"],
        "owner_actor": decision["owner_actor"],
        "owner_role": decision["owner_role"],
        "authority_scope": decision["authority_scope"],
        "reviewed_at": decision["reviewed_at"],
        "signature": signature,
    }
    return sha256_text(canonical_json(payload))


def publish_candidate(
    connection: object,
    *,
    snapshot_id: str,
    decision_set: dict[str, Any],
    decision: dict[str, Any],
    release_decision_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = candidate_row(connection, decision["candidate_key"])
    ensure_candidate_endpoint_entities(connection, candidate)
    evidence = candidate_evidence(connection, candidate["id"])
    validate_publishable(candidate, evidence, decision)
    reviewed_at = parse_dt(decision["reviewed_at"])
    relationship_id = reviewed_relationship_id(candidate["candidate_key"])
    source_min = int(candidate["structured_fact"].get("source_threshold_min", 2))
    primary_evidence = evidence[0]
    production_owner_signoff = bool(decision_set.get("production_owner_signoff"))
    signature_hash = owner_signature_hash(decision) if production_owner_signoff else None
    candidate_release_context = (
        release_decision_context["candidate_reviews"][candidate["candidate_key"]]
        if release_decision_context
        else {}
    )
    publication_structured_fact = {
        "published_relationship_id": relationship_id,
        "publisher_version": PUBLISHER_VERSION,
        "decision_set_key": decision_set["decision_set_key"],
        "review_context": decision_set["review_context"],
        "reviewer": decision["reviewer"],
        "reviewed_at": reviewed_at.isoformat(),
        "review_attestation": decision["attestation"],
        "source_threshold_min": source_min,
        "source_threshold_override": bool(decision.get("source_threshold_override")),
        "source_threshold_override_reason": decision.get("source_threshold_override_reason"),
        "fixture_review_only_not_production_clearance": bool(
            decision_set.get("fixture_review_only_not_production_clearance")
        ),
        "production_owner_signoff": production_owner_signoff,
        "owner_actor": decision.get("owner_actor"),
        "owner_role": decision.get("owner_role"),
        "authority_scope": decision.get("authority_scope"),
        "owner_signature_hash": signature_hash,
        "release_decision_bundle_id": (
            release_decision_context["bundle_id"] if release_decision_context else None
        ),
        "release_decision_bundle_sha256": (
            release_decision_context["bundle_sha256"] if release_decision_context else None
        ),
        "signed_decision_complete": (
            release_decision_context["signed_decision_complete"]
            if release_decision_context
            else False
        ),
        "legal_clearance_status": (
            release_decision_context["legal_clearance_status"]
            if release_decision_context
            else None
        ),
        "brand_decision": (
            release_decision_context["brand_decision"] if release_decision_context else None
        ),
        "supporting_anchor_ids": candidate_release_context.get("supporting_anchor_ids"),
        "supporting_passage_locator": candidate_release_context.get(
            "supporting_passage_locator"
        ),
        "passage_review_signature_hash": candidate_release_context.get(
            "passage_review_signature_hash"
        ),
        "owner_signoff_signature_hash": candidate_release_context.get(
            "owner_signoff_signature_hash"
        ),
    }
    qualifiers = {
        "candidate_key": candidate["candidate_key"],
        "record_mode": candidate["record_mode"],
        "path_role": candidate["structured_fact"].get("path_role"),
        "direction_note": candidate["structured_fact"].get("direction_note"),
        "decision_set_key": decision_set["decision_set_key"],
        "review_context": decision_set["review_context"],
        "reviewer": decision["reviewer"],
        "reviewed_at": reviewed_at.isoformat(),
        "source_threshold_policy": {
            "minimum_independent_sources": source_min,
            "independent_source_count": candidate["independent_source_count"],
            "met_by_review_override": bool(decision.get("source_threshold_override")),
        },
        "fixture_review_only_not_production_clearance": bool(
            decision_set.get("fixture_review_only_not_production_clearance")
        ),
        "production_owner_signoff": production_owner_signoff,
        "owner_actor": decision.get("owner_actor"),
        "owner_role": decision.get("owner_role"),
        "authority_scope": decision.get("authority_scope"),
        "owner_signature_hash": signature_hash,
        "release_decision_bundle_id": (
            release_decision_context["bundle_id"] if release_decision_context else None
        ),
        "release_decision_bundle_sha256": (
            release_decision_context["bundle_sha256"] if release_decision_context else None
        ),
        "signed_decision_complete": (
            release_decision_context["signed_decision_complete"]
            if release_decision_context
            else False
        ),
        "legal_clearance_status": (
            release_decision_context["legal_clearance_status"]
            if release_decision_context
            else None
        ),
        "brand_decision": (
            release_decision_context["brand_decision"] if release_decision_context else None
        ),
        "supporting_anchor_ids": candidate_release_context.get("supporting_anchor_ids"),
        "supporting_passage_locator": candidate_release_context.get(
            "supporting_passage_locator"
        ),
        "passage_review_signature_hash": candidate_release_context.get(
            "passage_review_signature_hash"
        ),
        "owner_signoff_signature_hash": candidate_release_context.get(
            "owner_signoff_signature_hash"
        ),
    }
    observed_at = primary_evidence["observed_at"] or reviewed_at
    connection.execute(
        """
        UPDATE relationship_fact_candidates
        SET publication_status = 'published',
            source_threshold_met = true,
            review_status = 'human_verified',
            structured_fact = structured_fact || %s,
            updated_at = now()
        WHERE id = %s
        """,
        (Jsonb(publication_structured_fact), candidate["id"]),
    )
    connection.execute(
        """
        UPDATE entity_resolution_candidates
        SET review_status = 'human_verified'
        WHERE id IN (%s, %s)
        """,
        (candidate["subject_resolution_id"], candidate["object_resolution_id"]),
    )
    connection.execute(
        """
        UPDATE ingestion_evidence_chain
        SET review_status = 'human_verified'
        WHERE id = ANY(%s::uuid[])
        """,
        ([row["ingestion_evidence_chain_id"] for row in evidence],),
    )
    connection.execute(
        """
        INSERT INTO relationships(
          id, subject_entity_id, object_entity_id, relationship_type, relationship_family,
          status, confidence, observed_at, qualifiers, derivation_rule, derivation_version
        )
        VALUES (%s, %s, %s, %s, %s, 'reported', %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
          subject_entity_id = EXCLUDED.subject_entity_id,
          object_entity_id = EXCLUDED.object_entity_id,
          relationship_type = EXCLUDED.relationship_type,
          relationship_family = EXCLUDED.relationship_family,
          status = EXCLUDED.status,
          confidence = EXCLUDED.confidence,
          observed_at = EXCLUDED.observed_at,
          qualifiers = EXCLUDED.qualifiers,
          derivation_rule = EXCLUDED.derivation_rule,
          derivation_version = EXCLUDED.derivation_version
        """,
        (
            relationship_id,
            candidate["subject_entity_id"],
            candidate["object_entity_id"],
            candidate["relationship_type"],
            candidate["relationship_family"],
            candidate["confidence"],
            observed_at,
            Jsonb(qualifiers),
            "reviewed_relationship_fact_publication",
            PUBLISHER_VERSION,
        ),
    )
    for row in evidence:
        relationship_evidence_structured_fact = dict(row["structured_fact"])
        relationship_evidence_structured_fact.update(publication_structured_fact)
        connection.execute(
            """
            INSERT INTO relationship_evidence(
              relationship_id, source_document_id, role, locator, support_excerpt,
              structured_fact
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (relationship_id, source_document_id, role) DO UPDATE SET
              locator = EXCLUDED.locator,
              support_excerpt = EXCLUDED.support_excerpt,
              structured_fact = EXCLUDED.structured_fact
            """,
            (
                relationship_id,
                row["source_document_id"],
                row["role"],
                row["locator"],
                row["support_excerpt"],
                Jsonb(relationship_evidence_structured_fact),
            ),
        )
    payload = {
        "relationship_id": relationship_id,
        "candidate_id": candidate["id"],
        "candidate_key": candidate["candidate_key"],
        "subject_entity_id": candidate["subject_entity_id"],
        "object_entity_id": candidate["object_entity_id"],
        "relationship_type": candidate["relationship_type"],
        "relationship_family": candidate["relationship_family"],
        "fact_status": "reported",
        "publication_status": "published",
        "review_status": "human_verified",
        "confidence": candidate["confidence"],
        "qualifiers": qualifiers,
    }
    fact_version_id = connection.execute(
        """
        INSERT INTO fact_versions(
          snapshot_id, object_type, object_id, version_no, fact_status, record_mode,
          observed_at, source_document_id, ingestion_run_id, parser_version,
          payload_hash, payload
        )
        VALUES (%s, 'relationship', %s, 1, 'reported', %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_id, object_type, object_id, version_no) DO UPDATE SET
          fact_status = EXCLUDED.fact_status,
          record_mode = EXCLUDED.record_mode,
          observed_at = EXCLUDED.observed_at,
          source_document_id = EXCLUDED.source_document_id,
          ingestion_run_id = EXCLUDED.ingestion_run_id,
          parser_version = EXCLUDED.parser_version,
          payload_hash = EXCLUDED.payload_hash,
          payload = EXCLUDED.payload
        RETURNING id
        """,
        (
            snapshot_id,
            relationship_id,
            candidate["record_mode"],
            observed_at,
            primary_evidence["source_document_id"],
            primary_evidence["ingestion_run_id"],
            PUBLISHER_VERSION,
            sha256_text(canonical_json(payload)),
            Jsonb(payload),
        ),
    ).fetchone()[0]
    for row in evidence:
        connection.execute(
            """
            INSERT INTO fact_version_evidence(
              fact_version_id, source_document_id, role, locator, support_excerpt,
              structured_fact
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (fact_version_id, source_document_id, role) DO UPDATE SET
              locator = EXCLUDED.locator,
              support_excerpt = EXCLUDED.support_excerpt,
              structured_fact = EXCLUDED.structured_fact
            """,
            (
                fact_version_id,
                row["source_document_id"],
                row["role"],
                row["locator"],
                row["support_excerpt"],
                Jsonb(publication_structured_fact),
            ),
        )
    connection.execute(
        """
        UPDATE manual_review_queue
        SET status = 'resolved',
            reviewer = %s,
            decision = %s,
            resolved_at = %s
        WHERE queue_key = %s
        """,
        (
            decision["reviewer"],
            REQUIRED_DECISION,
            reviewed_at,
            f"review:{candidate['candidate_key']}",
        ),
    )
    return {
        "candidate_key": candidate["candidate_key"],
        "candidate_id": candidate["id"],
        "relationship_id": relationship_id,
        "fact_version_id": str(fact_version_id),
        "evidence_rows": len(evidence),
    }


def publish_reviewed_facts(
    *,
    decision_path: Path,
    snapshot_key: str,
    allow_fixture_review: bool,
    allow_production_owner_signoff: bool,
    release_decision_bundle_path: Path | None = None,
) -> dict[str, Any]:
    decision_payload = read_decision_file(
        decision_path,
        allow_fixture_review=allow_fixture_review,
        allow_production_owner_signoff=allow_production_owner_signoff,
    )
    reviewed_at = max(
        parse_dt(decision["reviewed_at"]) for decision in decision_payload["decisions"]
    )
    release_decision_context = None
    if decision_payload.get("production_owner_signoff"):
        if release_decision_bundle_path is None:
            raise RuntimeError(
                "production owner sign-off publication requires --release-decision-bundle"
            )
        release_decision_context = validate_release_decision_bundle_for_publication(
            release_decision_bundle_path,
            decision_payload=decision_payload,
        )
    elif release_decision_bundle_path is not None:
        raise RuntimeError(
            "--release-decision-bundle is only allowed for production owner sign-off publication"
        )
    source_hash = sha256_text(decision_path.read_text(encoding="utf-8"))
    with connect_database() as connection:
        snapshot_id = activate_snapshot(
            connection,
            snapshot_key=snapshot_key,
            decision_payload=decision_payload,
            source_hash=source_hash,
            as_of=reviewed_at,
            release_decision_context=release_decision_context,
        )
        published = [
            publish_candidate(
                connection,
                snapshot_id=snapshot_id,
                decision_set=decision_payload,
                decision=decision,
                release_decision_context=release_decision_context,
            )
            for decision in decision_payload["decisions"]
        ]
    return {
        "published": True,
        "publisher_version": PUBLISHER_VERSION,
        "snapshot_key": snapshot_key,
        "decision_set_key": decision_payload["decision_set_key"],
        "fixture_review_only_not_production_clearance": bool(
            decision_payload.get("fixture_review_only_not_production_clearance")
        ),
        "production_owner_signoff": bool(decision_payload.get("production_owner_signoff")),
        "release_decision_bundle_id": (
            release_decision_context["bundle_id"] if release_decision_context else None
        ),
        "release_decision_bundle_sha256": (
            release_decision_context["bundle_sha256"] if release_decision_context else None
        ),
        "signed_decision_complete": (
            release_decision_context["signed_decision_complete"]
            if release_decision_context
            else False
        ),
        "legal_clearance_status": (
            release_decision_context["legal_clearance_status"]
            if release_decision_context
            else None
        ),
        "brand_decision": (
            release_decision_context["brand_decision"] if release_decision_context else None
        ),
        "published_count": len(published),
        "published_relationships": published,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish reviewed relationship fact candidates as formal relationship facts."
    )
    parser.add_argument("--review-decisions", required=True, type=Path)
    parser.add_argument(
        "--snapshot-key",
        default="a202-reviewed-golden-vertical",
        help="Data snapshot key for the reviewed publication set.",
    )
    parser.add_argument(
        "--allow-fixture-review",
        action="store_true",
        help=(
            "Allow test fixture decisions that are explicitly not production legal/data "
            "clearance."
        ),
    )
    parser.add_argument(
        "--allow-production-owner-signoff",
        action="store_true",
        help="Allow decisions signed by a production data owner authority contract.",
    )
    parser.add_argument(
        "--release-decision-bundle",
        type=Path,
        help=(
            "Signed A202/A210 release decision bundle required for production owner "
            "sign-off publication. Template bundles fail closed."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = publish_reviewed_facts(
        decision_path=args.review_decisions,
        snapshot_key=args.snapshot_key,
        allow_fixture_review=args.allow_fixture_review,
        allow_production_owner_signoff=args.allow_production_owner_signoff,
        release_decision_bundle_path=args.release_decision_bundle,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
