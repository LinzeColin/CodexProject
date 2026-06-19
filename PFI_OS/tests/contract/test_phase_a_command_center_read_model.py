import json
from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    build_command_center_read_model,
    empty_command_center_read_model,
    ingest_command_center_cache,
)


def test_command_center_read_model_uses_operational_store_sanitized_payload(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_dir = project_root / "data" / "commandCenter"
    cache_dir.mkdir(parents=True)
    cache_path = cache_dir / "PFICommandCenter_latest.json"
    cache_path.write_text(json.dumps(_payload(tmp_path), ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    ingest_command_center_cache(store, project_root=project_root)
    model = build_command_center_read_model(store)
    metadata_blob = "\n".join(row["metadata_json"] for row in store.table_rows("evidence_records"))

    assert model["schema"] == "PFIOSCommandCenterReadModelV1"
    assert model["command_status"] == "NeedsReview"
    assert model["action_queue"][0]["action"] == "Review provider readiness."
    assert model["evidence_sources"][0]["path"] == "[redacted-private-uri]"
    assert model["latest_report"]["path"] == "[redacted-private-uri]"
    assert model["source_uri"] == "data/commandCenter/PFICommandCenter_latest.json"
    assert model["evidence_id"]
    assert "OperationalStore -> command_center_summary" in model["read_model"]
    assert str(tmp_path) not in metadata_blob


def test_empty_command_center_read_model_is_fail_closed():
    model = empty_command_center_read_model()

    assert model["schema"] == "PFIOSCommandCenterReadModelV1"
    assert model["command_status"] == "NeedsReview"
    assert model["action_queue"] == []
    assert "No operational command-center evidence" in model["status_reason"]


def test_command_center_read_model_returns_empty_when_no_evidence_exists(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    model = build_command_center_read_model(store)

    assert model["command_status"] == "NeedsReview"
    assert model["evidence_id"] == ""
    assert model["source_id"] == ""


def _payload(tmp_path: Path) -> dict:
    return {
        "schema": "PFICommandCenterV1",
        "system": "PFI_OS",
        "display_name": "PFI_OS",
        "subsystem": "Executive Command Center",
        "as_of": "2026-06-19",
        "generated_at": "2026-06-19T09:30:00+00:00",
        "project_root": str(tmp_path / "PFI_OS"),
        "report_root": str(tmp_path / "reports"),
        "command_status": "NeedsReview",
        "status_reason": "Provider readiness needs review.",
        "scorecards": [{"metric": "Daily Readiness", "value": "NeedsReview", "status": "Review", "evidence": "fixture"}],
        "risk_gates": [{"gate": "DataTrust", "status": "Pass", "evidence": "fixture", "next_action": "Keep clean."}],
        "action_queue": [
            {
                "priority": "P0",
                "status": "Open",
                "owner": "PFI",
                "action": "Review provider readiness.",
                "source": "Daily Readiness",
            }
        ],
        "latest_report": {
            "name": "Backtest.docx",
            "artifact_type": "Backtest Word Report",
            "path": str(tmp_path / "reports" / "Backtest.docx"),
        },
        "evidence_sources": [
            {
                "source": "Daily Readiness",
                "status": "Present",
                "path": str(tmp_path / "data" / "systemAudit" / "Daily.json"),
                "schema": "PFIOSDailyReadinessV1",
            }
        ],
        "runtime_summary_sources": [],
        "business_system_summary": [],
    }
