from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

from pfi_os.application.use_cases.import_review_ledger import (
    UploadedImportFile,
    _detect_source,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from immutable_real_sources import load_locked_source_objects  # noqa: E402

PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_1"
SCRIPT = PFI_ROOT / "scripts/v025/release_acceptance.py"


def _json(relative: str) -> dict[str, object]:
    payload = json.loads((PHASE_DIR / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase121_contract_stops_before_target_mac_and_release_freeze() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'PHASE = "12.1"' in source
    assert 'TASK_IDS = ("S12-P1-T1", "S12-P1-T2", "S12-P1-T3", "S12-P1-T4")' in source
    assert "Phase 12.2" in source
    assert "finder-app-required" in source
    assert "production_accepted" in source


def test_real_gb18030_sources_are_detected_across_fixed_probe_boundaries() -> None:
    objects, attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    assert attestation["status"] == "pass"
    assert attestation["source_commit"] != "HEAD"
    assert attestation["source_blob_count"] == 4
    for row in objects:
        index = int(row["source_index"])
        content = row["content"]
        assert isinstance(content, bytes)
        source_id, parser_version, error = _detect_source(
            UploadedImportFile(
                name=f"real_source_{index}.csv",
                content=content,
                media_type="text/csv",
            )
        )
        assert (source_id, parser_version, error) == (
            "alipay_daily",
            "alipay_bill_csv_v1",
            None,
        )


def test_release_identity_is_synchronized_after_regression_fix() -> None:
    identity = _json("release_identity.json")
    assert identity["status"] == "pass"
    assert identity["version"] == "v0.2.5"
    assert identity["frontend_valid"] is True
    assert identity["disk_backend_valid"] is True
    assert identity["running_backend_valid"] is True
    assert identity["frontend_bundle_hash"] == identity["manifest_frontend_bundle_hash"]
    assert identity["backend_build_hash"] == identity["manifest_backend_build_hash"]
    assert identity["app_install_performed"] is False


def test_real_import_holding_and_report_flow_is_truthful_and_non_fixture() -> None:
    e2e = _json("real_data_e2e.json")
    assert e2e["status"] == "pass"
    source = e2e["source"]
    assert source["source_kind"] == "real_alipay_csv_git_objects"
    assert source["source_blob_count"] == 4
    assert source["source_unchanged"] is True
    assert source["fixture_used"] is False
    assert source["fallback_used"] is False

    imported = e2e["import"]
    assert imported["execution_status"] == "completed"
    assert imported["raw_record_count"] == 8815
    assert imported["transaction_count"] == 8808
    assert imported["confirmed_ledger_count"] == 8808
    assert imported["review_count"] == 803
    assert imported["replay_idempotent"] is True

    holding = e2e["holding"]
    assert holding["execution_status"] == "not_run"
    assert holding["truth_gate_status"] == "pass"
    assert holding["reason_code"] == "SRC_HOLDINGS_NOT_LOADED"
    assert holding["financial_pass_claimed"] is False
    assert holding["active_holding_count"] == 0

    report = e2e["report"]
    assert report["execution_status"] == "completed"
    assert report["analysis_validation_status"] == "pass"
    assert report["report_card_count"] == 5
    assert report["blocked_report_count"] == 3
    assert report["partial_report_count"] == 2
    assert report["financial_values_emitted"] == 0


def test_isolated_database_has_exact_import_counts_and_no_canonical_write() -> None:
    database = _json("database_before_after.json")
    assert database["status"] == "pass"
    assert database["before"] == {"database_exists": False, "ledger_entry_count": 0}
    after = database["after"]
    assert after["integrity_check"] == "ok"
    assert after["foreign_key_issue_count"] == 0
    assert after["import_batch_count"] == 1
    assert after["import_file_count"] == 4
    assert after["staged_transaction_count"] == 8808
    assert after["ledger_entry_count"] == 8808
    assert after["review_item_count"] == 803
    assert after["active_holding_count"] == 0
    assert database["canonical_database_read"] is False
    assert database["canonical_database_changed"] is False


def test_route_old_ui_false_zero_and_template_clone_regressions_pass() -> None:
    e2e = _json("real_data_e2e.json")
    routes = e2e["route_regression"]
    assert routes["primary_route_count"] == 10
    assert routes["canonical_primary_route_count"] == 10
    assert routes["legacy_primary_route_count"] == 0
    assert routes["secondary_route_count"] == 10
    assert all(row["active_primary_count"] == 1 for row in routes["primary_routes"])
    assert e2e["no_false_zero"] == {
        "holding_false_zero_count": 0,
        "report_financial_amount_visible": False,
        "status": "pass",
    }
    clone = e2e["no_template_clone"]
    assert clone["status"] == "pass"
    assert clone["representative_route_count"] == 10
    assert clone["distinct_structural_signature_count"] == 10
    assert clone["distinct_data_object_count"] == 10


def test_accessibility_performance_and_visual_quality_meet_current_thresholds() -> None:
    browser = _json("browser_validation.json")
    quality = _json("quality_evidence.json")
    wcag = _json("quality_browser/wcag_audit.json")
    visual = _json("quality_browser/visual_regression.json")
    ax_tree = _json("quality_browser/accessibility_tree.json")
    keyboard = _json("quality_browser/keyboard_flow.json")

    assert browser["status"] == "pass"
    assert browser["passed_check_count"] == browser["check_count"]
    assert browser["performance"]["maximum_route_navigation_ms"] <= 3000
    assert browser["accessibility"]["found_primary_navigation_count"] == 10
    assert quality["status"] == "pass"
    assert quality["axe_core_available"] is False
    assert quality["axe_pass_claimed"] is False
    assert quality["deterministic_wcag_substitute_status"] == "pass"
    assert wcag["status"] == "pass"
    assert wcag["standard"] == "WCAG 2.2 AA"
    assert wcag["blocking_violation_count"] == 0
    assert visual["status"] == "pass"
    assert visual["screenshot_count"] == 40
    assert visual["regression_failure_count"] == 0
    assert ax_tree["status"] == "pass"
    assert keyboard["status"] == "pass"


def test_report_pack_rebuild_and_current_real_source_statuses_pass() -> None:
    report = _json("report_regression.json")
    assert report["status"] == "pass"
    assert report["manifest_validation_status"] == "pass"
    assert report["registered_source_count"] == 7
    assert report["ready_source_count"] == 1
    assert report["partial_source_count"] == 1
    assert report["not_loaded_source_count"] == 5
    assert report["transaction_record_count"] == 8815
    assert report["report_statuses"] == {
        "cash": "blocked",
        "cashflow": "partial",
        "consumption": "partial",
        "data_quality": "complete",
        "investment": "blocked",
        "net_worth": "blocked",
    }
    assert report["financial_values_emitted"] == 0


def test_screenshots_and_sanitized_traces_are_bound_and_private_free() -> None:
    browser = _json("browser_validation.json")
    for row in browser["screenshots"]:
        path = PHASE_DIR / row["file"]
        assert path.is_file() and path.stat().st_size > 0
        assert _sha(path) == "sha256:" + row["sha256"]
    for relative in (
        "browser_trace_sanitized.zip",
        "quality_browser/browser_trace.zip",
    ):
        payload = (PHASE_DIR / relative).read_bytes()
        assert payload
        assert b"/Users/" not in payload
        assert b"/private/var/folders/" not in payload
        assert b"/tmp/" not in payload


def test_phase121_has_no_finder_install_push_or_acceptance_overclaim() -> None:
    e2e = _json("real_data_e2e.json")
    identity = _json("release_identity.json")
    for payload in (e2e, identity):
        assert payload["finder_used"] is False
    assert e2e["launchservices_used"] is False
    assert e2e["gui_file_operations_used"] is False
    assert identity["app_install_performed"] is False
    assert identity["push_performed"] is False
    assert identity["production_accepted"] is False
    assert identity["final_human_acceptance"] is False


def test_public_json_and_text_evidence_contains_no_private_paths_or_financial_values() -> None:
    forbidden = (
        re.compile(r"/Users/"),
        re.compile(r"/private/var/folders/"),
        re.compile(r"/tmp/"),
        re.compile(r"\bCNY\s+-?[0-9]"),
        re.compile(r"(?i)(?:account|card)[_-]?(?:number|identifier)"),
    )
    for path in PHASE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(pattern.search(text) for pattern in forbidden), path.relative_to(PHASE_DIR)
