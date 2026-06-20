import json
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import OperationalStore, build_homepage_summary, ingest_command_center_cache


def test_ingest_command_center_cache_writes_homepage_operational_records(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_dir = project_root / "data" / "commandCenter"
    cache_dir.mkdir(parents=True)
    cache_path = cache_dir / "PFICommandCenter_latest.json"
    cache_path.write_text(json.dumps(_command_center_payload(), ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_command_center_cache(store, project_root=project_root)
    summary = build_homepage_summary(store, now=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc))
    source = store.table_rows("source_records")[0]
    evidence = store.table_rows("evidence_records")[0]
    task = store.table_rows("task_records")[0]

    assert result["schema"] == "PFIOSHomepageCacheIngestionV1"
    assert result["status"] == "Ingested"
    assert source["source_type"] == "command_center_cache"
    assert source["uri"] == "data/commandCenter/PFICommandCenter_latest.json"
    assert source["domain"] == "PUBLIC_SHARED_CANONICAL"
    assert evidence["evidence_class"] == "command_center_summary"
    assert "NeedsReview" in evidence["summary"]
    assert task["owner_workspace"] == "home"
    assert task["human_review_required"] == 1
    assert summary["schema"] == "PFIOSHomeSummaryV1"
    assert summary["metric_cards"][0]["value"] == "1"
    assert summary["decision_rows"][0]["action"] == "Review provider readiness."
    assert summary["evidence_drawer"]["Raw document"] == "data/commandCenter/PFICommandCenter_latest.json"


def test_ingest_command_center_cache_skips_when_no_cache_exists(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_command_center_cache(store, project_root=project_root)

    assert result["status"] == "Skipped"
    assert store.table_rows("source_records") == []
    assert store.table_rows("evidence_records") == []


def test_ingest_command_center_cache_ignores_retired_eva_latest_cache_by_default(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_dir = project_root / "data" / "commandCenter"
    cache_dir.mkdir(parents=True)
    retired_prefix = "E" + "VA"
    (cache_dir / f"{retired_prefix}CommandCenter_latest.json").write_text(
        json.dumps(_retired_eva_command_center_payload(), ensure_ascii=False),
        encoding="utf-8",
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_command_center_cache(store, project_root=project_root)

    assert result["status"] == "Skipped"
    assert store.table_rows("source_records") == []
    assert store.table_rows("evidence_records") == []


def test_ingest_command_center_cache_does_not_store_private_absolute_paths_in_metadata(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_dir = project_root / "data" / "commandCenter"
    cache_dir.mkdir(parents=True)
    payload = _command_center_payload()
    payload["project_root"] = str(project_root)
    payload["report_root"] = str(tmp_path / "private_reports")
    cache_path = cache_dir / "PFICommandCenter_latest.json"
    cache_path.write_text(json.dumps(payload), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    ingest_command_center_cache(store, project_root=project_root)
    combined_metadata = "\n".join(row["metadata_json"] for row in [*store.table_rows("source_records"), *store.table_rows("evidence_records"), *store.table_rows("job_records")])

    assert str(project_root) not in combined_metadata
    assert "private_reports" not in combined_metadata
    assert "data/commandCenter/PFICommandCenter_latest.json" in combined_metadata


def test_homepage_summary_hides_retired_legacy_command_center_content(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_dir = project_root / "data" / "commandCenter"
    cache_dir.mkdir(parents=True)
    payload = _command_center_payload()
    retired_value_label = "Token" + " ROI"
    retired_artifact_prefix = "E" + "VA" + "Token"
    payload["scorecards"].append({"metric": f"{retired_value_label} Ledger", "value": "178", "status": "Pass"})
    payload["action_queue"].append(
        {
            "priority": "P2",
            "status": "Open",
            "owner": "PFI",
            "action": f"补齐 {retired_value_label} 台账。",
            "source": f"{retired_value_label} Ledger",
        }
    )
    payload["evidence_sources"] = [
        {"source": f"{retired_value_label} Ledger", "artifact_uri": f"data/value/{retired_artifact_prefix}ROILedger_latest.json"},
        {"source": "PFI Runtime", "artifact_uri": "data/runtime/PFIRuntime_latest.json"},
    ]
    cache_path = cache_dir / "PFICommandCenter_latest.json"
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    ingest_command_center_cache(store, project_root=project_root)
    summary = build_homepage_summary(store, now=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc))
    serialized = json.dumps(summary, ensure_ascii=False)

    assert summary["decision_rows"][0]["action"] == "Review provider readiness."
    assert retired_value_label not in serialized
    assert "E" + "VA" + "CommandCenter" not in serialized
    assert retired_artifact_prefix not in serialized


def _command_center_payload() -> dict:
    return {
        "schema": "PFICommandCenterV1",
        "system": "PFI_OS",
        "display_name": "PFI_OS",
        "subsystem": "Executive Command Center",
        "as_of": "2026-06-19",
        "generated_at": "2026-06-19T09:30:00+00:00",
        "project_root": "/private/example",
        "report_root": "/private/reports",
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
    }


def _retired_eva_command_center_payload() -> dict:
    payload = _command_center_payload()
    retired_prefix = "E" + "VA"
    payload["schema"] = retired_prefix + "CommandCenterV1"
    payload["system"] = retired_prefix + "_OS"
    payload["display_name"] = retired_prefix + " OS"
    payload["latest_report"] = {"name": retired_prefix + "CommandCenter_latest.json"}
    payload["scorecards"].append({"metric": "Token" + " ROI Ledger", "value": "178", "status": "Pass"})
    return payload
