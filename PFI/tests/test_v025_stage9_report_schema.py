from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.application.reports.contracts import (
    ACCEPTANCE_ID,
    COMPLETENESS_RULES_RELATIVE,
    PHASE_ID,
    REPORT_SCHEMA_RELATIVE,
    REPORT_TYPES,
    TASK_IDS,
    build_phase91_contract,
    build_phase91_report_pack,
    canonical_hash,
    derive_report_status,
    validate_phase91_report_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_1"
TASKPACK_REQUIRED_FIELDS = {
    "report_id",
    "report_type",
    "status",
    "version",
    "generated_at",
    "report_as_of",
    "data_range",
    "sample_counts",
    "hashes",
    "conclusions",
    "limitations",
}


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase91_contract_is_exactly_one_t2_phase() -> None:
    contract = build_phase91_contract()

    assert contract["phase_id"] == PHASE_ID
    assert contract["task_ids"] == list(TASK_IDS)
    assert contract["acceptance_id"] == ACCEPTANCE_ID
    assert contract["risk_tier"] == "T2"
    assert contract["current_phase_only"] is True
    assert contract["report_types"] == list(REPORT_TYPES)
    assert contract["completeness_statuses"] == ["complete", "partial", "blocked"]
    assert contract["data_quality_report_generatable_in_any_dependency_state"] is True
    assert contract["blocked_financial_conclusion_allowed"] is False
    assert contract["phase_9_2_started"] is False
    assert contract["phase_9_3_started"] is False
    assert contract["stage_9_whole_stage_review_done"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False
    assert contract["finder_used"] is False
    assert contract["external_network_performed"] is False


def test_report_schema_is_stricter_than_taskpack_and_validates_quality_report() -> None:
    schema = _json(PFI_ROOT / REPORT_SCHEMA_RELATIVE)
    pack = build_phase91_report_pack(
        PFI_ROOT, generated_at="2026-07-15T15:30:00Z"
    )
    quality = next(
        report for report in pack["reports"] if report["report_type"] == "data_quality"
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert TASKPACK_REQUIRED_FIELDS <= set(schema["required"])
    assert {
        "coverage",
        "dependencies",
        "completeness",
        "gaps",
        "review_links",
        "snapshot_hash",
    } <= set(schema["required"])
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(quality),
        key=lambda error: list(error.absolute_path),
    )
    assert errors == []


def test_current_real_aggregate_inputs_generate_truthful_report_manifest() -> None:
    pack = build_phase91_report_pack(
        PFI_ROOT, generated_at="2026-07-15T15:30:00Z"
    )
    gate = validate_phase91_report_pack(pack, pfi_root=PFI_ROOT)
    by_type = {report["report_type"]: report for report in pack["reports"]}

    assert gate["status"] == "pass"
    assert gate["errors"] == []
    assert pack["sample_counts"]["registered_source_count"] == 7
    assert pack["sample_counts"]["ready_source_count"] == 1
    assert pack["sample_counts"]["partial_source_count"] == 1
    assert pack["sample_counts"]["not_loaded_source_count"] == 5
    assert pack["sample_counts"]["transaction_record_count"] == 8815
    assert pack["sample_counts"]["operational_event_count"] == 1571
    assert pack["sample_counts"]["metric_count"] == 11
    assert pack["sample_counts"]["lineage_complete_count"] == 0
    assert pack["sample_counts"]["lineage_missing_count"] == 1571
    assert pack["data_range"] == {"start": "2022-06-06", "end": "2026-06-03"}
    assert pack["report_as_of"] == "2026-06-03"
    assert by_type["data_quality"]["status"] == "complete"
    assert by_type["consumption"]["status"] == "partial"
    assert by_type["cashflow"]["status"] == "partial"
    assert by_type["net_worth"]["status"] == "blocked"
    assert by_type["cash"]["status"] == "blocked"
    assert by_type["investment"]["status"] == "blocked"
    assert by_type["net_worth"]["conclusions"] == []
    assert by_type["cash"]["conclusions"] == []
    assert by_type["investment"]["conclusions"] == []
    assert all(report["financial_values_emitted"] == 0 for report in pack["reports"])
    assert all(report["contains_private_values"] is False for report in pack["reports"])


def test_all_reports_bind_the_same_current_data_read_model_formula_and_parameter() -> None:
    pack = build_phase91_report_pack(
        PFI_ROOT, generated_at="2026-07-15T15:30:00Z"
    )
    workflow = _json(
        PFI_ROOT
        / "reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json"
    )
    expected = pack["hashes"]

    assert expected["data_manifest_hash"] == _sha(
        PFI_ROOT / "reports/pfi_v025/stage_2/phase_2_1/source_manifest.json"
    )
    assert expected["formula_registry_hash"] == _sha(
        PFI_ROOT / "config/formulas/v025_formula_registry.json"
    )
    assert expected["parameter_hash"] == _sha(PFI_ROOT / "config/pfi_parameters.yaml")
    assert expected["read_model_hash"] == workflow["workflows"]["metric_lineage"][
        "interconnection_map"
    ]["read_model_hash"]
    assert all(report["hashes"] == expected for report in pack["reports"])
    assert len({report["snapshot_hash"] for report in pack["reports"]}) == len(
        REPORT_TYPES
    )


def test_completeness_rules_cover_complete_partial_blocked_and_any_state_quality() -> None:
    rules = _json(PFI_ROOT / COMPLETENESS_RULES_RELATIVE)
    blocked_states = {
        dependency_id: {"status": "blocked"}
        for rule in rules["report_dependencies"].values()
        for dependency_id in rule.get("critical", [])
    }
    blocked_states["SRC-TRANSACTIONS-ALIPAY"] = {"status": "ready"}

    assert derive_report_status("data_quality", blocked_states, rules) == (
        "complete",
        None,
    )
    assert derive_report_status("net_worth", blocked_states, rules) == (
        "blocked",
        None,
    )
    assert derive_report_status("consumption", blocked_states, rules) == (
        "partial",
        "transaction_source_coverage_only",
    )

    ready_states = {
        dependency_id: {"status": "ready"}
        for dependency_id in blocked_states
    }
    assert derive_report_status("net_worth", ready_states, rules) == (
        "complete",
        None,
    )


def test_validation_fails_closed_on_conclusion_hash_status_and_duplicate_tamper() -> None:
    original = build_phase91_report_pack(
        PFI_ROOT, generated_at="2026-07-15T15:30:00Z"
    )

    blocked_conclusion = deepcopy(original)
    blocked = next(
        report
        for report in blocked_conclusion["reports"]
        if report["report_type"] == "net_worth"
    )
    blocked["conclusions"].append(
        {
            "code": "INVALID",
            "scope": "financial",
            "statement_zh": "缺少依赖时仍输出确定性结论。",
            "evidence_refs": ["invalid"],
        }
    )
    assert validate_phase91_report_pack(
        blocked_conclusion, pfi_root=PFI_ROOT
    )["status"] == "fail"

    hash_drift = deepcopy(original)
    hash_drift["reports"][0]["hashes"]["parameter_hash"] = "sha256:" + "0" * 64
    assert validate_phase91_report_pack(hash_drift, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"

    whole_pack_hash_drift = deepcopy(original)
    forged_hash = "sha256:" + "0" * 64
    whole_pack_hash_drift["hashes"]["parameter_hash"] = forged_hash
    for report in whole_pack_hash_drift["reports"]:
        report["hashes"]["parameter_hash"] = forged_hash
        report["snapshot_hash"] = canonical_hash(
            {
                key: value
                for key, value in report.items()
                if key != "snapshot_hash"
            }
        )
    whole_pack_hash_drift["manifest_hash"] = canonical_hash(
        {
            key: value
            for key, value in whole_pack_hash_drift.items()
            if key != "manifest_hash"
        }
    )
    assert validate_phase91_report_pack(
        whole_pack_hash_drift, pfi_root=PFI_ROOT
    )["status"] == "fail"

    false_complete = deepcopy(original)
    next(
        report
        for report in false_complete["reports"]
        if report["report_type"] == "net_worth"
    )["status"] = "complete"
    assert validate_phase91_report_pack(false_complete, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"

    duplicate = deepcopy(original)
    duplicate["reports"].append(deepcopy(duplicate["reports"][0]))
    assert validate_phase91_report_pack(duplicate, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"


def test_phase91_evidence_pack_is_rebuildable_private_free_and_current_phase_only() -> None:
    expected_files = {
        "phase_contract.json",
        "report_schema.json",
        "completeness_rules.json",
        "report_manifest.json",
        "data_quality_report.json",
        "report_validation.json",
        "input_immutability.json",
        "artifact_hashes.json",
        "evidence.json",
        "terminal.log",
        "changed_files.txt",
        "risk_and_rollback.md",
        "privacy_scan.txt",
    }
    assert expected_files <= {path.name for path in PHASE_DIR.iterdir() if path.is_file()}

    evidence = _json(PHASE_DIR / "evidence.json")
    manifest = _json(PHASE_DIR / "report_manifest.json")
    validation = _json(PHASE_DIR / "report_validation.json")
    quality = _json(PHASE_DIR / "data_quality_report.json")
    immutability = _json(PHASE_DIR / "input_immutability.json")
    artifact_hashes = _json(PHASE_DIR / "artifact_hashes.json")
    rebuilt = build_phase91_report_pack(
        PFI_ROOT, generated_at=str(evidence["observed_at"])
    )

    assert manifest == rebuilt
    assert validation["status"] == "pass"
    assert quality == next(
        report for report in manifest["reports"] if report["report_type"] == "data_quality"
    )
    assert evidence["schema"] == "PFIV025Stage9Phase91EvidenceV1"
    assert evidence["status"] == "candidate_pass"
    assert evidence["phase_id"] == PHASE_ID
    assert evidence["task_ids"] == list(TASK_IDS)
    assert evidence["task_statuses"] == {
        task_id: "candidate_complete" for task_id in TASK_IDS
    }
    assert evidence["phase_9_2_started"] is False
    assert evidence["phase_9_3_started"] is False
    assert evidence["stage_9_whole_stage_review_done"] is False
    assert evidence["requires_stage_whole_review"] is True
    assert evidence["contains_private_values"] is False
    assert evidence["financial_values_emitted"] == 0
    assert evidence["database_read"] is False
    assert evidence["database_changed"] is False
    assert evidence["formula_values_changed"] is False
    assert evidence["parameter_values_changed"] is False
    assert evidence["finder_used"] is False
    assert evidence["external_network_performed"] is False
    assert evidence["push_performed"] is False
    assert evidence["app_install_performed"] is False
    assert immutability["status"] == "pass"
    assert immutability["before"] == immutability["after"]
    assert immutability["database_read"] is False
    assert immutability["database_changed"] is False
    assert artifact_hashes["status"] == "pass"
    for relative, expected_hash in artifact_hashes["files"].items():
        assert _sha(PFI_ROOT / relative) == expected_hash
    assert (PHASE_DIR / "privacy_scan.txt").read_text(encoding="utf-8").strip() == (
        "forbidden_hits=0\ncontains_private_values=false\nfinancial_values_emitted=0"
    )
