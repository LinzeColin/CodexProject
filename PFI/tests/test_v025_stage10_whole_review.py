from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

from jsonschema import Draft202012Validator

from pfi_v02.stage_v021_runtime_api import build_v025_release_asset_identity


PFI_ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_10/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REMEDIATION_COMMIT = "92579cfdd01e298d0121733375a2be8f1dbc5035"


def _json(name: str) -> dict[str, object]:
    payload = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _taskpack_schema(suffix: str) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        assert len(names) == 1
        payload = json.loads(archive.read(names[0]))
    assert isinstance(payload, dict)
    return payload


def test_contract_and_initial_review_preserve_the_stage_boundary() -> None:
    contract = _json("phase_contract.json")
    findings = _json("initial_review_findings.json")
    authorization = _json("transition_authorization_binding.json")

    assert contract["acceptance_id"] == "ACC-PFI-V025-STAGE10-WHOLE-REVIEW"
    assert contract["remediation_commit"] == "92579cfdd"
    assert contract["task_progress"] == {
        "completed": 12,
        "total": 12,
        "project_progress": "132/156 (84.62%)",
    }
    assert contract["stage_11_started"] is False
    assert contract["push_performed"] is contract["app_install_performed"] is False
    assert findings["initial_totals"] == {"critical": 1, "important": 7, "minor": 0}
    assert findings["status"] == "remediated_pending_final_rereview"
    assert len(findings["reviewers"]) == 3
    assert authorization["status"] == "accepted_via_standing_transition_authorization"
    assert authorization["stage_11_implementation_started"] is False
    assert authorization["finder_used"] is False


def test_phase_commit_chains_artifacts_and_normalized_evidence_are_exact() -> None:
    binding = _json("phase_commit_binding.json")
    assert binding["status"] == "pass"
    assert binding["remediation_commit"] == "92579cfdd"
    assert len(binding["phases"]) == 3
    assert all(row["commit_chain_match"] for row in binding["phases"])
    assert all(row["artifact_validation"]["all_match"] for row in binding["phases"])
    assert all(
        row["artifact_validation"]["declared_file_count"]
        == row["artifact_validation"]["verified_file_count"]
        for row in binding["phases"]
    )
    schema_rows = {row["phase"]: row for row in binding["evidence_schema_validation"]}
    assert schema_rows["10.1"]["source_schema_status"] == "pass"
    assert schema_rows["10.2"]["source_schema_status"] == "pass"
    assert schema_rows["10.3"]["source_schema_status"] == "fail"
    assert schema_rows["10.3"]["normalized_fields"] == ["changed_files"]
    assert all(row["normalized_schema_status"] == "pass" for row in schema_rows.values())

    validator = Draft202012Validator(_taskpack_schema("schemas/evidence_pack.schema.json"))
    for phase in ("10_1", "10_2", "10_3"):
        payload = _json(f"phase_evidence/phase_{phase}.json")
        assert list(validator.iter_errors(payload)) == []
        assert payload["changed_files"]
        assert payload["whole_review_normalization"]["source_immutable"] is True


def test_migration_before_backup_after_and_integrity_are_fail_closed() -> None:
    migration = _json("migration_before_after.json")
    database = _json("database_integrity.json")

    assert migration["status"] == "pass"
    assert migration["lifecycle_rows_unchanged"] is True
    assert migration["observability_backfill_consistent"] is True
    assert migration["backup"]["count"] == 1
    assert migration["backup"]["matches_before"] is True
    assert migration["database_file_mode"] == "0600"
    assert migration["backup_directory_mode"] == "0700"
    assert migration["canonical_private_database_used"] is False
    assert database["status"] == "pass"
    assert database["counts"]["durable_jobs"] == 4
    assert database["counts"]["durable_job_trace_contexts"] == 4
    assert database["counts"]["durable_job_events"] == database["counts"]["durable_job_spans"]
    assert database["counts"]["durable_job_events"] == database["counts"]["durable_job_logs"]


def test_browser_proves_healthy_heartbeat_exact_states_failure_and_accessibility() -> None:
    browser = _json("browser_validation.json")
    transitions = _json("job_state_transitions.json")
    failure = _json("failure_matrix.json")
    uat = _json("structured_uat.json")

    assert browser["status"] == "pass"
    assert len(browser["checks"]) == 22
    assert all(browser["checks"].values())
    assert browser["database_projection"]["attempt_count"] == 1
    assert browser["database_projection"]["retry_count"] == 0
    assert browser["leave_page_elapsed_ms"] >= 10_000
    assert browser["failure_database_projection"]["status"] == "failed"
    assert browser["failure_browser_projection"]["state"] == "failed"
    assert browser["failure_browser_projection"]["resultText"] == ""
    assert browser["fixture_projection"]["retrying"]["backendState"] == "retrying"
    assert browser["fixture_projection"]["dead_letter"]["backendState"] == "dead_letter"
    assert transitions["status"] == failure["status"] == "pass"
    assert transitions["healthy_long_task"]["attempt_count"] == 1
    assert transitions["healthy_long_task"]["heartbeat_count"] >= 2
    assert uat["overall_result"] == "pass_for_stage_transition_only"
    assert len(uat["checks"]) == 8
    assert (REVIEW_DIR / "job_recovery_redacted.png").is_file()
    assert (REVIEW_DIR / "job_failure_redacted.png").is_file()
    assert _json("dom_snapshot.json")["bodyJobStatus"] == "failed"
    assert _json("accessibility_tree.json")["nodes"]


def test_runtime_diff_network_trace_and_crash_evidence_remain_bound() -> None:
    runtime_diff = _json("runtime_diff.json")
    impacted = _json("impacted_metrics.json")
    network = _json("network_audit.json")
    crash = _json("crash_recovery.json")
    trace = _json("trace_export.json")

    no_diff = runtime_diff["no_diff_result"]
    assert no_diff["no_diff"] is True
    assert no_diff["recompute_scope"] == "none"
    assert no_diff["network_calls"] == no_diff["codex_calls"] == no_diff["llm_calls"] == 0
    assert len(no_diff["unchanged_domains"]) == 9
    assert impacted["all_nine_domains_exercised"] is True
    assert len(impacted["change_matrix"]) == 9
    assert all(row["network_calls"] == row["codex_calls"] == row["llm_calls"] == 0 for row in impacted["change_matrix"])
    assert network["status"] == "pass"
    assert network["ordinary_external_network_calls"] == 0
    assert network["codex_calls"] == network["llm_calls"] == 0
    assert crash["status"] == trace["status"] == "pass"


def test_release_identity_and_core_evidence_have_no_private_identity() -> None:
    identity = build_v025_release_asset_identity(PFI_ROOT)
    assert identity["valid"] is True
    assert identity["frontend_valid"] is True
    assert identity["disk_backend_valid"] is True
    assert identity["running_backend_valid"] is True

    forbidden_text = ("BEGIN PRIVATE KEY", "AKIA", "Bearer ")
    private_path = re.compile(r"/Users/[A-Za-z0-9._-]+/")
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".json", ".md", ".txt", ".log", ".html", ".csv"}:
            text = path.read_text(encoding="utf-8")
            assert not private_path.search(text), path
            assert all(marker not in text for marker in forbidden_text), path
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    value = archive.read(name)
                    assert not re.search(rb"/Users/[A-Za-z0-9._-]+/", value), f"{path}:{name}"
                    assert all(marker.encode() not in value for marker in forbidden_text), f"{path}:{name}"
