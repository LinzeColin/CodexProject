from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from stage12_whole_review_rereview import (  # noqa: E402
    FINAL_ACCEPTANCE,
    PRODUCT_CANDIDATE_COMMIT,
    RELEASE_SOURCE_COMMIT,
    REVIEWED_CLOSURE_COMMIT,
    REREVIEW_DIR,
    artifact_integrity_audit,
    binding_rereview,
    closure_overlay_audit,
    entry_rereview,
    verify_existing,
)


def test_exact_source_candidate_closure_chain_has_no_runtime_drift() -> None:
    audit = closure_overlay_audit()
    assert audit["status"] == "pass"
    assert audit["release_source_commit"] == RELEASE_SOURCE_COMMIT
    assert audit["product_candidate_commit"] == PRODUCT_CANDIDATE_COMMIT
    assert audit["reviewed_closure_commit"] == REVIEWED_CLOSURE_COMMIT
    assert audit["closure_disallowed_file_count"] == 0
    assert audit["current_overlay_disallowed_file_count"] == 0
    assert audit["runtime_payload_drift_count_through_current_head"] == 0
    assert all(audit["checks"].values())


def test_exact_binding_is_recomputed_and_acceptance_state_is_valid() -> None:
    audit = binding_rereview()
    assert audit["status"] == "pass"
    assert audit["product_candidate_commit"] == PRODUCT_CANDIDATE_COMMIT
    assert audit["indexed_file_mismatch_count"] == 0
    assert all(audit["checks"].values())
    assert audit["final_human_acceptance"] is FINAL_ACCEPTANCE.exists()


def test_live_cli_entry_census_is_recomputed_without_gui() -> None:
    audit = entry_rereview()
    assert audit["status"] == "pass"
    assert audit["noncanonical_entry_mismatch_count"] == 0
    assert audit["canonical_app_modified"] is False
    assert audit["finder_used"] is False
    assert audit["launchservices_used"] is False
    assert audit["gui_file_operations_used"] is False


def test_phase123_and_remediation_manifests_match_current_bytes() -> None:
    audit = artifact_integrity_audit()
    assert audit["status"] == "pass"
    assert audit["manifest_count"] == 2
    assert audit["total_mismatch_count"] == 0


def test_rereview_source_has_no_gui_command_invocation() -> None:
    source = (
        PFI_ROOT / "scripts/v025/stage12_whole_review_rereview.py"
    ).read_text(encoding="utf-8")
    forbidden_command_literals = (
        '["open"',
        "['open'",
        '["osascript"',
        "['osascript'",
        '["lsregister"',
        "['lsregister'",
    )
    assert not any(marker in source for marker in forbidden_command_literals)


def test_recorded_rereview_pack_is_consistent_when_present() -> None:
    evidence_path = REREVIEW_DIR / "evidence.json"
    if not evidence_path.is_file():
        return
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    findings = json.loads((REREVIEW_DIR / "findings.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "candidate_pass"
    assert evidence["rereview_result"] == "pass_waiting_explicit_final_acceptance"
    assert evidence["reviewed_closure_commit"] == REVIEWED_CLOSURE_COMMIT
    assert findings["rereview_open_p0_count"] == 0
    assert findings["rereview_open_p1_count"] == 0
    assert findings["rereview_minor_count"] == 0
    assert evidence["final_human_acceptance"] is False


def test_postcommit_verifier_passes_when_manifest_present() -> None:
    if not (REREVIEW_DIR / "artifact_manifest.json").is_file():
        return
    contract = json.loads(
        (REREVIEW_DIR / "phase_contract.json").read_text(encoding="utf-8")
    )
    if contract.get("status") == "in_progress":
        # A repeated finalizer rewrites core evidence before replacing the old
        # manifest.  The completed pack is verified after the atomic rebuild.
        return
    result = verify_existing()
    assert result["status"] == "pass"
    assert result["runtime_payload_drift_count"] == 0
    assert all(result["checks"].values())
