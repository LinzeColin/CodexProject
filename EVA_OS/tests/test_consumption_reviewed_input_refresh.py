from __future__ import annotations

import json
from pathlib import Path

from quantlab.consumption import refresh_consumption_from_reviewed_input
from quantlab.executive import refresh_runtime_summary_latest


def test_consumption_reviewed_input_refresh_blocks_when_private_input_missing(tmp_path: Path) -> None:
    payload = refresh_consumption_from_reviewed_input(as_of="2026-06-16", project_root=tmp_path)

    assert payload["schema"] == "EVAOSConsumptionGuardReviewedInputRefreshV1"
    assert payload["status"] == "Blocked"
    assert payload["guard_status"] == "MissingReviewedInput"
    assert payload["input_status"] == "Missing"
    assert payload["outputs"] == {}
    assert payload["input_contract"]["default_private_input"] == "data/private/consumption/ConsumptionGuardReviewedInput.json"
    assert "must not be committed" in payload["input_contract"]["private_upload_rule"]
    assert not (tmp_path / "data" / "consumption" / "ConsumptionGuard_latest.json").exists()


def test_consumption_reviewed_input_refresh_writes_full_and_runtime_outputs(tmp_path: Path) -> None:
    event_path = tmp_path / "data" / "private" / "consumption" / "ConsumptionGuardReviewedInput.json"
    _write_reviewed_input(event_path)
    output_dir = tmp_path / "data" / "consumption"

    payload = refresh_consumption_from_reviewed_input(
        as_of="2026-06-16",
        project_root=tmp_path,
        event_path=event_path,
        output_dir=output_dir,
        monthly_investable_budget=1000,
    )

    assert payload["status"] == "NeedsReview"
    assert payload["guard_status"] == "Watch"
    assert payload["input_status"] == "Present"
    assert payload["input_path"] == "data/private/consumption/ConsumptionGuardReviewedInput.json"
    assert payload["summary"]["event_count"] == 3
    assert payload["summary"]["counted_records"] == 3
    assert payload["summary"]["impulse_spend"] == 420.0
    assert payload["summary"]["fixed_cost"] == 89.0
    assert payload["summary"]["high_risk_event_count"] == 1
    assert "events" not in payload["runtime_summary"]
    assert payload["outputs"]["latest_runtime_summary_json"] == "data/consumption/ConsumptionGuardRuntimeSummary_latest.json"
    latest_runtime = json.loads((output_dir / "ConsumptionGuardRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    latest_full = json.loads((output_dir / "ConsumptionGuard_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["schema"] == "EVAOSConsumptionGuardRuntimeSummaryV1"
    assert "events" not in latest_runtime
    assert len(latest_full["events"]) == 3


def test_runtime_summary_refresh_accepts_consumption_reviewed_input_path(tmp_path: Path) -> None:
    event_path = tmp_path / "data" / "private" / "consumption" / "ConsumptionGuardReviewedInput.json"
    _write_reviewed_input(event_path)

    payload = refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        consumption_event_path=event_path,
        monthly_investable_budget=1000,
    )

    assert payload["status"] == "Pass"
    consumption_output = next(row for row in payload["outputs"] if row["subsystem"] == "Consumption Guard")
    assert consumption_output["schema"] == "EVAOSConsumptionGuardRuntimeSummaryV1"
    assert consumption_output["runtime_status"] == "NeedsReview"
    latest_runtime = json.loads((tmp_path / "data" / "consumption" / "ConsumptionGuardRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["guard_status"] == "Watch"
    assert latest_runtime["counted_records"] == 3


def test_public_consumption_reviewed_input_example_is_synthetic_and_schema_linked() -> None:
    root = Path(__file__).resolve().parents[1]
    example = json.loads((root / "data" / "consumption" / "ConsumptionGuardReviewedInput.example.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "shared" / "schema" / "consumption_guard_reviewed_input.schema.json").read_text(encoding="utf-8"))
    serialized = json.dumps(example, ensure_ascii=False)

    assert schema["title"] == "EVA_OS Consumption Guard Reviewed Input"
    assert "data/private/consumption" in schema["description"]
    assert len(example) >= 3
    assert all(row["review_status"] == "Reviewed" for row in example)
    assert all(str(row.get("evidence_link", "")).startswith("sample://consumption/") for row in example)
    assert "/Users/" not in serialized
    assert "Login Data" not in serialized
    assert "api_key" not in serialized.lower()


def _write_reviewed_input(path: Path) -> None:
    rows = [
        {
            "event_id": "reviewed_consumption_food_20260616",
            "event_date": "2026-06-16",
            "event_type": "Essential",
            "category": "Food",
            "amount": 38.5,
            "currency": "AUD",
            "merchant": "Reviewed Grocery",
            "payment_method": "Reviewed Card",
            "planned": True,
            "recurring": False,
            "necessity_score": 92,
            "impulse_score": 5,
            "regret_score": 0,
            "evidence_link": "sample://consumption/receipt-food-20260616",
            "review_status": "Reviewed",
        },
        {
            "event_id": "reviewed_consumption_subscription_20260616",
            "event_date": "2026-06-15",
            "event_type": "Subscription",
            "category": "Subscription",
            "amount": 89.0,
            "currency": "AUD",
            "merchant": "Reviewed Software",
            "payment_method": "Reviewed Card",
            "planned": True,
            "recurring": True,
            "necessity_score": 64,
            "impulse_score": 12,
            "regret_score": 18,
            "evidence_link": "sample://consumption/receipt-subscription-20260615",
            "review_status": "Reviewed",
        },
        {
            "event_id": "reviewed_consumption_impulse_20260616",
            "event_date": "2026-06-14",
            "event_type": "Impulse",
            "category": "Shopping",
            "amount": 420.0,
            "currency": "AUD",
            "merchant": "Reviewed Electronics",
            "payment_method": "Reviewed Card",
            "planned": False,
            "recurring": False,
            "necessity_score": 15,
            "impulse_score": 94,
            "regret_score": 78,
            "evidence_link": "sample://consumption/receipt-impulse-20260614",
            "review_status": "Reviewed",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
