from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WorkspaceContract:
    workspace_id: str
    label: str
    purpose: str
    cached_home_slice: str
    primary_state: str


@dataclass(frozen=True)
class FeedbackContract:
    threshold_ms: int
    state: str
    required_ui: str


@dataclass(frozen=True)
class WebShellContract:
    schema: str
    feature_flag: str
    fallback_value: str
    primary_workspaces: tuple[WorkspaceContract, ...]
    global_context_fields: tuple[str, ...]
    evidence_drawer_sections: tuple[str, ...]
    feedback_sla: tuple[FeedbackContract, ...]
    safety_boundary: str
    cached_home_target_seconds: int

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "primary_workspaces": [asdict(item) for item in self.primary_workspaces],
            "feedback_sla": [asdict(item) for item in self.feedback_sla],
        }


PRIMARY_WORKSPACES = (
    WorkspaceContract("home", "首页", "今日简报、阻塞项、数据新鲜度和下一步任务。", "daily_brief", "overview"),
    WorkspaceContract("market", "市场", "市场宽度、主题、催化、自选监控和来源状态。", "market_events", "overview"),
    WorkspaceContract("research", "研究", "研究库、证据、政策、公司、基金和估值线索。", "research_queue", "evidence"),
    WorkspaceContract("portfolio", "持仓", "组合暴露、归因、风险、纪律和决策队列。", "portfolio_risk", "review"),
    WorkspaceContract("strategy", "策略实验室", "回测、参数扫描、验证、模拟和盘感训练。", "strategy_runs", "experiment"),
    WorkspaceContract("data", "数据与系统", "来源、任务、质量、血缘、隐私、备份和诊断。", "data_freshness", "diagnostics"),
)

GLOBAL_CONTEXT_FIELDS = (
    "market",
    "entity",
    "portfolio",
    "as_of",
    "currency",
    "freshness",
    "research_task",
    "evidence_set",
    "simulation_scenario",
)

EVIDENCE_DRAWER_SECTIONS = (
    "证据",
    "来源",
    "模型",
    "参数",
    "数据血缘",
    "原始记录",
)

FEEDBACK_SLA = (
    FeedbackContract(100, "instant", "按下、聚焦、禁用或本地状态反馈"),
    FeedbackContract(300, "cached", "不刷新整页的工作区切换或缓存结果"),
    FeedbackContract(301, "loading", "超过 300ms 的任务显示骨架态"),
    FeedbackContract(1000, "stepped", "展示明确步骤、进度和当前阶段"),
    FeedbackContract(10000, "background", "展示可离页的后台任务编号和进度"),
)


def build_web_shell_contract() -> WebShellContract:
    return WebShellContract(
        schema="PFIOSWebShellContractV1",
        feature_flag="PFI_UI_V2",
        fallback_value="1",
        primary_workspaces=PRIMARY_WORKSPACES,
        global_context_fields=GLOBAL_CONTEXT_FIELDS,
        evidence_drawer_sections=EVIDENCE_DRAWER_SECTIONS,
        feedback_sla=FEEDBACK_SLA,
        safety_boundary=(
            "Local-first decision support shell; no live automatic orders, broker submission, "
            "payments, betting, unattended execution, or private-data commit path."
        ),
        cached_home_target_seconds=2,
    )
