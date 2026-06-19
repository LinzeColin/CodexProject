from __future__ import annotations

import csv
import json
from pathlib import Path

from quantlab.consumption import (
    append_consumption_event,
    build_consumption_guard,
    build_consumption_runtime_summary,
    consumption_guard_markdown,
    create_consumption_event,
    load_consumption_events,
    write_consumption_guard,
)


def test_consumption_guard_counts_only_reviewed_evidence_and_flags_pressure(tmp_path: Path) -> None:
    event_path = tmp_path / "ConsumptionGuardEvents.json"
    impulse = create_consumption_event(
        event_date="2026-06-13",
        event_type="Impulse",
        category="Shopping",
        amount=600.0,
        merchant="Gadget Store",
        planned=False,
        necessity_score=10,
        impulse_score=95,
        regret_score=80,
        evidence_link="receipt screenshot",
        review_status="Reviewed",
    )
    subscription = create_consumption_event(
        event_date="2026-06-12",
        event_type="Subscription",
        category="Subscription",
        amount=120.0,
        merchant="SaaS",
        planned=True,
        recurring=True,
        necessity_score=70,
        impulse_score=5,
        regret_score=10,
        evidence_path="/tmp/subscription.pdf",
        review_status="Reviewed",
    )
    pending = create_consumption_event(
        event_date="2026-06-11",
        event_type="Discretionary",
        category="Entertainment",
        amount=900.0,
        evidence_link="pending bill",
        review_status="PendingReview",
    )
    missing_evidence = create_consumption_event(
        event_date="2026-06-10",
        event_type="Impulse",
        category="Shopping",
        amount=500.0,
        review_status="Reviewed",
    )
    for event in [impulse, subscription, pending, missing_evidence]:
        append_consumption_event(event, event_path)

    payload = build_consumption_guard(
        as_of="2026-06-13",
        project_root=tmp_path,
        event_path=event_path,
        monthly_investable_budget=700.0,
    )
    summary = payload["summary"]

    assert payload["schema"] == "EVAOSConsumptionGuardV1"
    assert payload["subsystem"] == "Consumption Guard"
    assert payload["guard_status"] == "NeedsEvidence"
    assert summary["total_records"] == 4
    assert summary["counted_records"] == 2
    assert summary["pending_review_records"] == 1
    assert summary["reviewed_missing_evidence_records"] == 1
    assert summary["counted_spend"] == 720.0
    assert summary["impulse_spend"] == 600.0
    assert summary["fixed_cost"] == 120.0
    assert summary["discretionary_spend"] == 600.0
    assert summary["investable_cashflow_pressure"] == 0.8571
    assert payload["runtime_summary"]["schema"] == "EVAOSConsumptionGuardRuntimeSummaryV1"
    assert payload["runtime_summary"]["status"] == "NeedsReview"
    assert payload["runtime_summary"]["counted_records"] == 2
    assert payload["runtime_summary"]["reviewed_missing_evidence_records"] == 1
    assert payload["runtime_summary"]["pending_review_records"] == 1
    assert payload["runtime_summary"]["high_risk_event_count"] == 1
    assert "events" not in payload["runtime_summary"]
    assert "does not include full events" in payload["runtime_summary"]["token_policy"]
    assert any(row["source"] == "Evidence Gate" for row in payload["action_queue"])
    assert any(row["category"] == "Shopping" and row["high_risk_amount"] == 600.0 for row in payload["category_totals"])


def test_consumption_guard_missing_events_is_fail_closed(tmp_path: Path) -> None:
    payload = build_consumption_guard(as_of="2026-06-13", project_root=tmp_path, event_path=tmp_path / "missing.json")

    assert payload["guard_status"] == "MissingConsumptionEvidence"
    assert payload["runtime_summary"]["status"] == "Blocked"
    assert payload["summary"]["total_records"] == 0
    assert any(gate["gate"] == "ConsumptionEvidence" and gate["status"] == "Blocked" for gate in payload["runtime_summary"]["evidence_gate"])
    assert any(row["source"] == "Consumption Evidence" for row in payload["action_queue"])


def test_write_consumption_guard_outputs_json_csv_markdown_pdf_and_latest(tmp_path: Path) -> None:
    event_path = tmp_path / "ConsumptionGuardEvents.json"
    output_dir = tmp_path / "consumption"
    append_consumption_event(
        create_consumption_event(
            event_date="2026-06-13",
            event_type="Essential",
            category="Food",
            amount=30.0,
            planned=True,
            necessity_score=90,
            impulse_score=0,
            regret_score=0,
            evidence_link="receipt",
            review_status="Reviewed",
        ),
        event_path,
    )

    payload = write_consumption_guard(
        as_of="2026-06-13",
        project_root=tmp_path,
        event_path=event_path,
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

    assert json_path.name == "ConsumptionGuard_13062026.json"
    assert runtime_summary_json.name == "ConsumptionGuardRuntimeSummary_13062026.json"
    assert saved["schema"] == "EVAOSConsumptionGuardV1"
    assert runtime_summary["schema"] == "EVAOSConsumptionGuardRuntimeSummaryV1"
    assert runtime_summary["status"] == "NeedsReview"
    assert "events" not in runtime_summary
    assert rows[0]["event_type"] == "Essential"
    assert markdown_path.read_text(encoding="utf-8").startswith("# EVA_OS Consumption Guard")
    assert "## Runtime Evidence Gate" in markdown_path.read_text(encoding="utf-8")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert latest_json.exists()
    assert latest_csv.exists()
    assert latest_markdown.exists()
    assert latest_pdf.exists()
    assert latest_runtime_summary_json.exists()


def test_load_consumption_events_normalizes_records_and_markdown_contains_tables(tmp_path: Path) -> None:
    event_path = tmp_path / "ConsumptionGuardEvents.json"
    append_consumption_event(
        {
            "event_date": "2026-06-13",
            "event_type": "Impulse",
            "category": "Shopping",
            "amount": "1,000",
            "evidence_link": "receipt",
            "review_status": "approved",
            "impulse_score": 100,
            "regret_score": 80,
            "necessity_score": 10,
        },
        event_path,
    )

    events = load_consumption_events(event_path)
    payload = build_consumption_guard(as_of="2026-06-13", project_root=tmp_path, event_path=event_path)
    markdown = consumption_guard_markdown(payload)

    assert events[0]["amount"] == 1000.0
    assert events[0]["review_status"] == "Reviewed"
    assert events[0]["risk_level"] == "HighImpulse"
    assert "## Action Queue" in markdown
    assert "## Runtime Evidence Gate" in markdown
    assert "## Events" in markdown


def test_consumption_runtime_summary_blocks_bad_schema_and_stays_compact(tmp_path: Path) -> None:
    event_path = tmp_path / "ConsumptionGuardEvents.json"
    append_consumption_event(
        create_consumption_event(
            event_date="2026-06-13",
            event_type="Essential",
            category="Food",
            amount=30.0,
            planned=True,
            necessity_score=90,
            impulse_score=0,
            regret_score=0,
            evidence_link="receipt",
            review_status="Reviewed",
        ),
        event_path,
    )
    payload = build_consumption_guard(
        as_of="2026-06-13",
        project_root=tmp_path,
        event_path=event_path,
        monthly_investable_budget=1000.0,
    )
    payload["schema"] = "UnexpectedSchema"

    summary = build_consumption_runtime_summary(payload)

    assert summary["schema"] == "EVAOSConsumptionGuardRuntimeSummaryV1"
    assert summary["status"] == "Blocked"
    assert "events" not in summary
    assert any(gate["gate"] == "GuardSchema" and gate["status"] == "Blocked" for gate in summary["evidence_gate"])
