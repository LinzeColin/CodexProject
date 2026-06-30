from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
STAGE_ID = "Stage 0"
PHASE_ID = "0.1"

OFFICIAL_NAV = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]

FORBIDDEN_FINANCIAL_DATA_LABELS = [
    "mock",
    "sample",
    "demo",
    "synthetic",
    "fixture",
    "fake",
]

DEPRECATED_TOP_LEVEL_ALIASES = [
    "首页",
    "市场",
    "研究",
    "持仓",
    "策略实验室",
    "数据与系统",
]

DATA_STATE_REQUIREMENTS = [
    "confirmed_zero",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "filtered_empty",
    "ready",
]

DEPRECATED_CONSTRAINTS = [
    {
        "constraint_id": "old_nine_entry_primary_nav",
        "title": "历史 9 入口正式约束",
        "status": "deprecated",
        "replacement": "v0.2.4 固定 10 个正式一级入口",
    },
    {
        "constraint_id": "market_research_top_level_ban",
        "title": "市场与研究不得作为一级入口",
        "status": "deprecated",
        "replacement": "市场与研究是第 9 个正式一级入口",
    },
    {
        "constraint_id": "dark_ai_console_default_direction",
        "title": "暗色 AI 控制台默认视觉方向",
        "status": "deprecated",
        "replacement": "默认亮色、高质感、人类任务流",
    },
    {
        "constraint_id": "sample_data_acceptance",
        "title": "样例、演示、模拟财务数据可作为验收",
        "status": "deprecated",
        "replacement": "只允许真实数据或中文真实空态/阻断状态作为验收依据",
    },
]

RETAINED_REFERENCE_PRINCIPLES = [
    "每轮只执行一个 stage/phase，未经用户验收或明确指令不得进入下一阶段",
    "不得用 README/docs 声明替代真实 evidence",
    "不得使用 mock/sample/demo/synthetic/fixture/fake 财务数据",
    "不得用 long page 或 anchor scroll 冒充真实页面路由",
    "不得用 localStorage/sessionStorage/IndexedDB 冒充生产持久化",
]

FINANCIAL_DATA_ACCEPTANCE_POLICY = {
    "allowed": "real_data_or_real_empty_blocking_state",
    "forbidden": "mock/sample/demo/synthetic/fixture/fake financial data",
    "not_loaded_zero_policy": "not_loaded_must_not_render_as_confirmed_financial_zero",
}


@dataclass(frozen=True)
class V024Stage0Phase01Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_0_1_complete: bool
    stage_0_complete: bool
    max_phases_per_run: int
    official_nav: list[str]
    market_research_top_level: bool
    no_mock_financial_data: bool
    forbidden_financial_data_labels: list[str]
    data_state_requirements: list[str]
    one_stage_per_round_rule: bool
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage0_phase01_contract() -> V024Stage0Phase01Contract:
    return V024Stage0Phase01Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_ID,
        phase_name="需求合同冻结",
        task_ids=["T0.1.1", "T0.1.2", "T0.1.3", "T0.1.4"],
        phase_0_1_complete=True,
        stage_0_complete=False,
        max_phases_per_run=1,
        official_nav=OFFICIAL_NAV,
        market_research_top_level=True,
        no_mock_financial_data=True,
        forbidden_financial_data_labels=FORBIDDEN_FINANCIAL_DATA_LABELS,
        data_state_requirements=DATA_STATE_REQUIREMENTS,
        one_stage_per_round_rule=True,
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        next_phase_requires_user_acceptance=True,
    )


@dataclass(frozen=True)
class V024Stage0Phase02Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_0_1_complete: bool
    phase_0_2_complete: bool
    stage_0_complete: bool
    max_phases_per_run: int
    deprecated_constraints: list[dict[str, str]]
    retained_reference_principles: list[str]
    official_nav: list[str]
    market_research_top_level: bool
    default_visual_direction: str
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage0_phase02_contract() -> V024Stage0Phase02Contract:
    return V024Stage0Phase02Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id="0.2",
        phase_name="历史约束废弃",
        task_ids=["T0.2.1", "T0.2.2", "T0.2.3", "T0.2.4"],
        phase_0_1_complete=True,
        phase_0_2_complete=True,
        stage_0_complete=False,
        max_phases_per_run=1,
        deprecated_constraints=DEPRECATED_CONSTRAINTS,
        retained_reference_principles=RETAINED_REFERENCE_PRINCIPLES,
        official_nav=OFFICIAL_NAV,
        market_research_top_level=True,
        default_visual_direction="light_human_product_experience",
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        next_phase_requires_user_acceptance=True,
    )


@dataclass(frozen=True)
class V024Stage0Phase03Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_0_1_complete: bool
    phase_0_2_complete: bool
    phase_0_3_complete: bool
    stage_0_candidate_complete: bool
    stage_0_complete: bool
    max_phases_per_run: int
    official_nav: list[str]
    official_nav_count: int
    deprecated_top_level_aliases: list[str]
    market_research_top_level: bool
    no_mock_financial_data: bool
    forbidden_financial_data_labels: list[str]
    financial_data_acceptance_policy: dict[str, str]
    evidence_pack_required: list[str]
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    whole_stage_review_required: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage0_phase03_contract() -> V024Stage0Phase03Contract:
    return V024Stage0Phase03Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id="0.3",
        phase_name="Stage 0 测试与证据",
        task_ids=["T0.3.1", "T0.3.2", "T0.3.3", "T0.3.4"],
        phase_0_1_complete=True,
        phase_0_2_complete=True,
        phase_0_3_complete=True,
        stage_0_candidate_complete=True,
        stage_0_complete=False,
        max_phases_per_run=1,
        official_nav=OFFICIAL_NAV,
        official_nav_count=len(OFFICIAL_NAV),
        deprecated_top_level_aliases=DEPRECATED_TOP_LEVEL_ALIASES,
        market_research_top_level=True,
        no_mock_financial_data=True,
        forbidden_financial_data_labels=FORBIDDEN_FINANCIAL_DATA_LABELS,
        financial_data_acceptance_policy=FINANCIAL_DATA_ACCEPTANCE_POLICY,
        evidence_pack_required=[
            "evidence.json",
            "terminal.log",
            "changed_files.txt",
            "risk_and_rollback.md",
        ],
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        whole_stage_review_required=True,
        next_phase_requires_user_acceptance=True,
    )
