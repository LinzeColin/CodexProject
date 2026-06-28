from __future__ import annotations

from dataclasses import asdict, dataclass


VERSION_NAME = "v0.2.1.1 Product UI Recovery"
STAGE0_TASK_ID = "V0211-S0-T01"
STAGE1_TASK_ID = "V0211-S1-T01"
STAGE2_TASK_ID = "V0211-S2-T01"
STAGE3_TASK_ID = "V0211-S3-T01"
STAGE4_TASK_ID = "V0211-S4-T01"
TOTAL_EXECUTION_STAGES = 6


@dataclass(frozen=True)
class V0211SourceFile:
    label: str
    path: str
    role: str


@dataclass(frozen=True)
class V0211ExecutionStage:
    stage_id: str
    name: str
    inherited_phase_scope: tuple[str, ...]
    delivery_focus: tuple[str, ...]
    forbidden_work: tuple[str, ...]
    acceptance_gate: tuple[str, ...]


@dataclass(frozen=True)
class V0211Decision:
    item: str
    source_conflict: str
    default_resolution: str
    stage_to_finalize: str


@dataclass(frozen=True)
class V0211PageSkeleton:
    workspace_id: str
    label: str
    route: str
    purpose: str
    secondary_tabs: tuple[str, ...]


@dataclass(frozen=True)
class V0211OperationFlow:
    flow_id: str
    owner_entry: str
    route: str
    required_controls: tuple[str, ...]
    state_surfaces: tuple[str, ...]
    acceptance: tuple[str, ...]


@dataclass(frozen=True)
class V0211PersistenceSyncSurface:
    surface_id: str
    label: str
    source: str
    required_fields: tuple[str, ...]
    acceptance: tuple[str, ...]


SOURCE_FILES: tuple[V0211SourceFile, ...] = (
    V0211SourceFile(
        "用户 RTF 纠偏稿",
        "/Users/linzezhang/Downloads/v0.2.1.1.rtf",
        "最新产品判断和反 AI 演示壳约束",
    ),
    V0211SourceFile(
        "Markdown taskpack roadmap",
        "/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md",
        "受控重构任务包、验收条件和禁止事项",
    ),
)


RTF_PRIMARY_NAVIGATION = (
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
)

MARKDOWN_PRIMARY_NAVIGATION = (
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "设置",
)

LEGACY_ROUTE_ALIASES = {
    "首页": "首页总览",
    "市场": "市场与研究",
    "研究": "市场与研究",
    "持仓": "投资管理 > 持仓",
    "策略实验室": "市场与研究 > 策略实验室",
    "数据与系统": "设置 > 数据与系统",
}


EXECUTION_STAGES: tuple[V0211ExecutionStage, ...] = (
    V0211ExecutionStage(
        "S0",
        "准备轮：失败冻结与执行锁",
        ("Phase 0", "Stage 0.1", "资料读取", "路线纠偏"),
        (
            "标记当前 v0.2.1 前端优化不再作为正式 UI 交付基础",
            "锁定 6 个执行 Stage，纠正 roadmap 中 Phase/Stage 的母子关系",
            "建立来源清单、路线锁、Stage 0 合同和目标测试",
            "记录导航数量与策略实验室归属的来源差异和默认处理",
        ),
        (
            "不修改正式 Web Shell",
            "不重建导航",
            "不实现图表、上传、持仓保存或报告",
            "不声明 v0.2.1.1 完成",
        ),
        (
            "Stage 0 文档可读",
            "合同测试通过",
            "下一轮只能进入 Stage 1",
        ),
    ),
    V0211ExecutionStage(
        "S1",
        "产品壳与路由",
        ("原 P0", "原 P1"),
        (
            "重建正式主导航",
            "建立一级页面状态和 active 状态",
            "旧入口只作为 route alias、搜索别名或二级入口",
            "浏览器前进后退可用",
        ),
        (
            "不做图表",
            "不做上传闭环",
            "不做持仓编辑",
            "不做报告",
        ),
        (
            "真实浏览器点击路径：首页总览 -> 投资管理 -> 设置 -> 后退 -> 投资管理",
            "浏览器前进后退可用",
            "首页无设置栏、运行边界、反馈控制台、手机预览和 Task Pack",
        ),
    ),
    V0211ExecutionStage(
        "S2",
        "页面骨架与去 AI 化",
        ("原 P2", "原 P3"),
        (
            "清理正式 UI 中开发者词、演示模块和默认反馈控制台",
            "建立首页、账户、投资、消费、数据源、建议、报告、设置页面骨架",
            "设置内容只在设置页出现",
        ),
        (
            "不做数据库 migration",
            "不伪造趋势数据",
            "不写字符串式假验收",
        ),
        (
            "全局可见中文扫描通过",
            "各页面二级入口真实切换",
            "无开发者词污染正式页面",
        ),
    ),
    V0211ExecutionStage(
        "S3",
        "真实操作流",
        ("原 P4"),
        (
            "上传、解析预览、字段映射、待复核和确认入库路径",
            "账本筛选、分类、复核和导出路径",
            "持仓编辑表单和设置保存路径",
        ),
        (
            "不以 toast 代替真实操作",
            "不把生产保存写进 localStorage、sessionStorage 或 IndexedDB",
            "不新增测试数据污染正式页面",
        ),
        (
            "上传、账本、持仓编辑、设置保存均有真实浏览器行为验收",
            "无真实数据时显示中文空状态",
        ),
    ),
    V0211ExecutionStage(
        "S4",
        "持久化与同步",
        ("原 P6"),
        (
            "持仓修改写入本地 SQLite",
            "刷新页面和重启服务后仍可读取",
            "首页、投资图表和报告读取同一持仓读模型",
        ),
        (
            "不把浏览器缓存作为生产持久化来源",
            "不跳过 SQLite 查询验收",
            "不声明真实账户生产联通",
        ),
        (
            "页面编辑 -> 保存 -> SQLite 查询 -> 重启服务 -> 页面读取通过",
            "首页、投资、报告数据一致",
        ),
    ),
    V0211ExecutionStage(
        "S5",
        "真实图表与最终验收",
        ("原 P5", "原 P7"),
        (
            "账户、投资、消费趋势图读取真实数据层或显示中文空状态",
            "所有一级入口、二级入口和主要按钮真实可点",
            "桌面端和移动端截图验收",
            "最终验收禁止关键词测试替代行为测试",
        ),
        (
            "不伪造收益或消费趋势",
            "不使用 demo/sample/synthetic/fixture/mock/fake 数据作为产品依据",
            "不把截图路径当作截图证据",
        ),
        (
            "Playwright 或等效真实浏览器 E2E 通过",
            "图表数据源测试通过",
            "禁词和开发词 visible text scan 通过",
        ),
    ),
)


DECISIONS: tuple[V0211Decision, ...] = (
    V0211Decision(
        "正式主导航数量",
        "Markdown roadmap 写 9 个入口；RTF v0.2.1.1 纠偏稿写 10 个入口并加入市场与研究。",
        "Stage 1 默认按 RTF 最新稿执行：10 个正式入口，市场与研究作为一级入口；如用户明确要求 9 项，则 Stage 1 前更新本合同。",
        "S1",
    ),
    V0211Decision(
        "策略实验室归属",
        "旧 v0.2.1 合同归属投资管理；RTF 最新稿要求全系统唯一位置为市场与研究 > 策略实验室。",
        "Stage 1 默认按 RTF 最新稿执行：旧策略实验室入口重定向到市场与研究 > 策略实验室，不能生成第二个页面。",
        "S1",
    ),
    V0211Decision(
        "图表与持久化顺序",
        "Markdown 执行策略把图表放在持久化前；RTF 末段强调先做真实操作和持久化，再做图表。",
        "v0.2.1.1 执行顺序按用户最新纠偏：S3 操作流，S4 持久化，S5 图表与最终验收。",
        "S0",
    ),
)

STAGE0_FORBIDDEN_FILE_CHANGES = (
    "PFI/web/index.html",
    "PFI/web/app/shell.js",
    "PFI/src/pfi_os/app/streamlit_app.py",
)

STAGE1_PRIMARY_NAVIGATION = RTF_PRIMARY_NAVIGATION

STAGE1_LEGACY_ROUTE_ALIASES = {
    "首页": "/home",
    "市场": "/market-research?tab=market",
    "研究": "/market-research?tab=research",
    "持仓": "/investment?tab=holdings",
    "策略实验室": "/market-research/strategy-lab",
    "数据与系统": "/settings?tab=data-system",
}

STAGE2_PAGE_SKELETONS: dict[str, V0211PageSkeleton] = {
    "home": V0211PageSkeleton(
        "home",
        "首页总览",
        "/home",
        "回答当前财务状态和待处理事项",
        ("财务状态", "待办事项", "快捷操作", "最近报告"),
    ),
    "accounts": V0211PageSkeleton(
        "accounts",
        "账户与资产",
        "/accounts",
        "管理账户列表、账户详情、资产趋势和对账状态",
        ("账户总览", "账户列表", "资产趋势", "对账状态"),
    ),
    "ledger": V0211PageSkeleton(
        "ledger",
        "账本流水",
        "/ledger",
        "查看流水列表、搜索筛选、分类复核和导出",
        ("流水列表", "筛选搜索", "分类复核", "导出流水"),
    ),
    "investment": V0211PageSkeleton(
        "investment",
        "投资管理",
        "/investment",
        "查看投资总览、持仓、交易记录和收益分析",
        ("投资总览", "持仓", "交易记录", "收益分析"),
    ),
    "consumption": V0211PageSkeleton(
        "consumption",
        "消费管理",
        "/consumption",
        "查看消费总览、分类、预算、订阅、异常和现金流预测",
        ("消费总览", "分类分析", "预算", "订阅", "异常消费", "现金流预测"),
    ),
    "sync": V0211PageSkeleton(
        "sync",
        "数据源与上传",
        "/sources-upload",
        "上传数据、查看导入批次、管理数据源和待复核记录",
        ("上传中心", "导入中心", "数据源管理", "待复核", "导入历史"),
    ),
    "recommendations": V0211PageSkeleton(
        "recommendations",
        "建议与复盘",
        "/review",
        "查看建议、记录决策和复盘结果",
        ("建议列表", "建议详情", "决策记录", "复盘记录"),
    ),
    "insights": V0211PageSkeleton(
        "insights",
        "报告与洞察",
        "/reports",
        "查看月报、季报、年报、自定义报告和导出",
        ("月报", "季报", "年报", "自定义报告", "导出"),
    ),
    "market_research": V0211PageSkeleton(
        "market_research",
        "市场与研究",
        "/market-research",
        "查看市场观察、研究材料、政策研究和唯一策略实验室",
        ("市场观察", "公司研究", "基金研究", "政策研究", "策略实验室"),
    ),
    "settings": V0211PageSkeleton(
        "settings",
        "设置",
        "/settings",
        "管理账户偏好、数据与系统、隐私、本地存储、反馈、主题和备份",
        ("账户偏好", "数据与系统", "隐私与本地存储", "反馈偏好", "主题语言", "备份恢复"),
    ),
}

STAGE2_FORBIDDEN_VISIBLE_TEXT = (
    "运行边界",
    "使用限制",
    "隐私边界",
    "不做实盘自动下单",
    "Task Pack",
    "Demo",
    "Prototype",
    "AI 演示",
    "运行反馈控制台",
    "多模态交互反馈",
    "手机预览",
    "证据抽屉",
    "运行证据",
    "任务中心",
)

STAGE3_OPERATION_FLOWS: tuple[V0211OperationFlow, ...] = (
    V0211OperationFlow(
        "upload_import",
        "数据源与上传",
        "/sources-upload?tab=upload",
        ("上传中心", "解析预览", "字段映射", "确认入库", "进入账本复核"),
        ("上传状态", "解析预览", "导入摘要", "待复核队列"),
        (
            "未选择文件时显示中文提示，不制造记录数",
            "选择真实文件后显示文件名、大小、字段映射和待复核路径",
            "确认入库必须走后端或本地服务；失败时显示中文错误",
        ),
    ),
    V0211OperationFlow(
        "ledger_review_export",
        "账本流水",
        "/ledger?tab=review",
        ("账本筛选", "分类选择", "保存复核", "导出流水"),
        ("筛选状态", "分类复核状态", "导出状态"),
        (
            "无真实流水时显示中文空状态",
            "筛选、分类和复核动作必须改变页面状态",
            "导出路径只导出当前真实列表或空表头，不生成虚构流水",
        ),
    ),
    V0211OperationFlow(
        "holdings_edit",
        "投资管理",
        "/investment?tab=holdings",
        ("持仓编辑表单", "新增持仓", "保存修改", "放弃未提交草稿"),
        ("未提交草稿", "持仓摘要", "保存状态"),
        (
            "浏览器缓存只允许保存明确标注的未提交草稿",
            "生产保存必须调用本地 API 或后端服务",
            "无真实持仓时显示中文空状态，不伪造持仓",
        ),
    ),
    V0211OperationFlow(
        "settings_save",
        "设置",
        "/settings",
        ("账户偏好", "主题语言", "保存设置", "恢复默认"),
        ("设置保存状态", "反馈偏好状态", "本机设置摘要"),
        (
            "设置只在设置页显示",
            "保存和恢复动作必须改变设置页状态",
            "业务页面默认不展示反馈控制台或设置侧栏",
        ),
    ),
)

STAGE4_PERSISTENCE_SYNC_SURFACES: tuple[V0211PersistenceSyncSurface, ...] = (
    V0211PersistenceSyncSurface(
        "holdings_sqlite",
        "持仓 SQLite 保存",
        "V021HoldingsPersistenceService",
        (
            "snapshot_id",
            "instrument_id",
            "display_name",
            "quantity",
            "average_cost",
            "market_price",
            "currency",
            "portfolio_id",
            "as_of",
            "metadata.note",
        ),
        (
            "保存持仓修改必须调用 /api/holdings",
            "后端必须写入 v021_holding_snapshots 和 v021_position_adjustments",
            "浏览器缓存只允许未提交草稿，不能作为生产保存来源",
        ),
    ),
    V0211PersistenceSyncSurface(
        "refresh_reopen_readback",
        "刷新和重启后读取",
        "SQLite operational database",
        ("db_path", "snapshot_count", "adjustment_count", "rows"),
        (
            "页面保存后刷新必须从 /api/holdings 重新读取",
            "重启本机服务后仍能从同一 SQLite 读取持仓",
            "SQLite 查询能看到刚保存的 snapshot 和 adjustment",
        ),
    ),
    V0211PersistenceSyncSurface(
        "home_investment_report_sync",
        "首页、投资和报告同步",
        "PFIV021OperationalReadModelV1",
        (
            "home.net_worth_cny",
            "home.investment_market_value_cny",
            "investment.market_value_cny",
            "investment.unrealized_pnl_cny",
            "report.holding_count",
            "report.market_value_cny",
        ),
        (
            "首页摘要、投资管理和报告与洞察必须读取同一运行读模型",
            "修改持仓后三个页面展示的投资市值必须一致",
            "正式库无真实持仓时只显示中文空状态，不伪造收益",
        ),
    ),
)


def build_v0211_stage0_contract() -> dict[str, object]:
    return {
        "schema": "PFIV0211ProductUIRecoveryStage0ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S0 准备轮",
        "task_id": STAGE0_TASK_ID,
        "project_root": "CodexProject/PFI",
        "total_execution_stages": TOTAL_EXECUTION_STAGES,
        "one_run_max_stage_count": 1,
        "current_stage_only": True,
        "stage_parent_child_rule": "Stage is the pursuing-goal run gate; phase and task are children inside each Stage.",
        "product_register": "product",
        "source_files": [asdict(item) for item in SOURCE_FILES],
        "primary_navigation_default": RTF_PRIMARY_NAVIGATION,
        "primary_navigation_markdown_variant": MARKDOWN_PRIMARY_NAVIGATION,
        "legacy_route_aliases": LEGACY_ROUTE_ALIASES,
        "execution_stages": [asdict(item) for item in EXECUTION_STAGES],
        "decisions": [asdict(item) for item in DECISIONS],
        "stage0_forbidden_file_changes": STAGE0_FORBIDDEN_FILE_CHANGES,
        "stage0_stop_conditions": (
            "开始修改正式 Web Shell",
            "声明 v0.2.1.1 已完成",
            "把 Stage 1-5 提前并入 Stage 0",
            "继续把当前 v0.2.1 前端优化写成正式交付完成",
            "用字符串检查替代后续真实浏览器行为验收",
        ),
        "stage1_entry_conditions": (
            "Stage 0 合同测试通过",
            "路线锁文档存在",
            "三基文件已记录当前任务和下一轮边界",
            "工作区未因 Stage 0 触碰正式 UI shell",
        ),
    }


def build_v0211_stage1_contract() -> dict[str, object]:
    stage = next(item for item in EXECUTION_STAGES if item.stage_id == "S1")
    return {
        "schema": "PFIV0211ProductUIRecoveryStage1ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S1 产品壳与路由",
        "task_id": STAGE1_TASK_ID,
        "project_root": "CodexProject/PFI",
        "primary_navigation_count": len(STAGE1_PRIMARY_NAVIGATION),
        "primary_navigation": STAGE1_PRIMARY_NAVIGATION,
        "legacy_route_aliases": STAGE1_LEGACY_ROUTE_ALIASES,
        "delivery_focus": stage.delivery_focus,
        "forbidden_work": stage.forbidden_work,
        "acceptance_gate": stage.acceptance_gate,
        "browser_route_contract": {
            "state_source": "hash route",
            "click_updates_history": True,
            "back_forward_supported": True,
            "home_route": "/home",
            "strategy_lab_route": "/market-research/strategy-lab",
        },
        "home_forbidden_visible_text": (
            "运行边界",
            "Task Pack",
            "Demo",
            "Prototype",
            "手机预览",
            "运行反馈控制台",
            "多模态交互反馈",
        ),
        "stage1_non_goals": (
            "不做图表",
            "不做上传闭环",
            "不做持仓编辑",
            "不做报告",
            "不声明 v0.2.1.1 完成",
        ),
    }


def build_v0211_stage2_contract() -> dict[str, object]:
    stage = next(item for item in EXECUTION_STAGES if item.stage_id == "S2")
    return {
        "schema": "PFIV0211ProductUIRecoveryStage2ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S2 页面骨架与去 AI 化",
        "task_id": STAGE2_TASK_ID,
        "project_root": "CodexProject/PFI",
        "primary_navigation": STAGE1_PRIMARY_NAVIGATION,
        "page_skeletons": {
            key: {
                "label": value.label,
                "route": value.route,
                "purpose": value.purpose,
                "secondary_tabs": value.secondary_tabs,
            }
            for key, value in STAGE2_PAGE_SKELETONS.items()
        },
        "delivery_focus": stage.delivery_focus,
        "forbidden_work": stage.forbidden_work,
        "acceptance_gate": stage.acceptance_gate,
        "forbidden_visible_text": STAGE2_FORBIDDEN_VISIBLE_TEXT,
        "settings_only_controls": (
            "反馈偏好",
            "触感反馈",
            "声音反馈",
            "视觉反馈",
            "主题语言",
            "备份恢复",
        ),
        "stage2_non_goals": (
            "不做数据库 migration",
            "不做持仓 SQLite 持久化闭环",
            "不做真实图表数据接入",
            "不使用 demo/sample/synthetic/fixture/mock/fake 数据作为正式产品数据源",
        ),
    }


def build_v0211_stage3_contract() -> dict[str, object]:
    stage = next(item for item in EXECUTION_STAGES if item.stage_id == "S3")
    return {
        "schema": "PFIV0211ProductUIRecoveryStage3ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S3 真实操作流",
        "task_id": STAGE3_TASK_ID,
        "project_root": "CodexProject/PFI",
        "current_stage_only": True,
        "primary_navigation": STAGE1_PRIMARY_NAVIGATION,
        "operation_flows": [asdict(item) for item in STAGE3_OPERATION_FLOWS],
        "delivery_focus": stage.delivery_focus,
        "forbidden_work": stage.forbidden_work,
        "acceptance_gate": stage.acceptance_gate,
        "browser_behavior_required": (
            "点击一级入口和二级入口后，操作面板必须出现对应中文状态",
            "点击主要操作按钮必须改变页面状态、表格、摘要或状态条",
            "无真实数据时显示中文空状态，不用演示数据填充",
        ),
        "production_persistence_policy": (
            "持仓生产保存不得写入 localStorage、sessionStorage 或 IndexedDB",
            "localStorage 只允许保存明确标注的未提交草稿",
            "上传确认和持仓保存必须调用后端 API 或本地服务；失败要显示中文错误状态",
        ),
        "stage3_non_goals": (
            "不声明 Stage 4 持久化与同步完成",
            "不声明 Stage 5 真实图表与最终验收完成",
            "不新增测试数据、样例流水、模拟持仓或虚构财务事实",
        ),
    }


def build_v0211_stage4_contract() -> dict[str, object]:
    stage = next(item for item in EXECUTION_STAGES if item.stage_id == "S4")
    return {
        "schema": "PFIV0211ProductUIRecoveryStage4ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S4 持久化与同步",
        "task_id": STAGE4_TASK_ID,
        "project_root": "CodexProject/PFI",
        "current_stage_only": True,
        "delivery_focus": stage.delivery_focus,
        "forbidden_work": stage.forbidden_work,
        "acceptance_gate": stage.acceptance_gate,
        "persistence_surfaces": [asdict(item) for item in STAGE4_PERSISTENCE_SYNC_SURFACES],
        "sqlite_contract": {
            "service": "V021HoldingsPersistenceService",
            "tables": ("v021_holding_snapshots", "v021_position_adjustments"),
            "write_endpoint": "/api/holdings",
            "read_endpoint": "/api/holdings",
            "read_model_endpoint": "/api/read-model",
            "report_endpoint": "/api/reports/holdings",
        },
        "browser_e2e_required": (
            "打开投资管理 > 持仓",
            "新增或编辑持仓并点击保存修改",
            "查询 SQLite 中 snapshot 和 adjustment",
            "刷新页面后从后端读回",
            "重启本机服务后再次读回",
            "首页总览、投资管理、报告与洞察读取同一持仓读模型",
        ),
        "stage4_non_goals": (
            "不声明 Stage 5 图表与最终验收完成",
            "不伪造账户、收益、消费或持仓趋势",
            "不声明真实账户生产联通",
            "不把 demo/sample/synthetic/fixture/mock/fake 数据作为正式产品数据源",
        ),
    }


def v0211_stage_ids() -> tuple[str, ...]:
    return tuple(stage.stage_id for stage in EXECUTION_STAGES)


def v0211_default_navigation_labels() -> tuple[str, ...]:
    return RTF_PRIMARY_NAVIGATION


def v0211_stage1_navigation_labels() -> tuple[str, ...]:
    return STAGE1_PRIMARY_NAVIGATION


def v0211_stage2_page_labels() -> tuple[str, ...]:
    return tuple(item.label for item in STAGE2_PAGE_SKELETONS.values())


def v0211_stage3_operation_flow_ids() -> tuple[str, ...]:
    return tuple(item.flow_id for item in STAGE3_OPERATION_FLOWS)


def v0211_stage4_persistence_surface_ids() -> tuple[str, ...]:
    return tuple(item.surface_id for item in STAGE4_PERSISTENCE_SYNC_SURFACES)
