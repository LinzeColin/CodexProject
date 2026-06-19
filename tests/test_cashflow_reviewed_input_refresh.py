from __future__ import annotations

import json
from pathlib import Path

from quantlab.business import refresh_cashflow_from_reviewed_input
from quantlab.executive import refresh_runtime_summary_latest


def test_cashflow_reviewed_input_refresh_blocks_when_private_input_missing(tmp_path: Path) -> None:
    payload = refresh_cashflow_from_reviewed_input(as_of="2026-06-16", project_root=tmp_path)

    assert payload["schema"] == "EVAOSCompanyCashFlowReviewedInputRefreshV1"
    assert payload["status"] == "Blocked"
    assert payload["cashflow_status"] == "MissingReviewedInput"
    assert payload["input_status"] == "Missing"
    assert payload["outputs"] == {}
    assert payload["input_contract"]["default_private_input"] == "data/private/cashflow/CompanyCashFlowReviewedInput.json"
    assert "must not be committed" in payload["input_contract"]["private_upload_rule"]
    assert not (tmp_path / "data" / "cashflow" / "CompanyCashFlowCommand_latest.json").exists()


def test_cashflow_reviewed_input_refresh_writes_full_and_runtime_outputs(tmp_path: Path) -> None:
    entry_path = tmp_path / "data" / "private" / "cashflow" / "CompanyCashFlowReviewedInput.json"
    _write_reviewed_input(entry_path)
    output_dir = tmp_path / "data" / "cashflow"

    payload = refresh_cashflow_from_reviewed_input(
        as_of="2026-06-16",
        project_root=tmp_path,
        entry_path=entry_path,
        output_dir=output_dir,
        lookback_days=30,
    )

    assert payload["status"] == "Pass"
    assert payload["cashflow_status"] == "Stable"
    assert payload["input_status"] == "Present"
    assert payload["input_path"] == "data/private/cashflow/CompanyCashFlowReviewedInput.json"
    assert payload["summary"]["latest_balance"] == 18000.0
    assert payload["summary"]["net_cashflow"] == 3840.0
    assert payload["summary"]["runway_days"] == 1500.0
    assert "entries" not in payload["runtime_summary"]
    assert payload["outputs"]["latest_runtime_summary_json"] == "data/cashflow/CompanyCashFlowRuntimeSummary_latest.json"
    assert (output_dir / "CompanyCashFlowCommand_latest.json").exists()
    latest_runtime = json.loads((output_dir / "CompanyCashFlowRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    latest_full = json.loads((output_dir / "CompanyCashFlowCommand_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["status"] == "Pass"
    assert "entries" not in latest_runtime
    assert len(latest_full["entries"]) == 5


def test_runtime_summary_refresh_accepts_cashflow_reviewed_input_path(tmp_path: Path) -> None:
    entry_path = tmp_path / "data" / "private" / "cashflow" / "CompanyCashFlowReviewedInput.json"
    _write_reviewed_input(entry_path)

    payload = refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        cashflow_entry_path=entry_path,
        monthly_investable_budget=1000,
    )

    assert payload["status"] == "Pass"
    cashflow_output = next(row for row in payload["outputs"] if row["subsystem"] == "Company CashFlow Command")
    assert cashflow_output["schema"] == "EVAOSCompanyCashFlowRuntimeSummaryV1"
    assert cashflow_output["runtime_status"] == "Pass"
    latest_runtime = json.loads((tmp_path / "data" / "cashflow" / "CompanyCashFlowRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["latest_balance"] == 18000.0
    assert latest_runtime["net_cashflow"] == 3840.0


def test_public_cashflow_reviewed_input_example_is_synthetic_and_schema_linked() -> None:
    root = Path(__file__).resolve().parents[1]
    example = json.loads((root / "data" / "cashflow" / "CompanyCashFlowReviewedInput.example.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "shared" / "schema" / "company_cashflow_reviewed_input.schema.json").read_text(encoding="utf-8"))
    serialized = json.dumps(example, ensure_ascii=False)

    assert schema["title"] == "EVA_OS Company CashFlow Reviewed Input"
    assert "data/private/cashflow" in schema["description"]
    assert len(example) >= 5
    assert all(row["review_status"] == "Reviewed" for row in example)
    assert all(str(row.get("evidence_link", "")).startswith("sample://cashflow/") for row in example)
    assert "/Users/" not in serialized
    assert "Login Data" not in serialized
    assert "api_key" not in serialized.lower()


def _write_reviewed_input(path: Path) -> None:
    rows = [
        {
            "entry_id": "reviewed_balance_20260616",
            "entry_date": "2026-06-16",
            "direction": "BalanceSnapshot",
            "category": "Other",
            "amount": 18000.0,
            "evidence_link": "reviewed://balance",
            "review_status": "Reviewed",
        },
        {
            "entry_id": "reviewed_inflow_20260615",
            "entry_date": "2026-06-15",
            "direction": "Inflow",
            "category": "ServiceRevenue",
            "amount": 4200.0,
            "evidence_link": "reviewed://inflow",
            "review_status": "Reviewed",
        },
        {
            "entry_id": "reviewed_outflow_20260614",
            "entry_date": "2026-06-14",
            "direction": "Outflow",
            "category": "Software",
            "amount": 360.0,
            "evidence_link": "reviewed://outflow",
            "review_status": "Reviewed",
        },
        {
            "entry_id": "reviewed_receivable_20260616",
            "entry_date": "2026-06-16",
            "direction": "Receivable",
            "category": "SalesRevenue",
            "amount": 2500.0,
            "evidence_link": "reviewed://receivable",
            "review_status": "Reviewed",
        },
        {
            "entry_id": "reviewed_payable_20260616",
            "entry_date": "2026-06-16",
            "direction": "Payable",
            "category": "Compliance",
            "amount": 800.0,
            "evidence_link": "reviewed://payable",
            "review_status": "Reviewed",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
