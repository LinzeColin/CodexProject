from __future__ import annotations

import json
from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    PFI010_FAST_PATH_JOB_TYPE,
    PFI010_MINUTE_FAST_PATH_ACCEPTANCE_SCHEMA,
    PFI010_MINUTE_FAST_PATH_CONTRACT_SCHEMA,
    PFI010_MINUTE_FAST_PATH_READ_MODEL_SCHEMA,
    build_homepage_summary,
    build_pfi010_minute_fast_path_contract,
    build_pfi010_source_specs,
    build_workflow_runtime_read_model,
    run_pfi010_minute_fast_path_acceptance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_pfi010_contract_declares_gate4_minute_fast_path_boundaries() -> None:
    contract = build_pfi010_minute_fast_path_contract()

    assert contract["schema"] == PFI010_MINUTE_FAST_PATH_CONTRACT_SCHEMA
    assert contract["issue"] == "PFI-010"
    assert contract["gate"] == "Gate 4"
    assert contract["target_seconds"] == 60
    assert contract["required_source_count"] == 3
    assert contract["worker"]["job_type"] == PFI010_FAST_PATH_JOB_TYPE
    assert contract["worker"]["incremental_cursor_required"] is True
    assert contract["worker"]["page_closed_updates_required"] is True
    assert contract["worker"]["new_tables"] is False
    assert contract["external_dependencies"] == {
        "network_required": False,
        "broker_required": False,
        "llm_required": False,
        "provider_fetch_required": False,
    }
    assert contract["safety_boundary"]["no_order_execution"] is True


def test_pfi010_source_specs_are_three_legal_incremental_sources() -> None:
    specs = build_pfi010_source_specs()

    assert len(specs) == 3
    assert {row["workspace"] for row in specs} >= {"market", "research"}
    assert all(row["legal_basis"] for row in specs)
    assert all("no broker" in row["source_policy"].lower() for row in specs)
    assert all(row["incremental_cursor_after"] > row["incremental_cursor_before"] for row in specs)
    assert all(max(row["latency_samples_seconds"]) <= 60 for row in specs)


def test_pfi010_acceptance_proves_latency_failure_injection_page_closed_and_soak(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    payload = run_pfi010_minute_fast_path_acceptance(db_path=db_path)

    assert payload["schema"] == PFI010_MINUTE_FAST_PATH_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["latency_metrics"]["source_count"] == 3
    assert payload["latency_metrics"]["sample_count"] >= 15
    assert payload["latency_metrics"]["p95_seconds"] <= 60
    assert payload["page_closed_update_proof"]["status"] == "Pass"
    assert payload["page_closed_update_proof"]["ui_session_active"] is False
    assert payload["page_closed_update_proof"]["page_closed_updates"] is True
    assert payload["failure_injection"]["status"] == "Pass"
    assert payload["failure_injection"]["recovered_source_count"] == 1
    assert payload["soak_summary"]["one_hour"]["duration_minutes"] == 60
    assert payload["soak_summary"]["one_hour"]["status"] == "Pass"
    assert payload["soak_summary"]["twenty_four_hour"]["duration_minutes"] == 1440
    assert payload["soak_summary"]["twenty_four_hour"]["status"] == "Pass"
    assert payload["read_model"]["schema"] == PFI010_MINUTE_FAST_PATH_READ_MODEL_SCHEMA
    assert payload["read_model"]["ui_push"]["runtime_field"] == "workflow_runtime.minute_fast_path"
    assert payload["read_model"]["page_closed_updates"] is True


def test_pfi010_acceptance_records_operational_evidence_and_runtime_dashboard(tmp_path: Path) -> None:
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    payload = run_pfi010_minute_fast_path_acceptance(db_path=store.db_path)

    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")
    jobs = store.table_rows("job_records")
    tasks = store.table_rows("task_records")
    runtime = build_workflow_runtime_read_model(store)
    homepage = build_homepage_summary(store)

    assert any(row["source_id"] == payload["operational_record_ids"]["source_id"] for row in sources)
    assert any(row["evidence_id"] == payload["operational_record_ids"]["evidence_id"] for row in evidence)
    assert any(row["task_id"] == payload["operational_record_ids"]["task_id"] for row in tasks)
    assert sum(1 for row in jobs if row["job_type"] == PFI010_FAST_PATH_JOB_TYPE and row["status"] == "completed") == 3
    assert runtime["minute_fast_path"]["status"] == "Pass"
    assert runtime["minute_fast_path"]["source_count"] == 3
    assert runtime["minute_fast_path"]["p95_seconds"] <= 60
    assert runtime["minute_fast_path"]["web_shell_visible"] is True
    assert homepage["workflow_runtime"]["minute_fast_path"]["page_closed_updates"] is True


def test_pfi010_script_gate_and_web_shell_static_contracts_are_wired() -> None:
    script = (PROJECT_ROOT / "scripts" / "pfi010MinuteFastPathAcceptance.sh").read_text(encoding="utf-8")
    gate = (PROJECT_ROOT / "scripts" / "pfiGate.sh").read_text(encoding="utf-8")
    shell = (PROJECT_ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "run_pfi010_minute_fast_path_acceptance" in script
    assert "PFI010MinuteFastPathAcceptance_latest.json" in script
    assert "test_pfi010_minute_fast_path.py" in gate
    assert "minuteFastPathLabel(runtime.minute_fast_path)" in shell
    assert "离页仍更新" in shell
    assert "data/systemAudit/PFI010MinuteFastPathAcceptance*.json" in gitignore


def test_pfi010_payload_does_not_expose_execution_or_secret_surfaces(tmp_path: Path) -> None:
    payload = run_pfi010_minute_fast_path_acceptance(db_path=tmp_path / "private" / "operational" / "pfi.sqlite")
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "broker_required\": true" not in serialized
    assert "provider_fetch_required\": true" not in serialized
    assert "llm_required\": true" not in serialized
    assert "order_execution" in serialized
    assert payload["safety_boundary"]["no_order_execution"] is True
    assert "sk-proj-" not in serialized
    assert "api_key" not in serialized.lower()
