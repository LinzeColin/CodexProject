from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/whole_stage_review"
TASKPACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
CANDIDATE = "9a7245acf984a4eb98f93c4aab7bb4d02095294f"
FINAL_ACCEPTANCE = REVIEW_DIR / "human_acceptance.json"


def _json(name: str) -> dict[str, object]:
    payload = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_initial_review_contract_preserves_candidate_and_delivery_boundaries() -> None:
    contract = _json("phase_contract.json")
    evidence = _json("evidence.json")
    assert contract["candidate_commit"] == CANDIDATE
    assert contract["acceptance_id"] == "ACC-PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL"
    assert contract["finder_prohibited"] is True
    assert evidence["status"] == "fail"
    assert evidence["review_result"] == "remediation_required"
    assert evidence["open_p0_count"] == 0
    assert evidence["open_p1_count"] == 3
    assert evidence["finder_used"] is False
    assert evidence["app_install_performed"] is False
    assert evidence["push_performed"] is False
    assert evidence["final_human_acceptance"] is False
    assert not FINAL_ACCEPTANCE.exists()


def test_phase_commits_and_all_declared_artifacts_are_immutable() -> None:
    binding = _json("phase_commit_binding.json")
    assert binding["status"] == "pass"
    assert binding["phase_chain_linear"] is True
    assert binding["phase_count"] == 3
    assert binding["artifact_file_count"] == 119
    assert [row["artifact_file_count"] for row in binding["phases"]] == [73, 27, 19]
    assert all(row["all_artifacts_match"] for row in binding["phases"])
    assert all(row["evidence_schema_error_count"] == 0 for row in binding["phases"])
    assert all(row["task_ids_exact"] for row in binding["phases"])


def test_fresh_real_e2e_recheck_is_non_fixture_and_truthful() -> None:
    fresh = _json("fresh_real_e2e.json")
    assert fresh["status"] == "pass"
    assert fresh["source_blob_count"] == 4
    assert fresh["transaction_count"] == fresh["ledger_count"] == 8808
    assert fresh["review_count"] == 803
    assert fresh["replay_idempotent"] is True
    assert fresh["holding_execution_status"] == "not_run"
    assert fresh["holding_truth_gate_status"] == "pass"
    assert fresh["holding_financial_pass_claimed"] is False
    assert fresh["browser_check_count"] == fresh["browser_passed_check_count"]
    assert fresh["canonical_database_read"] is False
    assert fresh["canonical_database_changed"] is False
    assert fresh["external_network_performed"] is False
    assert fresh["temporary_artifacts_retained"] is False


def test_initial_findings_are_specific_and_release_blocking() -> None:
    findings = _json("initial_review_findings.json")
    assert findings["status"] == "remediation_required"
    assert findings["counts"] == {"critical": 0, "important": 3, "minor": 0}
    assert findings["open_p0_count"] == 0
    assert findings["open_p1_count"] == 3
    assert len(findings["findings"]) == 3
    assert all(row["release_blocking"] for row in findings["findings"])
    assert {row["finding_id"] for row in findings["findings"]} == {
        "S12-WR-I01-RELEASE-COMMIT-DRIFT",
        "S12-WR-I02-EXACT-ACCEPTANCE-BINDING",
        "S12-WR-I03-NONCANONICAL-OLD-APP",
    }
    assert len(findings["residual_risks"]) == 5
    assert findings["rereview_status"] == "not_started"


def test_release_identity_hashes_pass_but_manifest_commit_is_not_exact() -> None:
    release = _json("release_identity_audit.json")
    assert release["status"] == "fail_manifest_commit_precedes_runtime_changes"
    assert release["manifest_commit_is_ancestor"] is True
    assert release["manifest_commit_exact_for_runtime_files"] is False
    assert release["runtime_files_changed_after_manifest_commit_count"] > 0
    assert release["asset_hash_identity_valid"] is True
    assert release["installed_app_matches_phase122_receipt"] is True
    assert release["installed_app_codesign_valid"] is True
    assert release["finder_used"] is False


def test_final_index_bytes_pass_but_candidate_binding_is_not_exact() -> None:
    audit = _json("final_index_audit.json")
    assert audit["status"] == "fail_exact_candidate_binding_required"
    assert audit["candidate_commit"] == CANDIDATE
    assert audit["all_index_files_match_at_candidate"] is True
    assert audit["index_file_count"] == audit["index_match_count"] == 89
    assert audit["detached_hash_matches"] is True
    assert audit["acceptance_request_hash_matches"] is True
    assert audit["acceptance_request_commit_exact"] is False
    assert audit["state_head_exact"] is False
    assert audit["human_acceptance_artifact_exists"] is False


def test_entry_audit_requires_cli_only_old_copy_remediation() -> None:
    entry = _json("entry_audit.json")
    assert entry["status"] == "fail_noncanonical_old_app_remains"
    assert entry["canonical_app_version"] == "0.2.5"
    assert entry["desktop_targets_canonical"] is True
    assert entry["noncanonical_copy_mismatch_count"] == 1
    assert entry["noncanonical_copy_version"] == "0.2.3"
    assert entry["noncanonical_copies_modified"] is False
    assert entry["finder_used"] is False
    assert entry["remediation_must_remain_cli_only"] is True


def test_requirement_matrix_does_not_flatten_known_limitations_or_final_gate() -> None:
    matrix = _json("requirement_matrix.json")
    rows = {row["requirement_id"]: row for row in matrix["requirements"]}
    assert matrix["status"] == "remediation_required"
    assert matrix["requirement_count"] == 10
    assert matrix["status_counts"]["fail_remediation_required"] == 3
    assert rows["S12-ACC-03-HOLDING-TRUTH"]["status"] == "pass_with_known_limitation"
    assert rows["S12-ACC-05-ROUTES-UX-QUALITY"]["axe_pass_claimed"] is False
    assert rows["S12-ACC-06-TARGET-MAC-LIFECYCLE"]["actual_os_sleep_performed"] is False
    assert rows["S12-ACC-10-FINAL-HUMAN-ACCEPTANCE"]["status"] == "pending_after_rereview"


def test_review_evidence_schema_privacy_and_artifact_hashes_pass() -> None:
    evidence = _json("evidence.json")
    with zipfile.ZipFile(TASKPACK) as archive:
        schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
        )
    assert list(Draft202012Validator(schema).iter_errors(evidence)) == []
    privacy = (REVIEW_DIR / "privacy_scan.txt").read_text(encoding="utf-8")
    assert privacy.startswith("PASS\n")
    assert "absolute_private_paths=0" in privacy
    assert "financial_values=0" in privacy
    manifest = _json("artifact_manifest.json")
    assert manifest["status"] == "pass"
    assert manifest["privacy_scan_status"] == "pass"
    assert manifest["file_count"] == len(manifest["files"])
    for relative, expected in manifest["files"].items():
        actual = "sha256:" + hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected


def test_initial_reviewer_source_contains_no_gui_operation_command() -> None:
    source = (PFI_ROOT / "scripts/v025/stage12_whole_review_initial.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        '["open"',
        "['open'",
        '["osascript"',
        "['osascript'",
        '["lsregister"',
        "['lsregister'",
    )
    assert not any(marker in source for marker in forbidden)
