from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_REPORT = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE1_REVIEW_20260628.md"

STAGE1_TASK_IDS = (
    "S1-P1-T1",
    "S1-P1-T2",
    "S1-P1-T3",
    "S1-P2-T1",
    "S1-P2-T2",
    "S1-P2-T3",
)

REQUIRED_DOMAINS = (
    "货币",
    "汇率",
    "时间",
    "数据源",
    "账户角色",
    "事件类型",
    "Interconnection",
    "消费分类",
    "标签",
    "置信度",
    "消费模型",
    "投资模型",
    "现金流",
    "可视化",
    "测试",
)

STOP_CONDITIONS = (
    "参数仍散落在代码和文档中时停止",
    "Markdown 和 YAML 不一致时停止",
    "核心阈值多处不一致时停止",
    "只有英文变量或代码名时停止",
    "阈值无解释时停止",
    "用户看不懂变量含义时停止",
)


def test_stage1_review_report_covers_roadmap_acceptance_and_stop_conditions() -> None:
    text = REVIEW_REPORT.read_text(encoding="utf-8")

    assert "v0.2.2 Stage 1 复审" in text
    assert "本轮只复审解决 Stage 1" in text
    assert "不复审 Stage 2-13" in text
    assert "补齐 3 个阈值/开关键说明" in text
    assert "复审结论：通过" in text
    assert "上线阻塞项：0" in text

    for task_id in STAGE1_TASK_IDS:
        assert task_id in text
    for domain in REQUIRED_DOMAINS:
        assert domain in text
    for stop_condition in STOP_CONDITIONS:
        assert stop_condition in text

    required_evidence_terms = (
        "PFI/模型参数文件.md",
        "PFI/config/pfi_parameters.yaml",
        "PFI/tests/test_pfi_parameters_consistency.py",
        "PFI/docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md",
        "build_v022_stage1_contract()",
        "load_v022_parameter_catalog()",
        "验证命令",
        "证据来源",
        "停止条件复核",
        "剩余风险",
    )
    for term in required_evidence_terms:
        assert term in text


def test_stage1_current_parameter_catalog_still_matches_review_requirements() -> None:
    catalog = json.loads((ROOT / "config" / "pfi_parameters.yaml").read_text(encoding="utf-8"))
    parameter_text = (ROOT / "模型参数文件.md").read_text(encoding="utf-8")

    assert catalog["stage1_task_ids"] == list(STAGE1_TASK_IDS)
    domain_text = "\n".join(
        f"{item.get('key', '')} {item.get('label_zh', '')} {item.get('description_zh', '')}"
        for item in catalog["domains"]
    )
    for domain in REQUIRED_DOMAINS:
        assert domain in domain_text
        assert domain in parameter_text

    for formula in catalog["formulas"]:
        for key in ("name_zh", "purpose_zh", "inputs", "outputs", "logic_zh", "example_zh", "variable_aliases"):
            assert formula.get(key), f"{formula.get('formula_id')} missing {key}"
        assert formula["formula_id"] in parameter_text
        assert any("\u4e00" <= char <= "\u9fff" for char in formula["name_zh"])
        assert any("\u4e00" <= char <= "\u9fff" for char in formula["logic_zh"])
        for alias in formula["variable_aliases"].values():
            assert any("\u4e00" <= char <= "\u9fff" for char in alias)

    for threshold in catalog["threshold_index"]:
        for key in ("key", "current_value", "why_zh", "impact_surfaces", "user_editable"):
            assert key in threshold
        assert threshold["key"] in parameter_text
        assert any("\u4e00" <= char <= "\u9fff" for char in threshold["why_zh"])


def test_stage1_review_does_not_redefine_later_stage_completion() -> None:
    text = REVIEW_REPORT.read_text(encoding="utf-8")

    forbidden_phrases = (
        "Stage 2 复审结论：通过",
        "Stage 3 复审结论：通过",
        "Stage 13 复审结论：通过",
        "整体项目复审结论：通过",
        "重装 app 入口已完成",
    )
    for phrase in forbidden_phrases:
        assert phrase not in text
