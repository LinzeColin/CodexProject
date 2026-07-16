from __future__ import annotations

import json
from pathlib import Path
import zipfile

from jsonschema import Draft202012Validator

from pfi_os.application.read_models.account_balance import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_current_account_read_model,
    build_phase41_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCHEMA_PATH = PFI_ROOT / "docs" / "pfi_v025" / "stage_4" / "account_snapshot.schema.json"
METRIC_SCHEMA_PATH = PFI_ROOT / "docs" / "pfi_v025" / "stage_4" / "metric_state.schema.json"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_4" / "phase_4_1"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase_contract_is_exactly_phase_41() -> None:
    contract = build_phase41_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 4
    assert contract["phase_id"] == PHASE_ID == "V025-S4-P4.1"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S4-P1-T1",
        "S4-P1-T2",
        "S4-P1-T3",
        "S4-P1-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT"
    assert contract["current_phase_only"] is True
    assert contract["finder_used"] is False
    assert contract["financial_fixture_fallback_allowed"] is False
    assert any(item.startswith("Phase 4.2") for item in contract["explicitly_not_done"])


def test_account_snapshot_schema_is_draft_2020_12_and_amounts_are_decimal_strings() -> None:
    schema = _json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(
        {
            "schema": "PFIV025AccountSnapshotV1",
            "snapshot_id": "snapshot-contract-test",
            "snapshot_kind": "cash_account",
            "account_ref": "opaque-account-ref",
            "source_id": "SRC-ACCOUNT-BALANCES",
            "currency": "CNY",
            "opening_balance": "10.00",
            "closing_balance": "12.00",
            "coverage_start": "2026-07-01",
            "coverage_end": "2026-07-14",
            "data_as_of": "2026-07-14",
            "source_record_count": 1,
            "source_content_hash": "sha256:" + "a" * 64,
        }
    )
    assert schema["properties"]["opening_balance"]["type"] == "string"
    assert schema["properties"]["closing_balance"]["type"] == "string"


def test_metric_state_schema_matches_canonical_taskpack() -> None:
    taskpack = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    if not taskpack.is_file():
        return
    with zipfile.ZipFile(taskpack) as archive:
        upstream = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/metric_state.schema.json"))
    assert _json(METRIC_SCHEMA_PATH) == upstream


def test_current_real_source_state_is_not_loaded_and_never_false_zero() -> None:
    read_model = build_current_account_read_model(REPO_ROOT)
    metrics = {item["metric_id"]: item for item in read_model["metrics"]}
    metric_validator = Draft202012Validator(_json(METRIC_SCHEMA_PATH))

    assert read_model["status"] == "not_loaded"
    assert read_model["transactions_available_is_not_balance_proof"] is True
    assert read_model["financial_fixture_fallback_used"] is False
    assert read_model["financial_values_emitted"] == 0
    assert set(metrics) == {"account_assets_cny", "cash_balance_cny", "liabilities_cny"}
    for metric in metrics.values():
        metric_validator.validate(metric)
        assert metric["status"] == "not_loaded"
        assert metric["value"] is None
        assert metric["calculation_state"] == "not_run"
        assert metric["blocking_reason_zh"]
        assert metric["read_model_hash"] == read_model["read_model_hash"]
    assert metrics["cash_balance_cny"]["source_ids"] == ["SRC-ACCOUNT-BALANCES"]
    assert metrics["liabilities_cny"]["source_ids"] == ["SRC-LIABILITIES"]


def test_tracked_phase_41_reports_match_runtime_and_are_public_safe() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    read_model = build_current_account_read_model(REPO_ROOT, observed_at=str(evidence["observed_at"]))

    assert _json(REPORT_ROOT / "cash_read_model.json") == read_model
    no_false_zero = _json(REPORT_ROOT / "no_false_zero_result.json")
    assert no_false_zero["result"] == "pass"
    assert no_false_zero["non_ready_value_count"] == 0
    assert no_false_zero["confirmed_zero_count"] == 0
    assert no_false_zero["financial_values_emitted"] == 0
    assert no_false_zero["transaction_balance_inference_used"] is False
    assert evidence["status"] == "candidate_pass"
    assert evidence["requires_user_acceptance"] is True
    assert evidence["contains_private_values"] is False
