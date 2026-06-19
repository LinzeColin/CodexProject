from __future__ import annotations

import csv
import json
from pathlib import Path

from quantlab.business import (
    append_cashflow_entry,
    build_cashflow_command,
    build_cashflow_runtime_summary,
    cashflow_command_markdown,
    create_cashflow_entry,
    load_cashflow_entries,
    write_cashflow_command,
)


def test_cashflow_command_requires_reviewed_evidence_for_counted_totals(tmp_path: Path) -> None:
    entry_path = tmp_path / "CompanyCashFlowEntries.json"
    balance = create_cashflow_entry(
        entry_date="2026-06-13",
        direction="BalanceSnapshot",
        category="Other",
        amount=9000.0,
        evidence_link="bank screenshot",
        review_status="Reviewed",
    )
    income = create_cashflow_entry(
        entry_date="2026-06-12",
        direction="Inflow",
        category="SalesRevenue",
        amount=5000.0,
        evidence_link="invoice paid",
        review_status="Reviewed",
    )
    outflow = create_cashflow_entry(
        entry_date="2026-06-11",
        direction="Outflow",
        category="Software",
        amount=3000.0,
        evidence_path="/tmp/software-receipt.pdf",
        review_status="Reviewed",
    )
    pending_outflow = create_cashflow_entry(
        entry_date="2026-06-10",
        direction="Outflow",
        category="Vendor",
        amount=8000.0,
        evidence_link="pending invoice",
        review_status="PendingReview",
    )
    missing_evidence = create_cashflow_entry(
        entry_date="2026-06-09",
        direction="Outflow",
        category="Tax",
        amount=2000.0,
        review_status="Reviewed",
    )
    for entry in [balance, income, outflow, pending_outflow, missing_evidence]:
        append_cashflow_entry(entry, entry_path)

    payload = build_cashflow_command(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    summary = payload["summary"]

    assert payload["schema"] == "EVAOSCompanyCashFlowCommandV1"
    assert payload["subsystem"] == "Company CashFlow Command"
    assert payload["cashflow_status"] == "NeedsEvidence"
    assert summary["total_records"] == 5
    assert summary["counted_records"] == 3
    assert summary["pending_review_records"] == 1
    assert summary["reviewed_missing_evidence_records"] == 1
    assert summary["latest_balance"] == 9000.0
    assert summary["inflow"] == 5000.0
    assert summary["outflow"] == 3000.0
    assert summary["net_cashflow"] == 2000.0
    assert summary["runway_days"] == 90.0
    assert summary["latest_balance_date"] == "2026-06-13"
    assert payload["runtime_summary"]["schema"] == "EVAOSCompanyCashFlowRuntimeSummaryV1"
    assert payload["runtime_summary"]["status"] == "NeedsReview"
    assert payload["runtime_summary"]["reviewed_missing_evidence_records"] == 1
    assert payload["runtime_summary"]["pending_review_records"] == 1
    assert "entries" not in payload["runtime_summary"]
    assert "does not include full entries" in payload["runtime_summary"]["token_policy"]
    assert any(row["source"] == "Evidence Gate" for row in payload["action_queue"])


def test_cashflow_command_missing_balance_is_fail_closed(tmp_path: Path) -> None:
    entry_path = tmp_path / "CompanyCashFlowEntries.json"
    append_cashflow_entry(
        create_cashflow_entry(
            entry_date="2026-06-13",
            direction="Inflow",
            category="SalesRevenue",
            amount=1000.0,
            evidence_link="invoice paid",
            review_status="Reviewed",
        ),
        entry_path,
    )

    payload = build_cashflow_command(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)

    assert payload["cashflow_status"] == "MissingBalance"
    assert payload["runtime_summary"]["status"] == "Blocked"
    assert payload["summary"]["latest_balance"] is None
    assert any(gate["gate"] == "BalanceSnapshot" and gate["status"] == "Blocked" for gate in payload["runtime_summary"]["evidence_gate"])
    assert any(row["source"] == "BalanceSnapshot" for row in payload["action_queue"])


def test_write_cashflow_command_outputs_json_csv_markdown_pdf_and_latest(tmp_path: Path) -> None:
    entry_path = tmp_path / "CompanyCashFlowEntries.json"
    output_dir = tmp_path / "cashflow"
    append_cashflow_entry(
        create_cashflow_entry(
            entry_date="2026-06-13",
            direction="BalanceSnapshot",
            category="Other",
            amount=12000.0,
            evidence_link="bank screenshot",
            review_status="Reviewed",
        ),
        entry_path,
    )

    payload = write_cashflow_command(
        as_of="2026-06-13",
        project_root=tmp_path,
        entry_path=entry_path,
        output_dir=output_dir,
    )
    outputs = payload["outputs"]
    json_path = Path(outputs["json"])
    csv_path = Path(outputs["csv"])
    markdown_path = Path(outputs["markdown"])
    pdf_path = Path(outputs["pdf"])
    latest_json = Path(outputs["latest_json"])
    latest_csv = Path(outputs["latest_csv"])
    latest_markdown = Path(outputs["latest_markdown"])
    latest_pdf = Path(outputs["latest_pdf"])
    runtime_summary_json = Path(outputs["runtime_summary_json"])
    latest_runtime_summary_json = Path(outputs["latest_runtime_summary_json"])

    saved = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_summary = json.loads(runtime_summary_json.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

    assert json_path.name == "CompanyCashFlowCommand_13062026.json"
    assert runtime_summary_json.name == "CompanyCashFlowRuntimeSummary_13062026.json"
    assert saved["schema"] == "EVAOSCompanyCashFlowCommandV1"
    assert runtime_summary["schema"] == "EVAOSCompanyCashFlowRuntimeSummaryV1"
    assert runtime_summary["status"] == "NeedsReview"
    assert "entries" not in runtime_summary
    assert rows[0]["direction"] == "BalanceSnapshot"
    assert markdown_path.read_text(encoding="utf-8").startswith("# EVA_OS Company CashFlow Command")
    assert "## Runtime Evidence Gate" in markdown_path.read_text(encoding="utf-8")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert latest_json.exists()
    assert latest_csv.exists()
    assert latest_markdown.exists()
    assert latest_pdf.exists()
    assert latest_runtime_summary_json.exists()


def test_load_cashflow_entries_normalizes_records_and_markdown_contains_tables(tmp_path: Path) -> None:
    entry_path = tmp_path / "CompanyCashFlowEntries.json"
    append_cashflow_entry(
        {
            "entry_date": "2026-06-13",
            "direction": "收入",
            "category": "Sales Revenue",
            "amount": "1,500",
            "evidence_link": "invoice",
            "review_status": "approved",
        },
        entry_path,
    )

    entries = load_cashflow_entries(entry_path)
    payload = build_cashflow_command(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    markdown = cashflow_command_markdown(payload)

    assert entries[0]["direction"] == "Inflow"
    assert entries[0]["category"] == "SalesRevenue"
    assert entries[0]["amount"] == 1500.0
    assert "## Action Queue" in markdown
    assert "## Entries" in markdown


def test_cashflow_runtime_summary_blocks_bad_schema_and_stays_compact(tmp_path: Path) -> None:
    entry_path = tmp_path / "CompanyCashFlowEntries.json"
    append_cashflow_entry(
        create_cashflow_entry(
            entry_date="2026-06-13",
            direction="BalanceSnapshot",
            category="Other",
            amount=12000.0,
            evidence_link="bank screenshot",
            review_status="Reviewed",
        ),
        entry_path,
    )
    payload = build_cashflow_command(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    payload["schema"] = "UnexpectedSchema"

    summary = build_cashflow_runtime_summary(payload)

    assert summary["schema"] == "EVAOSCompanyCashFlowRuntimeSummaryV1"
    assert summary["status"] == "Blocked"
    assert "entries" not in summary
    assert any(gate["gate"] == "CommandSchema" and gate["status"] == "Blocked" for gate in summary["evidence_gate"])
