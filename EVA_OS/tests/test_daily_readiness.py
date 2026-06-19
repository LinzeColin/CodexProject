from __future__ import annotations

import json
from pathlib import Path

from quantlab.system.daily_readiness import build_daily_readiness, daily_readiness_markdown, write_daily_readiness


def test_daily_readiness_reports_ready_when_core_gates_pass(tmp_path: Path) -> None:
    payload = build_daily_readiness(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        data_trust_payload=_data_trust("Pass"),
        integration_payload=_integration("Pass"),
        health_checks=[],
        provider_rows=[{"provider": "Sample", "status": "Ready"}, {"provider": "Moomoo", "status": "NeedsOpenD"}],
        report_counts={"Run Metadata": 1},
        latest_report={"path": "/tmp/report.docx", "artifact_type": "Backtest Word Report", "modified_at": "2026-06-07T09:00:00"},
    )

    assert payload["schema"] == "QuantLabDailyReadinessV1"
    assert payload["readiness_status"] == "ReadyForResearch"
    assert payload["provider_summary"]["needs_opend"] == 1
    assert any("Moomoo OpenD" in item for item in payload["action_items"])


def test_daily_readiness_reviews_missing_report_or_audit_gap(tmp_path: Path) -> None:
    payload = build_daily_readiness(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        data_trust_payload=_data_trust("Review", review_count=1),
        integration_payload=_integration("Review"),
        health_checks=[{"status": "Review", "item_en": "Desktop App Launcher"}],
        provider_rows=[],
        report_counts={"Run Metadata": 0},
        latest_report={},
    )
    by_gate = {row["gate"]: row for row in payload["core_gates"]}

    assert payload["readiness_status"] == "NeedsReview"
    assert by_gate["DataTrust"]["status"] == "Review"
    assert by_gate["LatestWordReport"]["status"] == "Review"
    assert any("Review 1 local setup checks" in item for item in payload["action_items"])


def test_write_daily_readiness_outputs_json_markdown_and_pdf(tmp_path: Path) -> None:
    output_dir = tmp_path / "audit"

    payload = write_daily_readiness(as_of="2026-06-07", project_root=tmp_path, report_root=tmp_path / "reports", output_dir=output_dir)

    json_path = Path(payload["outputs"]["json"])
    markdown_path = Path(payload["outputs"]["markdown"])
    pdf_path = Path(payload["outputs"]["pdf"])
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_path.name == "QuantLabDailyReadiness_07062026.json"
    assert saved["schema"] == "QuantLabDailyReadinessV1"
    assert markdown_path.read_text(encoding="utf-8").startswith("# QuantLab Daily Readiness")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")


def test_daily_readiness_markdown_contains_gates_and_actions(tmp_path: Path) -> None:
    payload = build_daily_readiness(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        data_trust_payload=_data_trust("Pass"),
        integration_payload=_integration("Pass"),
        health_checks=[],
        provider_rows=[],
        report_counts={"Run Metadata": 1},
        latest_report={"path": "/tmp/report.docx"},
    )

    markdown = daily_readiness_markdown(payload)

    assert "## Core Gates" in markdown
    assert "DataTrust" in markdown
    assert "## Action Items" in markdown


def _data_trust(status: str, *, review_count: int = 0, rejected_count: int = 0) -> dict[str, object]:
    return {
        "audit_status": status,
        "record_count": 10,
        "review_count": review_count,
        "rejected_count": rejected_count,
        "status_counts": {},
    }


def _integration(status: str) -> dict[str, object]:
    layer_status = "Pass" if status == "Pass" else "Review"
    return {
        "status": status,
        "summary": {"pass": 6 if status == "Pass" else 5, "review": 0 if status == "Pass" else 1, "fail": 0, "item_count": 6},
        "items": [
            {"layer": "DataTrust", "status": layer_status},
            {"layer": "EntityRegistry", "status": "Pass"},
            {"layer": "WorkflowInputs", "status": "Pass"},
            {"layer": "ReportEvidence", "status": layer_status},
            {"layer": "ResearchBusInterop", "status": "Pass"},
            {"layer": "NoLiveTradingBoundary", "status": "Pass"},
        ],
    }
