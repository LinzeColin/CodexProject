from pathlib import Path

from app.core.notification import notify_run
from app.core.pipeline import import_alipay_csv, run_slot
from app.db import connect
from tests.helpers import copy_sample_data, temp_settings


def test_full_local_smoke_creates_db_report_notification_and_comparisons(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    imported = import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    assert imported["rows"] == 4

    first = run_slot(settings, "R6", dry_run=True)
    second = run_slot(settings, "R7", dry_run=True)
    notified = notify_run(settings, second["run_id"], dry_run=True)

    assert Path(second["report_path"]).exists()
    assert Path(second["offline_html_path"]).exists()
    assert Path(second["offline_index_path"]).exists()
    assert Path(notified["draft_path"]).exists()
    report_text = Path(second["report_path"]).read_text(encoding="utf-8")
    assert "## 运行状态" in report_text
    assert "数据质量：" in report_text
    assert "建议金额：0.00" in report_text
    assert "建议份额：0" in report_text
    assert "执行状态" in report_text
    assert "Execution lock" not in report_text

    with connect(settings.db_path) as conn:
        first_recs = conn.execute(
            "SELECT asset_id, target_weight, current_weight FROM recommendation_snapshot WHERE run_id=?",
            (first["run_id"],),
        ).fetchall()
        second_recs = conn.execute(
            "SELECT asset_id, target_weight, current_weight FROM recommendation_snapshot WHERE run_id=?",
            (second["run_id"],),
        ).fetchall()
        first_baseline = {
            row["asset_id"]: float(row["baseline_weight"])
            for row in conn.execute("SELECT asset_id, baseline_weight FROM baseline_snapshot WHERE run_id=?", (first["run_id"],))
        }
        comparisons = conn.execute(
            "SELECT COUNT(*) AS n FROM comparison_snapshot WHERE run_id=?",
            (second["run_id"],),
        ).fetchone()["n"]
        notifications = conn.execute(
            "SELECT COUNT(*) AS n FROM notification_log WHERE run_id=?",
            (second["run_id"],),
        ).fetchone()["n"]
    assert first_recs
    assert all(float(row["current_weight"] or 0.0) == 0.0 for row in first_recs)
    assert first_baseline
    for row in second_recs:
        assert float(row["current_weight"] or 0.0) == first_baseline.get(row["asset_id"], 0.0)
    assert comparisons > 0
    assert notifications > 0
