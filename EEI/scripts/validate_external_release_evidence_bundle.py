#!/usr/bin/env python3
"""Generate and validate the external release-evidence bundle preflight.

This preflight gives operators one contract for the external evidence still
blocking MVP release: A202 source/legal/owner decisions, A210 brand clearance,
A026/A027 production gold labels, and A209 final soak completion. It does not
close any of those gates by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-external-release-evidence-bundle-preflight-v1"
PACKET_SCHEMA_VERSION = "eei-external-release-operator-intake-packet-v1"
DEFAULT_RELEASE_DECISION_CONTRACT = (
    ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"
)
DEFAULT_A202_INTAKE_TEMPLATE = (
    ROOT / "artifacts/tests/a202/t1301_a202_release_decision_intake_template.json"
)
DEFAULT_A202_OPERATOR_REVIEW_PACKET = (
    ROOT / "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
)
DEFAULT_BRAND_PREFLIGHT = (
    ROOT / "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json"
)
DEFAULT_BRAND_INTAKE_TEMPLATE = (
    ROOT / "artifacts/tests/a210/t1309_brand_clearance_intake_template.json"
)
DEFAULT_ENTITY_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json"
)
DEFAULT_RELATIONSHIP_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json"
)
DEFAULT_GOLD_INTAKE_TEMPLATE = (
    ROOT / "artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json"
)
DEFAULT_GOLD_OPERATOR_LABELING_PACKET = (
    ROOT / "artifacts/tests/a026/t904_a026_a027_operator_labeling_packet.json"
)
DEFAULT_OPERATOR_SOAK_FINALIZATION = (
    ROOT / "artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json"
)
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a205/t1303_external_release_evidence_bundle_preflight.json"
DEFAULT_PACKET_OUTPUT = (
    ROOT / "artifacts/tests/a205/t1303_external_release_operator_intake_packet.json"
)

REQUIRED_TASK_IDS = ["T1301", "T1303", "T1307", "T1309", "T904"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A204", "A205", "A209", "A210", "A026", "A027"]
REQUIRED_EXTERNAL_INPUTS = [
    "A202_source_license_passage_owner_legal_release",
    "A210_brand_legal_market_clearance_or_risk_waiver",
    "A026_entity_resolution_production_gold_set",
    "A027_relationship_extraction_production_gold_set",
    "A209_24h_operator_soak_finalization",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{display_path(path)} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_ref(path: Path) -> dict[str, str]:
    return {"path": display_path(path), "sha256": sha256_file(path)}


def release_decision_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_contract": payload.get("release_gate_closed_by_contract"),
        "relationship_publication_allowed": payload.get("relationship_publication_allowed"),
        "public_brand_launch_allowed": payload.get("public_brand_launch_allowed"),
    }


def a202_operator_review_summary(payload: dict[str, Any]) -> dict[str, Any]:
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    publication_policy = (
        payload.get("publication_policy")
        if isinstance(payload.get("publication_policy"), dict)
        else {}
    )
    validation_summary = (
        payload.get("validation_summary")
        if isinstance(payload.get("validation_summary"), dict)
        else {}
    )
    gate_statuses = {
        str(gate.get("gate_id")): gate.get("status")
        for gate in payload.get("closure_gates", [])
        if isinstance(gate, dict) and gate.get("gate_id")
    }
    return {
        "status": payload.get("status"),
        "source_capture_artifact": payload.get("source_capture_artifact"),
        "source_capture_artifact_sha256": payload.get("source_capture_artifact_sha256"),
        "live_capture_ready_for_review": gate_statuses.get("live_capture_ready_for_review")
        == "present",
        "source_license_review_status": gate_statuses.get("source_license_review"),
        "passage_level_relationship_review_status": gate_statuses.get(
            "passage_level_relationship_review"
        ),
        "production_owner_signoff_status": gate_statuses.get("production_owner_signoff"),
        "legal_release_clearance_status": gate_statuses.get("legal_release_clearance"),
        "a209_24h_operator_soak_status": gate_statuses.get("a209_24h_operator_soak"),
        "anchors_ready_for_review": counts.get("anchors_ready_for_review"),
        "anchors_with_source_text_committed": counts.get("anchors_with_source_text_committed"),
        "relationship_candidates_ready_for_review": counts.get(
            "relationship_candidates_ready_for_review"
        ),
        "relationship_candidate_source_anchors": counts.get(
            "relationship_candidate_source_anchors"
        ),
        "relationship_fact_candidates_allowed": counts.get(
            "relationship_fact_candidates_allowed"
        ),
        "relationships_publishable": counts.get("relationships_publishable"),
        "relationship_fact_publication_allowed": publication_policy.get(
            "relationship_fact_publication_allowed"
        ),
        "relationship_edge_publication_allowed": publication_policy.get(
            "relationship_edge_publication_allowed"
        ),
        "release_clearance": publication_policy.get("release_clearance"),
        "full_text_committed": validation_summary.get("full_text_committed"),
    }


def brand_summary(payload: dict[str, Any]) -> dict[str, Any]:
    release_gate = (
        payload.get("release_gate") if isinstance(payload.get("release_gate"), dict) else {}
    )
    current = (
        payload.get("current_clearance_status")
        if isinstance(payload.get("current_clearance_status"), dict)
        else {}
    )
    return {
        "release_gate_status": release_gate.get("status"),
        "public_release_allowed": release_gate.get("public_release_allowed"),
        "a210_status": current.get("a210_status"),
        "formal_legal_clearance": current.get("formal_legal_clearance"),
        "market_clearance": current.get("market_clearance"),
        "signed_risk_waiver": current.get("signed_risk_waiver"),
        "owner_signoff": current.get("owner_signoff"),
    }


def gold_summary(payload: dict[str, Any], acceptance_id: str) -> dict[str, Any]:
    focus = (
        payload.get("focus_quality_result")
        if isinstance(payload.get("focus_quality_result"), dict)
        else {}
    )
    metrics = focus.get("metrics") if isinstance(focus.get("metrics"), dict) else {}
    fixture_policy = (
        payload.get("fixture_policy") if isinstance(payload.get("fixture_policy"), dict) else {}
    )
    return {
        "focus_acceptance_id": payload.get("focus_acceptance_id"),
        "expected_acceptance_id": acceptance_id,
        "status": focus.get("status"),
        "threshold_result": focus.get("threshold_result"),
        "release_gate_closure_allowed": focus.get("release_gate_closure_allowed"),
        "sample_count": metrics.get("sample_count"),
        "precision": metrics.get("precision"),
        "source_coverage_min": metrics.get("source_coverage_min"),
        "production_gold_set": fixture_policy.get("production_gold_set"),
    }


def soak_finalization_summary(payload: dict[str, Any]) -> dict[str, Any]:
    heartbeat = (
        (payload.get("source_statuses") or {}).get("heartbeat")
        if isinstance(payload.get("source_statuses"), dict)
        else {}
    )
    if not isinstance(heartbeat, dict):
        heartbeat = {}
    return {
        "status": payload.get("status"),
        "a209_evidence_ready_for_release_manager": payload.get(
            "a209_evidence_ready_for_release_manager"
        ),
        "downstream_release_gate_refresh_allowed": payload.get(
            "downstream_release_gate_refresh_allowed"
        ),
        "release_gate_closed_by_finalizer": payload.get("release_gate_closed_by_finalizer"),
        "windows_completed": heartbeat.get("windows_completed"),
        "target_windows": heartbeat.get("target_windows"),
        "windows_failed": heartbeat.get("windows_failed"),
        "progress_status": heartbeat.get("progress_status"),
    }


def missing_inputs(
    *,
    release_decision: dict[str, Any],
    a202_operator_review: dict[str, Any],
    brand: dict[str, Any],
    entity_gold: dict[str, Any],
    relationship_gold: dict[str, Any],
    soak_finalization: dict[str, Any],
) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    if release_decision.get("relationship_publication_allowed") is not True:
        reason = (
            "signed A202 source/license/passage/owner/legal release is not supplied; "
            "operator review packet is present for review"
            if a202_operator_review.get("live_capture_ready_for_review") is True
            else "live capture/operator review packet is not ready and relationship "
            "publication clearance is not supplied"
        )
        missing.append(
            {
                "input_id": "A202_source_license_passage_owner_legal_release",
                "acceptance_id": "A202",
                "reason": reason,
            }
        )
    if brand.get("public_release_allowed") is not True or brand.get("a210_status") != "DONE":
        missing.append(
            {
                "input_id": "A210_brand_legal_market_clearance_or_risk_waiver",
                "acceptance_id": "A210",
                "reason": "brand public release clearance or risk waiver is not complete",
            }
        )
    if entity_gold.get("release_gate_closure_allowed") is not True:
        missing.append(
            {
                "input_id": "A026_entity_resolution_production_gold_set",
                "acceptance_id": "A026",
                "reason": "entity-resolution production gold threshold is not met",
            }
        )
    if relationship_gold.get("release_gate_closure_allowed") is not True:
        missing.append(
            {
                "input_id": "A027_relationship_extraction_production_gold_set",
                "acceptance_id": "A027",
                "reason": "relationship-extraction production gold threshold is not met",
            }
        )
    if soak_finalization.get("downstream_release_gate_refresh_allowed") is not True:
        progress = ""
        if soak_finalization.get("windows_completed") is not None:
            progress = (
                f" at {soak_finalization.get('windows_completed')}/"
                f"{soak_finalization.get('target_windows')} windows"
            )
        missing.append(
            {
                "input_id": "A209_24h_operator_soak_finalization",
                "acceptance_id": "A209",
                "reason": f"A209 finalization does not allow downstream refresh{progress}",
            }
        )
    return missing


def build_preflight(
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    a202_operator_review_packet_path: Path = DEFAULT_A202_OPERATOR_REVIEW_PACKET,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    release_decision = release_decision_summary(read_json(release_decision_contract_path))
    a202_operator_review = a202_operator_review_summary(read_json(a202_operator_review_packet_path))
    brand = brand_summary(read_json(brand_preflight_path))
    entity_gold = gold_summary(read_json(entity_gold_evaluation_path), "A026")
    relationship_gold = gold_summary(read_json(relationship_gold_evaluation_path), "A027")
    soak_finalization = soak_finalization_summary(read_json(operator_soak_finalization_path))
    missing = missing_inputs(
        release_decision=release_decision,
        a202_operator_review=a202_operator_review,
        brand=brand,
        entity_gold=entity_gold,
        relationship_gold=relationship_gold,
        soak_finalization=soak_finalization,
    )
    ready = not missing
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1303-external-release-evidence-bundle-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_READY"
        if ready
        else "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED",
        "external_release_evidence_ready": ready,
        "release_manager_preflight_refresh_allowed": ready,
        "mvp_release_gate_refresh_allowed": ready,
        "release_gate_closed_by_bundle_preflight": False,
        "required_external_inputs": REQUIRED_EXTERNAL_INPUTS,
        "source_files": {
            "release_decision_contract": display_path(release_decision_contract_path),
            "release_decision_contract_sha256": sha256_file(release_decision_contract_path),
            "a202_operator_review_packet": display_path(a202_operator_review_packet_path),
            "a202_operator_review_packet_sha256": sha256_file(
                a202_operator_review_packet_path
            ),
            "brand_preflight": display_path(brand_preflight_path),
            "brand_preflight_sha256": sha256_file(brand_preflight_path),
            "entity_gold_evaluation": display_path(entity_gold_evaluation_path),
            "entity_gold_evaluation_sha256": sha256_file(entity_gold_evaluation_path),
            "relationship_gold_evaluation": display_path(relationship_gold_evaluation_path),
            "relationship_gold_evaluation_sha256": sha256_file(relationship_gold_evaluation_path),
            "operator_soak_finalization": display_path(operator_soak_finalization_path),
            "operator_soak_finalization_sha256": sha256_file(operator_soak_finalization_path),
        },
        "gate_statuses": {
            "release_decision": release_decision,
            "a202_operator_review": a202_operator_review,
            "brand": brand,
            "entity_gold": entity_gold,
            "relationship_gold": relationship_gold,
            "operator_soak_finalization": soak_finalization,
        },
        "missing_external_inputs": missing,
        "operator_next_actions": operator_next_actions(ready),
        "validation_policy": {
            "repository_templates_count_as_clearance": False,
            "repository_fixtures_count_as_clearance": False,
            "a209_partial_heartbeat_counts_as_clearance": False,
            "all_external_inputs_required_before_release_manager_refresh": True,
        },
        "non_claims": [
            "This bundle preflight does not certify legal, source-license, brand "
            "or market clearance.",
            "This bundle preflight does not convert templates or fixtures into clearance.",
            "This bundle preflight does not close A202, A209, A210, A026 or A027.",
            "This bundle preflight does not activate release-manager or MVP release gates.",
        ],
        "rollback": [
            "Regenerate this preflight from the source gate artifacts.",
            "Do not delete operator-supplied signed evidence bundles during rollback.",
            "Do not delete live A209 checkpoint or log files during rollback.",
        ],
    }


def operator_next_actions(ready: bool) -> list[str]:
    if ready:
        return [
            "Regenerate release-manager activation and MVP release-gate preflights.",
            "Run make verify and root governance before release-manager activation.",
        ]
    return [
        "Attach real signed A202 source/license/passage/owner/legal evidence.",
        "Attach real signed A210 brand clearance or risk waiver evidence.",
        "Attach production A026/A027 gold-label evidence that meets thresholds.",
        "Wait for A209 finalization to allow downstream release-gate refresh.",
    ]


def intake_item(
    *,
    input_id: str,
    acceptance_id: str,
    label: str,
    required_source: dict[str, str],
    supporting_sources: list[dict[str, str]] | None = None,
    validation_command: str,
    completion_criteria: list[str],
    missing_inputs: list[dict[str, str]],
) -> dict[str, Any]:
    missing_match = next(
        (row for row in missing_inputs if row.get("input_id") == input_id),
        None,
    )
    return {
        "input_id": input_id,
        "acceptance_id": acceptance_id,
        "label": label,
        "current_status": "MISSING_OR_BLOCKED" if missing_match else "READY_FOR_PREFLIGHT",
        "blocking_reason": missing_match.get("reason") if missing_match else "",
        "required_source": required_source,
        "supporting_sources": supporting_sources or [],
        "validation_command": validation_command,
        "completion_criteria": completion_criteria,
        "template_or_partial_evidence_counts_as_clearance": False,
    }


def build_operator_intake_packet(
    *,
    preflight_path: Path = DEFAULT_OUTPUT,
    a202_intake_template_path: Path = DEFAULT_A202_INTAKE_TEMPLATE,
    a202_operator_review_packet_path: Path = DEFAULT_A202_OPERATOR_REVIEW_PACKET,
    brand_intake_template_path: Path = DEFAULT_BRAND_INTAKE_TEMPLATE,
    gold_intake_template_path: Path = DEFAULT_GOLD_INTAKE_TEMPLATE,
    gold_operator_labeling_packet_path: Path = DEFAULT_GOLD_OPERATOR_LABELING_PACKET,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    preflight = read_json(preflight_path)
    missing = preflight.get("missing_external_inputs")
    if not isinstance(missing, list):
        raise ValueError("external release operator intake packet requires missing_external_inputs")
    gate_statuses = preflight.get("gate_statuses")
    if not isinstance(gate_statuses, dict):
        raise ValueError("external release operator intake packet requires gate_statuses")

    required_inputs = [
        intake_item(
            input_id="A202_source_license_passage_owner_legal_release",
            acceptance_id="A202",
            label="A202 signed source/license/passage/owner/legal release decision",
            required_source=source_ref(a202_intake_template_path),
            supporting_sources=[source_ref(a202_operator_review_packet_path)],
            validation_command=(
                "make generate-a202-signed-intake-preflight "
                "validate-a202-signed-intake-preflight"
            ),
            completion_criteria=[
                "source-license reviews cover every required Golden Vertical source anchor",
                "passage-level relationship reviews cover every Golden Vertical "
                "relationship candidate",
                "production owner signoffs cover every candidate without duplicates or unknowns",
                "legal release clearance is signed and hash-bound",
            ],
            missing_inputs=missing,
        ),
        intake_item(
            input_id="A210_brand_legal_market_clearance_or_risk_waiver",
            acceptance_id="A210",
            label="A210 formal brand legal/market clearance or signed risk waiver",
            required_source=source_ref(brand_intake_template_path),
            validation_command="make generate-brand-clearance-artifact validate-brand-clearance",
            completion_criteria=[
                "every required brand surface and jurisdiction is reviewed",
                "formal clearance or risk waiver has accepted signed status",
                "public launch decision scope is explicit",
            ],
            missing_inputs=missing,
        ),
        intake_item(
            input_id="A026_entity_resolution_production_gold_set",
            acceptance_id="A026",
            label="A026 production entity-resolution gold labels",
            required_source=source_ref(gold_intake_template_path),
            supporting_sources=[source_ref(gold_operator_labeling_packet_path)],
            validation_command=(
                "make generate-gold-quality-evaluation-artifacts "
                "validate-gold-quality-evaluation"
            ),
            completion_criteria=[
                "at least 50 operator-supplied non-fixture entity-resolution cases",
                "precision is at least 95%",
                "source-license and passage-review references are present",
            ],
            missing_inputs=missing,
        ),
        intake_item(
            input_id="A027_relationship_extraction_production_gold_set",
            acceptance_id="A027",
            label="A027 production relationship-extraction gold labels",
            required_source=source_ref(gold_intake_template_path),
            supporting_sources=[source_ref(gold_operator_labeling_packet_path)],
            validation_command=(
                "make generate-gold-quality-evaluation-artifacts "
                "validate-gold-quality-evaluation"
            ),
            completion_criteria=[
                "at least 100 operator-supplied non-fixture relationship cases",
                "precision is at least 90%",
                "source-license and passage-review references are present",
            ],
            missing_inputs=missing,
        ),
        intake_item(
            input_id="A209_24h_operator_soak_finalization",
            acceptance_id="A209",
            label="A209 24h operator soak finalization evidence",
            required_source=source_ref(operator_soak_finalization_path),
            validation_command=(
                "make generate-operator-soak-finalization-preflight "
                "validate-operator-soak-finalization-preflight"
            ),
            completion_criteria=[
                "288/288 five-minute windows pass",
                "0 failed windows",
                "operator soak evidence validation reports release-ready status",
                "downstream release-gate refresh is explicitly allowed by finalization preflight",
            ],
            missing_inputs=missing,
        ),
    ]

    ready_inputs = [
        item["input_id"]
        for item in required_inputs
        if item["current_status"] == "READY_FOR_PREFLIGHT"
    ]
    missing_inputs = [
        item["input_id"]
        for item in required_inputs
        if item["current_status"] != "READY_FOR_PREFLIGHT"
    ]
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "artifact_id": "t1303-external-release-operator-intake-packet",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_id": "T1303",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "packet_status": "READY_FOR_RELEASE_MANAGER_PREFLIGHT"
        if not missing_inputs
        else "WAITING_FOR_OPERATOR_INPUTS",
        "external_release_evidence_ready": preflight.get("external_release_evidence_ready"),
        "release_manager_preflight_refresh_allowed": preflight.get(
            "release_manager_preflight_refresh_allowed"
        ),
        "mvp_release_gate_refresh_allowed": preflight.get("mvp_release_gate_refresh_allowed"),
        "release_gate_closed_by_operator_packet": False,
        "source_files": {
            "external_release_evidence_bundle_preflight": source_ref(preflight_path),
            "a202_release_decision_intake_template": source_ref(a202_intake_template_path),
            "a202_operator_review_packet": source_ref(a202_operator_review_packet_path),
            "a210_brand_clearance_intake_template": source_ref(brand_intake_template_path),
            "a026_a027_gold_label_intake_template": source_ref(gold_intake_template_path),
            "a026_a027_operator_labeling_packet": source_ref(
                gold_operator_labeling_packet_path
            ),
            "a209_operator_soak_finalization_preflight": source_ref(
                operator_soak_finalization_path
            ),
        },
        "gate_statuses": gate_statuses,
        "required_operator_inputs": required_inputs,
        "ready_input_ids": ready_inputs,
        "missing_input_ids": missing_inputs,
        "operator_submission_order": [
            "A202_source_license_passage_owner_legal_release",
            "A210_brand_legal_market_clearance_or_risk_waiver",
            "A026_entity_resolution_production_gold_set",
            "A027_relationship_extraction_production_gold_set",
            "A209_24h_operator_soak_finalization",
        ],
        "post_submission_commands": [
            "make generate-external-release-evidence-bundle "
            "validate-external-release-evidence-bundle",
            "make generate-release-manager-activation-artifact validate-release-manager-activation",
            "make generate-mvp-release-gate-preflight validate-mvp-release-gate-preflight",
            "make verify",
        ],
        "validation_policy": {
            "repository_templates_count_as_clearance": False,
            "repository_fixtures_count_as_clearance": False,
            "partial_a209_checkpoint_counts_as_clearance": False,
            "operator_packet_closes_release_gate": False,
            "all_required_operator_inputs_must_be_ready": True,
        },
        "non_claims": [
            "This operator intake packet is a checklist and hash manifest, not legal clearance.",
            "This operator intake packet does not convert templates, fixtures, or "
            "partial soak progress into release evidence.",
            "This operator intake packet does not close A202, A209, A210, A026, "
            "A027, A204, A205, or MVP release.",
        ],
    }


def validate_preflight(
    payload: dict[str, Any],
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    a202_operator_review_packet_path: Path = DEFAULT_A202_OPERATOR_REVIEW_PACKET,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
) -> None:
    expected = build_preflight(
        release_decision_contract_path=release_decision_contract_path,
        a202_operator_review_packet_path=a202_operator_review_packet_path,
        brand_preflight_path=brand_preflight_path,
        entity_gold_evaluation_path=entity_gold_evaluation_path,
        relationship_gold_evaluation_path=relationship_gold_evaluation_path,
        operator_soak_finalization_path=operator_soak_finalization_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_id",
        "task_ids",
        "acceptance_ids",
        "status",
        "external_release_evidence_ready",
        "release_manager_preflight_refresh_allowed",
        "mvp_release_gate_refresh_allowed",
        "release_gate_closed_by_bundle_preflight",
        "required_external_inputs",
        "source_files",
        "gate_statuses",
        "missing_external_inputs",
        "operator_next_actions",
        "validation_policy",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"external release evidence bundle drift: {key}")
    ready = payload.get("external_release_evidence_ready") is True
    if ready and payload.get("missing_external_inputs"):
        raise ValueError("ready bundle cannot list missing external inputs")
    if ready and payload.get("release_manager_preflight_refresh_allowed") is not True:
        raise ValueError("ready bundle must allow release-manager preflight refresh")
    if not ready and payload.get("release_manager_preflight_refresh_allowed") is not False:
        raise ValueError("blocked bundle must not allow release-manager preflight refresh")
    if payload.get("release_gate_closed_by_bundle_preflight") is not False:
        raise ValueError("bundle preflight must not close release gates directly")


def validate_operator_intake_packet(
    payload: dict[str, Any],
    *,
    preflight_path: Path = DEFAULT_OUTPUT,
    a202_intake_template_path: Path = DEFAULT_A202_INTAKE_TEMPLATE,
    a202_operator_review_packet_path: Path = DEFAULT_A202_OPERATOR_REVIEW_PACKET,
    brand_intake_template_path: Path = DEFAULT_BRAND_INTAKE_TEMPLATE,
    gold_intake_template_path: Path = DEFAULT_GOLD_INTAKE_TEMPLATE,
    gold_operator_labeling_packet_path: Path = DEFAULT_GOLD_OPERATOR_LABELING_PACKET,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
) -> None:
    expected = build_operator_intake_packet(
        preflight_path=preflight_path,
        a202_intake_template_path=a202_intake_template_path,
        a202_operator_review_packet_path=a202_operator_review_packet_path,
        brand_intake_template_path=brand_intake_template_path,
        gold_intake_template_path=gold_intake_template_path,
        gold_operator_labeling_packet_path=gold_operator_labeling_packet_path,
        operator_soak_finalization_path=operator_soak_finalization_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "packet_status",
        "external_release_evidence_ready",
        "release_manager_preflight_refresh_allowed",
        "mvp_release_gate_refresh_allowed",
        "release_gate_closed_by_operator_packet",
        "source_files",
        "gate_statuses",
        "required_operator_inputs",
        "ready_input_ids",
        "missing_input_ids",
        "operator_submission_order",
        "post_submission_commands",
        "validation_policy",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"external release operator intake packet drift: {key}")
    if payload.get("release_gate_closed_by_operator_packet") is not False:
        raise ValueError("operator intake packet must not close release gates")
    if (
        payload.get("missing_input_ids")
        and payload.get("packet_status") != "WAITING_FOR_OPERATOR_INPUTS"
    ):
        raise ValueError("operator intake packet with missing inputs must wait for operator inputs")
    if (
        not payload.get("missing_input_ids")
        and payload.get("packet_status") != "READY_FOR_RELEASE_MANAGER_PREFLIGHT"
    ):
        raise ValueError(
            "operator intake packet with no missing inputs must be ready for preflight"
        )


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--release-decision-contract",
        type=Path,
        default=DEFAULT_RELEASE_DECISION_CONTRACT,
    )
    parser.add_argument("--brand-preflight", type=Path, default=DEFAULT_BRAND_PREFLIGHT)
    parser.add_argument(
        "--entity-gold-evaluation",
        type=Path,
        default=DEFAULT_ENTITY_GOLD_EVALUATION,
    )
    parser.add_argument(
        "--relationship-gold-evaluation",
        type=Path,
        default=DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    )
    parser.add_argument(
        "--operator-soak-finalization",
        type=Path,
        default=DEFAULT_OPERATOR_SOAK_FINALIZATION,
    )
    parser.add_argument(
        "--a202-intake-template",
        type=Path,
        default=DEFAULT_A202_INTAKE_TEMPLATE,
    )
    parser.add_argument(
        "--a202-operator-review-packet",
        type=Path,
        default=DEFAULT_A202_OPERATOR_REVIEW_PACKET,
    )
    parser.add_argument(
        "--brand-intake-template",
        type=Path,
        default=DEFAULT_BRAND_INTAKE_TEMPLATE,
    )
    parser.add_argument(
        "--gold-intake-template",
        type=Path,
        default=DEFAULT_GOLD_INTAKE_TEMPLATE,
    )
    parser.add_argument(
        "--gold-operator-labeling-packet",
        type=Path,
        default=DEFAULT_GOLD_OPERATOR_LABELING_PACKET,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("generate", "validate", "generate-packet", "validate-packet"),
    )
    add_common_args(parser)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--packet-output", type=Path, default=DEFAULT_PACKET_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        payload = build_preflight(
            release_decision_contract_path=args.release_decision_contract,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        validate_preflight(
            payload,
            release_decision_contract_path=args.release_decision_contract,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.output)}))
    elif args.command == "validate":
        validate_preflight(
            read_json(args.output),
            release_decision_contract_path=args.release_decision_contract,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    elif args.command == "generate-packet":
        payload = build_operator_intake_packet(
            preflight_path=args.output,
            a202_intake_template_path=args.a202_intake_template,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_intake_template_path=args.brand_intake_template,
            gold_intake_template_path=args.gold_intake_template,
            gold_operator_labeling_packet_path=args.gold_operator_labeling_packet,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        validate_operator_intake_packet(
            payload,
            preflight_path=args.output,
            a202_intake_template_path=args.a202_intake_template,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_intake_template_path=args.brand_intake_template,
            gold_intake_template_path=args.gold_intake_template,
            gold_operator_labeling_packet_path=args.gold_operator_labeling_packet,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        write_json(args.packet_output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.packet_output)}))
    else:
        validate_operator_intake_packet(
            read_json(args.packet_output),
            preflight_path=args.output,
            a202_intake_template_path=args.a202_intake_template,
            a202_operator_review_packet_path=args.a202_operator_review_packet,
            brand_intake_template_path=args.brand_intake_template,
            gold_intake_template_path=args.gold_intake_template,
            gold_operator_labeling_packet_path=args.gold_operator_labeling_packet,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.packet_output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
