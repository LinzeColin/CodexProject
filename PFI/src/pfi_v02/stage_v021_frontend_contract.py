from __future__ import annotations

from dataclasses import asdict, dataclass


VERSION_NAME = "v0.2.1 前端优化"
STAGE0_TASK_ID = "V021-P0-S0-T01"
STAGE1_TASK_IDS = (
    "V021-P1-S1-T01",
    "V021-P1-S1-T02",
    "V021-P1-S1-T03",
    "V021-P1-S1-T04",
)
STAGE2_TASK_IDS = (
    "V021-P2-S2-T01",
    "V021-P2-S2-T02",
    "V021-P2-S2-T03",
)
STAGE3_TASK_IDS = (
    "V021-P3-S3-T01",
    "V021-P3-S3-T02",
)
STAGE4_TASK_IDS = (
    "V021-P4-S4-T01",
    "V021-P4-S4-T02",
    "V021-P4-S4-T03",
    "V021-P4-S4-T04",
)
STAGE5_TASK_IDS = (
    "V021-P5-S5-T01",
    "V021-P5-S5-T02",
)
STAGE6_TASK_IDS = (
    "V021-P6-S6-T01",
    "V021-P6-S6-T02",
    "V021-P6-S6-T03",
)
STAGE7_TASK_IDS = (
    "V021-P7-S7-T01",
    "V021-P7-S7-T02",
)
STAGE8_TASK_IDS = (
    "V021-P8-S8-T01",
    "V021-P8-S8-T02",
    "V021-P8-S8-T03",
)
BASE_CURRENCY = "CNY"
UI_TARGET = "PFI/web HTML shell"


@dataclass(frozen=True)
class V021NavigationEntry:
    index: int
    label: str
    route: str
    page_owner: str
    entry_type: str
    creates_duplicate_workspace: bool


@dataclass(frozen=True)
class V021StageTask:
    phase: str
    stage: str
    task_id: str
    task: str
    done_standard: str


NAVIGATION_ENTRIES: tuple[V021NavigationEntry, ...] = (
    V021NavigationEntry(1, "首页总览", "/home", "首页总览", "v02_primary", False),
    V021NavigationEntry(2, "账户与资产", "/accounts", "账户与资产", "v02_primary", False),
    V021NavigationEntry(3, "账本流水", "/ledger", "账本流水", "v02_primary", False),
    V021NavigationEntry(4, "投资管理", "/investment", "投资管理", "v02_primary", False),
    V021NavigationEntry(5, "消费管理", "/consumption", "消费管理", "v02_primary", False),
    V021NavigationEntry(6, "数据源与上传", "/sources-upload", "数据源与上传", "v02_primary", False),
    V021NavigationEntry(7, "建议与复盘", "/review", "建议与复盘", "v02_primary", False),
    V021NavigationEntry(8, "报告与洞察", "/reports", "报告与洞察", "v02_primary", False),
    V021NavigationEntry(9, "首页", "/home", "首页总览", "v01_alias", False),
    V021NavigationEntry(10, "市场", "/investment?tab=market", "投资管理", "v01_alias", False),
    V021NavigationEntry(11, "研究", "/investment?tab=research", "投资管理", "v01_alias", False),
    V021NavigationEntry(12, "持仓", "/investment?tab=holdings", "投资管理", "v01_alias", False),
    V021NavigationEntry(13, "策略实验室", "/investment/strategy-lab", "投资管理", "v01_alias", False),
    V021NavigationEntry(14, "数据与系统", "/settings?tab=data-system", "设置", "v01_alias", False),
    V021NavigationEntry(15, "设置", "/settings", "设置", "settings", False),
)

FORBIDDEN_VISIBLE_NAV_GROUP_LABELS: tuple[str, ...] = (
    "PFI 2.0 当前入口",
    "PFI 1.0 兼容入口",
    "V0.2 当前入口",
    "V0.1 兼容入口",
    "运行边界",
    "Boundary",
    "Non-execution boundary",
)

FORBIDDEN_PRODUCT_L1_ENTRIES: tuple[str, ...] = (
    "QBVS",
    "Alpha",
    "Ralpha",
    "System",
    "Development",
    "系统与开发",
)

STAGE_TASKS: tuple[V021StageTask, ...] = (
    V021StageTask("P0", "S0 基线", "V021-P0-S0-T01", "建立 v0.2.1 任务记录", "文档、版本、范围明确。"),
    V021StageTask("P1", "S1 导航合并", "V021-P1-S1-T01", "删除新旧入口分组标题", "入口统一显示，无分组字样。"),
    V021StageTask("P1", "S1 导航合并", "V021-P1-S1-T02", "数据源与同步改为数据源与上传", "全站展示新名称。"),
    V021StageTask("P1", "S1 导航合并", "V021-P1-S1-T03", "低操作导入中心改为导入中心", "全站展示导入中心。"),
    V021StageTask("P1", "S1 导航合并", "V021-P1-S1-T04", "合并策略实验室", "只有一个策略实验室路由和状态源。"),
    V021StageTask("P2", "S2 文案清理", "V021-P2-S2-T01", "全局中文化", "禁用英文扫描通过。"),
    V021StageTask("P2", "S2 文案清理", "V021-P2-S2-T02", "删除运行边界 UI 板块", "用户界面不出现运行边界模块。"),
    V021StageTask("P2", "S2 文案清理", "V021-P2-S2-T03", "删除桌面手机预览框", "桌面无手机演示框，手机真实响应式可用。"),
    V021StageTask("P3", "S3 设置页", "V021-P3-S3-T01", "设置页独立路由", "默认不显示右侧设置。"),
    V021StageTask("P3", "S3 设置页", "V021-P3-S3-T02", "运行反馈控制台移入设置", "设置页可配置反馈。"),
    V021StageTask("P4", "S4 趋势模型", "V021-P4-S4-T01", "新增统一趋势数据结构", "三类页面可读同一趋势合同。"),
    V021StageTask("P4", "S4 趋势模型", "V021-P4-S4-T02", "账户与资产折线图", "现金 / 净资产趋势显示。"),
    V021StageTask("P4", "S4 趋势模型", "V021-P4-S4-T03", "投资管理折线图", "市值 / 总收益 / 现金仓位显示。"),
    V021StageTask("P4", "S4 趋势模型", "V021-P4-S4-T04", "消费管理折线图", "支出 / 预算 / 现金流显示。"),
    V021StageTask("P5", "S5 上传中心", "V021-P5-S5-T01", "上传中心", "上传、拖拽、状态、失败反馈可用。"),
    V021StageTask("P5", "S5 上传中心", "V021-P5-S5-T02", "导入中心", "批次、摘要、复核入口可用。"),
    V021StageTask("P6", "S6 持仓持久化", "V021-P6-S6-T01", "持仓编辑数据模型", "adjustment 和 snapshot 可写入数据库。"),
    V021StageTask("P6", "S6 持仓持久化", "V021-P6-S6-T02", "持仓编辑服务", "新增、修改、软删除、读取测试通过。"),
    V021StageTask("P6", "S6 持仓持久化", "V021-P6-S6-T03", "持仓编辑前端", "刷新 / 重启后修改仍存在。"),
    V021StageTask("P7", "S7 流畅度", "V021-P7-S7-T01", "所有入口和按钮可点击", "自动遍历无死按钮。"),
    V021StageTask("P7", "S7 流畅度", "V021-P7-S7-T02", "页面反馈统一", "成功、失败、进行中都有反馈。"),
    V021StageTask("P8", "S8 验收", "V021-P8-S8-T01", "前端合同测试", "新增测试通过。"),
    V021StageTask("P8", "S8 验收", "V021-P8-S8-T02", "浏览器验收", "桌面 / 手机关键路径通过。"),
    V021StageTask("P8", "S8 验收", "V021-P8-S8-T03", "命令验收", "单测、JS 检查、治理、diff 检查通过。"),
)


def build_v021_fx_badge_contract() -> dict[str, object]:
    return {
        "base_currency": BASE_CURRENCY,
        "quote_pair": "CNY/AUD",
        "semantic": "one AUD converted to CNY, shown as CNY per AUD for owner readability",
        "placement": "top_right",
        "visible_on_all_pages": True,
        "display_format": "CNY/AUD=4.70（YYYY/MM/DD HH:MM）",
        "example_display": "CNY/AUD=4.70（2026/06/27 06:00）",
        "snapshot_time_local": "06:00",
        "snapshot_timezone": "Australia/Sydney",
        "refresh_policy": "read the current local day's 06:00 exchange snapshot; do not invent rates when unavailable",
        "missing_data_state": "汇率数据待更新",
    }


def build_v021_feedback_contract() -> dict[str, object]:
    return {
        "ui_target": UI_TARGET,
        "formal_delivery_surface": "HTML",
        "settings_route": "/settings",
        "default_visible_on_business_pages": False,
        "feedback_controls": (
            "运行反馈控制台",
            "多模态反馈",
            "触感反馈强度",
            "声音反馈",
            "视觉反馈",
            "通知反馈",
            "反馈测试",
            "无障碍反馈",
        ),
        "haptic_levels": ("关闭", "轻", "标准", "强"),
        "browser_vibration_policy": "call navigator.vibrate only after user action and silently degrade when unavailable",
    }


def build_v021_stage0_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage0ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S0 基线",
        "task_id": STAGE0_TASK_ID,
        "project_root": "CodexProject/PFI",
        "scope": (
            "PFI 前端信息架构",
            "HTML Web Shell 交互",
            "中文化",
            "数据可视化",
            "上传命名",
            "设置页整合",
            "持仓编辑持久化",
            "CNY 基准与 CNY/AUD 顶栏汇率",
        ),
        "non_scope": (
            "不重构 QBVS",
            "不新增 Alpha/Ralpha/System/Development 产品一级入口",
            "不声明真实账户生产联通",
            "不执行实盘下单、支付提交或券商提交",
            "不把后续 stage 的 UI 实现塞进 stage0",
        ),
        "currency_contract": build_v021_fx_badge_contract(),
        "feedback_contract": build_v021_feedback_contract(),
        "navigation_entries": [asdict(entry) for entry in NAVIGATION_ENTRIES],
        "forbidden_visible_nav_group_labels": FORBIDDEN_VISIBLE_NAV_GROUP_LABELS,
        "forbidden_product_l1_entries": FORBIDDEN_PRODUCT_L1_ENTRIES,
        "stage_tasks": [asdict(task) for task in STAGE_TASKS],
        "stage0_acceptance": (
            "版本命名为 v0.2.1 前端优化",
            "任务记录写明本轮只做 PFI 前端、交互、图表、上传命名、设置页、持仓编辑持久化准备",
            "CNY 是系统基准货币，所有页面顶部右上角显示 CNY/AUD 06:00 汇率快照",
            "UIUX 多模态反馈以 HTML Web Shell 为正式目标，并收敛到设置页",
            "不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口",
        ),
    }


def build_v021_stage1_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage1ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S1 导航合并",
        "task_ids": STAGE1_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "navigation_entries": [asdict(entry) for entry in NAVIGATION_ENTRIES],
        "visible_navigation_label_order": v021_navigation_labels(),
        "primary_entry_count": len(NAVIGATION_ENTRIES),
        "forbidden_visible_nav_group_labels": FORBIDDEN_VISIBLE_NAV_GROUP_LABELS,
        "renamed_entries": {
            "数据源与同步": "数据源与上传",
            "低操作导入中心": "导入中心",
        },
        "single_route_contract": {
            "label": "策略实验室",
            "route": "/investment/strategy-lab",
            "page_owner": "投资管理",
            "workspace": "investment",
            "creates_duplicate_workspace": False,
        },
        "stage1_acceptance": (
            "不显示新旧入口分组标题",
            "15 个一级入口按合同顺序显示",
            "数据源与同步在用户可见 Web Shell 中改为数据源与上传",
            "低操作导入中心在用户可见 Web Shell 中改为导入中心",
            "策略实验室只路由到投资管理下的 /investment/strategy-lab，不创建 strategy 一级 workspace",
            "设置入口可点击，数据与系统旧入口映射到设置页",
        ),
    }


def build_v021_stage2_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage2ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S2 文案清理",
        "task_ids": STAGE2_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "acceptance": (
            "全局用户可见文案中文化，保留必要技术格式和文件格式 token。",
            "用户界面不出现运行边界、安全边界、验收边界、查看边界或英文 Boundary 模块。",
            "桌面端不出现手机演示框或预览框；手机端使用真实响应式布局。",
            "Stage 5/6 动态证据抽屉不得暴露 Review lifecycle、PFI Context Export、Synthetic E2E、TaskPack acceptance gates 等英文交付噪音。",
        ),
        "forbidden_visible_english_terms": (
            "Review lifecycle",
            "PFI Context Export",
            "Synthetic E2E",
            "Rollback plan",
            "Follow-up list",
            "owner docs",
            "diff summary",
            "changed-only governance",
            "focused tests",
            "Context Snapshot",
            "live trade",
            "read-only context",
            "owner gate",
            "Top N",
            "tradeoff",
            "parser / raw / batch",
        ),
        "forbidden_boundary_ui_terms": (
            "运行边界",
            "使用限制",
            "隐私边界",
            "数据边界",
            "安全边界",
            "验收边界",
            "查看边界",
            "只读边界",
            "只读",
            "实盘",
            "无实盘执行",
            "不下单",
            "不支付",
            "不登录",
            "交易密码",
            "Boundary",
            "Non-execution boundary",
        ),
        "forbidden_preview_terms": (
            "桌面手机预览框",
            "手机演示框",
            "desktop preview",
            "mobile preview",
            "phone-preview",
            "mobile-preview",
            "device-preview",
        ),
        "required_visible_chinese_terms": (
            "未提交草稿",
            "SQLite",
            "本机数据管理",
            "复盘生命周期",
            "PFI 上下文导出",
            "外部系统上下文出口",
            "解析器",
            "校验值",
        ),
        "forbidden_visible_stage_labels": (
            "第 3 阶段",
            "第 4 阶段",
            "第 5 阶段",
            "第 6 阶段",
            "Stage 3",
            "Stage 4",
            "Stage 5",
            "Stage 6",
        ),
        "allowed_technical_tokens": (
            "PFI",
            "CNY/AUD",
            "CSV",
            "ZIP",
            "JSON",
            "Markdown",
            "PDF",
            "CDR",
            "Open Banking",
            "Moomoo",
            "ETF",
            "PIT",
            "A/B/C/D",
        ),
    }


def build_v021_stage3_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage3ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S3 设置页与全局搜索",
        "task_ids": STAGE3_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "settings_contract": {
            "route": "/settings",
            "legacy_data_system_route": "/settings?tab=data-system",
            "presentation": "primary_workspace",
            "default_business_pages_show_settings_sidebar": False,
            "forbidden_surfaces": ("settings-drawer", "right-settings", "side-settings-panel"),
            "feedback_controls": build_v021_feedback_contract()["feedback_controls"],
        },
        "global_search_contract": {
            "surface": "top_bar_global_search",
            "html_id": "global-search",
            "result_container_id": "global-search-results",
            "scope": (
                "15 个一级导航入口",
                "V0.1 兼容入口别名",
                "工作区功能卡",
                "功能面板",
                "任务中心条目",
                "决策队列表格行",
                "设置页反馈控制项",
            ),
            "fuzzy_match_modes": (
                "substring",
                "subsequence",
                "alias_keywords",
                "English technical token",
            ),
            "keyboard_contract": ("ArrowDown", "ArrowUp", "Enter", "Escape", "Meta/Ctrl+K"),
            "ui_reference": "VS Code / Google Chrome style command search: input, ranked list, category, path, action hint",
            "empty_state": "没有匹配结果",
        },
        "acceptance": (
            "设置页通过 /settings 独立路由进入，并作为主工作区展示。",
            "数据与系统旧入口映射到 /settings?tab=data-system。",
            "业务页默认不展示右侧设置面板；运行反馈控制台、多模态反馈、触感、声音、视觉、通知和反馈测试进入设置页。",
            "顶部全局搜索支持跨入口、功能、任务、表格行和设置控件的模糊搜索。",
            "搜索结果必须显示分类、路径和操作提示，并支持键盘上下选择、Enter 打开、Escape 关闭。",
        ),
    }


def build_v021_stage4_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage4ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S4 趋势模型",
        "task_ids": STAGE4_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "trend_data_contract": {
            "object_name": "UNIFIED_TREND_DATA",
            "base_currency": BASE_CURRENCY,
            "time_grain": "month",
            "series_shape": {
                "id": "stable_metric_id",
                "label": "用户可读中文指标名",
                "unit": "CNY",
                "values": "ordered numeric list aligned to periods",
            },
            "required_pages": {
                "accounts": ("现金", "净资产", "总资产", "总负债"),
                "investment": ("投资市值", "总收益", "未实现盈亏", "现金仓位"),
                "consumption": ("本月支出", "预算剩余", "固定支出", "弹性支出", "现金流预测"),
            },
            "missing_data_state": "数据不足时显示中文空状态，不伪造收益或支出。",
        },
        "chart_contract": {
            "renderer": "Canvas2D line chart",
            "surface": "main_workspace_trend_panel",
            "html_markers": ("data-trend-panel", "data-trend-title", "data-trend-legend", "data-trend-empty"),
            "visible_without_hover": True,
            "direct_labels": True,
            "mobile_responsive": True,
            "color_role_count": 3,
        },
        "acceptance": (
            "账户与资产、投资管理、消费管理三类页面读取同一个统一趋势数据结构。",
            "账户与资产显示现金和净资产趋势。",
            "投资管理显示市值、总收益和现金仓位趋势。",
            "消费管理显示支出、预算和现金流趋势。",
            "趋势图必须有中文标题、图例、CNY 基准、中文空状态和非 hover 可读信息。",
            "不接真实账户、不伪造实时数据、不新增交易或支付动作。",
        ),
    }


def build_v021_stage5_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage5ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S5 上传中心",
        "task_ids": STAGE5_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "upload_center_contract": {
            "route": "/sources-upload",
            "workspace": "sync",
            "surface": "sync_workspace_upload_center",
            "accepted_file_types": ("CSV", "ZIP", "XLS", "XLSX"),
            "max_file_mb": 50,
            "html_markers": (
                "data-upload-import-panel",
                "data-upload-center",
                "data-upload-dropzone",
                "data-upload-input",
                "data-upload-status",
                "data-upload-error",
                "data-upload-file-list",
            ),
            "required_interactions": (
                "click_file_picker",
                "dragenter",
                "dragover",
                "dragleave",
                "drop",
                "local_validation",
                "status_update",
            ),
            "failure_feedback": (
                "空选择中文提示",
                "不支持的文件类型中文提示",
                "文件过大中文提示",
            ),
        },
        "import_center_contract": {
            "surface": "sync_workspace_import_center",
            "html_markers": (
                "data-import-center",
                "data-import-summary",
                "data-import-batches",
                "data-import-review-link",
            ),
            "batch_fields": ("批次", "来源", "文件数", "记录数", "待复核", "状态"),
            "summary_fields": ("已选择文件", "预计记录", "待复核", "失败反馈"),
            "review_entry": {
                "label": "进入账本复核",
                "target_workspace": "ledger",
                "target_route": "/ledger",
            },
        },
        "acceptance": (
            "数据源与上传页面必须显示上传中心，支持点击选择文件和拖拽投放。",
            "上传中心必须显示等待、已选择、预检完成和失败反馈四类中文状态。",
            "导入中心必须显示批次、摘要、待复核数量和复核入口。",
            "复核入口必须可点击进入账本流水，不触发真实外部上传、支付、券商或自动下单。",
            "原始用户数据不进入公共 Git；Stage 5 只交付 HTML Web Shell 合同和本地前端交互。",
        ),
    }


def build_v021_stage6_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage6ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S6 持仓持久化",
        "task_ids": STAGE6_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "sqlite_contract": {
            "default_db_path": "$PFI_DATA_HOME/private/operational/pfi.sqlite",
            "service_module": "pfi_v02.stage_v021_holdings_persistence",
            "schema": "PFIV021HoldingsPersistenceV1",
            "tables": ("v021_holding_snapshots", "v021_position_adjustments"),
            "snapshot_required_fields": (
                "snapshot_id",
                "portfolio_id",
                "instrument_id",
                "display_name",
                "quantity",
                "average_cost",
                "market_price",
                "market_value",
                "currency",
                "source_id",
                "as_of",
            ),
            "adjustment_required_fields": (
                "adjustment_id",
                "snapshot_id",
                "portfolio_id",
                "instrument_id",
                "adjustment_type",
                "changes_json",
                "reason",
                "status",
                "human_review_required",
            ),
        },
        "service_contract": {
            "class": "V021HoldingsPersistenceService",
            "required_methods": (
                "initialize",
                "upsert_snapshot",
                "get_snapshot",
                "list_snapshots",
                "soft_delete_snapshot",
                "create_adjustment",
                "update_adjustment",
                "soft_delete_adjustment",
                "get_adjustment",
                "list_adjustments",
                "persistence_summary",
            ),
            "crud_coverage": ("create", "read", "update", "soft_delete"),
            "default_seed": "build_v021_demo_holding_snapshots",
        },
        "frontend_contract": {
            "route": "/investment?tab=holdings",
            "workspace": "investment",
            "surface": "investment_holdings_persistence_panel",
            "html_markers": (
                "data-holdings-persistence-panel",
                "data-holdings-persistence-status",
                "data-holdings-summary",
                "data-holdings-rows",
                "data-holding-field",
                "data-holdings-save",
                "data-holdings-add",
                "data-holdings-reset",
            ),
            "draft_storage_key": "pfi-v021-unsubmitted-holdings-draft",
            "runtime_api": "/api/holdings",
            "required_interactions": (
                "edit_quantity",
                "edit_market_price",
                "save_to_runtime_api",
                "restore_after_service_restart",
                "add_holding",
                "soft_delete_holding",
            ),
        },
        "acceptance": (
            "持仓编辑数据模型必须把 snapshot 和 adjustment 写入 SQLite operational database。",
            "持仓编辑服务必须覆盖新增、修改、软删除、读取，并有目标单测证明。",
            "持仓前端必须能编辑数量和价格，点击保存后通过 /api/holdings 写入 SQLite。",
            "浏览器 localStorage 只能保存明确标注的未提交草稿，不能作为生产持久化来源。",
            "私有持仓和 SQLite runtime 数据不进入公共 Git。",
        ),
    }


def build_v021_stage7_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage7ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S7 流畅度",
        "task_ids": STAGE7_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "click_safe_contract": {
            "scope": (
                "15 个一级入口",
                "V0.1 兼容入口",
                "顶部操作按钮",
                "工作区功能按钮",
                "功能面板按钮",
                "上传 / 导入 / 持仓按钮",
                "任务中心按钮",
                "证据抽屉按钮",
                "命令面板按钮",
                "表格控制按钮",
            ),
            "required_routes": tuple(entry.route for entry in NAVIGATION_ENTRIES),
            "required_functions": (
                "applyRouteFromLocation",
                "bindClickSafeFeedback",
                "buildClickSafeInventory",
                "buttonReadableLabel",
                "setActionFeedback",
                "showToast",
            ),
            "browser_validation": "automatic traversal clicks every visible button on desktop and mobile with zero console errors",
            "dead_button_definition": "visible enabled button click produces no route change, panel state change, or unified feedback state",
        },
        "feedback_contract": {
            "surface_marker": "data-action-feedback",
            "toast_marker": "data-toast",
            "region_marker": "data-feedback-region",
            "states": ("progress", "success", "failure"),
            "visible_labels": ("进行中", "成功", "失败"),
            "state_attribute": "data-feedback-state",
            "aria": {
                "region": "aria-live",
                "toast_role": "status",
                "feedback_role": "status",
            },
            "business_page_default": "feedback region is available but settings console remains in settings page",
        },
        "acceptance": (
            "所有可见、未禁用按钮必须能被浏览器自动遍历点击，且无 console error。",
            "一级入口和 V0.1 兼容入口点击后必须进入对应 route 或功能面板。",
            "页面必须统一展示进行中、成功、失败三类反馈，不允许静默失败。",
            "反馈必须可被读屏读取，并保留中文用户可读文案。",
            "Stage 7 不新增交易、支付、券商提交或实盘自动下单能力。",
        ),
    }


def build_v021_stage8_contract() -> dict[str, object]:
    return {
        "schema": "PFIV021FrontendOptimizationStage8ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S8 最终验收",
        "task_ids": STAGE8_TASK_IDS,
        "project_root": "CodexProject/PFI",
        "ui_target": UI_TARGET,
        "acceptance_gate": "PFI-V021-S8-FINAL-ACCEPTANCE-GATE",
        "prior_stage_contracts": (
            "build_v021_stage0_contract",
            "build_v021_stage1_contract",
            "build_v021_stage2_contract",
            "build_v021_stage3_contract",
            "build_v021_stage4_contract",
            "build_v021_stage5_contract",
            "build_v021_stage6_contract",
            "build_v021_stage7_contract",
        ),
        "required_artifacts": (
            "docs/pfi_v02/STAGE_V021_FINAL_ACCEPTANCE_AUDIT.md",
            "docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md",
            "HANDOFF.md",
            "开发记录.md",
            "功能清单.md",
            "模型参数文件.md",
        ),
        "command_validation": {
            "frontend_contract_suite": (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest "
                "PFI.tests.test_v021_stage0_frontend_contract "
                "PFI.tests.test_v021_stage1_navigation_contract "
                "PFI.tests.test_v021_stage2_copy_cleanup_contract "
                "PFI.tests.test_v021_stage3_settings_search_contract "
                "PFI.tests.test_v021_stage4_trend_contract "
                "PFI.tests.test_v021_stage5_upload_import_contract "
                "PFI.tests.test_v021_stage6_holdings_persistence "
                "PFI.tests.test_v021_stage7_clicksafe_feedback "
                "PFI.tests.test_v021_stage8_final_acceptance -q"
            ),
            "full_unittest": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q",
            "web_shell_syntax": "node --check PFI/web/app/shell.js",
            "governance": "python3 scripts/validate_project_governance.py --project PFI",
            "diff_check": "git diff --check -- PFI",
            "macos_app_acceptance": "zsh scripts/macosAppAcceptanceLite.sh --project-root . --summary-json",
        },
        "browser_validation": {
            "desktop_viewport": "1440x1100",
            "mobile_viewport": "390x920",
            "required_routes": tuple(entry.route for entry in NAVIGATION_ENTRIES),
            "required_key_paths": (
                "top_right_fx_badge",
                "global_fuzzy_search",
                "sources_upload_file_picker_and_drag_drop",
                "ledger_review_entry",
                "investment_holdings_persistence",
                "settings_feedback_console",
                "stage7_clicksafe_feedback_states",
            ),
            "required_screenshots": (
                "/tmp/pfi-v021-stage8-final-desktop-verified.png",
                "/tmp/pfi-v021-stage8-final-mobile-verified.png",
            ),
            "console_errors_allowed": 0,
        },
        "local_sync_contract": {
            "github_branch": "main",
            "canonical_checkout": (
                "/Users/linzezhang/Documents/Codex/2026-06-19/"
                "current-phase-phase-0-goal-scope/work/CodexProject"
            ),
            "app_entries": ("/Applications/PFI.app", "~/Downloads/PFI.app", "~/Desktop/PFI.app"),
            "cleanup_scope": ("PFI/__pycache__", "PFI/.pytest_cache", "PFI/**/*.pyc", "temporary stage8 worktree"),
        },
        "safety_boundary": (
            "Stage 8 is validation, documentation, GitHub sync, app refresh and bounded cache cleanup only. "
            "It must not add broker submission, payment execution, live trading, trading password capture, "
            "external upload execution, or QBVS ownership inside PFI."
        ),
        "acceptance": (
            "Stage 0-8 前端合同测试通过。",
            "完整 PFI 单测、JS 语法、项目治理和 diff 检查通过。",
            "桌面和手机浏览器关键路径通过，截图和 console error 结果可追溯。",
            "GitHub main、canonical PFI 文件和 PFI.app 入口一致。",
            "本机非必要 PFI 缓存和本轮临时 worktree 已清理。",
            "无新增交易、支付、券商提交、实盘自动下单或 QBVS 内嵌能力。",
        ),
    }


def v021_navigation_labels() -> tuple[str, ...]:
    return tuple(entry.label for entry in NAVIGATION_ENTRIES)


def v021_stage_task_ids() -> tuple[str, ...]:
    return tuple(task.task_id for task in STAGE_TASKS)
