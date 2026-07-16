from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_v02.stage_v025_fx_policy import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    TEMPORAL_FIELDS,
    TIMEZONE_NAME,
    build_phase22_contract,
    build_temporal_coverage,
    normalize_temporal_record,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "temporal_record.schema.json"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_2" / "phase_2_2"
DOC_PATH = PFI_ROOT / "docs" / "pfi_v025" / "stage_2" / "temporal_truth.md"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase_contract_is_exactly_phase_22() -> None:
    contract = build_phase22_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 2
    assert contract["phase_id"] == PHASE_ID == "V025-S2-P2.2"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S2-P2-T1",
        "S2-P2-T2",
        "S2-P2-T3",
        "S2-P2-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S2-P22-TEMPORAL-FX"
    assert contract["acceptance_id_origin"] == "project_governance_assigned_not_taskpack"
    assert contract["timezone"] == TIMEZONE_NAME == "Australia/Sydney"
    assert contract["current_phase_only"] is True
    assert contract["ordinary_runtime_network_allowed"] is False
    assert contract["finder_used"] is False
    assert "Phase 2.3" in contract["explicitly_not_done"]


def test_temporal_field_set_and_schema_match_taskpack_exactly() -> None:
    assert TEMPORAL_FIELDS == (
        "transaction_time",
        "posted_at",
        "effective_at",
        "imported_at",
        "reconciled_at",
        "valued_at",
        "fx_effective_at",
        "report_as_of",
    )
    taskpack = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    assert taskpack.is_file()
    with zipfile.ZipFile(taskpack) as archive:
        upstream = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/temporal_record.schema.json"))
    assert _json(SCHEMA_PATH) == upstream
    Draft202012Validator.check_schema(upstream)


def test_normalize_temporal_record_requires_aware_rfc3339_values() -> None:
    record = {
        "transaction_time": "2026-07-14T08:00:00+10:00",
        "posted_at": "2026-07-14T00:00:00Z",
        "effective_at": None,
        "imported_at": "2026-07-14T09:30:00+10:00",
        "reconciled_at": None,
        "valued_at": None,
        "fx_effective_at": None,
        "report_as_of": "2026-07-14T18:00:00+10:00",
        "source_note": "additionalProperties remains permitted by TaskPack",
    }

    normalized = normalize_temporal_record(record)

    assert normalized["transaction_time"] == "2026-07-14T08:00:00+10:00"
    assert normalized["posted_at"] == "2026-07-14T00:00:00Z"
    assert normalized["effective_at"] is None
    assert normalized["source_note"] == record["source_note"]

    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_temporal_record({"transaction_time": "2026-07-14T08:00:00"})
    with pytest.raises(ValueError, match="RFC3339"):
        normalize_temporal_record({"posted_at": "2026/07/14 08:00"})
    with pytest.raises(TypeError, match="string or null"):
        normalize_temporal_record({"effective_at": 123})


def test_temporal_coverage_is_field_by_field_and_never_invents_missing_times() -> None:
    records = [
        {
            "transaction_time": "2026-07-13T23:00:00+10:00",
            "posted_at": None,
            "effective_at": None,
        },
        {
            "transaction_time": "2026-07-14T01:00:00+10:00",
            "posted_at": "2026-07-14T02:00:00+10:00",
            "effective_at": None,
        },
    ]

    coverage = build_temporal_coverage(records)

    assert coverage["schema"] == "PFIV025TemporalCoverageV1"
    assert coverage["timezone_contract"] == TIMEZONE_NAME
    assert coverage["record_count"] == 2
    assert coverage["fields"]["transaction_time"] == {
        "non_null_count": 2,
        "null_count": 0,
        "coverage_start": "2026-07-13T23:00:00+10:00",
        "coverage_end": "2026-07-14T01:00:00+10:00",
    }
    assert coverage["fields"]["posted_at"]["non_null_count"] == 1
    assert coverage["fields"]["effective_at"] == {
        "non_null_count": 0,
        "null_count": 2,
        "coverage_start": None,
        "coverage_end": None,
    }
    assert coverage["fields"]["valued_at"]["non_null_count"] == 0


def test_tracked_temporal_contract_and_coverage_are_public_aggregate_truth() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    coverage = _json(REPORT_ROOT / "temporal_coverage.json")

    for field in TEMPORAL_FIELDS:
        assert f"`{field}`" in doc
        assert field in coverage["fields"]
    assert "Australia/Sydney" in doc
    assert "naive datetime" in doc
    assert coverage["timezone_contract"] == TIMEZONE_NAME
    assert coverage["source_id"] == "SRC-TRANSACTIONS-ALIPAY"
    assert coverage["record_count"] == 8815
    assert coverage["private_values_included"] is False
    assert coverage["temporal_values_invented"] is False
    assert coverage["fields"]["transaction_time"]["status"] == "aggregate_coverage_only"
    assert all(
        row["status"] in {"aggregate_coverage_only", "not_verified"}
        for row in coverage["fields"].values()
    )
