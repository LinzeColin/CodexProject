from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.application.stage4_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage4_whole_review_contract,
    evaluate_stage4_phase_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = ROOT / "PFI/reports/pfi_v025/stage_4/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"


def _json(name: str) -> dict[str, object]:
    value = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_is_exactly_stage4_whole_review() -> None:
    contract = build_stage4_whole_review_contract()
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE4-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE == "8478bbc65ed739ef5f22b1cfc4a932f15837be1d"
    assert contract["task_ids"] == [f"S4-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert contract["stage_5_work_performed"] is False
    assert contract["finder_used"] is False


def test_phase_evidence_is_commit_bound() -> None:
    result = evaluate_stage4_phase_evidence(ROOT)
    assert result["status"] == "pass"
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["task_count"] == 12
    assert result["working_tree_matches_phase_commits"] is True


def test_initial_findings_are_fixed_and_rereview_is_clean() -> None:
    audit = _json("review_audit.json")
    assert audit["initial_review"]["counts"] == {"critical": 0, "important": 5, "minor": 1}
    assert all(item["status"] == "fixed" for item in audit["initial_review"]["findings"])
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}


def test_final_index_accepts_transition_without_financial_overclaim() -> None:
    index = _json("final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S4-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 6
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "safety_stop_active" for item in index["stop_conditions"])
    assert index["pass_gate_result"] == "pass_with_not_loaded_sources"
    assert index["stage_5_entry_authorized"] is True
    assert index["stage_5_status"] == "not_started"


def test_metric_disposition_is_fail_closed_and_cross_surface_consistent() -> None:
    disposition = _json("metric_disposition.json")
    assert disposition["metric_count"] == 7
    assert disposition["statuses"] == {"not_loaded": 7}
    assert disposition["non_null_value_count"] == 0
    assert disposition["confirmed_zero_count"] == 0
    assert disposition["false_zero_count"] == 0
    assert disposition["surface_count"] == 5
    assert disposition["surface_hash_count"] == 1
    assert disposition["read_model_hash"] == "sha256:56527147cd3bb48cd3262696a6289e0396208e4de751022368497dcce94d779e"


def test_acceptance_schema_and_index_binding() -> None:
    acceptance = _json("human_acceptance.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(acceptance)
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert any("not_loaded" in item for item in acceptance["known_defects"])


def test_browser_evidence_proves_fail_closed_rendering_without_finder() -> None:
    browser = _json("browser_validation.json")
    a11y = _json("accessibility_tree.json")
    assert browser["status"] == "pass"
    assert browser["finder_used"] is False
    assert browser["false_zero_render_count"] == 0
    assert browser["metric_count"] == 7
    assert browser["surface_hash_count"] == 1
    assert a11y["status"] == "pass"
    assert a11y["missing_state_explanation_count"] >= 1


def test_evidence_pack_is_schema_valid_and_safe() -> None:
    evidence = _json("evidence.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    Draft202012Validator(schema).validate(evidence)
    assert evidence["contains_private_values"] is False
    assert evidence["real_financial_data_read"] is False
    assert evidence["finder_used"] is False
    assert evidence["stage_5_work_performed"] is False
