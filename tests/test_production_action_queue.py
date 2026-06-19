from pathlib import Path
from csv import DictWriter
from datetime import date, timedelta

from app.core.production_action_queue import build_production_action_queue
from tests.helpers import copy_sample_data, temp_settings


def test_production_action_queue_writes_fail_closed_prioritized_rows(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    rules_path = settings.manual_dir / "fund_rules.csv"
    rules_text = rules_path.read_text(encoding="utf-8")
    rules_path.write_text(rules_text.replace("https://", "REPLACE_https://", 1), encoding="utf-8")

    result = build_production_action_queue(settings)

    assert result["production_ready"] is False
    assert result["no_new_order"] is True
    assert result["status"] == "blocked"
    assert result["row_count"] > 0
    assert result["priority_counts"]["P0"] > 0
    assert result["blocker_counts"]["fund_rules"] > 0

    md_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.md"
    csv_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.csv"
    json_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.json"
    assert md_path.exists()
    assert csv_path.exists()
    assert json_path.exists()

    md_text = md_path.read_text(encoding="utf-8")
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "No-New-Order" in md_text
    assert "does not place trades" in md_text
    assert "does not send email" in md_text
    assert "does not unlock production" in md_text
    assert "outputs/intake_pack/01_alipay_positions_to_fill.csv" not in csv_text
    assert "outputs/intake_pack/02_fund_rules_to_fill.csv" in csv_text
    assert "/Users/" not in md_text
    assert "/Users/" not in csv_text


def test_production_action_queue_tracks_benchmark_source_priority_per_index(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    history_path = settings.manual_dir / "benchmark_price_history.csv"
    rows = []
    start = date(2026, 3, 1)
    for code, source_type, source_priority in [
        ("000001.SH", "public_aggregation", "5"),
        ("SPX", "official_index_provider", "3"),
    ]:
        for offset in range(0, 100, 2):
            rows.append(
                {
                    "asset_code": code,
                    "date": (start + timedelta(days=offset)).isoformat(),
                    "close": str(4000 + offset),
                    "source_name": "test source",
                    "source_type": source_type,
                    "source_priority": source_priority,
                    "url_or_path": "https://example.com",
                    "evidence_level": "High",
                    "as_of": "2026-06-12",
                }
            )
    with history_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = build_production_action_queue(settings)

    csv_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.csv"
    csv_text = csv_path.read_text(encoding="utf-8")
    assert result["blocker_counts"]["benchmark_source_priority"] == 1
    assert "000001.SH" in csv_text
    assert "SPX,S&P 500" not in csv_text
