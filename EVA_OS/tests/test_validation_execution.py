from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from quantlab.data.validation import CrossSourceValidationResult
from quantlab.research import build_validation_task_execution, write_validation_task_execution


def test_validation_task_execution_runs_cross_source_and_writes_outputs(tmp_path: Path) -> None:
    queue_path = _queue(tmp_path)

    result = CrossSourceValidationResult(
        symbol="AAPL",
        market="US",
        interval="1d",
        providers=("Yahoo Finance", "Polygon"),
        overlap_rows=3,
        max_close_diff_pct=0.002,
        mean_close_diff_pct=0.001,
        status="Pass",
        details=pd.DataFrame({"datetime": pd.date_range("2024-01-01", periods=3), "Yahoo Finance": [1, 2, 3], "Polygon": [1, 2, 3]}),
    )

    with (
        patch("quantlab.research.validation_execution._default_providers_for_market", return_value=["Yahoo Finance", "Polygon"]),
        patch("quantlab.research.validation_execution.validate_close_across_sources", return_value=result),
    ):
        payload = write_validation_task_execution(
            as_of="2026-06-07",
            project_root=tmp_path,
            queue_path=queue_path,
            output_dir=tmp_path / "validationQueue",
        )

    assert payload["schema"] == "QuantLabValidationTaskExecutionV1"
    assert payload["execution_status"] == "Pass"
    assert payload["evidence_status"] == "EvidenceAvailable"
    assert payload["providers_used"] == ["Yahoo Finance", "Polygon"]
    assert payload["result"]["overlap_rows"] == 3
    assert Path(payload["cross_validation_report_path"]).exists()
    assert json.loads(queue_path.read_text(encoding="utf-8"))[0]["status"] == "待验证"
    assert Path(payload["outputs"]["json"]).exists()
    assert Path(payload["outputs"]["csv"]).exists()
    assert Path(payload["outputs"]["markdown"]).exists()
    assert Path(payload["outputs"]["pdf"]).read_bytes().startswith(b"%PDF-1.4")


def test_validation_task_execution_blocks_when_provider_coverage_is_insufficient(tmp_path: Path) -> None:
    queue_path = _queue(tmp_path)

    with patch("quantlab.research.validation_execution._default_providers_for_market", return_value=["Yahoo Finance"]):
        payload = build_validation_task_execution(
            as_of="2026-06-07",
            project_root=tmp_path,
            queue_path=queue_path,
        )

    assert payload["execution_status"] == "Blocked"
    assert payload["evidence_status"] == "NeedsMoreEvidence"
    assert "at_least_two_real_providers_required" in payload["blockers"]
    assert payload["result_status"] == "NotRun"


def _queue(tmp_path: Path) -> Path:
    path = tmp_path / "ValidationTasks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "task_id": "reportGapTask_aapl",
                    "created_at": "2026-06-07T09:00:00",
                    "status": "待验证",
                    "evidence_gap": "CrossSourceValidation",
                    "research_topic": "补齐报告证据：RunMetadata_07062026 / CrossSourceValidation",
                    "symbol": "AAPL",
                    "market": "US",
                    "signal_to_validate": "补跑多源交叉校验，比较至少两个可用真实数据源的关键价格。",
                    "source_report": "SampleBacktestReport_07062026.docx",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path
