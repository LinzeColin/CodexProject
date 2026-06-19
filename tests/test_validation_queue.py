from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from quantlab.research import (
    create_validation_task,
    load_validation_tasks,
    save_validation_task,
    validation_queue_cards,
    validation_task_frame,
)


def test_validation_queue_persists_tasks_and_cards():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "ValidationTasks.json"
        task = create_validation_task(
            {
                "source_report": "IndustryReport.docx",
                "source_paragraph": "新能源汽车需求可能改善。",
                "research_topic": "验证新能源车链条动量",
                "symbol": "300750.SZ",
                "market": "CN",
                "signal_to_validate": "20 日动量",
                "sample_period": "2020-01-01 to 2026-06-04",
                "cost_assumption": "佣金 0.10%，滑点 5 bps",
                "benchmark": "沪深300",
                "status": "待验证",
            }
        )
        completed = create_validation_task(
            {
                "source_report": "PolicyReport.docx",
                "research_topic": "验证政策催化后表现",
                "symbol": "AAPL",
                "market": "US",
                "status": "已完成",
                "validation_report_path": "/tmp/report.docx",
            }
        )

        save_validation_task(task, path)
        save_validation_task(completed, path)

        tasks = load_validation_tasks(path)
        frame = validation_task_frame(path)
        cards = validation_queue_cards(frame)

        assert len(tasks) == 2
        assert len(frame) == 2
        assert cards[0]["value"] == 2
        assert cards[1]["value"] == 1
        assert cards[2]["value"] == 1


def test_validation_queue_fail_closes_on_corrupt_json():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "ValidationTasks.json"
        path.write_text("{bad json", encoding="utf-8")
        task = create_validation_task({"research_topic": "验证坏文件保护", "status": "待验证"})

        with pytest.raises(ValueError):
            load_validation_tasks(path)
        with pytest.raises(ValueError):
            save_validation_task(task, path)
        assert path.read_text(encoding="utf-8") == "{bad json"
