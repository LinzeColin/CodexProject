from __future__ import annotations

from dataclasses import dataclass, asdict


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
PRE_STAGE_ID = "PRE-S0"
PHASE_ID = "P0.0"

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

DEPRECATED_CONSTRAINTS = [
    "历史 9 入口正式约束",
    "市场与研究不得作为一级入口",
    "暗色 AI 控制台作为默认视觉方向",
    "README/docs 声明替代真实 evidence",
    "mock/sample/demo/synthetic/fixture/fake 财务数据验收",
]

FORBIDDEN_FINANCIAL_DATA_LABELS = [
    "mock",
    "sample",
    "demo",
    "synthetic",
    "fixture",
    "fake",
]


@dataclass(frozen=True)
class V024PreStage0Contract:
    target_version: str
    source_package_version: str
    pre_stage_id: str
    phase_id: str
    phase_name: str
    max_phases_per_run: int
    stage_0_executed: bool
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    official_nav: list[str]
    market_research_top_level: bool
    deprecated_constraints: list[str]
    no_mock_financial_data: bool
    forbidden_financial_data_labels: list[str]
    source_files_are_external_inputs: bool
    current_main_must_be_verified_before_stage0: bool
    stop_after_pre_stage0: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_pre_stage0_contract() -> V024PreStage0Contract:
    return V024PreStage0Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        pre_stage_id=PRE_STAGE_ID,
        phase_id=PHASE_ID,
        phase_name="pre stage 0 context convergence",
        max_phases_per_run=1,
        stage_0_executed=False,
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        official_nav=OFFICIAL_NAV,
        market_research_top_level=True,
        deprecated_constraints=DEPRECATED_CONSTRAINTS,
        no_mock_financial_data=True,
        forbidden_financial_data_labels=FORBIDDEN_FINANCIAL_DATA_LABELS,
        source_files_are_external_inputs=True,
        current_main_must_be_verified_before_stage0=True,
        stop_after_pre_stage0=True,
    )

