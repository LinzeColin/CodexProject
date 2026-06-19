from pathlib import Path

from app.core.notification import notify_run
from app.core.pipeline import import_alipay_csv, run_slot
from tests.helpers import copy_sample_data, temp_settings


def test_notify_renders_mail_and_local_scripts(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    result = run_slot(settings, "R7", dry_run=True)
    pipeline_body = Path(result["notification_path"]).read_text(encoding="utf-8")
    pipeline_html_path = Path(result["notification_path"]).with_suffix(".html")
    pipeline_html = pipeline_html_path.read_text(encoding="utf-8")
    assert "## 结论" in pipeline_body
    assert "## 需要你做什么" in pipeline_body
    assert "## 持仓动作清单" in pipeline_body
    assert "## 风控兜底" in pipeline_body
    assert "当前禁止动作：禁止自动下单；必须人工确认" in pipeline_body
    assert "来源与时间戳" not in pipeline_body
    assert "source chain" not in pipeline_body.lower()
    assert "Manual platform confirmation required" not in pipeline_body
    assert pipeline_html_path.exists()
    assert "<!doctype html>" in pipeline_html
    assert "<h1" in pipeline_html
    assert "一、结论" in pipeline_html
    assert "二、需变化的行为" in pipeline_html
    assert "三、当前持仓建议" in pipeline_html
    assert "需操作行为" in pipeline_html
    assert "<table" in pipeline_html
    assert "background-color" in pipeline_html
    assert "运行 ID" not in pipeline_html

    notified = notify_run(settings, result["run_id"], dry_run=True)
    assert Path(notified["draft_path"]).exists()
    assert Path(notified["html_path"]).exists()
    assert Path(notified["local_script_path"]).exists()
    assert notified["send_status"] == "drafted"
    assert "Serenity自动化" in notified["title"]
    body = Path(notified["draft_path"]).read_text(encoding="utf-8")
    assert "## 结论" in body
    assert "## 需要你做什么" in body
    assert "## 持仓动作清单" in body
    assert "## 风控兜底" in body
    assert "- 本轮运行：" in body
    assert " - " in body
    assert "CST" in body
    assert "执行锁：OFF" in body
    assert "当前禁止动作：禁止自动下单；必须人工确认" in body
    assert "来源与时间戳" not in body
    assert "sources_json" not in body
    assert "source chain" not in body.lower()
    assert "Manual platform confirmation required" not in body
    html_body = Path(notified["html_path"]).read_text(encoding="utf-8")
    assert "一、结论" in html_body
    assert "二、需变化的行为" in html_body
    assert "三、当前持仓建议" in html_body
    assert "当前结论" in html_body
    assert "需操作行为" in html_body
    assert "<strong" in html_body
    assert "<em>" in html_body
