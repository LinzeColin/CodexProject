from __future__ import annotations

from hashlib import sha256
from typing import Mapping


STAGE12_REVIEW_DIMENSIONS = (
    "参数",
    "分类",
    "标签",
    "图表",
    "diff",
    "Interconnection",
)

STAGE12_REQUIRED_TRI_BASE_TERMS = (
    "参数中心",
    "标签系统",
    "Interconnection 可视化",
    "双消费口径",
    "现金流图表",
    "diff ticket",
    "公式",
    "阈值",
    "评分",
    "分类",
    "可视化规则",
)

STAGE12_FINAL_ARTIFACTS = (
    "PFI/模型参数文件.md",
    "PFI/config/pfi_v022_parameters.yaml",
    "PFI/docs/pfi_v022/INTERCONNECTION_MAP.md",
    "PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md",
    "PFI/web/pfi_v022_logic_review.html",
    "PFI/src/pfi_v02/stage_v022_tags_views.py",
    "PFI/src/pfi_v02/stage_v022_runtime_diff.py",
    "PFI/tests/test_v022_stage12_delivery.py",
    "PFI/docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/reports/pfi_v022_summary.md",
)

STAGE12_SIX_AGENT_NAMES = (
    "Agent 1 金融事实层与口径",
    "Agent 2 数据源、账户角色与 Interconnection",
    "Agent 3 参数、公式、阈值与中文解释",
    "Agent 4 消费、投资与现金流模型",
    "Agent 5 UI/UX、可视化与中文可读性",
    "Agent 6 测试、Runtime Diff 与 LLM Agent Trigger",
)


def _stable_hash(value: object) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


def build_stage12_delivery_payload(catalog: Mapping[str, object] | None = None) -> dict[str, object]:
    catalog_schema = catalog.get("schema") if catalog else None
    tri_base_documents = (
        {
            "task_id": "S12-P1-T1",
            "path": "PFI/模型参数文件.md",
            "required_terms": STAGE12_REQUIRED_TRI_BASE_TERMS,
            "status": "updated",
        },
        {
            "task_id": "S12-P1-T2",
            "path": "PFI/功能清单.md",
            "required_terms": (
                "参数中心",
                "标签系统",
                "Interconnection 可视化",
                "双消费口径",
                "现金流图表",
                "diff ticket",
            ),
            "status": "updated",
        },
        {
            "task_id": "S12-P1-T3",
            "path": "PFI/开发记录.md",
            "required_terms": ("完成任务", "变更文件", "测试结果", "未完成项", "下轮建议"),
            "status": "updated",
        },
    )
    issues = (
        {"round": 1, "agent": STAGE12_SIX_AGENT_NAMES[0], "issue": "投资入金和基金申购口径需要在最终摘要显式保留。", "status": "已修复"},
        {"round": 1, "agent": STAGE12_SIX_AGENT_NAMES[2], "issue": "参数、公式、阈值、评分需要在三基文件中成组呈现。", "status": "已修复"},
        {"round": 1, "agent": STAGE12_SIX_AGENT_NAMES[4], "issue": "审查 HTML 不能替代主 Web Shell，也不能污染正式运行页面。", "status": "已修复"},
        {"round": 2, "agent": STAGE12_SIX_AGENT_NAMES[1], "issue": "确认 Interconnection Map/Matrix 与 Runtime Diff 记录均可追溯。", "status": "非阻塞"},
        {"round": 2, "agent": STAGE12_SIX_AGENT_NAMES[5], "issue": "确认 Stage 12 只交付文档和本地审查页，不提前执行 Stage 13。", "status": "已修复"},
    )
    return {
        "schema": "PFIV022Stage12DeliveryPayloadV1",
        "catalog_schema": catalog_schema,
        "tri_base_documents": tri_base_documents,
        "review_html": {
            "task_id": "S12-P2-T1",
            "path": "PFI/web/pfi_v022_logic_review.html",
            "language": "zh-CN",
            "dimensions": STAGE12_REVIEW_DIMENSIONS,
            "clickable_sections": 7,
            "main_shell_mutation": False,
        },
        "roadmap_validation": {
            "task_id": "S12-P2-T2",
            "path": "PFI/docs/pfi_v022/STAGE12_DELIVERY_REPORT.md",
            "structure": "Stage -> Phase -> Task",
            "milestone_list_rejected": True,
        },
        "final_summary": {
            "task_id": "S12-P2-T3",
            "path": "PFI/reports/pfi_v022_summary.md",
            "language": "zh-CN",
            "includes_done": True,
            "includes_validation": True,
            "includes_not_done": True,
            "includes_manual_review": True,
        },
        "roadmap_structure": "Stage -> Phase -> Task",
        "milestone_list_rejected": True,
        "six_agent_review": {
            "path": "PFI/docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md",
            "round_count": 2,
            "agents": STAGE12_SIX_AGENT_NAMES,
            "issues": issues,
            "blocking_issue_count": sum(1 for item in issues if item["status"] == "阻塞"),
        },
        "final_artifacts": STAGE12_FINAL_ARTIFACTS,
        "delivery_hash": _stable_hash((catalog_schema, STAGE12_FINAL_ARTIFACTS, STAGE12_REVIEW_DIMENSIONS)),
        "stage12_ready_for_stage13": True,
    }
