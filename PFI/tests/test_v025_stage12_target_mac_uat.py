from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_2"
HARNESS = PFI_ROOT / "scripts/v025/target_mac_uat.py"
DISPATCHER = PFI_ROOT / "scripts/v025/release_acceptance.py"


def _json(name: str) -> dict[str, object]:
    payload = json.loads((PHASE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase122_contract_is_cli_only_and_stops_before_phase123() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")
    assert 'PHASE = "12.2"' in source
    assert 'TASK_IDS = ("S12-P2-T1", "S12-P2-T2", "S12-P2-T3", "S12-P2-T4")' in source
    assert 'CANONICAL_APP = Path("/Applications/PFI.app")' in source
    assert '"-nobrowse"' in source
    assert '"/usr/bin/open"' not in source
    assert "lsregister" not in source.lower()
    assert 'actual_os_sleep_performed": False' in source
    assert '"phase_12_3_started": False' in source
    assert 'args.phase == "12.2"' in dispatcher
    assert "--canonical-app-required" in dispatcher
    assert "--no-finder-authorized" in dispatcher


def test_cli_install_replaced_the_canonical_app_with_the_bound_build() -> None:
    install = _json("app_installation.json")
    identity = _json("release_identity.json")
    assert install["status"] == "pass"
    assert install["installation_mode"] == "cli_atomic_replace"
    assert install["install_performed_in_phase"] is True
    assert install["rollback_archive_retained"] is True
    assert install["after"]["short_version"] == "0.2.5"
    assert install["after"]["project_binding_matches"] is True
    assert install["after"]["codesign_valid"] is True
    assert identity["status"] == "pass"
    assert identity["same_build"] is True
    assert identity["installed_app_matches"] is True
    assert identity["runtime_manifest_matches"] is True
    assert install["finder_used"] is False
    assert install["launchservices_used"] is False
    assert install["open_command_used"] is False


def test_target_mac_lifecycle_recovers_without_gui_file_operations() -> None:
    lifecycle = _json("target_mac_lifecycle.json")
    assert lifecycle["status"] == "pass"
    assert lifecycle["launcher_mode"] == "direct_canonical_bundle_executable"
    assert lifecycle["initial_start_healthy"] is True
    assert lifecycle["repeated_start"] == {
        "existing_service_reused": True,
        "health_preserved": True,
        "launch_count": 3,
        "single_runtime_preserved": True,
    }
    assert lifecycle["browser_close_service_healthy"] is True
    assert lifecycle["offline_recovery"]["offline_failure_observed"] is True
    assert lifecycle["offline_recovery"]["online_recovery_observed"] is True
    assert lifecycle["suspend_resume"]["status"] == "pass"
    assert lifecycle["suspend_resume"]["actual_os_sleep_performed"] is False
    assert lifecycle["suspend_resume"]["service_suspend_resume_proxy_performed"] is True
    assert lifecycle["restart_healthy"] is True
    assert lifecycle["restart_created_new_runtime"] is True
    assert lifecycle["restart_persistence_verified"] is True
    assert lifecycle["first_stop"]["unowned_process_signaled"] is False
    assert lifecycle["second_stop"]["unowned_process_signaled"] is False
    assert lifecycle["finder_used"] is False
    assert lifecycle["launchservices_used"] is False
    assert lifecycle["open_command_used"] is False
    assert lifecycle["gui_file_operations_used"] is False


def test_installed_app_human_task_protocol_uses_real_sources_and_persists() -> None:
    browser = _json("target_mac_browser.json")
    human = _json("human_task_uat.json")
    initial = browser["initial"]
    restart = browser["restart"]
    assert browser["status"] == "pass"
    assert initial["status"] == "pass"
    assert initial["primary_entry_count"] == 10
    assert initial["route_audit_count"] == 10
    uat = initial["uat"]
    assert uat["source_blob_count"] == 4
    assert uat["raw_record_count"] == 8815
    assert uat["transaction_count"] == 8808
    assert uat["ledger_count"] == 8808
    assert uat["review_count_after"] == uat["review_count_before"] - 1
    assert uat["fixture_used"] is False
    assert uat["fallback_used"] is False
    assert uat["holdings"]["truthful_not_loaded"] is True
    assert uat["holdings"]["false_zero_count"] == 0
    assert all(uat["drilldown"].values())
    assert uat["reports"] == {
        "blocked_count": 3,
        "partial_count": 2,
        "report_count": 5,
        "status": "pass",
    }
    assert restart["status"] == "pass"
    assert restart["uat"]["observed_ledger_count"] == 8808
    assert restart["uat"]["observed_review_count"] == uat["review_count_after"]
    assert human["status"] == "pass"
    assert human["manual_user_click_claimed"] is False
    assert human["final_human_acceptance_claimed"] is False
    assert human["one_review_completed"] is True
    assert human["ledger_persisted_after_restart"] is True
    assert human["holding_uat"]["financial_pass_claimed"] is False


def test_database_backup_restore_and_real_disk_pressure_are_truthful() -> None:
    database = _json("database_before_after.json")
    backup = _json("backup_restore_result.json")
    disk = _json("disk_pressure_result.json")
    assert database["status"] == "pass"
    after = database["after_restart"]
    assert after["integrity_check"] == ["ok"]
    assert after["foreign_key_issue_count"] == 0
    assert after["import_file_count"] == 4
    assert after["ledger_entry_count"] == 8808
    assert after["pending_review_count"] == 802
    assert after["resolved_review_count"] == 1
    assert database["canonical_private_database_mutated"] is False
    assert backup["status"] == "pass"
    assert backup["canonical_private_database_used"] is True
    assert backup["canonical_private_database_mutated"] is False
    assert backup["source_file_state_unchanged"] is True
    assert backup["source_directory_entries_unchanged"] is True
    assert backup["isolated_success_restore_status"] == "restored"
    assert backup["isolated_automatic_rollback_performed"] is True
    assert disk["status"] == "pass"
    assert disk["volume_kind"] == "temporary_hfs_sparse_image_nobrowse"
    assert disk["sqlite_full_observed"] is True
    assert disk["sqlite_error_code"] == 13
    assert disk["recovery_backup_integrity_check"] == ["ok"]
    assert disk["host_volume_filled"] is False
    assert disk["technical_nonfinancial_payload"] is True
    assert disk["finder_used"] is False


def test_phase122_evidence_is_candidate_only_and_private_safe() -> None:
    evidence = _json("evidence.json")
    defects = _json("defect_register.json")
    assert evidence["status"] == "candidate_pass"
    assert evidence["phase"] == "12.2"
    assert evidence["task_ids"] == ["S12-P2-T1", "S12-P2-T2", "S12-P2-T3", "S12-P2-T4"]
    assert evidence["open_p0_count"] == 0
    assert evidence["open_p1_count"] == 0
    assert evidence["canonical_app_installed"] is True
    assert evidence["app_install_performed"] is True
    assert evidence["canonical_private_database_changed"] is False
    assert evidence["finder_used"] is False
    assert evidence["launchservices_used"] is False
    assert evidence["open_command_used"] is False
    assert evidence["actual_os_sleep_performed"] is False
    assert evidence["phase_12_3_started"] is False
    assert evidence["push_performed"] is False
    assert evidence["release_freeze_performed"] is False
    assert evidence["production_accepted"] is False
    assert evidence["final_human_acceptance"] is False
    assert defects["open_p0_count"] == 0
    assert defects["open_p1_count"] == 0

    forbidden = (
        re.compile(r"/Users/"),
        re.compile(r"/private/(?:var/folders|tmp)/"),
        re.compile(r"/tmp/"),
        re.compile(r"\bCNY\s+-?[0-9]"),
        re.compile(r'(?i)"(?:pid|process_id)"\s*:\s*[1-9][0-9]*'),
    )
    for path in PHASE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(pattern.search(text) for pattern in forbidden), path.relative_to(PHASE_DIR)


def test_browser_images_and_sanitized_traces_are_hash_bound() -> None:
    browser = _json("target_mac_browser.json")
    for mode in ("initial", "restart"):
        row = browser[mode]
        screenshot = PHASE_DIR / row["screenshot"]["file"]
        trace = PHASE_DIR / row["trace"]["file"]
        assert screenshot.is_file() and screenshot.stat().st_size > 0
        assert trace.is_file() and trace.stat().st_size > 0
        assert _sha(screenshot) == row["screenshot"]["sha256"]
        assert _sha(trace) == row["trace"]["sha256"]
        assert row["trace"]["privacy_status"] == "pass"
        payload = trace.read_bytes()
        assert b"/Users/" not in payload
        assert b"/private/var/folders/" not in payload
        assert b"/tmp/" not in payload
