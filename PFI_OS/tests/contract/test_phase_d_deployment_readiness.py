from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    PHASE_D_DEPLOYMENT_READINESS_SCHEMA,
    build_phase_d_deployment_readiness,
    build_phase_d_deployment_readiness_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_phase_d_deployment_readiness_contract_declares_read_only_boundaries(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"

    contract = build_phase_d_deployment_readiness_contract(project_root, data_home)

    assert contract["schema"] == "PFIOSPhaseDDeploymentReadinessContractV1"
    assert contract["read_model_schema"] == PHASE_D_DEPLOYMENT_READINESS_SCHEMA
    assert contract["phase"] == "Phase D"
    assert {item["key"] for item in contract["required_repo_surfaces"]} == {
        "pyproject",
        "web_shell",
        "operational_store",
        "start_script",
        "status_script",
        "macos_app_template",
    }
    assert contract["backup_restore_policy"]["readiness_check_creates_directories"] is False
    assert contract["local_model_policy"]["default_provider"] == "DisabledProvider"
    assert contract["local_model_policy"]["ollama_provider_optional"] is True
    assert contract["safety_boundary"]["read_only"] is True
    assert contract["safety_boundary"]["broker_calls"] is False
    assert contract["safety_boundary"]["order_execution"] is False


def test_phase_d_deployment_readiness_passes_for_minimal_local_surfaces_without_mutating_paths(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"
    backup_dir = data_home / "runtime" / "backups"
    restore_dir = data_home / "runtime" / "restore_staging"

    payload = build_phase_d_deployment_readiness(
        project_root,
        data_home,
        now=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert payload["schema"] == PHASE_D_DEPLOYMENT_READINESS_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["operational_db_path"].endswith("/private/operational/pfi.sqlite")
    assert payload["backup_restore"]["readiness_check_created_paths"] is False
    assert payload["local_model"]["provider"] == "DisabledProvider"
    assert payload["local_model"]["required_for_core_workflows"] is False
    assert payload["phase6_preparation"]["ready_for_phase6"] is False
    assert not backup_dir.exists()
    assert not restore_dir.exists()
    assert {check["status"] for check in payload["checks"]} == {"Pass"}


def test_phase_d_deployment_readiness_blocks_missing_surfaces_and_repo_local_data_home(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    (project_root / "web" / "index.html").unlink()
    data_home = project_root / ".pfi_os"

    payload = build_phase_d_deployment_readiness(project_root, data_home)
    codes = {check["code"] for check in payload["checks"] if check["status"] == "Fail"}

    assert payload["status"] == "Blocked"
    assert "WEB_SHELL_PRESENT" in codes
    assert "DATA_HOME_OUTSIDE_REPO" in codes
    assert "OPERATIONAL_DB_OUTSIDE_REPO" in codes
    assert payload["safety_boundary"]["starts_services"] is False
    assert payload["safety_boundary"]["network_calls"] is False


def test_phase_d_local_model_provider_is_optional_and_does_not_block_core_readiness(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"

    missing_ollama = build_phase_d_deployment_readiness(
        project_root,
        data_home,
        env={"PFI_OS_LLM_PROVIDER": "OllamaProvider"},
    )
    configured_ollama = build_phase_d_deployment_readiness(
        project_root,
        data_home,
        env={"PFI_OS_LLM_PROVIDER": "OllamaProvider", "OLLAMA_BASE_URL": "http://127.0.0.1:11434"},
    )

    assert missing_ollama["status"] == "Review"
    assert configured_ollama["status"] == "Review"
    for payload in (missing_ollama, configured_ollama):
        model_check = next(check for check in payload["checks"] if check["category"] == "local_model")
        assert model_check["required"] is False
        assert model_check["status"] == "Review"
        assert payload["local_model"]["network_probe_performed"] is False
        assert payload["local_model"]["required_for_core_workflows"] is False


def test_phase_d_docs_and_handoff_reference_deployment_readiness_gate():
    phase_doc = (PROJECT_ROOT / "docs" / "phase" / "PHASE_D_DEPLOYMENT_READINESS.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    dev_record = (PROJECT_ROOT / "docs" / "development" / "PFI_PHASE_0_TO_A_RECORD.md").read_text(
        encoding="utf-8"
    )

    assert "PFIOSPhaseDDeploymentReadinessContractV1" in phase_doc
    assert "PFIOSPhaseDLocalDeploymentReadinessV1" in phase_doc
    assert "first read-only readiness slice complete" in handoff
    assert "docs/phase/PHASE_D_DEPLOYMENT_READINESS.md" in handoff
    assert "Phase D local deployment readiness" in dev_record
    assert "tests/contract/test_phase_d_deployment_readiness.py" in dev_record


def _minimal_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "PFI_OS"
    for relative_path in [
        "web/index.html",
        "src/pfi_os/application/operational_store.py",
        "scripts/startPFIOS.sh",
        "scripts/statusPFIOS.sh",
        "macos/PFI_OS.app",
    ]:
        path = root / relative_path
        if relative_path.endswith(".app"):
            path.mkdir(parents=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = \"pfi-os\"\n", encoding="utf-8")
    return root
