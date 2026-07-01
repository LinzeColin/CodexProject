from app.models.schemas import ModuleType
from app.services.analysis import analyze_case


def test_dynamic_analysis_generates_visualizations_without_model_key():
    result = analyze_case(
        ModuleType.dynamic,
        {
            "centerline_offset": 3.8,
            "ovality": 0.026,
            "eccentricity": 0.013,
            "runout": 1.5,
            "temperature": 420,
            "rotation_speed": 2.2,
        },
        [],
    )

    assert result["module"] == "dynamic"
    assert result["risk_score"] > 0
    assert result["model_status"]["provider"] == "offline_rules"
    assert len(result["visualizations"]) >= 3


def test_machining_analysis_returns_process_plan():
    result = analyze_case(
        ModuleType.machining,
        {
            "material": "42CrMo",
            "diameter": 3200,
            "length": 7800,
            "tolerance": 0.04,
            "process_type": "turning",
        },
        [],
    )

    assert "8m 数控立车" in result["metrics"]["machine"]
    assert result["risk_level"] in {"normal", "warning", "critical"}
    assert any("推荐工艺路线" in item for item in result["suggestions"])

