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

