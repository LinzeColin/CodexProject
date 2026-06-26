from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from src.monitoring.reconciliation import build_reconciliation_audit, write_reconciliation_audit


def test_reconciliation_passes_data_trust_bundle_consistency(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    source = root / "data" / "sample" / "watchlist_moomoo.csv"
    source.parent.mkdir(parents=True)
    source.write_text("symbol,name,exchange,asset_class\n512620,农业ETF天弘,SSE,ETF\n", encoding="utf-8")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    records = [
        {
            "record_id": "dataTrust_1",
            "source_type": "csv_artifact",
            "source_name": "watchlist_moomoo.csv",
            "source_path": str(source),
            "data_trust_status": "RECONCILED",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "freshness": "Fresh",
            "row_count": 1,
            "required_fields_present": True,
            "source_url_count": 0,
            "fetch_time_min": "2026-06-06",
            "fetch_time_max": "2026-06-06",
            "sha256": source_hash,
            "issues": "",
            "next_action": "ok",
        }
    ]
    outputs = _write_data_trust_bundle(audit_dir, "2026-06-06", records)
    (root / "HANDOFF.md").write_text("Data Trust Layer v1 data_trust_audit_2026-06-06", encoding="utf-8")
    (root / "README.md").write_text("python3 -m src.cli data-trust-audit", encoding="utf-8")

    audit = build_reconciliation_audit("2026-06-06", root=root, reports_home=tmp_path / "reports")
    checks = {row["check_name"]: row for row in audit["checks"]}

    assert outputs["json"].exists()
    assert checks["data_trust_record_count"]["status"] == "pass"
    assert checks["data_trust_status_counts"]["status"] == "pass"
    assert checks["data_trust_csv_rows"]["status"] == "pass"
    assert checks["data_trust_source_hashes"]["status"] == "pass"


def test_reconciliation_flags_data_trust_hash_drift(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    source = root / "data" / "sample" / "watchlist_moomoo.csv"
    source.parent.mkdir(parents=True)
    source.write_text("symbol,name,exchange,asset_class\n512620,农业ETF天弘,SSE,ETF\n", encoding="utf-8")
    records = [
        {
            "record_id": "dataTrust_1",
            "source_type": "csv_artifact",
            "source_name": "watchlist_moomoo.csv",
            "source_path": str(source),
            "data_trust_status": "RECONCILED",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "freshness": "Fresh",
            "row_count": 1,
            "required_fields_present": True,
            "source_url_count": 0,
            "fetch_time_min": "2026-06-06",
            "fetch_time_max": "2026-06-06",
            "sha256": "bad_hash",
            "issues": "",
            "next_action": "ok",
        }
    ]
    _write_data_trust_bundle(audit_dir, "2026-06-06", records)

    audit = build_reconciliation_audit("2026-06-06", root=root, reports_home=tmp_path / "reports")
    checks = {row["check_name"]: row for row in audit["checks"]}

    assert checks["data_trust_source_hashes"]["status"] == "fail"
    assert audit["audit_status"] == "Blocked"


def test_reconciliation_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    source = root / "data" / "sample" / "watchlist_moomoo.csv"
    source.parent.mkdir(parents=True)
    source.write_text("symbol,name,exchange,asset_class\n512620,农业ETF天弘,SSE,ETF\n", encoding="utf-8")
    records = [
        {
            "record_id": "dataTrust_1",
            "source_type": "csv_artifact",
            "source_name": "watchlist_moomoo.csv",
            "source_path": str(source),
            "data_trust_status": "RECONCILED",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "freshness": "Fresh",
            "row_count": 1,
            "required_fields_present": True,
            "source_url_count": 0,
            "fetch_time_min": "2026-06-06",
            "fetch_time_max": "2026-06-06",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "issues": "",
            "next_action": "ok",
        }
    ]
    _write_data_trust_bundle(audit_dir, "2026-06-06", records)

    audit = write_reconciliation_audit("2026-06-06", root=root, reports_home=tmp_path / "reports")

    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()


def _write_data_trust_bundle(audit_dir: Path, as_of: str, records: list[dict[str, object]]) -> dict[str, Path]:
    status_counts: dict[str, int] = {}
    for row in records:
        status = str(row["data_trust_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    outputs = {
        "json": audit_dir / f"data_trust_audit_{as_of}.json",
        "csv": audit_dir / f"data_trust_audit_{as_of}.csv",
        "markdown": audit_dir / f"data_trust_audit_{as_of}.md",
        "pdf": audit_dir / f"data_trust_audit_{as_of}.pdf",
    }
    payload = {
        "schema": "AIResearchDataTrustV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": "2026-06-06T00:00:00+10:00",
        "audit_status": "Pass",
        "status_counts": status_counts,
        "record_count": len(records),
        "records": records,
        "outputs": {key: str(value) for key, value in outputs.items()},
    }
    outputs["json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with outputs["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    outputs["markdown"].write_text("# Data Trust", encoding="utf-8")
    outputs["pdf"].write_bytes(b"%PDF-1.4\n")
    return outputs
