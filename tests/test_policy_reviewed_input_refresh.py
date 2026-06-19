from __future__ import annotations

import json
from pathlib import Path

from quantlab.executive import refresh_runtime_summary_latest
from quantlab.policy import refresh_policy_from_reviewed_input


def test_policy_reviewed_input_refresh_blocks_when_private_input_missing(tmp_path: Path) -> None:
    payload = refresh_policy_from_reviewed_input(as_of="2026-06-16", project_root=tmp_path)

    assert payload["schema"] == "EVAOSPolicyReviewedInputRefreshV1"
    assert payload["status"] == "Blocked"
    assert payload["policy_status"] == "MissingReviewedInput"
    assert payload["input_status"] == "Missing"
    assert payload["outputs"] == {}
    assert payload["input_contract"]["default_private_input"] == "data/private/policy/PolicyReviewedInput.json"
    assert "must not be committed" in payload["input_contract"]["private_upload_rule"]
    assert not (tmp_path / "data" / "policy" / "PolicyIntelligenceRadar_latest.json").exists()


def test_policy_reviewed_input_refresh_writes_full_and_runtime_outputs(tmp_path: Path) -> None:
    entry_path = tmp_path / "data" / "private" / "policy" / "PolicyReviewedInput.json"
    _write_reviewed_input(entry_path)
    output_dir = tmp_path / "data" / "policy"

    payload = refresh_policy_from_reviewed_input(
        as_of="2026-06-16",
        project_root=tmp_path,
        entry_path=entry_path,
        output_dir=output_dir,
    )

    assert payload["status"] == "Pass"
    assert payload["policy_status"] == "Actionable"
    assert payload["input_status"] == "Present"
    assert payload["input_path"] == "data/private/policy/PolicyReviewedInput.json"
    assert payload["summary"]["opportunity_count"] == 2
    assert payload["summary"]["actionable_count"] == 1
    assert payload["summary"]["authoritative_source_records"] == 2
    assert payload["opportunity_limit"] == 300
    assert "opportunities" not in payload["runtime_summary"]
    assert payload["outputs"]["latest_runtime_summary_json"] == "data/policy/PolicyIntelligenceRuntimeSummary_latest.json"
    latest_runtime = json.loads((output_dir / "PolicyIntelligenceRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    latest_full = json.loads((output_dir / "PolicyIntelligenceRadar_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["status"] == "Pass"
    assert "opportunities" not in latest_runtime
    assert len(latest_full["opportunities"]) == 2


def test_runtime_summary_refresh_accepts_policy_reviewed_input_path(tmp_path: Path) -> None:
    entry_path = tmp_path / "data" / "private" / "policy" / "PolicyReviewedInput.json"
    _write_reviewed_input(entry_path)

    payload = refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        policy_entry_path=entry_path,
        monthly_investable_budget=1000,
    )

    assert payload["status"] == "Pass"
    policy_output = next(row for row in payload["outputs"] if row["subsystem"] == "Policy Intelligence Radar")
    assert policy_output["schema"] == "EVAOSPolicyIntelligenceRuntimeSummaryV1"
    assert policy_output["runtime_status"] == "Pass"
    latest_runtime = json.loads((tmp_path / "data" / "policy" / "PolicyIntelligenceRuntimeSummary_latest.json").read_text(encoding="utf-8"))
    assert latest_runtime["policy_status"] == "Actionable"
    assert latest_runtime["actionable_count"] == 1


def test_public_policy_reviewed_input_example_is_synthetic_and_schema_linked() -> None:
    root = Path(__file__).resolve().parents[1]
    example = json.loads((root / "data" / "policy" / "PolicyReviewedInput.example.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "shared" / "schema" / "policy_reviewed_input.schema.json").read_text(encoding="utf-8"))
    serialized = json.dumps(example, ensure_ascii=False)

    assert schema["title"] == "EVA_OS Policy Reviewed Input"
    assert "data/private/policy" in schema["description"]
    assert len(example) >= 2
    assert all(row["review_status"] == "Reviewed" for row in example)
    assert all(str(row.get("source_url", "")).startswith("https://example.gov/") for row in example)
    assert "/Users/" not in serialized
    assert "Login Data" not in serialized
    assert "api_key" not in serialized.lower()


def _write_reviewed_input(path: Path) -> None:
    rows = [
        {
            "policy_id": "reviewed_policy_ai_support_20260616",
            "published_date": "2026-06-16",
            "title": "Reviewed AI compute support notice",
            "jurisdiction": "AU",
            "policy_level": "National",
            "source_name": "Reviewed Government Department",
            "source_type": "Government",
            "source_url": "https://example.gov/policy/ai-compute-support",
            "review_status": "Reviewed",
            "opportunity_type": "IndustrySupport",
            "sectors": "AI, Cloud Infrastructure",
            "affected_entities": "Local AI suppliers",
            "impact_summary": "Reviewed official-source opportunity.",
            "required_action": "Verify eligibility and deadline.",
            "authority_score": 95,
            "relevance_score": 88,
            "urgency_score": 76,
            "feasibility_score": 72,
        },
        {
            "policy_id": "reviewed_policy_grid_watch_20260616",
            "published_date": "2026-06-16",
            "title": "Reviewed energy grid consultation",
            "jurisdiction": "AU",
            "policy_level": "Agency",
            "source_name": "Reviewed Regulator",
            "source_type": "Regulator",
            "source_url": "https://example.gov/policy/grid-consultation",
            "review_status": "Reviewed",
            "opportunity_type": "RegulatoryChange",
            "sectors": "Energy, Grid",
            "affected_entities": "Infrastructure operators",
            "impact_summary": "Reviewed regulator-source watch item.",
            "required_action": "Track consultation timeline.",
            "authority_score": 90,
            "relevance_score": 64,
            "urgency_score": 45,
            "feasibility_score": 50,
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
