from pathlib import Path

from app.core.risk_gate_regression import run_risk_gate_regression
from tests.helpers import temp_settings


def test_risk_gate_regression_writes_repeatable_hard_gate_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)

    result = run_risk_gate_regression(settings)

    assert result["status"] == "pass"
    assert {case["case_id"] for case in result["cases"]} == {"max_drawdown_block", "recovery_time_block"}
    cases = {case["case_id"]: case for case in result["cases"]}
    assert cases["max_drawdown_block"]["score"]["grade"] == "Block"
    assert cases["max_drawdown_block"]["score"]["action_label"] == "Clear"
    assert "max_drawdown" in cases["max_drawdown_block"]["score"]["hard_block_reason"]
    assert cases["recovery_time_block"]["score"]["action_label"] == "Manual Review"
    assert "recovery_time_days" in cases["recovery_time_block"]["score"]["hard_block_reason"]
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["csv_path"]).exists()
