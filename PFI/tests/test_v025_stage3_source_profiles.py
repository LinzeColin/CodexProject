from __future__ import annotations

import hashlib
import inspect
import json
import zipfile
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_os.application.source_account_roles import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_ID,
    TASK_IDS,
    assert_public_safe_payload,
    build_phase31_contract,
    build_review_queue_summary,
    build_schema_inventory,
    load_phase31_policy,
    route_account_role,
)
from pfi_os.domain.source_accounts import (
    AccountRoleAssignment,
    ParserProvenance,
    SourceProfile,
    roles_for_account,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCHEMA_ROOT = PFI_ROOT / "config" / "schemas" / "v025"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_3" / "phase_3_1"
POLICY_PATH = PFI_ROOT / "config" / "sources" / "v025_phase_3_1_source_account_policy.json"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
SCHEMA_FILES = (
    "parser_provenance.schema.json",
    "source_profile.schema.json",
    "account_role_assignment.schema.json",
    "role_review_item.schema.json",
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _profile() -> SourceProfile:
    return SourceProfile(
        source_id="src_generic_001",
        source_type="custom.adapter",
        capabilities=("records.transaction", "links.refund"),
        parser_provenance=ParserProvenance(
            parser_id="parser.generic_csv",
            parser_version="2.4.1",
            source_hash="sha256:" + "a" * 64,
        ),
    )


def test_phase_contract_is_exactly_stage3_phase31() -> None:
    contract = build_phase31_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 3
    assert contract["phase_id"] == PHASE_ID == "V025-S3-P3.1"
    assert contract["contract_id"] == CONTRACT_ID == "PFI-V025-STAGE3-PHASE31-SOURCE-ACCOUNT"
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S3-P1-T1",
        "S3-P1-T2",
        "S3-P1-T3",
        "S3-P1-T4",
    ]
    assert contract["current_phase_only"] is True
    assert contract["real_financial_data_read"] is False
    assert contract["source_name_classification"] is False
    assert contract["finder_used"] is False
    assert "Phase 3.2" in contract["explicitly_not_done"]


def test_all_phase31_schemas_are_valid_draft_2020_12() -> None:
    for filename in SCHEMA_FILES:
        schema = _json(SCHEMA_ROOT / filename)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert str(schema["$id"]).endswith(filename)


def test_source_profile_schema_is_extensible_not_source_name_enumerated() -> None:
    schema = _json(SCHEMA_ROOT / "source_profile.schema.json")
    properties = schema["properties"]

    assert "enum" not in properties["source_type"]
    assert "enum" not in properties["capabilities"]["items"]
    assert properties["capabilities"]["uniqueItems"] is True
    Draft202012Validator(schema).validate(_profile().to_dict())


def test_parser_provenance_binds_parser_version_and_source_hash() -> None:
    provenance = _profile().parser_provenance
    schema = _json(SCHEMA_ROOT / "parser_provenance.schema.json")

    Draft202012Validator(schema).validate(provenance.to_dict())
    assert provenance.hash_algorithm == "sha256"
    with pytest.raises(ValueError, match="source_hash"):
        ParserProvenance("parser.generic_csv", "2.4.1", "not-a-hash")
    with pytest.raises(ValueError, match="parser_version"):
        ParserProvenance("parser.generic_csv", "", "sha256:" + "b" * 64)


def test_custom_source_type_and_capabilities_require_no_core_code_change() -> None:
    profile = _profile()

    assert profile.source_type == "custom.adapter"
    assert profile.capabilities == ("links.refund", "records.transaction")
    assert profile.status == "active"
    assert "label" not in profile.to_dict()


def test_account_roles_can_overlap_and_have_effective_ranges() -> None:
    assignments = (
        AccountRoleAssignment(
            assignment_id="role_assignment_001",
            account_ref="account_ref_001",
            source_id="src_generic_001",
            role="cash_account",
            effective_from=date(2025, 1, 1),
        ),
        AccountRoleAssignment(
            assignment_id="role_assignment_002",
            account_ref="account_ref_001",
            source_id="src_generic_001",
            role="investment_funding_source",
            effective_from=date(2025, 6, 1),
            effective_to=date(2025, 12, 31),
        ),
    )

    assert roles_for_account(assignments, "account_ref_001", date(2025, 7, 1)) == (
        "cash_account",
        "investment_funding_source",
    )
    assert roles_for_account(assignments, "account_ref_001", date(2026, 1, 1)) == ("cash_account",)
    schema = _json(SCHEMA_ROOT / "account_role_assignment.schema.json")
    for assignment in assignments:
        Draft202012Validator(schema).validate(assignment.to_dict())


def test_invalid_effective_range_fails_closed() -> None:
    with pytest.raises(ValueError, match="effective_to"):
        AccountRoleAssignment(
            assignment_id="role_assignment_003",
            account_ref="account_ref_001",
            source_id="src_generic_001",
            role="cash_account",
            effective_from=date(2026, 1, 2),
            effective_to=date(2026, 1, 1),
        )


def test_known_role_is_publishable_without_source_name_inference() -> None:
    policy = load_phase31_policy()
    decision = route_account_role(
        _profile(),
        account_ref="account_ref_001",
        proposed_role="cash_account",
        effective_from=date(2026, 1, 1),
        policy=policy,
        created_at="2026-07-14T10:00:00Z",
    )

    assert decision.status == "publishable"
    assert decision.publish_allowed is True
    assert decision.assignment is not None
    assert decision.review_item is None


def test_unknown_role_enters_review_queue_and_never_auto_publishes() -> None:
    policy = load_phase31_policy()
    decision = route_account_role(
        _profile(),
        account_ref="account_ref_001",
        proposed_role="unregistered_role",
        effective_from=date(2026, 1, 1),
        policy=policy,
        created_at="2026-07-14T10:00:00Z",
    )

    assert decision.status == "review_required"
    assert decision.publish_allowed is False
    assert decision.assignment is None
    assert decision.review_item is not None
    assert decision.review_item.reason_code == "unknown_role"
    assert decision.review_item.publish_allowed is False
    Draft202012Validator(_json(SCHEMA_ROOT / "role_review_item.schema.json")).validate(
        decision.review_item.to_dict()
    )


def test_policy_has_role_registry_but_no_source_name_mapping() -> None:
    policy = load_phase31_policy()

    assert policy["multiple_roles_per_account"] is True
    assert policy["overlapping_role_periods_allowed"] is True
    assert policy["unknown_role_policy"] == "review_queue"
    assert policy["unknown_role_publish_allowed"] is False
    assert policy["source_name_classification"] is False
    assert "source_name_role_mapping" not in policy
    assert "cash_account" in policy["role_registry"]
    assert_public_safe_payload(policy)


def test_application_logic_contains_no_named_source_classification() -> None:
    source = inspect.getsource(route_account_role).lower()

    for forbidden in ("alipay", "wechat", "broker", "支付宝", "微信", "券商"):
        assert forbidden not in source
    assert "role_registry" in source
    assert "review_required" in source


def test_schema_inventory_and_review_summary_are_public_safe() -> None:
    inventory = build_schema_inventory()
    summary = build_review_queue_summary()

    assert inventory["status"] == "pass"
    assert inventory["schema_count"] == 4
    assert set(inventory["schemas"]) == set(SCHEMA_FILES)
    assert all(str(value).startswith("sha256:") for value in inventory["schemas"].values())
    assert summary == {
        "schema": "PFIV025Stage3Phase31ReviewQueueSummaryV1",
        "status": "pass",
        "unknown_role_policy": "review_queue",
        "unknown_role_publish_allowed": False,
        "source_name_classification": False,
        "private_account_identifiers_emitted": 0,
        "financial_records_read": 0,
        "financial_values_emitted": 0,
    }
    assert_public_safe_payload(inventory)
    assert_public_safe_payload(summary)


def test_tracked_phase31_artifacts_are_complete_and_bound() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    schema_inventory = _json(REPORT_ROOT / "schema_inventory.json")
    review_summary = _json(REPORT_ROOT / "review_queue_summary.json")
    changed = (REPORT_ROOT / "changed_files.txt").read_text(encoding="utf-8").splitlines()

    assert evidence["status"] == "candidate_pass"
    assert evidence["phase_id"] == PHASE_ID
    assert evidence["task_ids"] == list(TASK_IDS)
    assert evidence["stage_3_status"] == "in_progress"
    assert evidence["stage_3_phase_3_1_status"] == "candidate_pass"
    assert evidence["stage_3_phase_3_2_status"] == "not_started"
    assert evidence["real_financial_data_read"] is False
    assert evidence["financial_fixture_fallback_used"] is False
    assert evidence["finder_used"] is False
    assert schema_inventory == build_schema_inventory()
    assert review_summary == build_review_queue_summary()
    assert changed == sorted(changed)
    assert len(changed) == len(set(changed))
    assert "PFI/tests/test_v025_stage3_source_profiles.py" in changed
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
        "credentials",
        "source_name_role_mappings",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in privacy


def test_governance_stops_at_phase31_candidate() -> None:
    project = (PFI_ROOT / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    roadmap = (PFI_ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")

    for token in (
        'current_status: "stage_3_phase_3_1_candidate_pass"',
        'stage_3_status: "in_progress"',
        'stage_3_phase_3_1_status: "candidate_pass"',
        'stage_3_phase_3_2_status: "not_started"',
    ):
        assert token in project
    assert 'current_stage_id: "V025-S3"' in roadmap
    assert 'current_phase_id: "V025-S3-P3.1"' in roadmap
    assert 'next_gate_id: "ACC-PFI-V025-S3-P32-NORMALIZED-EVENT"' in roadmap
    assert 'stage_3_phase_3_1_status: "candidate_pass"' in roadmap
    assert 'stage_3_phase_3_2_status: "not_started"' in roadmap
