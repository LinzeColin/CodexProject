from __future__ import annotations

from pathlib import Path
import csv

from app.core.fund_nav_history_collector import collect_fund_nav_history
from app.core.intake_validator import validate_intake
from app.core.preflight import _check_candidate_nav_history
from tests.helpers import copy_sample_data, temp_settings


def test_collect_fund_nav_history_applies_24_month_rows_and_backup(tmp_path: Path, monkeypatch):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    def fake_fetch(asset_code: str, start_date: str, end_date: str, timeout_seconds: float, **kwargs):
        rows = [
            {"FSRQ": "2024-06-01", "DWJZ": "1.0000", "LJJZ": "1.0000"},
            {"FSRQ": "2025-06-01", "DWJZ": "1.2000", "LJJZ": "1.2000"},
            {"FSRQ": "2026-06-12", "DWJZ": "1.5000", "LJJZ": "1.5000"},
        ]
        return rows, f"https://api.example.test/nav?fundCode={asset_code}"

    monkeypatch.setattr("app.core.fund_nav_history_collector._fetch_eastmoney_nav", fake_fetch)

    result = collect_fund_nav_history(settings, asset_codes=["008887"], apply=True)

    assert result["status"] == "pass"
    assert result["applied"] is True
    assert result["backup_path"]
    text = (settings.manual_dir / "price_history.csv").read_text(encoding="utf-8")
    assert "source_name,source_type,source_priority,url_or_path,evidence_level,as_of" in text
    assert "008887,2024-06-01,1.0" in text


def test_candidate_nav_history_validation_blocks_short_history(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    with (settings.manual_dir / "price_history.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
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
        )
        writer.writeheader()
        for code in ["008887", "011839", "110026", "007300", "270042", "018043", "013171"]:
            writer.writerow(
                {
                    "asset_code": code,
                    "date": "2026-01-01",
                    "close": "1.0",
                    "source_name": "test",
                    "source_type": "official",
                    "source_priority": "3",
                    "url_or_path": "https://example.com/nav",
                    "evidence_level": "Strong",
                    "as_of": "2026-06-12",
                }
            )

    result = validate_intake(settings)

    assert result["production_ready"] is False
    assert any(
        gap["area"] == "candidate_nav_history" and gap["field"] == "date_span"
        for gap in result["gaps"]
    )


def test_candidate_nav_history_preflight_passes_after_collect(tmp_path: Path, monkeypatch):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    def fake_fetch(asset_code: str, start_date: str, end_date: str, timeout_seconds: float, **kwargs):
        return [
            {"FSRQ": "2024-06-01", "DWJZ": "1.0000", "LJJZ": "1.0000"},
            {"FSRQ": "2025-06-01", "DWJZ": "1.2000", "LJJZ": "1.2000"},
            {"FSRQ": "2026-06-12", "DWJZ": "1.5000", "LJJZ": "1.5000"},
        ], f"https://api.example.test/nav?fundCode={asset_code}"

    monkeypatch.setattr("app.core.fund_nav_history_collector._fetch_eastmoney_nav", fake_fetch)
    collect_fund_nav_history(settings, apply=True)

    result = _check_candidate_nav_history(settings)

    assert result.status == "pass"


def test_collect_fund_nav_history_does_not_apply_when_blocked(tmp_path: Path, monkeypatch):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    before = (settings.manual_dir / "price_history.csv").read_text(encoding="utf-8")

    def fake_fetch(asset_code: str, start_date: str, end_date: str, timeout_seconds: float, **kwargs):
        return [], f"https://api.example.test/nav?fundCode={asset_code}"

    monkeypatch.setattr("app.core.fund_nav_history_collector._fetch_eastmoney_nav", fake_fetch)

    result = collect_fund_nav_history(settings, asset_codes=["008887"], apply=True)

    assert result["status"] == "blocked"
    assert result["applied"] is False
    assert result["apply_requested"] is True
    assert (settings.manual_dir / "price_history.csv").read_text(encoding="utf-8") == before
