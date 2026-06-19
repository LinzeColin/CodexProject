import json
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    PHASE5_ACCEPTANCE_PACKAGE_SCHEMA,
    build_phase5_acceptance_package,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_phase5_acceptance_package_is_github_safe_and_phase6_ready_for_engineering_handoff():
    payload = build_phase5_acceptance_package(
        PROJECT_ROOT,
        git_head="cde21dc",
        pr_url="https://github.com/LinzeColin/CodexProject/pull/2",
        now=datetime(2026, 6, 20, 13, 0, tzinfo=timezone.utc),
    )
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    inventory_paths = {item["path"] for item in payload["file_inventory"]}

    assert payload["schema"] == PHASE5_ACCEPTANCE_PACKAGE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["package_policy"]["github_safe"] is True
    assert payload["package_policy"]["uses_relative_paths_only"] is True
    assert payload["package_policy"]["physical_zip_required_for_this_pr"] is False
    assert payload["package_policy"]["private_runtime_artifacts_committed"] is False
    assert payload["missing_required_files"] == []
    assert "docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md" in inventory_paths
    assert "src/pfi_os/application/deployment_backup_restore.py" in inventory_paths
    assert "tests/contract/test_phase5_acceptance_package.py" in inventory_paths
    assert payload["phase6_preparation"]["engineering_package_ready"] is True
    assert payload["phase6_preparation"]["deployment_data_home"] == "$PFI_OS_DATA_HOME"
    assert payload["phase6_preparation"]["default_model_provider"] == "DisabledProvider"
    assert payload["safety_boundary"]["autonomous_order_execution"] is False
    assert payload["safety_boundary"]["private_data_in_public_git"] is False
    assert "/Users/" not in serialized
    assert "private_artifacts" not in payload


def test_phase5_acceptance_package_blocks_missing_required_manifest_file(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    (project_root / "README.md").write_text("ok", encoding="utf-8")

    payload = build_phase5_acceptance_package(project_root)

    assert payload["status"] == "Blocked"
    assert "AGENTS.md" in payload["missing_required_files"]
    assert "docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md" in payload["missing_required_files"]
    assert payload["phase6_preparation"]["engineering_package_ready"] is False
    assert payload["safety_boundary"]["network_calls"] is False
    assert payload["safety_boundary"]["starts_services"] is False


def test_phase5_package_keeps_user_supplied_phase6_materials_external():
    payload = build_phase5_acceptance_package(PROJECT_ROOT)
    materials = {item["item"]: item for item in payload["phase6_preparation"]["user_supplied_materials"]}

    assert materials["local_repository_backup"]["status"] == "user_supplied_or_external"
    assert materials["hardware_and_disk_audit"]["status"] == "user_supplied_or_external"
    assert materials["sanitized_test_holdings"]["status"] == "user_supplied_or_external"
    assert materials["user_subjective_acceptance_score"]["status"] == "pending_user_acceptance"
    assert payload["phase6_preparation"]["controlled_local_deployment_acceptance"] == (
        "deferred_until_release_gate_requires_service_start"
    )


def test_phase5_docs_handoff_and_development_record_reference_package():
    phase_doc = (PROJECT_ROOT / "docs" / "phase" / "PHASE_5_ACCEPTANCE_PACKAGE.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    plan = (PROJECT_ROOT / "PLANS.md").read_text(encoding="utf-8")
    dev_record = (PROJECT_ROOT / "docs" / "development" / "PFI_PHASE_0_TO_A_RECORD.md").read_text(
        encoding="utf-8"
    )

    assert "PFIOSPhase5AcceptancePackageV1" in phase_doc
    assert "Phase 5 acceptance package complete" in handoff
    assert "Phase 5 packaging" in plan
    assert "tests/contract/test_phase5_acceptance_package.py" in dev_record
