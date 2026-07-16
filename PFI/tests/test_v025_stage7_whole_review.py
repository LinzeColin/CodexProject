from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from pfi_v02.stage_v025_stage7_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage7_whole_review_contract,
    evaluate_stage7_phase_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        assert key not in payload, f"duplicate JSON key: {key}"
        payload[key] = value
    return payload


def _json(name: str) -> dict[str, object]:
    payload = json.loads(
        (REVIEW_DIR / name).read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    assert isinstance(payload, dict)
    return payload


def _taskpack_schema(name: str) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        return json.loads(archive.read(f"PFI_v0.2.5_TaskPack/schemas/{name}"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_overlay() -> dict[str, object]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    review_prefix = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    entries = [entry for entry in raw.split("\0") if len(entry) >= 4]
    unsupported = [entry[:2] for entry in entries if any(marker in entry[:2] for marker in ("D", "R", "C"))]
    assert not unsupported, f"unsupported delete/rename/copy worktree states: {unsupported}"
    paths = sorted({
        entry[3:]
        for entry in entries
        if not entry[3:].startswith(review_prefix)
        and (REPO_ROOT / entry[3:]).is_file()
    })
    files = [
        {"path": path, "sha256": "sha256:" + _sha256(REPO_ROOT / path)}
        for path in paths
    ]
    records = "".join(
        f"{item['path']}\0{item['sha256']}\n" for item in files
    ).encode("utf-8")
    return {
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _load_builder():
    path = PFI_ROOT / "scripts/v025/build_stage7_whole_review.py"
    spec = importlib.util.spec_from_file_location("pfi_stage7_whole_review_builder_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_is_exactly_stage7_whole_review() -> None:
    contract = build_stage7_whole_review_contract()
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE7-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE
    assert contract["phase_commits"] == PHASE_COMMITS
    assert contract["task_ids"] == [f"S7-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert len(contract["workflow_ids"]) == 3
    assert contract["stage_8_started"] is False
    assert contract["finder_used"] is False


def test_phase_evidence_is_immutably_commit_bound() -> None:
    result = evaluate_stage7_phase_evidence(REPO_ROOT)
    assert result["status"] == "pass"
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["task_count"] == 12
    assert result["linear_commit_chain"] is True
    assert result["all_phase_evidence_present_in_bound_commits"] is True
    assert result["all_phase_evidence_candidate_pass"] is True


def test_all_phase_evidence_packs_validate_taskpack_schema() -> None:
    validator = Draft202012Validator(_taskpack_schema("evidence_pack.schema.json"))
    for phase in ("7_1", "7_2", "7_3"):
        validator.validate(json.loads(
            (PFI_ROOT / f"reports/pfi_v025/stage_7/phase_{phase}/evidence.json").read_text(encoding="utf-8")
        ))


def test_stage7_json_inputs_reject_duplicate_keys() -> None:
    for path in (
        PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_1/real_source_boundary.json",
        PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_1/evidence.json",
        PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_2/evidence.json",
        PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_3/evidence.json",
    ):
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        assert isinstance(payload, dict)


def test_current_head_three_workflow_review_passes() -> None:
    workflow = _json("workflow_validation.json")
    assert workflow["status"] == "pass"
    assert workflow["current_head"] == REVIEW_BASE
    assert workflow["workflow_status"] == {
        "holding_settings": True,
        "import_review_ledger": True,
        "metric_lineage": True,
    }
    assert workflow["browser_check_count"] == 68
    assert workflow["phase_evidence_overwritten"] is False
    assert workflow["finder_used"] is False
    assert workflow["external_network_performed"] is False
    assert workflow["database_scope"] == "isolated_/tmp_only"
    assert workflow["workflows"]["import_review_ledger"]["preview_ledger_count"] == 0
    assert workflow["workflows"]["import_review_ledger"]["confirmed_ledger_count"] == 1571
    assert workflow["workflows"]["holding_settings"]["restart_persistence"]["status"] == "pass"
    assert workflow["workflows"]["holding_settings"]["browser_storage_used_for_formal_settings"] is False
    assert workflow["workflows"]["metric_lineage"]["financial_values_persisted"] == 0
    overlay = _json("reviewed_worktree_overlay.json")
    assert {
        key: overlay[key]
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    } == _current_overlay()
    assert overlay["base_commit"] == REVIEW_BASE
    assert overlay["content_manifest_sha256"] == workflow["reviewed_worktree_overlay"]["content_manifest_sha256"]
    assert workflow["reviewed_worktree_overlay"]["post_run_rescan_identical"] is True
    records = "".join(
        f"{item['path']}\0{item['sha256']}\n" for item in overlay["files"]
    ).encode("utf-8")
    assert overlay["content_manifest_sha256"] == "sha256:" + hashlib.sha256(records).hexdigest()
    assert workflow["persisted_trace_hashes"] == {
        name: "sha256:" + _sha256(REVIEW_DIR / name)
        for name in (
            "holding_browser_trace_sanitized.zip",
            "holding_restart_browser_trace_sanitized.zip",
            "import_browser_trace_sanitized.zip",
            "metric_browser_trace_sanitized.zip",
        )
    }
    for name in workflow["persisted_trace_hashes"]:
        with zipfile.ZipFile(REVIEW_DIR / name) as archive:
            assert "trace.trace" in archive.namelist()


def test_initial_findings_fixed_and_rereview_clean() -> None:
    audit = _json("review_audit.json")
    assert audit["status"] == "pass"
    source_reviews = audit["initial_review"]["source_reviews"]
    dynamic_counts = {
        severity: sum(row[severity] for row in source_reviews.values())
        for severity in ("critical", "important", "minor")
    }
    assert audit["initial_review"]["counts"] == dynamic_counts
    assert sum(audit["initial_review"]["counts"].values()) >= 1
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}


def test_phase_evidence_amendments_disclose_original_schema_gaps() -> None:
    binding = _json("phase_evidence_amendment_binding.json")
    assert binding["status"] == "pass"
    assert binding["taskpack_schema_sha256"].startswith("sha256:")
    by_phase = {row["phase"]: row for row in binding["phase_evidence"]}
    assert by_phase["7.1"]["original_schema_valid"] is True
    assert by_phase["7.2"]["original_schema_valid"] is False
    assert by_phase["7.3"]["original_schema_valid"] is False
    assert all(row["amended_schema_valid"] is True for row in by_phase.values())
    assert all(row["amended_sha256"].startswith("sha256:") for row in by_phase.values())


def test_real_verification_and_three_independent_reviews_are_bound() -> None:
    verification = _json("verification_results.json")
    assert verification["status"] == "pass"
    assert verification["overlay_stable_during_verification"] is True
    assert verification["verified_overlay"] == _current_overlay()
    commands = {row["command_id"]: row for row in verification["commands"]}
    assert {"focused_stage7", "syntax_and_diff", "changed_scope_governance"} <= set(commands)
    assert all(row["exit_code"] == 0 for row in commands.values())
    assert all(row["output_sha256"].startswith("sha256:") for row in commands.values())

    reviewers = _json("reviewer_results.json")
    assert reviewers["status"] == "pass"
    assert {row["reviewer_id"] for row in reviewers["reviewers"]} == {
        "final_code_security_review",
        "final_governance_renderer_review",
        "final_acceptance_evidence_review",
    }
    for row in reviewers["reviewers"]:
        assert row["decision"] == "ACCEPT"
        assert row["counts"] == {"critical": 0, "important": 0, "minor": 0}
        assert row["result_sha256"] == "sha256:" + hashlib.sha256(
            row["result_text"].encode("utf-8")
        ).hexdigest()
        assert row["review_base"] == REVIEW_BASE
        assert row["reviewed_overlay_file_count"] == _current_overlay()["file_count"]
        assert row["reviewed_overlay_sha256"] == _current_overlay()["content_manifest_sha256"]

    builder = _load_builder()
    overlay = _json("reviewed_worktree_overlay.json")
    builder._require_reviewers(reviewers, overlay)
    stale = json.loads(json.dumps(reviewers))
    stale["reviewers"][0]["reviewed_overlay_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="not bound to the current frozen overlay"):
        builder._require_reviewers(stale, overlay)


def test_verification_rejects_stale_overlay_and_private_paths() -> None:
    verification = _json("verification_results.json")
    overlay = _json("reviewed_worktree_overlay.json")
    builder = _load_builder()
    stale = dict(overlay)
    stale["content_manifest_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="not content-bound"):
        builder._require_verification(verification, stale)

    persisted = json.dumps(verification, ensure_ascii=False)
    assert str(Path.home()) not in persisted
    assert "/Users/" not in persisted
    for row in verification["commands"]:
        log_text = (REPO_ROOT / row["output_ref"]).read_text(encoding="utf-8")
        assert str(Path.home()) not in log_text
        assert "/Users/" not in log_text

    tampered = json.loads(json.dumps(verification))
    tampered["commands"][0]["command"] += " /Users/private/python3"
    with pytest.raises(RuntimeError, match="private absolute path"):
        builder._require_verification(tampered, overlay)


def test_builder_rejects_unsafe_workflow_and_trace_hash_tampering() -> None:
    workflow = _json("workflow_validation.json")
    builder = _load_builder()
    builder._require_workflow_safety_and_traces(workflow)

    unsafe = json.loads(json.dumps(workflow))
    unsafe["contains_private_values"] = True
    with pytest.raises(RuntimeError, match="safety flags"):
        builder._require_workflow_safety_and_traces(unsafe)

    stale_trace = json.loads(json.dumps(workflow))
    stale_trace["persisted_trace_hashes"]["holding_browser_trace_sanitized.zip"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="trace hash mismatch"):
        builder._require_workflow_safety_and_traces(stale_trace)


def test_final_index_accepts_stage7_and_stops_before_stage8() -> None:
    index = _json("final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S7-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 6
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "safety_stop_active" for item in index["stop_conditions"])
    assert index["pass_gate_result"] == "pass"
    assert index["stage_8_entry_authorized"] is True
    assert index["stage_8_status"] == "not_started"
    artifacts = {row["path"]: row["sha256"] for row in index["evidence_artifacts"]}
    required = {
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewed_worktree_overlay.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/phase_commit_binding.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/phase_evidence_amendment_binding.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/verification_results.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewer_results.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/security_validation.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/review_audit.json",
    }
    assert required <= set(artifacts)
    for path, expected in artifacts.items():
        assert expected == "sha256:" + _sha256(REPO_ROOT / path)


def test_human_acceptance_schema_and_final_index_binding() -> None:
    acceptance = _json("human_acceptance.json")
    Draft202012Validator(
        _taskpack_schema("human_acceptance.schema.json"), format_checker=FormatChecker()
    ).validate(acceptance)
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert acceptance["user_confirmation_reference"] == "thread_pre_final_acceptance_blanket_authorization_and_no_more_blocks"


def test_review_evidence_pack_is_schema_valid_and_safe() -> None:
    evidence = _json("evidence.json")
    Draft202012Validator(_taskpack_schema("evidence_pack.schema.json")).validate(evidence)
    assert evidence["contains_private_values"] is False
    assert evidence["real_financial_data_mutated"] is False
    assert evidence["database_scope"] == "isolated_/tmp_only"
    assert evidence["finder_used"] is False
    assert evidence["reviewed_source_overlay_files"] == [
        row["path"] for row in _json("reviewed_worktree_overlay.json")["files"]
    ]
    assert set(evidence["reviewed_source_overlay_files"]) < set(evidence["changed_files"])
    assert "PFI/reports/pfi_v025/stage_7/whole_stage_review/evidence.json" in evidence["changed_files"]
    assert evidence["stage_7_status"] == "accepted_for_transition"
    assert evidence["stage_8_work_performed"] is False
    assert evidence["push_performed"] is False
    assert evidence["app_install_performed"] is False
