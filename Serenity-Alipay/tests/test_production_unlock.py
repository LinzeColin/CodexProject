from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import app.core.production_unlock as production_unlock
from app.core.production_intake_pack import build_production_intake_pack
from app.core.production_unlock import run_production_unlock_check
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


def _fill_pack(pack_dir: Path) -> None:
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    evidence_dir = pack_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "alipay_current_holding_evidence.txt"
    evidence_file.write_text("verified current Alipay holding evidence", encoding="utf-8")
    _write_csv(
        pack_dir / "01_alipay_positions_to_fill.csv",
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
                "source_note": "Alipay current page verified; evidence=evidence/alipay_current_holding_evidence.txt",
            }
        ],
    )
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


def test_production_unlock_check_blocks_unfilled_pack_without_apply(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_fund001_price_history(settings.manual_dir / "price_history.csv")
    build_production_intake_pack(settings)

    result = run_production_unlock_check(settings, apply=True)

    assert result["status"] == "blocked"
    assert result["pack_ready_to_apply"] is False
    assert result["apply_performed"] is False
    assert Path(result["json_path"]).exists()
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["source_evidence_audit_pack"]["status"] == "block"
    assert stages["promote_intake_pack_apply"]["status"] == "skipped"
    assert stages["preflight"]["status"] == "skipped"
    assert stages["completion_audit"]["status"] == "skipped"


def test_production_unlock_full_diagnostics_keeps_running_read_only_gates(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    build_production_intake_pack(settings)

    result = run_production_unlock_check(settings, apply=True, full_diagnostics=True, package=True)

    assert result["status"] == "blocked"
    assert result["full_diagnostics"] is True
    assert result["pack_ready_to_apply"] is False
    assert result["apply_performed"] is False
    assert result["stop_reason"] == "pack source evidence audit failed"
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["source_evidence_audit_pack"]["status"] == "block"
    assert stages["promote_intake_pack_apply"]["status"] == "skipped"
    assert stages["preflight"]["status"] == "block"
    assert stages["completion_audit"]["status"] == "block"
    assert stages["package_delivery"]["status"] == "skipped"
    assert stages["package_delivery"]["skipped_reason"] == "pack source evidence audit failed"


def test_production_unlock_keeps_child_preflight_stdout_out_of_json_stream(monkeypatch, capsys, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    build_production_intake_pack(settings)

    def noisy_preflight(settings, scan_paths):
        print("child sdk stdout noise")
        return {
            "production_ready": False,
            "shadow_ready": True,
            "status": "blocked",
            "blockers": [{"name": "alipay_positions"}],
            "warnings": [],
            "json_path": "outputs/preflight/preflight_latest.json",
            "markdown_path": "outputs/preflight/preflight_latest.md",
        }

    monkeypatch.setattr(production_unlock, "run_preflight", noisy_preflight)

    run_production_unlock_check(settings, full_diagnostics=True)

    captured = capsys.readouterr()
    assert "child sdk stdout noise" not in captured.out
    assert "child sdk stdout noise" in captured.err


def test_production_unlock_check_applies_valid_pack_but_keeps_preflight_blocked_by_mail(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_fund001_price_history(settings.manual_dir / "price_history.csv")
    build_production_intake_pack(settings)
    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    _fill_pack(pack_dir)

    result = run_production_unlock_check(settings, apply=True)

    assert result["pack_ready_to_apply"] is True
    assert result["apply_performed"] is True
    assert result["production_ready"] is False
    assert result["stop_reason"] in {"production preflight is still blocked", "completion audit is still blocked"}
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["promote_intake_pack_apply"]["status"] == "pass"
    assert "mail_send_config" in stages["preflight"]["summary"]["blockers"]
