from __future__ import annotations

from dataclasses import asdict, dataclass


VERSION_NAME = "v0.2.1 前端优化"
STAGE0_TASK_ID = "V021-P0-S0-T01"
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
        "display_format": "CNY/AUD=4.70（YYYYMMDD--HH:MM）",
        "example_display": "CNY/AUD=4.70（20260627--06:00）",
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


def v021_navigation_labels() -> tuple[str, ...]:
    return tuple(entry.label for entry in NAVIGATION_ENTRIES)


def v021_stage_task_ids() -> tuple[str, ...]:
    return tuple(task.task_id for task in STAGE_TASKS)
