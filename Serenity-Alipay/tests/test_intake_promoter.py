from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.intake_promoter import promote_intake_pack
from app.core.production_intake_pack import build_production_intake_pack
from tests.helpers import copy_sample_data, temp_settings


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_fund001_price_history(path: Path) -> None:
    start = datetime(2024, 1, 1).date()
    _write_csv(
        path,
        [
            "asset_code",
            "date",
            "close",
            "source_name",
            "source_type",
            "source_priority",
            "url_or_path",
            "evidence_level",
            "as_of",
        ],
        [
            {
                "asset_code": "FUND001",
                "date": (start + timedelta(days=idx)).isoformat(),
                "close": f"{1.0 + idx * 0.001:.4f}",
                "source_name": "test official NAV",
                "source_type": "official",
                "source_priority": "3",
                "url_or_path": "https://example.com/fund001/nav",
                "evidence_level": "Strong",
                "as_of": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
            }
            for idx in range(760)
        ],
    )


def _fill_pack_with_production_like_data(pack_dir: Path) -> None:
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    evidence_dir = pack_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "alipay_current_holding_evidence.txt"
    evidence_file.write_text("verified test evidence", encoding="utf-8")
    alipay_fields = [
        "asset_code",
        "asset_name",
        "platform",
        "current_amount",
        "current_weight",
        "cost_basis",
        "unrealized_pnl",
        "as_of",
        "source_note",
    ]
    _write_csv(
        pack_dir / "01_alipay_positions_to_fill.csv",
        alipay_fields,
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
                "source_note": f"Alipay verified export {today}; evidence=evidence/alipay_current_holding_evidence.txt",
            }
        ],
    )
    fund_fields = [
        "asset_code",
        "subscription_status",
        "redemption_status",
        "cutoff_time",
        "confirm_lag",
        "redeem_lag",
        "subscription_fee",
        "redemption_fee",
        "subscription_fee_schedule",
        "redemption_fee_schedule",
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
        "fee_schedule_as_of",
        "fee_schedule_note",
    ]
    _write_csv(
        pack_dir / "02_fund_rules_to_fill.csv",
        fund_fields,
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
                "subscription_fee_schedule": "M<100万元 0.10%",
                "redemption_fee_schedule": "N<7天 0.50%；N>=7天 0.00%",
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
                "as_of": today,
                "fee_schedule_as_of": today,
                "fee_schedule_note": "test fee schedule",
            }
        ],
    )
    candidate_fields = [
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
    ]
    _write_csv(
        pack_dir / "03_candidates_to_fill.csv",
        candidate_fields,
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


def test_promote_intake_pack_blocks_placeholders(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_fund001_price_history(settings.manual_dir / "price_history.csv")
    build_production_intake_pack(settings)

    result = promote_intake_pack(settings, apply=True)

    assert result["placeholder_blocked"] is True
    assert result["applied"] is False
    assert result["production_ready"] is False
    assert result["issues"]
    promotion_md = settings.root_dir / "outputs" / "intake_pack" / "promotion_latest.md"
    assert str(settings.root_dir) not in promotion_md.read_text(encoding="utf-8")


def test_promote_intake_pack_apply_copies_after_validation(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_fund001_price_history(settings.manual_dir / "price_history.csv")
    build_production_intake_pack(settings)
    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    _fill_pack_with_production_like_data(pack_dir)

    dry_run = promote_intake_pack(settings, apply=False)
    assert dry_run["placeholder_blocked"] is False
    assert dry_run["production_ready"] is True
    assert dry_run["applied"] is False

    applied = promote_intake_pack(settings, apply=True)
    assert applied["applied"] is True
    assert applied["production_ready"] is True
    assert applied["copy_result"]["backup_dir"]
    assert applied["copy_result"]["evidence_copied"]
    assert (settings.root_dir / "evidence" / "alipay_current_holding_evidence.txt").exists()
    assert (settings.imports_dir / "alipay_positions.csv").read_text(encoding="utf-8").find("Alipay verified export") == -1
    assert (settings.manual_dir / "fund_rules.csv").read_text(encoding="utf-8").find("Alipay fund rule page") >= 0
    promotion_md = settings.root_dir / "outputs" / "intake_pack" / "promotion_latest.md"
    assert str(settings.root_dir) not in promotion_md.read_text(encoding="utf-8")
