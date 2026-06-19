from pathlib import Path
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.intake_validator import validate_intake
from tests.helpers import copy_sample_data, temp_settings


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_validate_intake_writes_gap_reports_for_sample_data(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = validate_intake(settings)

    assert result["production_ready"] is True
    assert result["block_count"] == 0
    assert result["warn_count"] > 0
    areas = {gap["area"] for gap in result["gaps"]}
    assert "alipay_positions" in areas
    assert "benchmark_history" in areas
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["csv_path"]).exists()


def test_validate_intake_blocks_unverifiable_source_references(tmp_path: Path):
    settings = temp_settings(tmp_path)
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    evidence = settings.root_dir / "evidence" / "alipay_export.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("verified alipay evidence", encoding="utf-8")

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
                "current_amount": "10000",
                "current_weight": "100%",
                "cost_basis": "9500",
                "unrealized_pnl": "500",
                "as_of": today,
                "source_note": f"Alipay verified export; evidence={evidence}",
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
                "url_or_path": "not-a-real-source-file",
                "evidence_level": "Strong",
                "fallback_aggregated": "false",
                "as_of": today,
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
                "source_name": "Fund company official page and Alipay detail",
                "source_type": "official",
                "source_url": "https://example.com/fund001",
                "missing_nav_days": "0",
                "missing_holding_days": "0",
                "conflict_flag": "false",
                "as_of": today,
            }
        ],
    )

    result = validate_intake(settings)

    assert result["production_ready"] is False
    assert any(
        gap["area"] == "fund_rules" and gap["field"] == "url_or_path" and "not verifiable" in gap["message"]
        for gap in result["gaps"]
    )
