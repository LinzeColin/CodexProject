from __future__ import annotations

import hashlib
import inspect
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_os.application.economic_event_pipeline import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_ID,
    TASK_IDS,
    build_economic_event,
    build_event_type_matrix,
    build_interconnection_groups,
    build_lineage_samples_redacted,
    build_phase32_contract,
    build_schema_inventory,
    load_phase32_policy,
    normalize_transaction,
    publish_ledger_event,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCHEMA_ROOT = PFI_ROOT / "config" / "schemas" / "v025"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_3" / "phase_3_2"
POLICY_PATH = PFI_ROOT / "config" / "event_types" / "v025_phase_3_2_event_policy.json"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
SCHEMA_FILES = (
    "normalized_transaction.schema.json",
    "interconnection_group.schema.json",
    "economic_event.schema.json",
    "ledger_event.schema.json",
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _transaction(
    raw_suffix: str,
    *,
    direction: str = "outflow",
    link_reference: str | None = None,
    transaction_time: str = "2026-07-14T08:00:00+10:00",
):
    return normalize_transaction(
        raw_record_id=f"raw_{raw_suffix}",
        source_id=f"src_{raw_suffix}",
        account_ref=f"account_ref_{raw_suffix}",
        source_record_hash="sha256:" + raw_suffix[0] * 64,
        amount="1.00",
        currency="CNY",
        direction=direction,
        transaction_time=transaction_time,
        posted_at="2026-07-14T08:01:00+10:00",
        effective_at="2026-07-14T08:02:00+10:00",
        imported_at="2026-07-14T08:03:00+10:00",
        link_reference=link_reference,
    )


def test_phase_contract_is_exactly_stage3_phase32() -> None:
    contract = build_phase32_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 3
    assert contract["phase_id"] == PHASE_ID == "V025-S3-P3.2"
    assert contract["contract_id"] == CONTRACT_ID == "PFI-V025-STAGE3-PHASE32-NORMALIZED-EVENT"
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S3-P32-NORMALIZED-EVENT"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S3-P2-T1",
        "S3-P2-T2",
        "S3-P2-T3",
        "S3-P2-T4",
    ]
    assert contract["real_financial_data_read"] is False
    assert contract["database_changed"] is False
    assert contract["finder_used"] is False
    assert "Phase 3.3" in contract["explicitly_not_done"]


def test_all_phase32_schemas_are_valid_draft_2020_12() -> None:
    for filename in SCHEMA_FILES:
        schema = _json(SCHEMA_ROOT / filename)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert str(schema["$id"]).endswith(filename)


def test_normalized_transaction_requires_amount_currency_direction_and_temporal_truth() -> None:
    transaction = _transaction("a")
    payload = transaction.to_dict()

    assert payload["amount"] == "1.00"
    assert payload["currency"] == "CNY"
    assert payload["direction"] == "outflow"
    for field in ("transaction_time", "posted_at", "effective_at", "imported_at"):
        assert payload[field].endswith("+10:00")
    Draft202012Validator(_json(SCHEMA_ROOT / "normalized_transaction.schema.json")).validate(payload)

    with pytest.raises(ValueError, match="amount"):
        replace(_transaction("b"), amount="-1.00")
    with pytest.raises(ValueError, match="currency"):
        replace(_transaction("b"), currency="cny")
    with pytest.raises(ValueError, match="direction"):
        replace(_transaction("b"), direction="debit")


def test_normalized_identity_is_deterministic_and_provenance_bound() -> None:
    first = _transaction("a")
    repeated = _transaction("a")
    changed_source_record = normalize_transaction(
        raw_record_id="raw_a",
        source_id="src_a",
        account_ref="account_ref_a",
        source_record_hash="sha256:" + "b" * 64,
        amount="1.00",
        currency="CNY",
        direction="outflow",
        transaction_time="2026-07-14T08:00:00+10:00",
        posted_at="2026-07-14T08:01:00+10:00",
        effective_at="2026-07-14T08:02:00+10:00",
        imported_at="2026-07-14T08:03:00+10:00",
    )

    assert first.normalized_transaction_id == repeated.normalized_transaction_id
    assert first.normalized_transaction_id != changed_source_record.normalized_transaction_id
    assert first.source_record_hash == "sha256:" + "a" * 64


def test_grouping_uses_explicit_link_reference_and_is_order_independent() -> None:
    policy = load_phase32_policy()
    linked_outflow = _transaction("a", link_reference="link_chain_001")
    linked_inflow = _transaction("b", direction="inflow", link_reference="link_chain_001")
    singleton = _transaction("c")

    forward = build_interconnection_groups(
        (linked_outflow, linked_inflow, singleton),
        policy=policy,
        created_at="2026-07-14T09:00:00+10:00",
    )
    reverse = build_interconnection_groups(
        (singleton, linked_inflow, linked_outflow),
        policy=policy,
        created_at="2026-07-14T09:00:00+10:00",
    )

    assert [item.to_dict() for item in forward] == [item.to_dict() for item in reverse]
    assert sorted(len(item.normalized_transaction_ids) for item in forward) == [1, 2]
    linked_group = next(item for item in forward if len(item.normalized_transaction_ids) == 2)
    assert linked_group.grouping_rule_id == "explicit_link_reference_exact"
    assert linked_group.reason_codes == ("explicit_link_reference_exact",)
    assert linked_group.link_reference_hash.startswith("sha256:")
    assert "link_chain_001" not in json.dumps(linked_group.to_dict())
    Draft202012Validator(_json(SCHEMA_ROOT / "interconnection_group.schema.json")).validate(
        linked_group.to_dict()
    )


def test_grouping_never_guesses_from_equal_amount_time_or_source_name() -> None:
    policy = load_phase32_policy()
    first = _transaction("a")
    second = _transaction("b")

    groups = build_interconnection_groups(
        (first, second),
        policy=policy,
        created_at="2026-07-14T09:00:00+10:00",
    )

    assert len(groups) == 2
    assert all(item.grouping_rule_id == "singleton_normalized_transaction" for item in groups)
    assert policy["amount_time_heuristic_grouping"] is False
    assert policy["source_name_inference"] is False
    source = inspect.getsource(build_interconnection_groups).lower()
    for forbidden in ("alipay", "wechat", "broker", "支付宝", "微信", "券商"):
        assert forbidden not in source


def test_event_policy_covers_required_chains_with_explicit_impact_flags() -> None:
    matrix = build_event_type_matrix()
    policies = {item["event_type"]: item["impact_flags"] for item in matrix["event_types"]}

    for event_type in (
        "own_account_transfer",
        "credit_card_repayment",
        "refund",
        "investment_funding",
        "fund_subscription",
        "gold_subscription",
        "investment_purchase",
        "investment_sale",
    ):
        assert event_type in policies
    assert policies["own_account_transfer"]["net_worth_effect"] == "neutral"
    assert policies["credit_card_repayment"]["living_consumption_included"] is False
    assert policies["refund"]["requires_offset_event_id"] is True
    for event_type in ("investment_funding", "fund_subscription", "gold_subscription", "investment_purchase"):
        assert policies[event_type]["activity_outflow_included"] is True
        assert policies[event_type]["living_consumption_included"] is False
        assert policies[event_type]["investment_allocation_included"] is True
    assert matrix["same_economic_event_per_metric_max_count"] == 1
    assert matrix["financial_values_emitted"] == 0


def test_economic_event_preserves_complete_lineage_and_fails_closed_for_unknown_type() -> None:
    policy = load_phase32_policy()
    later = _transaction("a", link_reference="link_chain_001", transaction_time="2026-07-14T08:02:00+10:00")
    earlier = _transaction(
        "b",
        direction="inflow",
        link_reference="link_chain_001",
        transaction_time="2026-07-14T08:00:00+10:00",
    )
    group = build_interconnection_groups(
        (later, earlier),
        policy=policy,
        created_at="2026-07-14T09:00:00+10:00",
    )[0]

    event = build_economic_event(
        group,
        (later, earlier),
        event_type="own_account_transfer",
        policy=policy,
    )

    assert event.interconnection_group_id == group.interconnection_group_id
    assert event.normalized_transaction_ids == tuple(sorted((later.normalized_transaction_id, earlier.normalized_transaction_id)))
    assert event.raw_record_ids == ("raw_a", "raw_b")
    assert event.event_time == "2026-07-14T08:00:00+10:00"
    assert event.impact_flags.net_worth_effect == "neutral"
    Draft202012Validator(_json(SCHEMA_ROOT / "economic_event.schema.json")).validate(event.to_dict())

    with pytest.raises(ValueError, match="review_required"):
        build_economic_event(group, (later, earlier), event_type="unregistered_event", policy=policy)
    with pytest.raises(ValueError, match="offset_economic_event_id"):
        build_economic_event(group, (later, earlier), event_type="refund", policy=policy)
    refund = build_economic_event(
        group,
        (later, earlier),
        event_type="refund",
        policy=policy,
        offset_economic_event_id="economic_event_" + "a" * 20,
    )
    assert refund.offset_economic_event_id == "economic_event_" + "a" * 20
    Draft202012Validator(_json(SCHEMA_ROOT / "economic_event.schema.json")).validate(refund.to_dict())


def test_ledger_event_has_postings_complete_lineage_and_stable_idempotency_key() -> None:
    policy = load_phase32_policy()
    outflow = _transaction("a", link_reference="link_chain_001")
    inflow = _transaction("b", direction="inflow", link_reference="link_chain_001")
    group = build_interconnection_groups(
        (outflow, inflow),
        policy=policy,
        created_at="2026-07-14T09:00:00+10:00",
    )[0]
    event = build_economic_event(
        group,
        (outflow, inflow),
        event_type="own_account_transfer",
        policy=policy,
    )

    first = publish_ledger_event(event, (outflow, inflow))
    repeated = publish_ledger_event(event, (inflow, outflow))

    assert first == repeated
    assert first.idempotency_key.startswith("sha256:")
    assert first.raw_record_ids == ("raw_a", "raw_b")
    assert first.normalized_transaction_ids == event.normalized_transaction_ids
    assert first.interconnection_group_id == group.interconnection_group_id
    assert first.economic_event_id == event.economic_event_id
    assert len(first.postings) == 2
    assert {posting.direction for posting in first.postings} == {"inflow", "outflow"}
    assert "aggregate_amount" not in first.to_dict()
    Draft202012Validator(_json(SCHEMA_ROOT / "ledger_event.schema.json")).validate(first.to_dict())


def test_schema_inventory_event_matrix_and_redacted_lineage_are_public_safe() -> None:
    inventory = build_schema_inventory()
    matrix = build_event_type_matrix()
    lineage = build_lineage_samples_redacted()

    assert inventory["status"] == "pass"
    assert inventory["schema_count"] == 4
    assert set(inventory["schemas"]) == set(SCHEMA_FILES)
    assert all(str(value).startswith("sha256:") for value in inventory["schemas"].values())
    assert matrix["status"] == "pass"
    assert lineage["status"] == "pass"
    assert lineage["financial_values_emitted"] == 0
    assert lineage["private_identifiers_emitted"] == 0
    serialized = json.dumps(lineage)
    for forbidden in ("amount", "account_ref", "/Users/", "link_chain_001"):
        assert forbidden not in serialized


def test_tracked_phase32_artifacts_are_complete_and_bound() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    schema_inventory = _json(REPORT_ROOT / "schema_inventory.json")
    event_matrix = _json(REPORT_ROOT / "event_type_matrix.json")
    lineage = _json(REPORT_ROOT / "lineage_samples_redacted.json")
    changed = (REPORT_ROOT / "changed_files.txt").read_text(encoding="utf-8").splitlines()

    assert evidence["status"] == "candidate_pass"
    assert evidence["phase_id"] == PHASE_ID
    assert evidence["task_ids"] == list(TASK_IDS)
    assert evidence["stage_3_status"] == "in_progress"
    assert evidence["stage_3_phase_3_2_status"] == "candidate_pass"
    assert evidence["stage_3_phase_3_3_status"] == "not_started"
    assert evidence["real_financial_data_read"] is False
    assert evidence["financial_fixture_fallback_used"] is False
    assert evidence["production_financial_acceptance_claimed"] is False
    assert evidence["database_changed"] is False
    assert evidence["finder_used"] is False
    assert schema_inventory == build_schema_inventory()
    assert event_matrix == build_event_type_matrix()
    assert lineage == build_lineage_samples_redacted()
    assert changed == sorted(changed)
    assert len(changed) == len(set(changed))
    assert "PFI/tests/test_v025_stage3_interconnection.py" in changed
    for relative, expected in evidence["artifact_hashes"].items():
        assert hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest() == expected


def test_phase_evidence_validates_against_taskpack_schema() -> None:
    if not TASK_PACK.is_file():
        return
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    evidence = _json(REPORT_ROOT / "evidence.json")

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)
    assert evidence["git_commit"] == "SELF"
    assert evidence["requires_user_acceptance"] is True


def test_privacy_scan_is_deterministic_and_has_zero_findings() -> None:
    privacy = (REPORT_ROOT / "privacy_scan.txt").read_text(encoding="utf-8")

    assert privacy.splitlines()[0] == "PASS"
    for counter in (
        "absolute_private_paths",
        "financial_row_values",
        "account_identifiers",
        "link_references",
        "credentials",
        "source_name_inference",
        "amount_time_heuristic_grouping",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in privacy


def test_governance_stops_at_phase32_candidate() -> None:
    project = (PFI_ROOT / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    roadmap = (PFI_ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")

    for token in (
        'current_status: "stage_3_phase_3_2_candidate_pass"',
        'stage_3_status: "in_progress"',
        'stage_3_phase_3_1_status: "candidate_pass"',
        'stage_3_phase_3_2_status: "candidate_pass"',
        'stage_3_phase_3_3_status: "not_started"',
    ):
        assert token in project
    assert 'current_stage_id: "V025-S3"' in roadmap
    assert 'current_phase_id: "V025-S3-P3.2"' in roadmap
    assert 'next_gate_id: "ACC-PFI-V025-S3-P33-RECONCILIATION"' in roadmap
    assert 'stage_3_phase_3_2_status: "candidate_pass"' in roadmap
    assert 'stage_3_phase_3_3_status: "not_started"' in roadmap
