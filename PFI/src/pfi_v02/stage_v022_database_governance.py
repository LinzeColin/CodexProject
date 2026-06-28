from __future__ import annotations

import json
from pathlib import Path

from pfi_v02.stage2_registry import REQUIRED_STAGE2_SOURCE_IDS
from pfi_v02.stage3_read_mvp import STAGE3_FX_TO_AUD, STAGE3_REQUIRED_ACCOUNT_SOURCES
from pfi_v02.stage_v022_fx import (
    BASE_CURRENCY as V022_BASE_CURRENCY,
    DEFAULT_FX_PAIR as V022_FX_PAIR,
    DEFAULT_CUTOFF_LOCAL as V022_FX_CUTOFF_LOCAL,
    FX_LEDGER_AMOUNT_SCHEMA,
    FX_SNAPSHOT_SCHEMA,
)
from pfi_v02.stage_v022_source_profile import build_stage3_profile_contract
from pfi_v02.stage_v022_interconnection import (
    STAGE4_MATRIX_FIELDS,
    STAGE4_REQUIRED_EVENT_TYPES,
    build_metric_dependency_graph,
    build_stage4_interconnection_contract,
)
from pfi_v02.stage_v022_ledger_taxonomy import (
    STAGE5_LEDGER_EVENT_TYPES,
    STAGE5_TAXONOMY_LIMITS,
    build_stage5_contract_payload,
)
from pfi_v02.stage_v022_tags_views import (
    STAGE6_DEFAULT_TAG_GROUPS,
    STAGE6_TAG_RULE_DIMENSIONS,
    STAGE6_TAG_TABLES,
    build_stage6_contract_payload,
)
from pfi_v02.stage_v022_formula_scoring import (
    STAGE7_CASHFLOW_WINDOWS_DAYS,
    STAGE7_CONFIDENCE_WEIGHTS,
    STAGE7_REVIEW_THRESHOLD,
    build_stage7_contract_payload,
)


V022_STAGE1_TASK_IDS = (
    "S1-P1-T1",
    "S1-P1-T2",
    "S1-P1-T3",
    "S1-P2-T1",
    "S1-P2-T2",
    "S1-P2-T3",
)

V022_STAGE1_REQUIRED_PARAMETER_DOMAINS = (
    "currency",
    "fx",
    "time",
    "data_sources",
    "account_roles",
    "event_types",
    "interconnection",
    "consumption_categories",
    "tags",
    "confidence",
    "consumption_model",
    "investment_model",
    "cashflow",
    "visualization",
    "testing",
)

V022_STAGE2_TASK_IDS = (
    "S2-P1-T1",
    "S2-P1-T2",
    "S2-P1-T3",
    "S2-P2-T1",
    "S2-P2-T2",
    "S2-P2-T3",
)

V022_STAGE3_TASK_IDS = (
    "S3-P1-T1",
    "S3-P1-T2",
    "S3-P1-T3",
    "S3-P2-T1",
    "S3-P2-T2",
    "S3-P2-T3",
)

V022_STAGE4_TASK_IDS = (
    "S4-P1-T1",
    "S4-P1-T2",
    "S4-P1-T3",
    "S4-P2-T1",
    "S4-P2-T2",
    "S4-P2-T3",
)

V022_STAGE5_TASK_IDS = (
    "S5-P1-T1",
    "S5-P1-T2",
    "S5-P2-T1",
    "S5-P2-T2",
    "S5-P2-T3",
    "S5-P3-T1",
    "S5-P3-T2",
    "S5-P3-T3",
    "S5-P3-T4",
)

V022_STAGE6_TASK_IDS = (
    "S6-P1-T1",
    "S6-P1-T2",
    "S6-P1-T3",
    "S6-P2-T1",
    "S6-P2-T2",
    "S6-P2-T3",
    "S6-P3-T1",
    "S6-P3-T2",
    "S6-P3-T3",
)

V022_STAGE7_TASK_IDS = (
    "S7-P1-T1",
    "S7-P1-T2",
    "S7-P1-T3",
    "S7-P2-T1",
    "S7-P2-T2",
    "S7-P2-T3",
    "S7-P2-T4",
    "S7-P3-T1",
    "S7-P3-T2",
    "S7-P3-T3",
    "S7-P4-T1",
    "S7-P4-T2",
    "S7-P4-T3",
)

V022_STAGE0_TASK_IDS = (
    "S0-P1-T1",
    "S0-P1-T2",
    "S0-P1-T3",
    "S0-P2-T1",
    "S0-P2-T2",
)

V022_STAGE0_TASKS = (
    {
        "task_id": "S0-P1-T1",
        "phase": "Phase 0.1",
        "task": "在开发记录中新增任务条目 PFI v0.2.2 E2E 逻辑优化",
        "deliverable": "PFI/开发记录.md",
        "acceptance": "任务名、目标、范围、非目标均为中文且清晰。",
    },
    {
        "task_id": "S0-P1-T2",
        "phase": "Phase 0.1",
        "task": "定位三基文件与本次会修改的核心文件",
        "deliverable": "文件清单",
        "acceptance": "至少包含模型参数文件、功能清单、开发记录、参数 YAML、前端 HTML、测试文件。",
    },
    {
        "task_id": "S0-P1-T3",
        "phase": "Phase 0.1",
        "task": "明确本次不做的内容",
        "deliverable": "非目标清单",
        "acceptance": "明确本次不做真实交易、自动投资、隐私私有化重构、每次运行联网抓汇率。",
    },
    {
        "task_id": "S0-P2-T1",
        "phase": "Phase 0.2",
        "task": "新增参数版本号",
        "deliverable": "PFI/模型参数文件.md metadata",
        "acceptance": "出现 task_name=PFI v0.2.2 E2E 逻辑优化 和 parameter_version=v0.2.2。",
    },
    {
        "task_id": "S0-P2-T2",
        "phase": "Phase 0.2",
        "task": "新增参数变更记录文件",
        "deliverable": "PFI/config/parameter_changelog.md",
        "acceptance": "每次参数变化可追踪：字段、旧值、新值、原因、影响范围。",
    },
)

V022_STAGE0_SOURCE_PACK = (
    {
        "file": "PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md",
        "sha256": "94950e0cc4a46cfd19dfa2ed5ff2ebcab10909775e20d8bae1a4a2fe6f8b879c",
        "role": "stage_phase_task_roadmap",
    },
    {
        "file": "PFI_v0.2.2_E2E_logic_optimization_package (1).zip",
        "sha256": "57143e8bf96fb148f72d4b8a086adbb75334de6a1d4389fb940038e5effff925",
        "role": "stage_phase_task_source_package_archive",
    },
    {
        "file": "PFI_v0.2.2_Roadmap_Acceptance_Stop_Validation_zh.md",
        "sha256": "6c3d54696095c28cfaeb134ba609d9ea240ee56732dab05621c61a3f36db4af7",
        "role": "roadmap_acceptance_stop_validation",
    },
    {
        "file": "PFI_v0.2.2_Codex_Task_Pack_zh.md",
        "sha256": "027ce56c62bdd66727d7457cec89f3883f3653ed99bc37a3421383624952c2de",
        "role": "codex_task_pack",
    },
    {
        "file": "PFI_v0.2.2_Parameter_Draft_zh.md",
        "sha256": "861faa6c0ef458bd730a0e7da78d11b39e839177441689664922fdf36444cd93",
        "role": "parameter_draft",
    },
    {
        "file": "PFI_v0.2.2_6Agent_CrossReview_zh.md",
        "sha256": "7677a34add6b7a61b26f2a5d2262750cd232315f407e014a6a684e6d7a830ebd",
        "role": "six_agent_cross_review_draft",
    },
    {
        "file": "PFI_v0.2.2_UIUX_Logic_Review_Template.html",
        "sha256": "d8a19f901d2396582de5b2ab65f3ba945624b58e9a81636a0b5f9107404ab0f2",
        "role": "future_logic_review_reference_only",
    },
    {
        "file": "PFI_v0.2.2_E2E_logic_optimization_package.zip",
        "sha256": "7ea03c89a7720dd8b5f498833c11a7d286e2e9d132fe48eb24eefef85ea78cfe",
        "role": "source_package_archive",
    },
)


def build_v022_stage0_contract() -> dict[str, object]:
    """Return the v0.2.2 Stage 0 database-governance preparation contract."""
    return {
        "schema": "PFIV022DatabaseGovernanceStage0ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 0",
        "stage_name_zh": "现状盘点与任务锁定",
        "goal": "按 Stage -> Phase -> Task roadmap 锁定 v0.2.2 只做数据库治理和 E2E 逻辑优化，生成中文 baseline report。",
        "task_ids": V022_STAGE0_TASK_IDS,
        "tasks": V022_STAGE0_TASKS,
        "source_pack": V022_STAGE0_SOURCE_PACK,
        "roadmap_shape": {
            "format": "Stage -> Phase -> Task",
            "stage_count": 14,
            "stage_range": "Stage 0-13",
            "stage0_phases": ("Phase 0.1", "Phase 0.2"),
            "stage0_task_count": 5,
            "next_stage": "Stage 1 模型参数文件重构",
        },
        "scope": {
            "product_root": "PFI/",
            "domain": "database_governance_and_e2e_logic",
            "frontend_baseline": "v0.2.1 HTML Web Shell remains the UIUX baseline",
            "html_template_policy": "reference_only_not_stage0_ui_change",
            "allowed_stage0_changes": (
                "PFI/docs/pfi_v022/*",
                "PFI/src/pfi_v02/stage_v022_database_governance.py",
                "PFI/tests/test_v022_stage0_database_governance.py",
                "PFI/config/parameter_changelog.md",
                "PFI/HANDOFF.md",
                "PFI/功能清单.md",
                "PFI/开发记录.md",
                "PFI/模型参数文件.md",
            ),
            "forbidden_stage0_changes": (
                "PFI/web/index.html",
                "PFI/web/app/shell.js",
                "PFI/web/styles/tokens.css",
                "PFI/web/pfi_v022_logic_review.html",
                "PFI/config/pfi_parameters.yaml",
                "PFI/db/schema_tags.sql",
            ),
        },
        "current_inventory": {
            "human_entry_files": ("PFI/模型参数文件.md", "PFI/功能清单.md", "PFI/开发记录.md"),
            "stage0_core_file_list": (
                "PFI/模型参数文件.md",
                "PFI/功能清单.md",
                "PFI/开发记录.md",
                "PFI/config/pfi_parameters.yaml",
                "PFI/config/parameter_changelog.md",
                "PFI/web/index.html",
                "PFI/web/app/shell.js",
                "PFI/tests/test_pfi_parameters_consistency.py",
                "PFI/tests/test_v022_stage0_database_governance.py",
            ),
            "stage6_artifacts": (
                "PFI/src/pfi_v02/stage6_e2e_stabilization.py",
                "PFI/tests/test_stage6_e2e_stabilization.py",
                "PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md",
            ),
            "frontend_entries": ("PFI/web/index.html", "PFI/web/app/shell.js"),
            "source_ids": REQUIRED_STAGE2_SOURCE_IDS,
            "account_source_ids": STAGE3_REQUIRED_ACCOUNT_SOURCES,
            "fx_to_aud_fixture": dict(STAGE3_FX_TO_AUD),
            "known_thresholds": {
                "default_cash_review_amount": 1000,
                "low_confidence_review_threshold": 0.70,
                "large_spend_aud_threshold": 500,
                "electronics_impulse_aud_threshold": 300,
                "night_window_current": "23:00-05:00",
                "night_window_v022_required": "22:00-06:00",
                "monthly_budget_aud": 3600,
                "monthly_income_aud": 7200,
                "reserve_floor_aud": 5000,
                "concentration_watch_weight_pct": 35,
                "buy_chase_pct": 3.0,
                "sell_panic_pct": -5.0,
                "short_holding_days": 3,
                "stage5_top_n": 3,
                "upload_max_file_mb": 50,
                "upload_review_ratio": 0.04,
                "click_feedback_delay_ms": 180,
            },
            "current_cashflow_windows": (30, 90, 180),
            "v022_required_cashflow_windows": (7, 21, 30, 60, 90, 180, 360),
            "current_consumption_policy": "transfers_and_investments_excluded_from_living_consumption",
            "v022_required_consumption_policy": "total_outflow_consumption and living_consumption must be separate",
        },
        "baseline_conflicts": (
            {
                "id": "V022-S0-CONFLICT-001",
                "topic": "currency_and_fx",
                "current": "Stage 3/4/5 多数指标仍以 AUD fixture 派生，v0.2.1 顶栏为 CNY/AUD。",
                "required": "v0.2.2 全局以 CNY 为主口径，汇率展示采用 AUD/CNY=4.81 并使用 06:00 有效日规则。",
                "next_stage": "Stage 1/2",
            },
            {
                "id": "V022-S0-CONFLICT-002",
                "topic": "consumption_scope",
                "current": "分类规则只有 affects_consumption，Stage 4 把 transfer/investment 从生活消费排除。",
                "required": "新增消费总流出金额与生活消费金额双口径，投资入金、基金申购、投资买入计入总流出但不计生活消费。",
                "next_stage": "Stage 1/4/5",
            },
            {
                "id": "V022-S0-CONFLICT-003",
                "topic": "interconnection",
                "current": "有 transfer dedupe_key 和 Stage 6 ledger loop，但没有 economic_event_id / interconnection_group_id 事实层。",
                "required": "建立 Raw Record -> Transaction -> Interconnection Group -> Economic Event -> Ledger Event -> Metric 链路。",
                "next_stage": "Stage 4",
            },
            {
                "id": "V022-S0-CONFLICT-004",
                "topic": "cashflow_windows",
                "current": "现金流窗口为 30/90/180。",
                "required": "现金流窗口必须为 7/21/30/60/90/180/360。",
                "next_stage": "Stage 7",
            },
            {
                "id": "V022-S0-CONFLICT-005",
                "topic": "category_and_tags",
                "current": "存在 Stage 1/4 消费分类和行为标签，但没有 12 大类 / 50 中类 taxonomy，也没有标签持久化 schema。",
                "required": "分类与标签分离，默认标签和自定义标签写入 SQLite 并进入 diff/changelog。",
                "next_stage": "Stage 6",
            },
            {
                "id": "V022-S0-CONFLICT-006",
                "topic": "runtime_diff",
                "current": "Stage 6 有 gate/audit，但没有 dependency hash、impacted metrics 收紧逻辑和 Codex Review Ticket。",
                "required": "无 diff 不联网不触发 agent；重要 diff 生成中文复审票据。",
                "next_stage": "Stage 8",
            },
        ),
        "acceptance_criteria": (
            "Stage 0 已按 Stage -> Phase -> Task roadmap 补做，不再只保留 milestone 摘要。",
            "开发记录包含 PFI v0.2.2 E2E 逻辑优化任务名、目标、范围、非目标。",
            "模型参数文件 metadata 包含 task_name=PFI v0.2.2 E2E 逻辑优化 和 parameter_version=v0.2.2。",
            "PFI/config/parameter_changelog.md 已创建并能追踪参数变化字段、旧值、新值、原因、影响范围。",
            "已列出现有参数与硬编码阈值。",
            "已列出现有消费、投资、现金流、建议模块的计算口径。",
            "已标记哪些逻辑与 v0.2.2 要求冲突。",
            "已确认不会破坏已有 v0.2 Stage 6 基础。",
            "HTML 模板仅作为逻辑审查参考，Stage 0 不修改 v0.2.1 前端显示。",
        ),
        "validation_commands": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "stop_conditions": (
            "无法定位现有模型参数文件。",
            "无法定位现有前端入口。",
            "无法判断现有测试框架。",
            "Stage 0 改动触碰 PFI/web 正式前端。",
        ),
    }


def build_v022_stage0_agent_review() -> dict[str, object]:
    contract = build_v022_stage0_contract()
    return {
        "schema": "PFIV022Stage0AgentReviewV1",
        "agent_1_financial_logic": {
            "status": "通过",
            "finding": "已识别投资入金、基金申购、投资买入需要进入消费总流出但不得进入生活消费。",
            "evidence": ("V022-S0-CONFLICT-002", "V022-S0-CONFLICT-003"),
        },
        "agent_3_parameter_governance": {
            "status": "通过",
            "finding": "已列出散落在代码、Markdown、Web fixture 和测试中的阈值，后续必须迁入参数文件/YAML。",
            "threshold_count": len(contract["current_inventory"]["known_thresholds"]),
        },
        "blocking": False,
        "stage0_result": "baseline_ready_for_owner_review",
    }


def default_v022_parameter_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "pfi_parameters.yaml"


def load_v022_parameter_catalog(path: Path | None = None) -> dict[str, object]:
    """Load the Stage 1 machine-readable parameter catalog.

    The file uses JSON-compatible YAML so it can be parsed without adding a
    runtime YAML dependency. JSON is a valid YAML subset and keeps local tests
    deterministic in the current PFI environment.
    """
    catalog_path = path or default_v022_parameter_catalog_path()
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def build_v022_stage1_contract() -> dict[str, object]:
    return {
        "schema": "PFIV022ParameterGovernanceStage1ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 1",
        "stage_name_zh": "模型参数文件重构",
        "task_ids": V022_STAGE1_TASK_IDS,
        "goal": "建立中文可读参数总目录、机器可读参数 YAML 和参数一致性测试。",
        "deliverables": (
            "PFI/模型参数文件.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/tests/test_pfi_parameters_consistency.py",
            "PFI/docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md",
            "PFI/config/parameter_changelog.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
        ),
        "required_parameter_domains": V022_STAGE1_REQUIRED_PARAMETER_DOMAINS,
        "machine_readable_parameter_file": {
            "path": "PFI/config/pfi_parameters.yaml",
            "format": "JSON-compatible YAML",
            "draft_alias_not_used": "PFI/config/pfi_v022_parameters.yaml",
            "reason": "Stage -> Phase -> Task roadmap and Stage 0 core list name PFI/config/pfi_parameters.yaml as the canonical target; one source avoids YAML drift.",
        },
        "acceptance_criteria": (
            "模型参数文件包含货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化、测试。",
            "YAML 与 Markdown 参数含义一致，字段中文说明可在 Markdown 查到。",
            "参数一致性测试确认 Markdown、YAML 和前端显示的核心阈值一致。",
            "每个公式有中文名称、用途、输入、输出、计算逻辑、示例。",
            "每个阈值有当前值、存在原因、影响页面和是否允许用户修改。",
            "公式变量有中文别名。",
        ),
        "stop_conditions": (
            "参数仍散落在代码和文档中且没有统一目录。",
            "Markdown 和 YAML 核心参数不一致。",
            "核心阈值多处不一致且没有明确标记为后续阶段差异。",
            "公式只有英文变量或代码名，用户无法理解。",
        ),
        "validation_commands": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_pfi_parameters_consistency -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "non_goals": (
            "不改 v0.2.1 HTML Web Shell 正式前端显示。",
            "不提前实现 Stage 2 汇率快照读取。",
            "不新增真实交易、自动投资、支付或券商提交。",
            "不生成 Stage 9/12 的 HTML 逻辑审查页。",
        ),
    }


def build_v022_stage2_contract() -> dict[str, object]:
    return {
        "schema": "PFIV022CnyFxGovernanceStage2ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 2",
        "stage_name_zh": "CNY 基准与汇率规则",
        "task_ids": V022_STAGE2_TASK_IDS,
        "goal": "建立 CNY 主显示、原币辅助、账本金额追溯字段、06:00 有效汇率日和每日一次本地汇率快照。",
        "currency_policy": {
            "base_currency": V022_BASE_CURRENCY,
            "display_pair": V022_FX_PAIR,
            "display_semantic_zh": "1 AUD = x CNY",
            "effective_time_local": V022_FX_CUTOFF_LOCAL,
            "timezone": "Australia/Sydney",
            "ordinary_runtime_network_refresh": False,
            "explicit_refresh_requires_allow_network": True,
        },
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_fx.py",
            "PFI/data/fx_snapshots/AUD_CNY/<YYYY-MM-DD>.json",
            "PFI/tests/test_v022_fx_effective_date.py",
            "PFI/docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/web/index.html",
            "PFI/web/app/shell.js",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
        ),
        "ledger_amount_schema": {
            "schema": FX_LEDGER_AMOUNT_SCHEMA,
            "required_fields": ("original_amount", "original_currency", "amount_cny", "fx_snapshot_id"),
        },
        "fx_snapshot_schema": {
            "schema": FX_SNAPSHOT_SCHEMA,
            "required_fields": (
                "snapshot_id",
                "effective_date",
                "effective_time_local",
                "display_pair",
                "rate",
                "source_provider",
                "source_url",
                "source_observed_date",
                "fetched_at",
                "hash",
            ),
        },
        "acceptance_criteria": (
            "首页、投资、消费、现金流、报告主显示均为 CNY。",
            "原币作为辅助显示，例如 ¥2,405.00 / 约 500.00 AUD / AUD/CNY=4.81。",
            "每条账本金额字段明确原始金额、原始币种、CNY 金额和汇率快照 ID。",
            "06:00 前使用昨天有效汇率，06:00 后使用当天有效汇率。",
            "普通本地运行只读本地快照，不默认联网抓汇率。",
            "显式刷新才能联网读取真实 Frankfurter AUD/CNY 汇率并写入本地快照。",
            "汇率快照含来源、读取时间、币种对和 hash，hash 可校验。",
        ),
        "stop_conditions": (
            "任一核心板块仍以 AUD 为主显示。",
            "原币丢失或汇率不显示。",
            "金额无法追溯汇率快照。",
            "03:00 错用当天汇率。",
            "普通运行触发网络抓取。",
            "汇率无快照或无法追溯。",
        ),
        "validation_commands": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_fx_effective_date -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx read",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "non_goals": (
            "不做真实交易、自动投资、支付或券商提交。",
            "不把普通页面加载变成联网抓汇率。",
            "不提前实现 Stage 3 数据源 profile 或 Stage 4 Interconnection Matrix。",
        ),
    }


def build_v022_stage3_contract() -> dict[str, object]:
    profile_contract = build_stage3_profile_contract()
    return {
        "schema": "PFIV022SourceAccountProfileStage3ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 3",
        "stage_name_zh": "数据源、账户角色与可扩展结构",
        "task_ids": V022_STAGE3_TASK_IDS,
        "goal": "建立通用 source profile、capabilities、other_source_template、账户多角色和角色生效期，避免按 source 名称硬编码计算。",
        "source_profile_contract": profile_contract,
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_source_profile.py",
            "PFI/tests/test_v022_stage3_source_account_profiles.py",
            "PFI/docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
        ),
        "acceptance_criteria": (
            "source profile schema 支持 wallet、bank、broker、fund_platform、bullion_platform、payment_platform、manual_snapshot、other。",
            "数据源能力由 capabilities 描述，覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。",
            "提供 other_source_template，新增数据源可通过 profile 扩展，不需要改核心计算代码。",
            "账户角色 schema 允许同一账户同时是主钱包、消费账户、投资入金来源和收入账户。",
            "账户角色有 role_effective_from 和 role_effective_to，角色历史可追踪。",
            "所有计算按角色和事件类型，不按 source 名称硬编码。",
        ),
        "stop_conditions": (
            "新增 source 必须修改核心计算代码。",
            "数据源能力写死在 source 名称里。",
            "无法添加 other source。",
            "一个账户只能有一个角色。",
            "角色历史无法追踪。",
            "公式按 source 名称写死。",
        ),
        "validation_commands": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage3_source_account_profiles -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date PFI.tests.test_v022_stage3_source_account_profiles -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "non_goals": (
            "不实现 Stage 4 economic_event_id 或 interconnection_group_id。",
            "不修改 v0.2.1 HTML Web Shell 交互架构。",
            "不做真实交易、自动投资、支付或券商提交。",
            "不按支付宝、微信、银行卡等 source 名称定义消费公式。",
        ),
    }


def build_v022_stage4_contract() -> dict[str, object]:
    interconnection_contract = build_stage4_interconnection_contract()
    return {
        "schema": "PFIV022InterconnectionStage4ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 4",
        "stage_name_zh": "Economic Event 与 Interconnection 逻辑",
        "task_ids": V022_STAGE4_TASK_IDS,
        "goal": "建立 economic_event_id、interconnection_group_id、事件影响 flags、Interconnection Matrix 和 no-double-count 计算规则，保证多来源记录可多处展示但核心口径只计算一次。",
        "economic_event_contract": {
            "economic_event_id_required": True,
            "interconnection_group_id_required": True,
            "single_true_event_single_economic_event_id": True,
            "single_interconnection_group_not_repeated_in_core_amounts": True,
            "required_event_types": STAGE4_REQUIRED_EVENT_TYPES,
            "matrix_fields": STAGE4_MATRIX_FIELDS,
        },
        "interconnection_contract": interconnection_contract,
        "metric_dependency_graph": build_metric_dependency_graph(),
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_interconnection.py",
            "PFI/src/pfi_v02/stage_v022_database_governance.py",
            "PFI/tests/test_v022_interconnection_no_double_count.py",
            "PFI/tests/test_v022_consumption_investment_outflow.py",
            "PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md",
            "PFI/docs/pfi_v022/STAGE4_INTERCONNECTION.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
        ),
        "acceptance_criteria": (
            "同一真实事件只有一个 economic_event_id。",
            "同一 interconnection_group 不会重复计入核心金额。",
            "每个 event type 有明确 affects flags。",
            "首页、投资、消费、现金流、报告口径一致。",
            "投资入金计入消费总流出，不计入生活消费，计入投资现金。",
            "基金申购计入消费总流出，不计入生活消费，计入基金资产。",
            "投资买入计入消费总流出，不计入生活消费，计入投资持仓。",
            "信用卡还款不重复计入生活消费。",
            "退款抵消原消费或对应总流出。",
        ),
        "stop_conditions": (
            "同一记录被重复计入核心金额。",
            "投资入金未进入消费总流出。",
            "基金申购未进入消费总流出。",
            "投资入金错误进入生活消费。",
            "同一 interconnection_group 因重复来源记录导致核心金额重复计算。",
        ),
        "validation_commands": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_interconnection_no_double_count PFI.tests.test_v022_consumption_investment_outflow -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date PFI.tests.test_v022_stage3_source_account_profiles PFI.tests.test_v022_interconnection_no_double_count PFI.tests.test_v022_consumption_investment_outflow -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "cross_review": {
            "Agent 1": "消费、投资、现金流口径复审通过；投资入金/基金申购/投资买入均进入消费总流出但不进入生活消费。",
            "Agent 2": "source -> transaction -> group -> economic event -> ledger -> metric 链路复审通过。",
        },
        "non_goals": (
            "不实现 Stage 5 分类 taxonomy 和双口径 UI。",
            "不实现 Stage 6 标签持久化。",
            "不修改 v0.2.1 HTML Web Shell 交互架构。",
            "不做真实交易、自动投资、支付或券商提交。",
        ),
    }


def build_v022_stage5_contract() -> dict[str, object]:
    stage5_payload = build_stage5_contract_payload()
    return {
        "schema": "PFIV022LedgerTaxonomyStage5ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 5",
        "stage_name_zh": "统一账本事件、消费双口径与分类体系",
        "task_ids": V022_STAGE5_TASK_IDS,
        "goal": "把 Stage 4 的 Interconnection 事实口径收敛为统一账本事件类型表、首页/消费页/报告共用的双消费口径，以及 L1 ≤ 12、每类 L2 ≤ 5、总 L2 ≤ 50 的中文消费分类 taxonomy。",
        "ledger_event_type_policy": {
            "required_event_types": STAGE5_LEDGER_EVENT_TYPES,
            "required_affects_flags": (
                "affects_total_consumption_outflow",
                "affects_living_consumption",
                "affects_investment",
                "affects_net_worth",
                "affects_cashflow",
            ),
            "event_type_table": stage5_payload["ledger_event_type_table"],
        },
        "double_consumption_policy": {
            "gross_consumption_label_zh": "消费总流出金额",
            "living_consumption_label_zh": "生活消费金额",
            "gross_includes": ("生活消费", "投资入金", "基金申购", "黄金申购", "投资买入", "金融费用"),
            "living_excludes": ("投资入金", "基金申购", "黄金申购", "投资买入", "内部转账", "信用卡还款"),
            "required_surfaces": stage5_payload["double_consumption_surface_required"],
            "source_metric_function": "pfi_v02.stage_v022_interconnection.aggregate_core_metrics",
        },
        "consumption_taxonomy_policy": {
            "limits": STAGE5_TAXONOMY_LIMITS,
            "taxonomy": stage5_payload["taxonomy"],
            "validation": stage5_payload["taxonomy_validation"],
            "future_merge_field_required": True,
        },
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_ledger_taxonomy.py",
            "PFI/src/pfi_v02/stage_v022_database_governance.py",
            "PFI/tests/test_v022_stage5_ledger_taxonomy.py",
            "PFI/docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
            "PFI/README.md",
        ),
        "acceptance_criteria": (
            "统一账本事件类型表包含消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。",
            "每种事件绑定影响消费总流出、生活消费、投资、净资产和现金流的 flags。",
            "消费总流出金额包含生活消费、投资入金、基金申购、黄金申购、投资买入和金融费用。",
            "生活消费金额只包含普通生活消费，排除投资入金、基金申购、黄金申购、投资买入、内部转账和信用卡还款。",
            "首页、消费页、报告模板同时展示消费总流出与生活消费，并解释差异。",
            "消费分类 L1 ≤ 12，每个 L1 的 L2 ≤ 5，总 L2 不超过 50。",
            "每个 L1 保留 future_merge_to 或 merge_candidate，后续可压缩到 10 类或更少。",
        ),
        "stop_conditions": (
            "事件类型不足以表达真实资金流。",
            "任一事件影响口径缺失。",
            "投资入金未计入消费总流出。",
            "生活消费被投资入金污染。",
            "首页、消费页、报告只显示一个消费数字导致误解。",
            "L1 超过 12、任一 L1 的 L2 超过 5、或总 L2 超过 50。",
            "后续无法合并分类。",
        ),
        "validation_commands": (
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage5_ledger_taxonomy.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "cross_review": {
            "Agent 1": "复核双消费口径：投资入金、基金申购、黄金申购、投资买入和费用进入消费总流出，但不进入生活消费。",
            "Agent 3": "复核分类参数：12 大类 / 每类 5 中类 / 总中类 50，分类与 Stage 6 标签系统分离。",
        },
        "non_goals": (
            "Stage 6 标签持久化不在本轮实现。",
            "不修改 v0.2.1 HTML Web Shell UIUX 基线。",
            "不新增真实交易、自动投资、支付或券商提交。",
            "不实现 Stage 7 评分公式、Stage 8 runtime diff 或 Stage 9 可视化页面。",
        ),
    }


def build_v022_stage6_contract() -> dict[str, object]:
    stage6_payload = build_stage6_contract_payload()
    return {
        "schema": "PFIV022TagViewStage6ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 6",
        "stage_name_zh": "标签系统与自定义视图",
        "task_ids": V022_STAGE6_TASK_IDS,
        "goal": "在 Stage 5 单一主分类之外，建立可持久化、多标签、可追踪历史、可规则自动赋值、可筛选账本、可进入报告和可保存自定义视图的标签系统。",
        "tag_persistence_policy": {
            "tables": STAGE6_TAG_TABLES,
            "default_tag_groups": STAGE6_DEFAULT_TAG_GROUPS,
            "tag_rule_dimensions": STAGE6_TAG_RULE_DIMENSIONS,
            "persistence": stage6_payload["persistence"],
            "system_default_physical_delete_allowed": False,
            "custom_tag_lifecycle": ("新增", "重命名", "停用", "删除"),
        },
        "default_tag_library": stage6_payload["default_tag_library"],
        "tag_rules": stage6_payload["tag_rules"],
        "custom_view_policy": {
            "required_surfaces": stage6_payload["custom_view_surfaces"],
            "html_deliverable": "PFI/web/pfi_v022_tag_views.html",
            "saved_view_table": "pfi_custom_views",
            "examples": ("订阅检查", "投资追涨复盘", "夜间大额复盘"),
        },
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_tags_views.py",
            "PFI/src/pfi_v02/stage_v022_database_governance.py",
            "PFI/tests/test_v022_stage6_tags_views.py",
            "PFI/docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md",
            "PFI/web/pfi_v022_tag_views.html",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
            "PFI/README.md",
        ),
        "acceptance_criteria": (
            "pfi_tags 表或本地等价存储包含 tag_id、中文名、范围、类型、是否系统默认、是否可编辑、是否启用。",
            "pfi_tag_assignments 支持同一交易、经济事件、持仓或账户拥有多个标签。",
            "pfi_tag_rules 支持金额、时间、分类、事件类型和账户角色自动打标签。",
            "默认标签库覆盖通用、消费、投资、数据质量、现金流和复盘。",
            "自定义标签支持新增、重命名、停用和删除，且默认系统标签不能被物理删除。",
            "标签变更历史记录旧值、新值、时间、影响对象和原因。",
            "账本可按标签组合筛选，例如夜间 + 大额 + 计划外。",
            "报告可按标签聚合消费、投资、异常和复盘项。",
            "本地 HTML 可展示并保存自定义标签视图，例如订阅检查和投资追涨复盘。",
        ),
        "stop_conditions": (
            "标签不能持久化。",
            "一笔记录只能有一个标签。",
            "标签只能手动添加。",
            "默认标签缺失关键分析维度。",
            "自定义标签无法修改。",
            "标签历史不可追踪。",
            "标签无法筛选账本。",
            "标签不参与报告。",
            "自定义视图不能保存。",
        ),
        "validation_commands": (
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage6_tags_views.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py PFI/tests/test_v022_stage6_tags_views.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "cross_review": {
            "Agent 4": "标签体系复核：分类保持单一主分类，标签承担多维分析、建议、视图和复盘。",
            "Agent 5": "视图与报告复核：标签筛选不改变原始账本金额，自定义视图只是保存筛选条件。",
        },
        "non_goals": (
            "Stage 7 现金流窗口不在本轮实现。",
            "不修改 v0.2.1 HTML Web Shell UIUX 基线。",
            "不新增真实交易、自动投资、支付或券商提交。",
            "不实现 Stage 8 runtime diff、Stage 9 参数中心或 Stage 12 逻辑审查页。",
        ),
    }


def build_v022_stage7_contract() -> dict[str, object]:
    stage7_payload = build_stage7_contract_payload()
    return {
        "schema": "PFIV022FormulaScoringStage7ContractV1",
        "version": "v0.2.2",
        "stage": "Stage 7",
        "stage_name_zh": "模型公式、阈值与评分标准",
        "goal": "把置信度、消费、投资和现金流模型公式固定为中文可解释、参数可追踪、测试可验证的 Stage 7 合同。",
        "task_ids": V022_STAGE7_TASK_IDS,
        "phases": {
            "Phase 7.1": ("置信度评分", "S7-P1-T1", "S7-P1-T2", "S7-P1-T3"),
            "Phase 7.2": ("消费模型公式", "S7-P2-T1", "S7-P2-T2", "S7-P2-T3", "S7-P2-T4"),
            "Phase 7.3": ("投资模型公式", "S7-P3-T1", "S7-P3-T2", "S7-P3-T3"),
            "Phase 7.4": ("现金流模型公式", "S7-P4-T1", "S7-P4-T2", "S7-P4-T3"),
        },
        "confidence_scoring": {
            "total_score": 100,
            "weights": stage7_payload["confidence_weights"],
            "required_weight_phrase": "字段完整度 30 分，金额方向 10 分，规则命中 20 分，商户/对手方 15 分，关联匹配 15 分，历史一致性 10 分",
            "review_threshold": STAGE7_REVIEW_THRESHOLD,
            "threshold_policy": "统一复核阈值 70 分；不按 source 分层。",
        },
        "consumption_model": {
            "gross_formula_zh": "消费总流出金额 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消。",
            "living_formula_zh": "生活消费金额 = 普通生活消费 - 已关联退款 - 已关联撤销。",
            "large_spend_threshold": "CNY ≥ 2000 或 AUD 原币 ≥ 500。",
            "night_window": "22:00-06:00 本地时间；电子产品冲动独立规则已删除并并入夜间/大额逻辑。",
        },
        "investment_model": {
            "market_value_formula_zh": "投资市值 = 投资现金 + Σ(持仓数量 × 最新价格 × 汇率)，主显示 CNY。",
            "pnl_formula_scope": "成本、费用、税费、汇率影响、已实现、未实现、总收益均有中文解释。",
            "behavior_scope": "交易频率、换手率、持仓周期、追涨候选、杀跌候选、现金拖累、集中度。",
        },
        "cashflow_model": {
            "windows_days": STAGE7_CASHFLOW_WINDOWS_DAYS,
            "windows_display": "7 / 21 / 30 / 60 / 90 / 180 / 360",
            "reserve_floor_formula_zh": "储备金底线 = max(用户自定义最低储备金, 平均月固定支出 × 储备月份数)。",
            "investment_squeeze_formula_zh": "若计划投资入金后未来生活现金低于储备金底线，则标记投资入金挤压生活现金。",
            "visualizations": stage7_payload["cashflow_visualizations"],
        },
        "deliverables": (
            "PFI/src/pfi_v02/stage_v022_formula_scoring.py",
            "PFI/src/pfi_v02/stage_v022_database_governance.py",
            "PFI/tests/test_v022_stage7_formula_scoring.py",
            "PFI/docs/pfi_v022/STAGE7_FORMULA_SCORING.md",
            "PFI/config/pfi_parameters.yaml",
            "PFI/config/parameter_changelog.md",
            "PFI/模型参数文件.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/HANDOFF.md",
            "PFI/README.md",
        ),
        "acceptance_criteria": (
            "置信度评分为 100 分制，权重严格为 30/10/20/15/15/10。",
            "每个评分项都有 0 分、低分、中分、高分、满分中文解释。",
            "统一复核阈值为 70 分，低于 70 分进入复核；不按 source 分层。",
            "消费总流出金额包含生活消费、投资入金、基金申购、黄金申购、投资买入和金融费用。",
            "生活消费金额排除投资入金、基金申购、投资买入、内部转账和信用卡还款。",
            "大额消费阈值为 CNY ≥ 2000 或 AUD 原币 ≥ 500。",
            "夜间消费窗口为 22:00-06:00，电子产品冲动独立规则并入夜间/大额逻辑。",
            "投资市值公式为持仓数量 × 最新价格 × 汇率，主显示 CNY 且可追溯汇率。",
            "成本、已实现、未实现、总收益公式解释费用、税费和汇率影响。",
            "投资行为公式覆盖交易频率、换手率、持仓周期、追涨、杀跌、现金拖累和集中度。",
            "现金流窗口支持 7/21/30/60/90/180/360 天。",
            "储备金安全线支持用户自定义最低储备金和固定支出 × 月数。",
            "投资入金挤压模型能说明投资入金是否挤压生活现金。",
        ),
        "stop_conditions": (
            "权重与用户要求不一致。",
            "只有公式没有中文评分标准。",
            "出现按 source 分层的复核阈值。",
            "消费总流出公式漏掉投资相关流出。",
            "生活消费口径被投资入金或基金申购污染。",
            "大额或夜间阈值与参数文件不一致。",
            "仍存在独立电子产品冲动阈值。",
            "投资市值无法追溯汇率。",
            "收益公式忽略费用、税费或汇率。",
            "投资行为只显示收益，不显示行为。",
            "现金流窗口仍只有 30/90/180。",
            "储备金不可解释。",
            "投资入金只进投资、不影响现金流分析。",
            "Stage 8 Runtime Diff 不在本轮实现。",
        ),
        "validation_commands": (
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage7_formula_scoring.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py PFI/tests/test_v022_stage6_tags_views.py PFI/tests/test_v022_stage7_formula_scoring.py -q",
            "PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q",
            "node --check PFI/web/app/shell.js",
            "python3 scripts/validate_project_governance.py --project PFI",
            "git diff --check -- PFI",
        ),
        "cross_review": {
            "Agent 3": "参数、公式、阈值审查：检查权重、阈值、中文解释和参数一致性。",
            "Agent 1": "消费、投资、现金流口径复核：检查投资流出、生活消费和现金流挤压不冲突。",
            "Agent 4": "标签衔接复核：检查大额、夜间、订阅、追涨、杀跌等公式输出可被标签体系消费。",
        },
        "non_goals": (
            "Stage 8 Runtime Diff 不在本轮实现。",
            "Stage 9 参数中心和 HTML 关系图不在本轮实现。",
            "Stage 10 建议评分生命周期不在本轮实现。",
            "不修改 v0.2.1 HTML Web Shell UIUX 基线。",
            "不新增真实交易、自动投资、支付或券商提交。",
        ),
    }
