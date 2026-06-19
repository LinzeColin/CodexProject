from __future__ import annotations

import json
from pathlib import Path

from quantlab.integrations.research_bus_api import submit_chat_input
from quantlab.system.integration_audit import build_quantlab_integration_audit, write_quantlab_integration_audit


def test_quantlab_integration_audit_passes_when_all_layers_have_evidence(tmp_path: Path) -> None:
    root = _integration_root(tmp_path)
    report_root = tmp_path / "reports"
    report_root.mkdir()
    db_path = tmp_path / "ResearchBus.sqlite"
    _write_entity_registry(root)
    _write_report_metadata(report_root, with_evidence=True)
    submit_chat_input("请验证 AAPL 的 RSI 策略", source_system="UnitTest", db_path=db_path)

    payload = build_quantlab_integration_audit(
        as_of="2026-06-06",
        project_root=root,
        report_root=report_root,
        db_path=db_path,
        data_trust_payload=_data_trust_payload("Pass"),
        research_bus_payload={"status": "Pass", "summary": {"pass": 15, "warn": 0, "fail": 0}},
    )

    assert payload["schema"] == "QuantLabIntegrationAuditV1"
    assert payload["status"] == "Pass"
    assert payload["summary"] == {"pass": 6, "review": 0, "fail": 0, "item_count": 6}
    assert {item["layer"] for item in payload["items"]} == {
        "DataTrust",
        "EntityRegistry",
        "WorkflowInputs",
        "ReportEvidence",
        "ResearchBusInterop",
        "NoLiveTradingBoundary",
    }


def test_quantlab_integration_audit_reviews_missing_artifacts(tmp_path: Path) -> None:
    root = _integration_root(tmp_path)
    report_root = tmp_path / "reports"
    report_root.mkdir()
    db_path = tmp_path / "ResearchBus.sqlite"

    payload = build_quantlab_integration_audit(
        as_of="2026-06-06",
        project_root=root,
        report_root=report_root,
        db_path=db_path,
        data_trust_payload=_data_trust_payload("Pass"),
        research_bus_payload={"status": "Pass", "summary": {"pass": 15, "warn": 0, "fail": 0}},
    )
    by_layer = {item["layer"]: item for item in payload["items"]}

    assert payload["status"] == "Review"
    assert by_layer["EntityRegistry"]["status"] == "Review"
    assert by_layer["WorkflowInputs"]["status"] == "Review"
    assert by_layer["ReportEvidence"]["status"] == "Review"


def test_write_quantlab_integration_audit_outputs_json_and_markdown(tmp_path: Path) -> None:
    root = _integration_root(tmp_path)
    report_root = tmp_path / "reports"
    report_root.mkdir()
    db_path = tmp_path / "ResearchBus.sqlite"
    output_dir = tmp_path / "audit"

    payload = write_quantlab_integration_audit(
        as_of="2026-06-06",
        project_root=root,
        report_root=report_root,
        db_path=db_path,
        output_dir=output_dir,
    )

    json_path = Path(payload["outputs"]["json"])
    markdown_path = Path(payload["outputs"]["markdown"])
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_path.name == "QuantLabIntegrationAudit_06062026.json"
    assert saved["schema"] == "QuantLabIntegrationAuditV1"
    assert markdown_path.read_text(encoding="utf-8").startswith("# QuantLab Integration Audit")


def _integration_root(tmp_path: Path) -> Path:
    root = tmp_path / "QuantLab"
    (root / "docs").mkdir(parents=True)
    (root / "AGENTS.md").write_text("禁止接入实盘，禁止真实下单。", encoding="utf-8")
    (root / "README.md").write_text("No live trading. This system must not place real orders.", encoding="utf-8")
    (root / "docs" / "RiskAndLimits.md").write_text("研究 only。", encoding="utf-8")
    return root


def _write_entity_registry(root: Path) -> None:
    entity_dir = root / "data" / "entityRegistry"
    entity_dir.mkdir(parents=True)
    (entity_dir / "EntityRegistry.json").write_text(
        json.dumps(
            {
                "schema": "QuantLabEntityRegistryV1",
                "record_count": 1,
                "status_counts": {"TradableSymbol": 1},
                "records": [{"canonical_symbol": "AAPL", "status": "TradableSymbol"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (entity_dir / "EntityRegistry.csv").write_text("canonical_symbol,status\nAAPL,TradableSymbol\n", encoding="utf-8")
    (entity_dir / "EntityRegistry.md").write_text("# Entity Registry\n", encoding="utf-8")


def _write_report_metadata(report_root: Path, *, with_evidence: bool) -> None:
    payload = {"metrics": {}, "metadata": {}}
    if with_evidence:
        payload["report_evidence"] = {"schema": "QuantLabReportEvidenceV1", "evidence_status": "ContinueResearch"}
    (report_root / "RunMetadata_06062026.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _data_trust_payload(status: str) -> dict[str, object]:
    return {
        "audit_status": status,
        "record_count": 10,
        "review_count": 0 if status == "Pass" else 1,
        "rejected_count": 0,
    }
