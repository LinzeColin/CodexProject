from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from pfi_v02.stage_v025_stage2_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage2_whole_review_contract,
    evaluate_stage2_phase_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports" / "pfi_v025" / "stage_2" / "whole_stage_review"
DOC = PFI_ROOT / "docs" / "pfi_v025" / "stage_2" / "STAGE_2_WHOLE_STAGE_REVIEW.md"
VERIFIER = PFI_ROOT / "scripts" / "v025" / "verify_stage2_whole_review.py"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_contract_is_exactly_stage2_gate() -> None:
    contract = build_stage2_whole_review_contract()
    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 2
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE2-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE == "431ddb30c483f6451c29dfb6890c4bee5690c57c"
    assert contract["task_ids"] == [f"S2-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert contract["acceptance_criteria_count"] == 6
    assert contract["stop_condition_count"] == 4
    assert contract["independent_review_tracks"] == [
        "requirements_evidence",
        "code_security_privacy",
        "governance_renderer",
    ]
    assert contract["stage_3_work_performed"] is False
    assert contract["finder_used"] is False


def test_phase_evidence_is_commit_bound_and_immutable() -> None:
    result = evaluate_stage2_phase_evidence(ROOT)
    assert result["status"] == "pass"
    assert result["phase_count"] == 3
    assert result["task_count"] == 12
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["working_tree_matches_phase_commits"] is True
    assert result["phase_evidence_sha256"] == {
        "2.1": "81fb9fb6b1f4fef1974474622c08b1b08510f1692014bc896f689d3de14723db",
        "2.2": "dcefd989c4c82dadbcee03037318bff978cadf1158b1d160c9ed703316dc15f7",
        "2.3": "b1cd5ed64fd0af3433547c5c142f0f26263e5b0d94df0c294f41bb5f32f2ecfc",
    }


def test_review_audit_records_findings_remediation_and_clean_rereview() -> None:
    audit = _json(REVIEW_DIR / "review_audit.json")
    assert audit["initial_review"]["counts"] == {"critical": 0, "important": 3, "minor": 1}
    assert {finding["finding_id"] for finding in audit["initial_review"]["findings"]} == {
        "S2-WR-I01",
        "S2-WR-I02",
        "S2-WR-I03",
        "S2-WR-M01",
    }
    assert all(finding["status"] == "fixed" for finding in audit["initial_review"]["findings"])
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}
    assert audit["post_remediation_review"]["result"] == "pass"
    assert audit["independent_review_tracks"] == {
        "requirements_evidence": "pass",
        "code_security_privacy": "pass",
        "governance_renderer": "pass",
    }


def test_final_index_closes_all_stage2_contract_items() -> None:
    index = _json(REVIEW_DIR / "final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S2-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 6
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "clear" for item in index["stop_conditions"])
    assert index["pass_gate_status"] == "pass"
    assert index["stage_2_user_acceptance_status"] == "accepted"
    assert index["stage_3_entry_authorized"] is True
    assert index["stage_3_status"] == "not_started"


def test_source_disposition_accepts_truthful_scope_and_no_false_zero() -> None:
    disposition = _json(REVIEW_DIR / "source_disposition.json")
    assert disposition["canonical_private_root_alias"] == "$PFI_DATA_HOME"
    assert disposition["transaction_source"] == {
        "source_id": "SRC-TRANSACTIONS-ALIPAY",
        "status": "ready",
        "record_count": 8815,
        "coverage_start": "2022-06-06",
        "coverage_end": "2026-06-03",
    }
    assert disposition["operational_sqlite"]["status"] == "ready_metadata_only"
    assert disposition["operational_sqlite"]["isolation_verified"] is True
    assert disposition["production_fx"]["status"] == "not_loaded"
    assert disposition["production_fx"]["rate_present"] is False
    assert disposition["metric_computability"] == {
        "consumption_classification": "blocked_missing_dependencies",
        "consumption_outflow_cny": "blocked_missing_dependencies",
        "cash_balance_cny": "blocked_missing_dependencies",
        "investment_market_value_cny": "blocked_missing_dependencies",
        "net_worth_cny": "blocked_missing_dependencies",
    }
    assert disposition["financial_zero_claims"] == 0


def test_human_acceptance_is_schema_valid_and_binds_final_index() -> None:
    acceptance = _json(REVIEW_DIR / "human_acceptance.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(acceptance)
    assert acceptance["stage"] == 2
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert acceptance["accepted_scope"] == [
        "canonical private data root is $PFI_DATA_HOME with explicit aliases and no migration",
        "transaction source scope is 8815 records covering 2022-06-06 through 2026-06-03",
        "all five current finance metrics remain blocked/null until listed dependencies are satisfied",
        "production FX remains not_loaded/null and ordinary runtime remains offline",
        "real-data validation is read-only, redacted and has no financial fixture fallback",
    ]
    assert acceptance["user_confirmation_reference"] == "conversation_user_blanket_interim_authorization_before_final_acceptance"


def test_taskpack_evidence_schema_accepts_whole_review_evidence() -> None:
    evidence = _json(REVIEW_DIR / "evidence.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)
    assert evidence["status"] == "candidate_pass"
    assert evidence["stage_2_status"] == "accepted_for_transition"
    assert evidence["stage_3_entry_authorized"] is True
    assert evidence["stage_3_work_performed"] is False
    assert evidence["production_accepted"] is False
    assert evidence["final_human_acceptance"] is False


def test_artifact_hashes_and_privacy_scan_are_bound() -> None:
    evidence = _json(REVIEW_DIR / "evidence.json")
    for relative, expected in evidence["artifact_hashes"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
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


def test_canonical_governance_accepts_stage2_without_starting_stage3() -> None:
    project = (PFI_ROOT / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    roadmap = (PFI_ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
    assert 'current_status: "stage_2_accepted_for_transition"' in project
    assert 'stage_2_status: "accepted_for_transition"' in project
    assert 'stage_3_entry_authorized: true' in project
    assert 'stage_3_status: "not_started"' in project
    assert 'tracked_status: "stage_2_accepted_for_transition"' in roadmap
    assert 'stage_2_status: "accepted_for_transition"' in roadmap
    assert 'stage_3_entry_authorized: true' in roadmap
    assert 'stage_3_status: "not_started"' in roadmap
    assert 'next_gate_id: "ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT"' in roadmap


def test_review_document_and_risk_boundary_are_explicit() -> None:
    review = DOC.read_text(encoding="utf-8")
    risk = (REVIEW_DIR / "risk_and_rollback.md").read_text(encoding="utf-8")
    for token in (
        "12/12",
        "6/6",
        "4/4",
        "accepted_for_transition",
        "Stage 3 未开始",
        "未使用 Finder",
    ):
        assert token in review
    assert "production FX" in risk
    assert "0755" in risk and "0644" in risk
    assert "不触碰真实数据" in risk


def test_verifier_is_read_only_and_passes_current_candidate() -> None:
    before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    completed = subprocess.run(
        [
            str(PFI_ROOT / ".venv" / "bin" / "python"),
            "-B",
            str(VERIFIER),
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
    assert before == after
