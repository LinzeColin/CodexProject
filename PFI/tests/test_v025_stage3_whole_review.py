from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.application.stage3_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage3_whole_review_contract,
    evaluate_stage3_phase_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports" / "pfi_v025" / "stage_3" / "whole_stage_review"
DOC = PFI_ROOT / "docs" / "pfi_v025" / "stage_3" / "STAGE_3_WHOLE_STAGE_REVIEW.md"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_contract_is_exactly_stage3_gate() -> None:
    contract = build_stage3_whole_review_contract()
    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 3
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE3-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE == "0f9672081463523bab35a2b310216078fd3ad9d3"
    assert contract["task_ids"] == [f"S3-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert contract["acceptance_criteria_count"] == 6
    assert contract["stop_condition_count"] == 4
    assert contract["stage_4_work_performed"] is False
    assert contract["finder_used"] is False


def test_phase_evidence_is_commit_bound_and_immutable() -> None:
    result = evaluate_stage3_phase_evidence(ROOT)
    assert result["status"] == "pass"
    assert result["phase_count"] == 3
    assert result["task_count"] == 12
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["working_tree_matches_phase_commits"] is True
    assert result["phase_evidence_sha256"] == {
        "3.1": "e73fc62cfd58b0a6dc04372ab4a5420d3bb81e078fed4b0b83287d93205c84d7",
        "3.2": "884e73071d9afd7658e86ab79b58ac120c0a37deaafa6c8867c750315d839fcd",
        "3.3": "c9195e92f84123a528ef650cd8bfbaf999d5092a19501eec01b32e95d930cf6f",
    }


def test_review_audit_records_remediation_and_clean_rereview() -> None:
    audit = _json(REVIEW_DIR / "review_audit.json")
    assert audit["initial_review"]["counts"] == {"critical": 0, "important": 3, "minor": 1}
    assert {item["finding_id"] for item in audit["initial_review"]["findings"]} == {
        "S3-WR-I01",
        "S3-WR-I02",
        "S3-WR-I03",
        "S3-WR-M01",
    }
    assert all(item["status"] == "fixed" for item in audit["initial_review"]["findings"])
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}
    assert audit["post_remediation_review"]["result"] == "pass"


def test_final_index_closes_stage3_without_overclaiming_residual_chains() -> None:
    index = _json(REVIEW_DIR / "final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S3-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 6
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "clear" for item in index["stop_conditions"])
    assert index["pass_gate_status"] == "pass"
    assert index["pass_gate_result"] == "pass_with_review_queue"
    assert index["stage_3_user_acceptance_status"] == "accepted"
    assert index["stage_4_entry_authorized"] is True
    assert index["stage_4_status"] == "not_started"


def test_source_disposition_preserves_exact_real_snapshot_partition() -> None:
    disposition = _json(REVIEW_DIR / "source_disposition.json")
    assert disposition["real_snapshot"] == {
        "source_id": "SRC-TRANSACTIONS-ALIPAY",
        "isolation_mode": "immutable_git_object_snapshot",
        "input_record_count": 8815,
        "published_record_count": 6879,
        "review_queue_record_count": 1936,
        "silent_drop_count": 0,
    }
    assert disposition["review_reason_counts"] == {
        "refund_offset_missing": 249,
        "transfer_role_or_link_missing": 1250,
        "upstream_review_required": 406,
        "zero_amount": 31,
    }
    assert disposition["transfer_chain"]["confirmed"] is False
    assert disposition["transfer_chain"]["unresolved_review_count"] == 1250
    assert disposition["refund_chain"]["confirmed"] is False
    assert disposition["refund_chain"]["unresolved_review_count"] == 249
    assert disposition["investment_chain"]["published_count"] == 3166
    assert disposition["financial_zero_claims"] == 0


def test_human_acceptance_is_schema_valid_and_binds_final_index() -> None:
    acceptance = _json(REVIEW_DIR / "human_acceptance.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(acceptance)
    assert acceptance["stage"] == 3
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert acceptance["user_confirmation_reference"] == "conversation_user_blanket_interim_authorization_before_final_acceptance"
    assert any("1,250" in item and "未确认" in item for item in acceptance["known_defects"])
    assert any("249" in item and "未确认" in item for item in acceptance["known_defects"])


def test_taskpack_evidence_schema_accepts_whole_review_evidence() -> None:
    evidence = _json(REVIEW_DIR / "evidence.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)
    assert evidence["status"] == "candidate_pass"
    assert evidence["stage_3_status"] == "accepted_for_transition"
    assert evidence["stage_4_entry_authorized"] is True
    assert evidence["stage_4_work_performed"] is False
    assert evidence["production_accepted"] is False
    assert evidence["final_human_acceptance"] is False


def test_artifact_hashes_and_privacy_scan_are_bound() -> None:
    evidence = _json(REVIEW_DIR / "evidence.json")
    for relative, expected in evidence["artifact_hashes"].items():
        assert _sha256(ROOT / relative) == expected
    privacy = (REVIEW_DIR / "privacy_scan.txt").read_text(encoding="utf-8")
    assert privacy.splitlines()[0] == "PASS"
    for counter in (
        "absolute_private_paths",
        "financial_row_values",
        "account_identifiers",
        "credentials",
        "sqlite_table_names",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in privacy


def test_canonical_governance_accepts_stage3_without_starting_stage4() -> None:
    project = (PFI_ROOT / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    roadmap = (PFI_ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
    for text in (project, roadmap):
        assert 'stage_3_status: "accepted_for_transition"' in text
        assert "stage_4_entry_authorized: true" in text
        assert 'stage_4_status: "not_started"' in text
    assert 'next_gate_id: "ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT"' in roadmap


def test_review_document_states_limits_and_no_forbidden_actions() -> None:
    review = DOC.read_text(encoding="utf-8")
    risk = (REVIEW_DIR / "risk_and_rollback.md").read_text(encoding="utf-8")
    for token in ("12/12", "6/6", "4/4", "accepted_for_transition", "Stage 4 未开始", "未使用 Finder"):
        assert token in review
    assert "1,250" in review and "249" in review and "未确认" in review
    assert "不触碰真实数据" in risk
    assert "Stage 4" in risk and "production" in risk


def test_verifier_is_read_only_and_passes_postcommit_candidate() -> None:
    before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    completed = subprocess.run(
        [
            str(PFI_ROOT / ".venv" / "bin" / "python"),
            "-B",
            "-m",
            "pfi_os.application.stage3_whole_review",
            "--repo-root",
            str(ROOT),
            "--candidate",
            "HEAD",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(PFI_ROOT / "src")},
    )
    after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "pass"
    assert result["review_findings"] == {"critical": 0, "important": 0, "minor": 0}
    assert result["stage_3_status"] == "accepted_for_transition"
    assert result["stage_4_entry_authorized"] is True
    assert before == after
