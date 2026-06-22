#!/usr/bin/env python3
"""Build and validate the A202 operator/legal review packet.

The packet is intentionally fail-closed: it summarizes selected live official
capture evidence for human review, but it never marks source-license review,
legal clearance, owner approval, or relationship publication as complete.
"""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from db_tools import ROOT
    from fetch_official_source_full_text import file_hash
    from load_live_official_captures import (
        LIVE_PARSER_VERSION,
        relative_artifact_locator,
        validate_live_capture_artifact,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts package.
    from scripts.db_tools import ROOT
    from scripts.fetch_official_source_full_text import file_hash
    from scripts.load_live_official_captures import (
        LIVE_PARSER_VERSION,
        relative_artifact_locator,
        validate_live_capture_artifact,
    )

SCHEMA_VERSION = "eei-a202-operator-review-packet-v1"
DEFAULT_CAPTURE_ARTIFACT = (
    ROOT / "artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json"
)
DEFAULT_PACKET_ARTIFACT = (
    ROOT / "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
)
REQUIRED_PACKET_STATUS = "PENDING_OWNER_LEGAL_CLEARANCE"
REQUIRED_GATE_IDS = (
    "live_capture_ready_for_review",
    "source_license_review",
    "passage_level_relationship_review",
    "production_owner_signoff",
    "legal_release_clearance",
    "a206_scheduler_retry_dead_letter",
    "a209_24h_operator_soak",
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def anchor_review_item(anchor: dict[str, Any]) -> dict[str, Any]:
    source_health = anchor.get("source_health")
    if not isinstance(source_health, dict):
        raise ValueError(f"{anchor.get('anchor_id')} source_health must be present")
    return {
        "anchor_id": anchor["anchor_id"],
        "title": anchor["title"],
        "document_date": anchor["document_date"],
        "official_publisher": anchor["official_publisher"],
        "source_url": anchor["source_url"],
        "source_url_sha256": anchor["source_url_sha256"],
        "source_text_sha256": anchor["source_text_sha256"],
        "source_text_excerpt": anchor["source_text_excerpt"],
        "source_health": {
            "status": source_health.get("status"),
            "http_status": source_health.get("http_status"),
            "content_type": source_health.get("content_type"),
            "text_char_count": source_health.get("text_char_count"),
            "token_coverage": source_health.get("token_coverage"),
            "attempts_count": len(source_health.get("attempts") or []),
        },
        "anchor_scope": {
            "evidence_role": anchor.get("evidence_role"),
            "publication_scope": anchor.get("publication_scope"),
            "source_use_limit": anchor.get("source_use_limit"),
        },
        "review_required": {
            "source_license_review_status": "missing",
            "passage_level_relationship_review_status": "missing",
            "production_owner_signoff_status": "missing",
            "legal_clearance_status": "missing",
        },
        "publication_controls": {
            "relationship_publication_allowed": False,
            "release_clearance": False,
            "may_create_relationship_fact_candidates": False,
            "may_publish_relationships": False,
        },
    }


def build_review_packet(
    capture_payload: dict[str, Any],
    *,
    capture_artifact_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validation = validate_live_capture_artifact(capture_payload)
    anchors = [anchor_review_item(anchor) for anchor in validation["anchors"]]
    source_health_statuses = sorted(
        {str(anchor["source_health"]["status"]) for anchor in anchors}
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1301-a202-operator-review-packet",
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_id": "T1301",
        "acceptance_ids": ["A202"],
        "status": REQUIRED_PACKET_STATUS,
        "record_mode": "live",
        "parser_version": LIVE_PARSER_VERSION,
        "generated_at": generated_at or utc_now(),
        "source_capture_artifact": relative_artifact_locator(capture_artifact_path),
        "source_capture_artifact_sha256": file_hash(capture_artifact_path),
        "source_registry": capture_payload["source_registry"],
        "source_registry_sha256": capture_payload["source_registry_sha256"],
        "counts": {
            "anchors_total": len(anchors),
            "anchors_ready_for_review": len(anchors),
            "anchors_with_source_text_committed": 0,
            "anchors_with_release_clearance": 0,
            "relationship_fact_candidates_allowed": 0,
            "relationships_publishable": 0,
        },
        "review_packet_scope": [
            "Summarize selected live official-source evidence for operator review.",
            "Bind source URL, source text hash, excerpt, source health and anchor scope.",
            "Preserve no-full-text, no-relationship-publication and no-release-clearance controls.",
            "List exact human/legal decision fields required before any stronger claim.",
        ],
        "anchors": anchors,
        "required_decision_fields": {
            "source_license_review": [
                "reviewer",
                "reviewed_at",
                "source_license_status",
                "allowed_use_scope",
                "evidence_uri",
            ],
            "passage_level_relationship_review": [
                "candidate_key",
                "supporting_anchor_ids",
                "supporting_passage_locator",
                "counter_evidence_reviewed",
                "decision",
            ],
            "production_owner_signoff": [
                "owner_actor",
                "owner_role",
                "authority_scope",
                "signature",
                "signed_at",
            ],
            "legal_release_clearance": [
                "legal_reviewer",
                "clearance_status",
                "clearance_scope",
                "risk_waiver_id_or_opinion_ref",
                "signed_at",
            ],
        },
        "closure_gates": [
            {
                "gate_id": "live_capture_ready_for_review",
                "status": "present",
                "evidence": relative_artifact_locator(capture_artifact_path),
            },
            {
                "gate_id": "source_license_review",
                "status": "missing",
                "evidence": "required before A202 closure",
            },
            {
                "gate_id": "passage_level_relationship_review",
                "status": "missing",
                "evidence": "required before relationship_fact_candidates publication",
            },
            {
                "gate_id": "production_owner_signoff",
                "status": "missing",
                "evidence": "required before production-approved facts",
            },
            {
                "gate_id": "legal_release_clearance",
                "status": "missing",
                "evidence": "required before public launch or publication claims",
            },
            {
                "gate_id": "a206_scheduler_retry_dead_letter",
                "status": "present",
                "evidence": "artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json",
            },
            {
                "gate_id": "a209_24h_operator_soak",
                "status": "missing",
                "evidence": "required long-duration operator stability evidence",
            },
        ],
        "publication_policy": {
            "relationship_fact_publication_allowed": False,
            "relationship_edge_publication_allowed": False,
            "release_clearance": False,
            "reason": (
                "Live capture evidence is ready for review only; source-license, "
                "passage-level, owner, legal and A209 gates are not complete."
            ),
        },
        "validation_summary": {
            "source_health_statuses": source_health_statuses,
            "full_text_committed": False,
            "release_clearance": False,
            "relationship_publication": False,
        },
    }


def validate_review_packet(
    packet: dict[str, Any],
    *,
    capture_artifact_path: Path = DEFAULT_CAPTURE_ARTIFACT,
) -> None:
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if packet.get("task_id") != "T1301":
        raise ValueError("task_id must be T1301")
    if packet.get("acceptance_ids") != ["A202"]:
        raise ValueError("acceptance_ids must be ['A202']")
    if packet.get("status") != REQUIRED_PACKET_STATUS:
        raise ValueError(f"status must be {REQUIRED_PACKET_STATUS}")
    if packet.get("source_capture_artifact_sha256") != file_hash(capture_artifact_path):
        raise ValueError("source_capture_artifact_sha256 does not match capture artifact")
    counts = packet.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("counts must be present")
    if counts.get("anchors_with_source_text_committed") != 0:
        raise ValueError("operator review packet must not include committed full text")
    if counts.get("anchors_with_release_clearance") != 0:
        raise ValueError("operator review packet must not claim release clearance")
    if counts.get("relationship_fact_candidates_allowed") != 0:
        raise ValueError("operator review packet must not allow relationship candidates")
    if counts.get("relationships_publishable") != 0:
        raise ValueError("operator review packet must not allow relationship publication")

    anchors = packet.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        raise ValueError("anchors must be a non-empty list")
    if counts.get("anchors_total") != len(anchors):
        raise ValueError("counts.anchors_total must match anchors length")
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise ValueError("anchor entries must be objects")
        controls = anchor.get("publication_controls")
        if not isinstance(controls, dict):
            raise ValueError(f"{anchor.get('anchor_id')} publication_controls missing")
        forbidden_true = [
            "relationship_publication_allowed",
            "release_clearance",
            "may_create_relationship_fact_candidates",
            "may_publish_relationships",
        ]
        for key in forbidden_true:
            if controls.get(key) is not False:
                raise ValueError(f"{anchor.get('anchor_id')} {key} must be false")
        if "source_text" in anchor:
            raise ValueError(f"{anchor.get('anchor_id')} must not contain source_text")
        review_required = anchor.get("review_required")
        if not isinstance(review_required, dict):
            raise ValueError(f"{anchor.get('anchor_id')} review_required missing")
        for status_key, status in review_required.items():
            if status != "missing":
                raise ValueError(f"{anchor.get('anchor_id')} {status_key} must be missing")

    gate_ids = {
        str(gate.get("gate_id"))
        for gate in packet.get("closure_gates", [])
        if isinstance(gate, dict)
    }
    if gate_ids != set(REQUIRED_GATE_IDS):
        raise ValueError("closure_gates do not match the required A202 gate set")
    for gate in packet["closure_gates"]:
        if gate["gate_id"] in {
            "live_capture_ready_for_review",
            "a206_scheduler_retry_dead_letter",
        }:
            if gate.get("status") != "present":
                raise ValueError(f"{gate['gate_id']} must be present")
        elif gate.get("status") != "missing":
            raise ValueError(f"{gate['gate_id']} must remain missing")
    policy = packet.get("publication_policy")
    if not isinstance(policy, dict):
        raise ValueError("publication_policy must be present")
    for key in (
        "relationship_fact_publication_allowed",
        "relationship_edge_publication_allowed",
        "release_clearance",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"publication_policy.{key} must be false")


def generate_packet(capture_artifact: Path, output: Path) -> dict[str, Any]:
    capture_payload = read_json(capture_artifact)
    packet = build_review_packet(
        capture_payload,
        capture_artifact_path=capture_artifact,
    )
    validate_review_packet(packet, capture_artifact_path=capture_artifact)
    write_json(output, packet)
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["generate", "validate"])
    parser.add_argument("--capture-artifact", type=Path, default=DEFAULT_CAPTURE_ARTIFACT)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET_ARTIFACT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.action == "generate":
        packet = generate_packet(args.capture_artifact, args.packet)
    else:
        packet = read_json(args.packet)
        validate_review_packet(packet, capture_artifact_path=args.capture_artifact)
    if not args.quiet:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "packet": relative_artifact_locator(args.packet),
                    "capture_artifact": relative_artifact_locator(args.capture_artifact),
                    "anchors_total": packet["counts"]["anchors_total"],
                    "publication_allowed": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
