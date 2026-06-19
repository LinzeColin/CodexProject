from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from app.core.source_evidence_audit import build_source_evidence_audit
from app.db import connect
from tests.helpers import copy_sample_data, temp_settings


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_source_evidence_audit_hashes_local_files_and_accepts_urls(tmp_path: Path):
    settings = temp_settings(tmp_path)
    evidence_file = settings.root_dir / "evidence" / "alipay_export.csv"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text("asset,amount\nFUND001,100\n", encoding="utf-8")
    expected_hash = hashlib.sha256(evidence_file.read_bytes()).hexdigest()

    _write_csv(
        settings.imports_dir / "alipay_positions.csv",
        [
            "asset_code",
            "asset_name",
            "platform",
            "current_amount",
            "current_weight",
            "cost_basis",
            "unrealized_pnl",
            "as_of",
            "source_note",
        ],
        [
            {
                "asset_code": "FUND001",
                "asset_name": "AI Infrastructure Growth Fund",
                "platform": "Alipay",
                "current_amount": "100",
                "current_weight": "100%",
                "cost_basis": "90",
                "unrealized_pnl": "10",
                "as_of": "2026-06-12",
                "source_note": f"Alipay export; evidence={evidence_file}",
            }
        ],
    )
    _write_csv(
        settings.manual_dir / "fund_rules.csv",
        [
            "asset_code",
            "subscription_status",
            "redemption_status",
            "cutoff_time",
            "confirm_lag",
            "redeem_lag",
            "subscription_fee",
            "redemption_fee",
            "management_fee",
            "custody_fee",
            "sales_service_fee",
            "min_purchase_amount",
            "source_name",
            "source_type",
            "source_priority",
            "url_or_path",
            "evidence_level",
            "fallback_aggregated",
            "as_of",
        ],
        [
            {
                "asset_code": "FUND001",
                "subscription_status": "open",
                "redemption_status": "open",
                "cutoff_time": "15:00",
                "confirm_lag": "T+1",
                "redeem_lag": "T+3",
                "subscription_fee": "0.001",
                "redemption_fee": "0.005",
                "management_fee": "0.012",
                "custody_fee": "0.002",
                "sales_service_fee": "0",
                "min_purchase_amount": "10",
                "source_name": "Alipay fund rule page",
                "source_type": "alipay",
                "source_priority": "2",
                "url_or_path": "https://example.com/fund001/rules",
                "evidence_level": "Strong",
                "fallback_aggregated": "false",
                "as_of": "2026-06-12",
            }
        ],
    )
    _write_csv(
        settings.manual_dir / "candidates.csv",
        [
            "asset_code",
            "asset_name",
            "asset_type",
            "market",
            "fund_company",
            "risk_level",
            "theme",
            "is_off_platform_fund",
            "is_excluded",
            "exclusion_reason",
            "official_source_count",
            "fallback_aggregated",
            "evidence_level",
            "source_name",
            "source_type",
            "source_url",
            "missing_nav_days",
            "missing_holding_days",
            "conflict_flag",
            "as_of",
        ],
        [
            {
                "asset_code": "FUND001",
                "asset_name": "AI Infrastructure Growth Fund",
                "asset_type": "off_platform_fund",
                "market": "CN/US",
                "fund_company": "Verified Fund Co",
                "risk_level": "high",
                "theme": "AI infrastructure",
                "is_off_platform_fund": "true",
                "is_excluded": "false",
                "exclusion_reason": "",
                "official_source_count": "2",
                "fallback_aggregated": "false",
                "evidence_level": "Strong",
                "source_name": "Fund company official page",
                "source_type": "official",
                "source_url": str(evidence_file),
                "missing_nav_days": "0",
                "missing_holding_days": "0",
                "conflict_flag": "false",
                "as_of": "2026-06-12",
            }
        ],
    )

    result = build_source_evidence_audit(settings)

    assert result["status"] == "pass"
    assert result["invalid_count"] == 0
    assert result["db_rows_written"] == result["row_count"]
    assert result["local_hashed_count"] == 1
    csv_text = Path(result["files"]["csv"]).read_text(encoding="utf-8")
    assert expected_hash in csv_text
    assert "valid_url" in csv_text
    with connect(settings.db_path) as conn:
        db_count = conn.execute(
            "SELECT count(*) FROM source_evidence_audit_snapshot WHERE audit_run_id=?",
            (result["audit_run_id"],),
        ).fetchone()[0]
    assert db_count == result["row_count"]


def test_source_evidence_audit_blocks_sample_references(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    rules_path = settings.manual_dir / "fund_rules.csv"
    rules_text = rules_path.read_text(encoding="utf-8")
    rules_path.write_text(rules_text.replace("https://", "REPLACE_https://", 1), encoding="utf-8")

    result = build_source_evidence_audit(settings)

    assert result["status"] == "blocked"
    assert result["invalid_count"] > 0
    assert result["db_rows_written"] == result["row_count"]
    csv_text = Path(result["files"]["csv"]).read_text(encoding="utf-8")
    assert "placeholder_reference" in csv_text


def test_source_evidence_audit_resolves_pack_relative_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)
    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    evidence_dir = pack_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    evidence_file = evidence_dir / "fund_rules_2026-06-12.csv"
    evidence_file.write_text("asset,amount\nFUND001,100\n", encoding="utf-8")
    expected_hash = hashlib.sha256(evidence_file.read_bytes()).hexdigest()

    _write_csv(
        pack_dir / "02_fund_rules_to_fill.csv",
        [
            "asset_code",
            "subscription_status",
            "redemption_status",
            "cutoff_time",
            "confirm_lag",
            "redeem_lag",
            "subscription_fee",
            "redemption_fee",
            "management_fee",
            "custody_fee",
            "sales_service_fee",
            "min_purchase_amount",
            "source_name",
            "source_type",
            "source_priority",
            "url_or_path",
            "evidence_level",
            "fallback_aggregated",
            "as_of",
        ],
        [
            {
                "asset_code": "FUND001",
                "subscription_status": "open",
                "redemption_status": "open",
                "cutoff_time": "15:00",
                "confirm_lag": "T+1",
                "redeem_lag": "T+3",
                "subscription_fee": "0.001",
                "redemption_fee": "0.005",
                "management_fee": "0.012",
                "custody_fee": "0.002",
                "sales_service_fee": "0",
                "min_purchase_amount": "10",
                "source_name": "Fund company official rule page",
                "source_type": "official",
                "source_priority": "3",
                "url_or_path": "evidence/fund_rules_2026-06-12.csv",
                "evidence_level": "Strong",
                "fallback_aggregated": "false",
                "as_of": "2026-06-12",
            }
        ],
    )
    _write_csv(
        pack_dir / "03_candidates_to_fill.csv",
        [
            "asset_code",
            "asset_name",
            "asset_type",
            "market",
            "fund_company",
            "risk_level",
            "theme",
            "is_off_platform_fund",
            "is_excluded",
            "exclusion_reason",
            "official_source_count",
            "fallback_aggregated",
            "evidence_level",
            "source_name",
            "source_type",
            "source_url",
            "missing_nav_days",
            "missing_holding_days",
            "conflict_flag",
            "as_of",
        ],
        [],
    )

    result = build_source_evidence_audit(settings, pack_dir=pack_dir)

    assert result["status"] == "pass"
    assert result["local_hashed_count"] == 1
    csv_text = Path(result["files"]["csv"]).read_text(encoding="utf-8")
    assert expected_hash in csv_text
