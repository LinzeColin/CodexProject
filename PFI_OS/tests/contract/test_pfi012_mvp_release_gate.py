from __future__ import annotations

import json
from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA,
    PFI012_MVP_RELEASE_GATE_CONTRACT_SCHEMA,
    PFI012_RELEASE_MANIFEST_SCHEMA,
    build_pfi012_mvp_release_gate_contract,
    build_pfi012_release_checksum_manifest,
    run_pfi012_mvp_release_gate_acceptance,
)
from pfi_os.application.pfi012_mvp_release_gate import PFI012_RELEASE_FILES, PFI012_REQUIRED_LATEST_ARTIFACTS


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_pfi012_contract_declares_gate6_gate7_release_conditions() -> None:
    contract = build_pfi012_mvp_release_gate_contract()

    assert contract["schema"] == PFI012_MVP_RELEASE_GATE_CONTRACT_SCHEMA
    assert contract["issue"] == "PFI-012"
    assert contract["gates"] == ["Gate 6", "Gate 7"]
    for required in [
        "p0_open_count_zero",
        "all_p1_have_release_disposition",
        "release_matrix_covers_pfi001_to_pfi012_and_gate1_to_gate7",
        "uat_evidence_present",
        "privacy_audit_pass",
        "legacy_freeze_pass",
        "checksum_manifest_signed",
        "external_ci_and_rollback_evidence_recorded_fail_closed",
    ]:
        assert required in contract["required_conditions"]
    assert contract["safety_boundary"]["autonomous_order_execution"] is False
    assert contract["safety_boundary"]["private_data_in_public_git"] is False


def test_pfi012_release_manifest_signs_all_required_files(tmp_path: Path) -> None:
    project = _release_project(tmp_path)

    manifest = build_pfi012_release_checksum_manifest(project, git_head="abc123")

    assert manifest["schema"] == PFI012_RELEASE_MANIFEST_SCHEMA
    assert manifest["status"] == "Pass"
    assert manifest["missing_files"] == []
    assert manifest["signature"]["algorithm"] == "sha256-canonical-json"
    assert len(manifest["signature"]["value"]) == 64
    paths = {row["path"] for row in manifest["files"]}
    assert "docs/development/PFI012_MVP_RELEASE_GATE.md" in paths
    assert "scripts/pfi012MVPReleaseGate.sh" in paths
    assert "tests/contract/test_pfi012_mvp_release_gate.py" in paths


def test_pfi012_acceptance_closes_local_release_candidate_and_records_external_pending(tmp_path: Path) -> None:
    project = _release_project(tmp_path)
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")

    payload = run_pfi012_mvp_release_gate_acceptance(project, db_path=store.db_path, git_head="abc123")

    assert payload["schema"] == PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["local_release_candidate_status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["release_matrix"]["issue_count"] == 12
    assert payload["release_matrix"]["gate_count"] == 7
    assert payload["release_matrix"]["covers_pfi001_to_pfi012"] is True
    assert payload["release_matrix"]["covers_gate1_to_gate7"] is True
    assert payload["blocker_disposition"]["p0_open_count"] == 0
    assert payload["blocker_disposition"]["p1_without_disposition_count"] == 0
    assert payload["uat_evidence"]["status"] == "Pass"
    assert payload["privacy_audit"]["status"] == "Pass"
    assert payload["legacy_freeze"]["status"] == "Pass"
    assert payload["checksum_manifest"]["status"] == "Pass"
    assert payload["external_release_evidence"]["overall_status"] == "PendingExternal"
    assert any(row["evidence_id"] == payload["operational_record_ids"]["evidence_id"] for row in store.table_rows("evidence_records"))
    assert any(row["task_id"] == payload["operational_record_ids"]["task_id"] for row in store.table_rows("task_records"))


def test_pfi012_external_required_mode_fails_closed_without_ci_and_rollback(tmp_path: Path) -> None:
    project = _release_project(tmp_path)

    payload = run_pfi012_mvp_release_gate_acceptance(
        project,
        db_path=tmp_path / "private" / "operational" / "pfi.sqlite",
        git_head="abc123",
        require_external_release_evidence=True,
    )

    assert payload["local_release_candidate_status"] == "Fail"
    assert payload["status"] == "Review"
    assert payload["external_release_evidence"]["overall_status"] == "Fail"
    assert any(row["name"] == "ExternalCIAndRollback" and row["status"] == "Fail" for row in payload["checks"])


def test_pfi012_missing_uat_artifact_blocks_local_candidate(tmp_path: Path) -> None:
    project = _release_project(tmp_path)
    (project / "data" / "systemAudit" / "UIVisualAcceptance_latest.json").unlink()

    payload = run_pfi012_mvp_release_gate_acceptance(project, db_path=tmp_path / "private" / "operational" / "pfi.sqlite")

    assert payload["local_release_candidate_status"] == "Fail"
    assert any(row["name"] == "RequiredArtifactsPass" and row["status"] == "Fail" for row in payload["checks"])
    assert payload["uat_evidence"]["status"] == "Review"


def test_pfi012_script_gate_gitignore_and_docs_are_wired() -> None:
    script = (PROJECT_ROOT / "scripts" / "pfi012MVPReleaseGate.sh").read_text(encoding="utf-8")
    gate = (PROJECT_ROOT / "scripts" / "pfiGate.sh").read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    doc = (PROJECT_ROOT / "docs" / "development" / "PFI012_MVP_RELEASE_GATE.md").read_text(encoding="utf-8")

    assert "run_pfi012_mvp_release_gate_acceptance" in script
    assert "PFI012MVPReleaseGate_latest.json" in script
    assert "--require-external-release-evidence" in script
    assert "test_pfi012_mvp_release_gate.py" in gate
    assert "data/systemAudit/PFI012MVPReleaseGate*.json" in gitignore
    assert "PFI012MVPReleaseGateAcceptanceV1" in doc


def test_pfi012_payload_does_not_expose_secret_or_execution_surfaces(tmp_path: Path) -> None:
    payload = run_pfi012_mvp_release_gate_acceptance(_release_project(tmp_path), db_path=tmp_path / "private" / "operational" / "pfi.sqlite")
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "sk-proj-" not in serialized
    assert "api_key" not in serialized.lower()
    assert "broker_calls\": true" not in serialized
    assert "autonomous_order_execution\": true" not in serialized
    assert payload["safety_boundary"]["starts_services"] is False
    assert payload["safety_boundary"]["network_calls_required"] is False


def _release_project(tmp_path: Path) -> Path:
    project = tmp_path / "PFI_OS"
    project.mkdir()
    for relative in PFI012_RELEASE_FILES:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {relative}\nPFI OS release fixture.\n", encoding="utf-8")
    for relative in [
        ".gitignore",
        "src/pfi_os/app/streamlit_app.py",
        "data/systemAudit/.gitkeep",
    ]:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    (project / ".gitignore").write_text(
        "\n".join(
            [
                "data/private/**",
                "data/systemAudit/UIVisualAcceptance*.json",
                "data/systemAudit/PFI011LocalLLMDeepPathAcceptance*.json",
                "shared/secrets/**",
            ]
        ),
        encoding="utf-8",
    )
    for name, relative in PFI012_REQUIRED_LATEST_ARTIFACTS:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema": f"{name}FixtureV1",
                    "status": "Pass",
                    "summary": {"pass": 1, "fail": 0, "info": 0, "total": 1},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return project
