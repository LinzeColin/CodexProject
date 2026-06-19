from __future__ import annotations

import csv
import json
from pathlib import Path

from quantlab.policy import (
    append_policy_opportunity,
    build_policy_radar,
    build_policy_runtime_summary,
    create_policy_opportunity,
    load_policy_opportunities,
    policy_radar_markdown,
    write_policy_radar,
)


def test_policy_radar_promotes_only_reviewed_authoritative_evidence(tmp_path: Path) -> None:
    entry_path = tmp_path / "PolicyOpportunityEntries.json"
    actionable = create_policy_opportunity(
        published_date="2026-06-13",
        title="Official AI industry support notice",
        source_name="Department of Industry",
        source_type="Government",
        source_url="https://example.gov/policy",
        jurisdiction="AU",
        policy_level="National",
        opportunity_type="IndustrySupport",
        sectors="AI, Semiconductor",
        affected_entities="Local AI suppliers",
        impact_summary="Official support may create procurement and grant opportunities.",
        required_action="Check eligibility and deadline.",
        authority_score=95,
        relevance_score=85,
        urgency_score=75,
        feasibility_score=70,
        review_status="Reviewed",
    )
    news_only = create_policy_opportunity(
        published_date="2026-06-13",
        title="News summary of possible tax change",
        source_name="News Site",
        source_type="News",
        source_url="https://example.com/news",
        opportunity_type="Tax",
        sectors="Software",
        authority_score=90,
        relevance_score=90,
        urgency_score=90,
        feasibility_score=90,
        review_status="Reviewed",
    )
    pending = create_policy_opportunity(
        published_date="2026-06-13",
        title="Manual policy idea",
        source_name="Manual note",
        source_type="Manual",
        opportunity_type="Other",
        sectors="Energy",
        authority_score=50,
        relevance_score=50,
        urgency_score=50,
        feasibility_score=50,
        review_status="PendingReview",
    )
    for entry in [actionable, news_only, pending]:
        append_policy_opportunity(entry, entry_path)

    payload = build_policy_radar(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    rows = {row["title"]: row for row in payload["opportunities"]}

    assert payload["schema"] == "EVAOSPolicyIntelligenceRadarV1"
    assert payload["subsystem"] == "Policy Intelligence Radar"
    assert payload["policy_status"] == "Actionable"
    assert payload["summary"]["total_records"] == 3
    assert payload["summary"]["actionable_count"] == 1
    assert payload["summary"]["missing_evidence_count"] == 2
    assert payload["runtime_summary"]["schema"] == "EVAOSPolicyIntelligenceRuntimeSummaryV1"
    assert payload["runtime_summary"]["status"] == "NeedsReview"
    assert payload["runtime_summary"]["actionable_count"] == 1
    assert payload["runtime_summary"]["needs_authority_review_records"] == 1
    assert payload["runtime_summary"]["pending_review_count"] == 1
    assert "opportunities" not in payload["runtime_summary"]
    assert "does not include full opportunities" in payload["runtime_summary"]["token_policy"]
    assert rows["Official AI industry support notice"]["opportunity_status"] == "Actionable"
    assert rows["Official AI industry support notice"]["impact_score"] == 83.0
    assert rows["News summary of possible tax change"]["evidence_status"] == "NeedsAuthorityReview"
    assert rows["News summary of possible tax change"]["opportunity_status"] == "NeedsEvidence"
    assert rows["Manual policy idea"]["opportunity_status"] == "PendingReview"
    assert any(row["sector"] == "AI" for row in payload["sector_exposure"])


def test_policy_radar_missing_entries_is_fail_closed(tmp_path: Path) -> None:
    payload = build_policy_radar(as_of="2026-06-13", project_root=tmp_path, entry_path=tmp_path / "missing.json")

    assert payload["policy_status"] == "MissingPolicyEvidence"
    assert payload["runtime_summary"]["status"] == "Blocked"
    assert payload["summary"]["total_records"] == 0
    assert any(gate["gate"] == "PolicyEvidence" and gate["status"] == "Blocked" for gate in payload["runtime_summary"]["evidence_gate"])
    assert any(row["source"] == "Policy Evidence" for row in payload["action_queue"])


def test_write_policy_radar_outputs_json_csv_markdown_pdf_and_latest(tmp_path: Path) -> None:
    entry_path = tmp_path / "PolicyOpportunityEntries.json"
    output_dir = tmp_path / "policy"
    append_policy_opportunity(
        create_policy_opportunity(
            published_date="2026-06-13",
            title="Official procurement notice",
            source_name="Government Procurement",
            source_type="Official",
            source_url="https://example.gov/procurement",
            opportunity_type="Procurement",
            sectors="Cloud",
            authority_score=90,
            relevance_score=80,
            urgency_score=70,
            feasibility_score=60,
            review_status="Reviewed",
        ),
        entry_path,
    )

    payload = write_policy_radar(
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

    assert json_path.name == "PolicyIntelligenceRadar_13062026.json"
    assert runtime_summary_json.name == "PolicyIntelligenceRuntimeSummary_13062026.json"
    assert saved["schema"] == "EVAOSPolicyIntelligenceRadarV1"
    assert runtime_summary["schema"] == "EVAOSPolicyIntelligenceRuntimeSummaryV1"
    assert runtime_summary["status"] == "Pass"
    assert "opportunities" not in runtime_summary
    assert rows[0]["title"] == "Official procurement notice"
    assert markdown_path.read_text(encoding="utf-8").startswith("# EVA_OS Policy Intelligence Radar")
    assert "## Runtime Evidence Gate" in markdown_path.read_text(encoding="utf-8")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert latest_json.exists()
    assert latest_csv.exists()
    assert latest_markdown.exists()
    assert latest_pdf.exists()
    assert latest_runtime_summary_json.exists()


def test_load_policy_opportunities_normalizes_records_and_markdown_contains_tables(tmp_path: Path) -> None:
    entry_path = tmp_path / "PolicyOpportunityEntries.json"
    append_policy_opportunity(
        {
            "published_date": "2026-06-13",
            "title": "Manual clean energy note",
            "source_name": "Manual",
            "source_type": "Manual",
            "source_url": "https://example.com/note",
            "sectors": ["Energy", "Grid"],
            "authority_score": "10",
            "relevance_score": "60",
            "urgency_score": "40",
            "feasibility_score": "50",
            "review_status": "approved",
        },
        entry_path,
    )

    entries = load_policy_opportunities(entry_path)
    payload = build_policy_radar(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    markdown = policy_radar_markdown(payload)

    assert entries[0]["sectors"] == "Energy, Grid"
    assert entries[0]["review_status"] == "Reviewed"
    assert entries[0]["evidence_status"] == "NeedsAuthorityReview"
    assert "## Action Queue" in markdown
    assert "## Runtime Evidence Gate" in markdown
    assert "## Opportunities" in markdown


def test_policy_runtime_summary_blocks_bad_schema_and_stays_compact(tmp_path: Path) -> None:
    entry_path = tmp_path / "PolicyOpportunityEntries.json"
    append_policy_opportunity(
        create_policy_opportunity(
            published_date="2026-06-13",
            title="Official policy item",
            source_name="Regulator",
            source_type="Regulator",
            source_url="https://example.gov/item",
            opportunity_type="RegulatoryChange",
            sectors="Finance",
            authority_score=90,
            relevance_score=80,
            urgency_score=70,
            feasibility_score=70,
            review_status="Reviewed",
        ),
        entry_path,
    )
    payload = build_policy_radar(as_of="2026-06-13", project_root=tmp_path, entry_path=entry_path)
    payload["schema"] = "UnexpectedSchema"

    summary = build_policy_runtime_summary(payload)

    assert summary["schema"] == "EVAOSPolicyIntelligenceRuntimeSummaryV1"
    assert summary["status"] == "Blocked"
    assert "opportunities" not in summary
    assert any(gate["gate"] == "CommandSchema" and gate["status"] == "Blocked" for gate in summary["evidence_gate"])
