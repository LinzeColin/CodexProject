from __future__ import annotations

from pathlib import Path

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE12_TASK_IDS,
    build_v022_stage12_contract,
    load_v022_parameter_catalog,
)
from pfi_v02.stage_v022_delivery import (
    STAGE12_FINAL_ARTIFACTS,
    STAGE12_REQUIRED_TRI_BASE_TERMS,
    STAGE12_REVIEW_DIMENSIONS,
    build_stage12_delivery_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_stage12_contract_matches_roadmap_scope() -> None:
    contract = build_v022_stage12_contract()

    assert contract["stage"] == "Stage 12"
    assert contract["stage_name_zh"] == "文档同步与交付"
    assert contract["task_ids"] == V022_STAGE12_TASK_IDS
    assert contract["phases"]["Phase 12.1"] == (
        "三基文件更新",
        "S12-P1-T1",
        "S12-P1-T2",
        "S12-P1-T3",
    )
    assert contract["phases"]["Phase 12.2"] == (
        "本地交付物",
        "S12-P2-T1",
        "S12-P2-T2",
        "S12-P2-T3",
    )
    assert "Stage 13 后置触发型复核不在本轮实现。" in contract["non_goals"]
    assert "不修改 v0.2.1 主 Web Shell UIUX 基线。" in contract["non_goals"]


def test_stage12_delivery_payload_covers_all_required_artifacts() -> None:
    payload = build_stage12_delivery_payload(load_v022_parameter_catalog())

    assert payload["schema"] == "PFIV022Stage12DeliveryPayloadV1"
    assert payload["stage12_ready_for_stage13"] is True
    assert payload["roadmap_structure"] == "Stage -> Phase -> Task"
    assert payload["milestone_list_rejected"] is True
    assert payload["final_artifacts"] == STAGE12_FINAL_ARTIFACTS
    assert payload["review_html"]["path"] == "PFI/web/pfi_v022_logic_review.html"
    assert payload["review_html"]["language"] == "zh-CN"
    assert payload["review_html"]["clickable_sections"] >= len(STAGE12_REVIEW_DIMENSIONS)
    assert tuple(payload["review_html"]["dimensions"]) == STAGE12_REVIEW_DIMENSIONS

    six_agent = payload["six_agent_review"]
    assert six_agent["path"] == "PFI/docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md"
    assert six_agent["round_count"] == 2
    assert len(six_agent["agents"]) == 6
    assert all(item["status"] in {"已修复", "非阻塞"} for item in six_agent["issues"])
    assert six_agent["blocking_issue_count"] == 0


def test_stage12_parameter_catalog_records_delivery_gate() -> None:
    catalog = load_v022_parameter_catalog()

    assert catalog["schema"] == "PFIParametersV022Stage12"
    assert catalog["current_stage"] == "Stage 12 - 文档同步与交付"
    assert catalog["stage12_task_ids"] == list(V022_STAGE12_TASK_IDS)
    delivery_params = catalog["parameters"]["delivery"]
    assert delivery_params["roadmap_structure"]["value"] == "Stage -> Phase -> Task"
    assert delivery_params["review_html_path"]["value"] == "PFI/web/pfi_v022_logic_review.html"
    assert delivery_params["final_summary_path"]["value"] == "PFI/reports/pfi_v022_summary.md"
    assert delivery_params["six_agent_review_rounds"]["value"] == 2
    assert delivery_params["six_agent_blocking_issue_count"]["value"] == 0


def test_stage12_tri_base_docs_and_summary_contain_required_terms() -> None:
    docs = (
        "模型参数文件.md",
        "功能清单.md",
        "开发记录.md",
        "docs/pfi_v022/STAGE12_DELIVERY_REPORT.md",
        "docs/pfi_v022/ROADMAP_LOCK.md",
        "reports/pfi_v022_summary.md",
        "HANDOFF.md",
        "README.md",
    )
    required_terms = (
        "Stage 12 - 文档同步与交付",
        "S12-P1-T1",
        "S12-P1-T2",
        "S12-P1-T3",
        "S12-P2-T1",
        "S12-P2-T2",
        "S12-P2-T3",
        "参数中心",
        "标签系统",
        "Interconnection 可视化",
        "双消费口径",
        "现金流图表",
        "diff ticket",
        "Stage -> Phase -> Task",
        "2 轮 × 6 Agent 自检",
        "用户人工复核",
    )
    for path in docs:
        text = read_text(path)
        for term in required_terms:
            assert term in text, f"{path} missing {term}"

    for path in ("模型参数文件.md", "功能清单.md", "开发记录.md"):
        text = read_text(path)
        for term in STAGE12_REQUIRED_TRI_BASE_TERMS:
            assert term in text, f"{path} missing tri-base term {term}"


def test_stage12_review_html_is_chinese_clickable_and_not_main_shell() -> None:
    html = read_text("web/pfi_v022_logic_review.html")

    assert "<html lang=\"zh-CN\">" in html
    assert "PFI v0.2.2 逻辑审查" in html
    assert "Stage 12 - 文档同步与交付" in html
    for dimension in STAGE12_REVIEW_DIMENSIONS:
        assert dimension in html
    for section_id in (
        "parameters",
        "classification",
        "tags",
        "charts",
        "runtime-diff",
        "interconnection",
        "six-agent",
    ):
        assert f"data-section-target=\"{section_id}\"" in html
        assert f"id=\"{section_id}\"" in html
    assert "window.location" not in html
    assert "自动买入" not in html
    assert "自动卖出" not in html
