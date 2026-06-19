import json
from pathlib import Path

from pfi_os.app.dashboard import macos_runtime_evidence_summary
from pfi_os.application import (
    OperationalStore,
    build_macos_runtime_acceptance_read_model,
    empty_macos_runtime_acceptance_read_model,
    ingest_macos_runtime_acceptance_cache,
)


def test_macos_runtime_read_model_ingests_latest_cache_without_private_paths(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_path = project_root / "data" / "systemAudit" / "MacOSRuntimeAcceptance_latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps(_payload(tmp_path), ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_macos_runtime_acceptance_cache(store, project_root=project_root)
    model = build_macos_runtime_acceptance_read_model(store)
    source = store.table_rows("source_records")[0]
    evidence = store.table_rows("evidence_records")[0]
    metadata_blob = "\n".join(
        row["metadata_json"]
        for row in [*store.table_rows("source_records"), *store.table_rows("evidence_records"), *store.table_rows("job_records")]
    )

    assert result["schema"] == "PFIOSMacOSRuntimeCacheIngestionV1"
    assert result["status"] == "Ingested"
    assert source["source_type"] == "macos_runtime_acceptance_cache"
    assert source["domain"] == "PRIVATE_DERIVED"
    assert source["uri"] == "data/systemAudit/MacOSRuntimeAcceptance_latest.json"
    assert evidence["evidence_class"] == "macos_runtime_acceptance_summary"
    assert model["schema"] == "PFIOSMacOSRuntimeAcceptanceV1"
    assert model["status"] == "Pass"
    assert model["summary"]["pass"] == 10
    assert model["checks"][0]["evidence"] == "[redacted-runtime-evidence]"
    assert model["source_uri"] == "data/systemAudit/MacOSRuntimeAcceptance_latest.json"
    assert model["evidence_id"]
    assert "OperationalStore -> macos_runtime_acceptance_summary" in model["read_model"]
    assert str(tmp_path) not in metadata_blob
    assert "/Users/" not in metadata_blob
    assert store.table_rows("task_records") == []


def test_macos_runtime_read_model_creates_review_task_for_blocked_status(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_path = project_root / "data" / "systemAudit" / "MacOSRuntimeAcceptance_latest.json"
    cache_path.parent.mkdir(parents=True)
    payload = _payload(tmp_path)
    payload["status"] = "Blocked"
    payload["summary"] = {"pass": 9, "fail": 1, "info": 0, "total": 10}
    payload["checks"].append({"target": "Runtime", "check": "NoPreExistingService", "status": "Fail", "evidence": "healthy_ports=[8501]"})
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_macos_runtime_acceptance_cache(store, project_root=project_root)
    task = store.table_rows("task_records")[0]
    model = build_macos_runtime_acceptance_read_model(store)

    assert result["status"] == "Ingested"
    assert result["task_id"] == task["task_id"]
    assert task["owner_workspace"] == "local_runtime"
    assert task["human_review_required"] == 1
    assert "Blocked" in task["action"]
    assert model["status"] == "Blocked"


def test_macos_runtime_read_model_skips_missing_or_wrong_schema_cache(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    missing = ingest_macos_runtime_acceptance_cache(store, project_root=project_root)
    cache_path = project_root / "data" / "systemAudit" / "MacOSRuntimeAcceptance_latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps({"schema": "Wrong"}), encoding="utf-8")
    wrong_schema = ingest_macos_runtime_acceptance_cache(store, project_root=project_root)
    model = build_macos_runtime_acceptance_read_model(store)

    assert missing["status"] == "Skipped"
    assert wrong_schema["status"] == "Skipped"
    assert model["status"] == "Missing"
    assert store.table_rows("source_records") == []
    assert store.table_rows("evidence_records") == []


def test_empty_macos_runtime_read_model_is_compatible_with_shell_summary():
    model = empty_macos_runtime_acceptance_read_model()
    summary = macos_runtime_evidence_summary(model)

    assert model["schema"] == "PFIOSMacOSRuntimeAcceptanceV1"
    assert summary["schema"] == "MacOSRuntimeEvidenceSummaryV1"
    assert summary["status"] == "Missing"
    assert summary["rows"] == []
    assert "Terminal-only" in summary["safety_policy"]


def _payload(tmp_path: Path) -> dict:
    return {
        "schema": "PFIOSMacOSRuntimeAcceptanceV1",
        "system": "PFI_OS",
        "subsystem": "macOS Runtime Acceptance",
        "generated_at": "2026-06-19T09:30:00",
        "status": "Pass",
        "project_root": str(tmp_path / "PFI_OS"),
        "summary": {"pass": 10, "fail": 0, "info": 0, "total": 10},
        "pre_existing_healthy_ports": [],
        "post_healthy_ports": [],
        "started_by_acceptance": True,
        "launch_method": "app",
        "app_acceptance": {"schema": "PFIOSMacOSAppAcceptanceLiteV1", "status": "Pass", "pid": 1234},
        "checks": [
            {
                "target": "Start",
                "check": "AppOpenLaunched",
                "status": "Pass",
                "evidence": f"opened={tmp_path / 'Downloads' / 'PFI_OS.app'}; pid=1234",
            }
        ],
        "runtime_contract": {"start": "Launches the local app in controlled mode."},
        "heavy_smoke_policy": "Does not run finalAcceptanceCheck.sh, ciSmoke.sh, full pytest, browser automation, orders, or holdings writes.",
        "safety_boundary": "Controlled local start/health/stop/cache-guard acceptance.",
        "next_action": "Optional visual UI verification.",
        "outputs": {"latest_json": str(tmp_path / "PFI_OS" / "data" / "systemAudit" / "MacOSRuntimeAcceptance_latest.json")},
    }
