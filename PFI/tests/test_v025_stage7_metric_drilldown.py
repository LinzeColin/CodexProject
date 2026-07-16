from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from pfi_os.application.use_cases.metric_lineage_drilldown import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_stage7_phase73_evidence_projection,
    build_stage7_phase73_payload,
)
from pfi_v02.stage_v021_runtime_api import build_v025_stage1_candidate_read_model_status


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SOURCE_LOCK_PATH = PFI_ROOT / "config/sources/v025_immutable_real_source_lock.json"
SOURCE_GIT_PATH = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
FORMAL_ROUTES = (
    "/settings/parameters",
    "/data/interconnection",
    "/reports/metric-drilldown",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _locked_source_commit() -> str:
    payload = json.loads(SOURCE_LOCK_PATH.read_text(encoding="utf-8"))
    return str(payload["source_commit"])


def _source_blob_sha256() -> str:
    raw = subprocess.run(
        ["git", "cat-file", "blob", f"{_locked_source_commit()}:{SOURCE_GIT_PATH}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return hashlib.sha256(raw).hexdigest()


def test_phase73_payload_is_read_only_formal_and_source_unchanged() -> None:
    before = _source_blob_sha256()
    payload = build_stage7_phase73_payload(PFI_ROOT)
    after = _source_blob_sha256()

    assert before == after
    assert payload["phase_id"] == PHASE_ID
    assert payload["task_ids"] == list(TASK_IDS)
    assert payload["acceptance_id"] == ACCEPTANCE_ID
    assert payload["status"] == "ready"
    assert payload["formal_routes"] == list(FORMAL_ROUTES)
    assert payload["sidecar_html_used"] is False
    assert payload["finder_used"] is False
    assert payload["external_network_used"] is False
    assert payload["write_operation_count"] == 0
    assert payload["whole_stage_review_started"] is False
    assert payload["next_phase_started"] is False


def test_parameter_center_is_chinese_readable_and_registry_backed() -> None:
    center = build_stage7_phase73_payload(PFI_ROOT)["parameter_center"]

    assert center["status"] == "ready"
    assert center["title_zh"] == "参数中心"
    assert center["write_enabled"] is False
    assert center["domain_count"] == 15
    assert center["parameter_count"] >= 90
    assert center["formula_count"] == 20
    assert center["consistency_conflict_count"] == 0
    assert center["parameter_hash"] == "sha256:" + _sha256(PFI_ROOT / "config/pfi_parameters.yaml")
    assert center["formula_registry_hash"] == "sha256:" + _sha256(
        PFI_ROOT / "config/formulas/v025_formula_registry.json"
    )
    assert all(domain["label_zh"] for domain in center["domains"])
    assert all(entry["label_zh"] for domain in center["domains"] for entry in domain["entries"])
    assert all(formula["formula_hash"].startswith("sha256:") for formula in center["formulas"])


def test_interconnection_map_is_current_clickable_aggregate_lineage() -> None:
    interconnection = build_stage7_phase73_payload(PFI_ROOT)["interconnection_map"]

    assert interconnection["status"] == "ready"
    assert interconnection["data_hash"].startswith("sha256:")
    assert interconnection["read_model_hash"].startswith("sha256:")
    assert interconnection["lineage_complete_count"] > 0
    assert interconnection["lineage_missing_count"] == 0
    assert interconnection["same_economic_event_per_metric_max_count"] == 1
    assert interconnection["silent_drop_count"] == 0
    assert len(interconnection["nodes"]) == 7
    assert len(interconnection["edges"]) == 6
    assert all(node["route"].startswith("/") for node in interconnection["nodes"])
    assert interconnection["financial_values_emitted"] == 0
    assert interconnection["private_identifiers_emitted"] == 0
    assert '"value":' not in json.dumps(interconnection, ensure_ascii=False)


def test_metric_drilldown_has_range_four_hashes_sources_events_and_fail_closed_values() -> None:
    drilldown = build_stage7_phase73_payload(PFI_ROOT)["metric_drilldown"]

    assert drilldown["status"] == "ready"
    assert drilldown["metric_count"] == 11
    assert drilldown["non_ready_false_zero_count"] == 0
    assert drilldown["persist_private_values_to_evidence_allowed"] is False
    required = set(drilldown["required_fields"])
    assert required == {
        "data_range",
        "formula_hash",
        "parameter_hash",
        "data_hash",
        "read_model_hash",
        "source_ids",
        "event_lineage",
        "blocking_reason_zh",
    }
    by_id = {item["metric_id"]: item for item in drilldown["metrics"]}
    blocked = by_id["net_worth_cny"]
    assert blocked["value"] is None
    assert blocked["blocking_reason_zh"]
    assert blocked["formula_hash"].startswith("sha256:")
    assert blocked["parameter_hash"].startswith("sha256:")
    assert blocked["data_hash"] is None
    assert blocked["read_model_hash"].startswith("sha256:")
    assert blocked["source_ids"]

    ready = by_id["living_consumption_cny"]
    assert ready["status"] == "ready"
    assert ready["formula_id"] == "FORM-PFI-015"
    assert ready["data_range"]["start"]
    assert ready["data_range"]["end"]
    assert all(ready[field].startswith("sha256:") for field in (
        "formula_hash", "parameter_hash", "data_hash", "read_model_hash"
    ))
    assert ready["source_ids"] == ["SRC-TRANSACTIONS-ALIPAY"]
    assert ready["event_lineage"]["economic_event_count"] > 0
    assert ready["event_lineage"]["economic_event_set_hash"].startswith("sha256:")


def test_evidence_projection_redacts_values_and_candidate_mode_stays_unknown() -> None:
    payload = build_stage7_phase73_payload(PFI_ROOT)
    evidence = build_stage7_phase73_evidence_projection(payload)
    serialized = json.dumps(evidence, ensure_ascii=False, sort_keys=True)

    assert evidence["status"] == "pass"
    assert evidence["contains_private_values"] is False
    assert evidence["financial_values_emitted"] == 0
    assert evidence["metric_drilldown"]["all_required_fields_present"] is True
    assert evidence["metric_drilldown"]["required_field_values_valid"] is True
    assert "526749" not in serialized
    assert "345071" not in serialized

    candidate = build_stage7_phase73_payload(
        PFI_ROOT,
        read_model_status=build_v025_stage1_candidate_read_model_status(),
    )
    assert candidate["contains_private_values"] is False
    assert candidate["interconnection_map"]["status"] == "not_loaded"
    assert candidate["interconnection_map"]["lineage_complete_count"] is None
    assert all(item["value"] is None for item in candidate["metric_drilldown"]["metrics"])


def test_non_ready_source_zero_and_blocked_interconnection_fail_the_overall_contract() -> None:
    status = build_v025_stage1_candidate_read_model_status()
    status["core_metric_states"][0]["status"] = "not_loaded"
    status["core_metric_states"][0]["value"] = 0
    payload = build_stage7_phase73_payload(PFI_ROOT, read_model_status=status)

    assert payload["status"] == "blocked"
    assert payload["interconnection_map"]["status"] == "not_loaded"
    assert payload["metric_drilldown"]["status"] == "blocked"
    assert payload["metric_drilldown"]["non_ready_false_zero_count"] == 1
    row = payload["metric_drilldown"]["metrics"][0]
    assert row["value"] is None
    assert row["non_ready_source_value_present"] is True
