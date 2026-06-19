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
    WorkspaceContract("home", "首页", "Daily brief, blockers, freshness, and next work.", "daily_brief", "overview"),
    WorkspaceContract("market", "市场", "Market breadth, themes, catalysts, and watchlist context.", "market_events", "overview"),
    WorkspaceContract("research", "研究", "Research library, evidence, policy, companies, funds, and estimates.", "research_queue", "evidence"),
    WorkspaceContract("portfolio", "持仓", "Portfolio exposure, attribution, risk, discipline, and decision queue.", "portfolio_risk", "review"),
    WorkspaceContract("strategy", "策略实验室", "Backtests, parameter scans, validation, simulation, and training mode.", "strategy_runs", "experiment"),
    WorkspaceContract("data", "数据与系统", "Sources, jobs, quality, lineage, privacy, backup, and diagnostics.", "data_freshness", "diagnostics"),
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
    "Evidence",
    "Source",
    "Model",
    "Parameters",
    "Data lineage",
    "Raw document",
)

FEEDBACK_SLA = (
    FeedbackContract(100, "instant", "pressed, focus, disabled, or local state feedback"),
    FeedbackContract(300, "cached", "page switch or cached result without full reload"),
    FeedbackContract(301, "loading", "skeleton for work taking more than 300ms"),
    FeedbackContract(1000, "stepped", "explicit step, progress, and current phase"),
    FeedbackContract(10000, "background", "background job id with leave-page-safe progress"),
)


def build_web_shell_contract() -> WebShellContract:
    return WebShellContract(
        schema="PFIOSWebShellContractV1",
        feature_flag="PFI_UI_V2",
        fallback_value="0",
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
