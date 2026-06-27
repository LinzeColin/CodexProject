from __future__ import annotations

from pfi_v02.stage2_registry import REQUIRED_STAGE2_SOURCE_IDS
from pfi_v02.stage3_read_mvp import STAGE3_FX_TO_AUD, STAGE3_REQUIRED_ACCOUNT_SOURCES


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
