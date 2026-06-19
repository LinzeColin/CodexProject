from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path

from pfi_os.system import build_data_trust_audit, write_data_trust_audit


def test_data_trust_audit_classifies_core_pfi_os_sources(tmp_path: Path) -> None:
    root = _fixture_project(tmp_path)
    _write_json(root / "data" / "researchBus" / "ResearchBusInteropAudit.json", {"schema": "ResearchBusInteropAuditV1", "status": "Pass"})
    _write_json(root / "data" / "researchBus" / "ResearchBusSnapshot.json", {"schema": "ResearchBusV1", "tables": {}})
    (root / "data" / "researchBus" / "ResearchBus.sqlite").write_bytes(b"sqlite")
    _write_json(root / "data" / "validationQueue" / "ValidationTasks.json", [{"task_id": "task1", "status": "待验证"}])
    _write_json(
        root / "data" / "independentValidation" / "IndependentValidationRun_20260606_010101.json",
        {"run_id": "run1", "status": "Completed", "mode": "checksum"},
    )
    (root / "data" / "cache" / "streamlit_restart.pid").write_text("123", encoding="utf-8")
    report_root = tmp_path / "reports"
    report_root.mkdir()
    (report_root / "BacktestReport_06062026.docx").write_bytes(b"docx")

    audit = build_data_trust_audit(as_of="2026-06-06", project_root=root, report_root=report_root)
    by_path = {row["source_path"]: row for row in audit["records"]}

    assert audit["schema"] == "PFIOSDataTrustAuditV1"
    assert audit["audit_status"] == "Review"
    assert by_path["data/holdings/HoldingsBook.json"]["trust_status"] == "RECONCILED"
    assert by_path["data/holdings/imports/video_position_candidates_20260606.csv"]["trust_status"] == "PARSED_CANDIDATE"
    assert by_path["data/validationQueue/ValidationTasks.json"]["trust_status"] == "PARSED_CANDIDATE"
    assert by_path["data/cache/streamlit_restart.pid"]["trust_status"] == "ARCHIVED"
    assert "RECONCILED" in audit["status_counts"]
    assert "PARSED_CANDIDATE" in audit["status_counts"]
    assert audit["rejected_count"] == 0


def test_data_trust_audit_rejects_malformed_json(tmp_path: Path) -> None:
    root = _fixture_project(tmp_path)
    bad = root / "data" / "researchBus" / "ResearchBusInteropAudit.json"
    bad.write_text("{bad json", encoding="utf-8")

    audit = build_data_trust_audit(as_of="2026-06-06", project_root=root, report_root=tmp_path / "reports")
    by_path = {row["source_path"]: row for row in audit["records"]}

    assert audit["audit_status"] == "Blocked"
    assert by_path["data/researchBus/ResearchBusInteropAudit.json"]["trust_status"] == "REJECTED"
    assert by_path["data/researchBus/ResearchBusInteropAudit.json"]["decision_grade"] == "Reject"


def test_data_trust_audit_covers_providers_strategies_and_experiments(tmp_path: Path) -> None:
    root = _fixture_project(tmp_path)
    _write_provider_and_strategy_files(root)
    experiment = root / "data" / "results" / "experiments" / "ma_scan_AAPL"
    experiment.mkdir(parents=True)
    _write_csv(experiment / "summary.csv", [["run_id", "sharpe"], ["run1", "1.2"]])
    _write_json(experiment / "runs.json", [{"run_id": "run1"}])
    _write_json(experiment / "stability.json", {"stability_status": "Stable"})

    audit = build_data_trust_audit(as_of="2026-06-06", project_root=root, report_root=tmp_path / "reports")
    by_path = {row["source_path"]: row for row in audit["records"]}

    assert by_path["PLANS.md"]["trust_status"] == "NEEDS_REVIEW"
    assert by_path["src/pfi_os/data/providers/moomoo_provider.py"]["trust_status"] == "RECONCILED"
    assert by_path["src/pfi_os/data/providers/sample_provider.py"]["issue"] == "Sample Provider 存在。"
    assert by_path["src/pfi_os/strategies/behavioral/alipay.py"]["trust_status"] == "RECONCILED"
    assert by_path["data/approvals"]["trust_status"] == "NEEDS_REVIEW"
    assert by_path["data/results/experiments/ma_scan_AAPL"]["trust_status"] == "RECONCILED"
    assert by_path["data/results/experiments/ma_scan_AAPL/summary.csv"]["trust_status"] == "RECONCILED"
    assert by_path["data/results/experiments/ma_scan_AAPL/runs.json"]["trust_status"] == "RECONCILED"
    assert by_path["data/results/experiments/ma_scan_AAPL/train_test_validation.json"]["trust_status"] == "NEEDS_REVIEW"
    assert by_path["data/results/experiments/ma_scan_AAPL/walk_forward_validation.json"]["user_confirmation_required"] is True


def test_data_trust_audit_archives_stale_empty_lock_files(tmp_path: Path) -> None:
    root = _fixture_project(tmp_path)
    lock_path = root / "data" / "holdings" / "HoldingsBook.lock"
    lock_path.write_text("", encoding="utf-8")
    stale = time.time() - 7200
    os.utime(lock_path, (stale, stale))

    audit = build_data_trust_audit(as_of="2026-06-06", project_root=root, report_root=tmp_path / "reports")
    by_path = {row["source_path"]: row for row in audit["records"]}

    assert by_path["data/holdings/HoldingsBook.lock"]["trust_status"] == "ARCHIVED"
    assert by_path["data/holdings/HoldingsBook.lock"]["user_confirmation_required"] is False


def test_write_data_trust_audit_outputs_machine_and_formal_files(tmp_path: Path) -> None:
    root = _fixture_project(tmp_path)
    output_dir = tmp_path / "audit"

    audit = write_data_trust_audit(as_of="2026-06-06", project_root=root, report_root=tmp_path / "reports", output_dir=output_dir)

    json_path = Path(audit["outputs"]["json"])
    csv_path = Path(audit["outputs"]["csv"])
    md_path = Path(audit["outputs"]["markdown"])
    pdf_path = Path(audit["outputs"]["pdf"])
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))

    assert json_path.name == "PFIOSDataTrustAudit_06062026.json"
    assert saved["schema"] == "PFIOSDataTrustAuditV1"
    assert len(csv_rows) == saved["record_count"]
    assert md_path.read_text(encoding="utf-8").startswith("# PFIOS Data Trust Audit")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")


def _fixture_project(tmp_path: Path) -> Path:
    root = tmp_path / "PFIOS"
    for path in [
        root / "data" / "holdings" / "imports",
        root / "data" / "researchBus",
        root / "data" / "validationQueue",
        root / "data" / "independentValidation",
        root / "data" / "cache",
        root / "data" / "raw",
        root / "data" / "processed",
    ]:
        path.mkdir(parents=True, exist_ok=True)
    for name in ["AGENTS.md", "HANDOFF.md", "README.md"]:
        (root / name).write_text(name, encoding="utf-8")
    _write_json(root / "data" / "holdings" / "HoldingsBook.json", {"schema": "PFIOSHoldingsBookV1", "holdings": [{"name": "A"}]})
    _write_csv(root / "data" / "holdings" / "HoldingsBook.csv", [["name", "position_value"], ["A", "100"]])
    _write_json(root / "data" / "holdings" / "HoldingsImportHistory.json", {"schema": "PFIOSHoldingsImportHistoryV1", "history": []})
    _write_csv(root / "data" / "holdings" / "imports" / "video_position_candidates_20260606.csv", [["name", "amount", "status"], ["A", "100", "candidate"]])
    _write_csv(root / "data" / "holdings" / "imports" / "confirmed_holding_candidates.csv", [["name", "amount"], ["A", "100"]])
    return root


def _write_provider_and_strategy_files(root: Path) -> None:
    for path in [
        root / "pyproject.toml",
        root / "docs" / "DataSources.md",
        root / "docs" / "RiskAndLimits.md",
        root / "docs" / "ResearchBus.md",
        root / "src" / "pfi_os" / "data" / "quality.py",
        root / "src" / "pfi_os" / "data" / "validation.py",
        root / "src" / "pfi_os" / "data" / "providers" / "base.py",
        root / "src" / "pfi_os" / "data" / "providers" / "factory.py",
        root / "src" / "pfi_os" / "data" / "providers" / "moomoo_provider.py",
        root / "src" / "pfi_os" / "data" / "providers" / "yahoo_finance.py",
        root / "src" / "pfi_os" / "data" / "providers" / "akshare_provider.py",
        root / "src" / "pfi_os" / "data" / "providers" / "tushare_provider.py",
        root / "src" / "pfi_os" / "data" / "providers" / "alpha_vantage.py",
        root / "src" / "pfi_os" / "data" / "providers" / "polygon_provider.py",
        root / "src" / "pfi_os" / "data" / "providers" / "csv_provider.py",
        root / "src" / "pfi_os" / "data" / "providers" / "sample_provider.py",
        root / "src" / "pfi_os" / "strategies" / "base.py",
        root / "src" / "pfi_os" / "strategies" / "profiles.py",
        root / "src" / "pfi_os" / "strategies" / "templates.py",
        root / "src" / "pfi_os" / "strategies" / "behavioral" / "alipay.py",
        root / "src" / "pfi_os" / "strategies" / "trend" / "ma_crossover.py",
        root / "src" / "pfi_os" / "strategies" / "trend" / "breakout.py",
        root / "src" / "pfi_os" / "strategies" / "mean_reversion" / "rsi_reversion.py",
        root / "src" / "pfi_os" / "strategies" / "mean_reversion" / "bollinger_reversion.py",
        root / "src" / "pfi_os" / "strategies" / "momentum" / "momentum_rotation.py",
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(path.name, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
