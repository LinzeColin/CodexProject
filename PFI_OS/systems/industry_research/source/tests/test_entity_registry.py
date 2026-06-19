from __future__ import annotations

import csv
import json
from pathlib import Path

from src.monitoring.entity_registry import build_entity_registry_audit, normalize_alias, write_entity_registry_audit


def test_normalize_alias_removes_common_variants() -> None:
    assert normalize_alias(" SH.512620 ") == "sh512620"
    assert normalize_alias("农业 ETF 天弘") == "农业etf天弘"
    assert normalize_alias("RunMetadata7_04062026") == "runmetadata704062026"


def test_entity_registry_collects_watchlist_and_manual_review(tmp_path: Path) -> None:
    root = tmp_path / "project"
    sample = root / "data" / "sample"
    sample.mkdir(parents=True)
    _write_csv(
        sample / "watchlist_moomoo.csv",
        ["symbol", "code", "name", "eng_name", "exchange", "asset_class", "research_group"],
        [{"symbol": "512620", "code": "512620", "name": "农业ETF天弘", "eng_name": "Tianhong Agriculture ETF", "exchange": "SSE", "asset_class": "ETF", "research_group": "农业/周期"}],
    )
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_json(
        audit_dir / "manual_review_queue_2026-06-06.json",
        {
            "items": [
                {
                    "review_id": "manualReview_1",
                    "item_name": "source_log_pdf_pairing",
                    "source_layer": "Reconciliation",
                    "source_domain": "report_chain",
                    "priority": "P1",
                    "evidence_classification": "FACT",
                    "decision_grade": "Watch",
                    "issue": "missing pdf",
                }
            ]
        },
    )

    audit = build_entity_registry_audit("2026-06-06", root=root)
    entities = audit["entities"]
    aliases = audit["aliases"]

    assert any(row["entity_type"] == "FinancialInstrument" and row["symbol"] == "512620" for row in entities)
    assert any(row["entity_type"] == "ReviewItem" and row["canonical_name"] == "manualReview_1" for row in entities)
    assert any(row["alias"] == "Tianhong Agriculture ETF" for row in aliases)


def test_entity_registry_detects_alias_conflict(tmp_path: Path) -> None:
    root = tmp_path / "project"
    sample = root / "data" / "sample"
    sample.mkdir(parents=True)
    _write_csv(
        sample / "watchlist_moomoo.csv",
        ["symbol", "code", "name", "exchange", "asset_class"],
        [
            {"symbol": "111111", "code": "DUP", "name": "对象A", "exchange": "SSE", "asset_class": "ETF"},
            {"symbol": "222222", "code": "DUP", "name": "对象B", "exchange": "SSE", "asset_class": "ETF"},
        ],
    )

    audit = build_entity_registry_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Review"
    assert audit["alias_conflict_count"] >= 2
    assert any(row["normalized_alias"] == "dup" for row in audit["conflicts"])


def test_alias_scope_prevents_cross_entity_type_false_conflict(tmp_path: Path) -> None:
    root = tmp_path / "project"
    bridge = root / "data" / "report_artifacts" / "pfi_os_bridge"
    bridge.mkdir(parents=True)
    _write_json(
        bridge / "PFIOSResults.json",
        {"results": [{"strategy_id": "alipay", "status": "Pass", "metadata_path": str(bridge / "meta.json")}]},
    )

    audit = build_entity_registry_audit("2026-06-06", root=root)

    assert any(row["entity_type"] == "Strategy" and row["canonical_name"] == "alipay" for row in audit["entities"])
    assert any(row["entity_type"] == "System" and row["canonical_name"] == "Alipay" for row in audit["entities"])
    assert not any(row["normalized_alias"] == "alipay" for row in audit["conflicts"])


def test_cn_validation_symbol_uses_watchlist_market_hint(tmp_path: Path) -> None:
    root = tmp_path / "project"
    sample = root / "data" / "sample"
    sample.mkdir(parents=True)
    _write_csv(
        sample / "watchlist_moomoo.csv",
        ["symbol", "code", "name", "exchange", "asset_class"],
        [{"symbol": "000688", "code": "000688", "name": "科创50", "exchange": "SSE", "asset_class": "Index"}],
    )
    bridge = root / "data" / "report_artifacts" / "research_bus_bridge"
    bridge.mkdir(parents=True)
    _write_json(
        bridge / "ValidationTasksFromBus.json",
        {
            "validation_tasks": [
                {
                    "task_id": "task_000688",
                    "symbol": "000688",
                    "market": "CN",
                    "status": "Pending",
                    "source_report_path": str(root / "report.md"),
                }
            ]
        },
    )

    audit = build_entity_registry_audit("2026-06-06", root=root)
    instruments = [row for row in audit["entities"] if row["entity_type"] == "FinancialInstrument" and row["symbol"] == "000688"]

    assert len(instruments) == 1
    assert instruments[0]["market"] == "SSE"
    assert not any(row["normalized_alias"] == "000688" for row in audit["conflicts"])


def test_entity_registry_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    sample = root / "data" / "sample"
    sample.mkdir(parents=True)
    _write_csv(
        sample / "watchlist_moomoo.csv",
        ["symbol", "name", "exchange", "asset_class"],
        [{"symbol": "512620", "name": "农业ETF天弘", "exchange": "SSE", "asset_class": "ETF"}],
    )

    audit = write_entity_registry_audit("2026-06-06", root=root)

    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["entity_csv"]).exists()
    assert Path(audit["outputs"]["alias_csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
