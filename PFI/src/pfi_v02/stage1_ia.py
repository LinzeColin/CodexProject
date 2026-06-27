from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Stage1Entry:
    index: int
    label: str
    purpose: str
    second_level_areas: tuple[str, ...]
    acceptance_markers: tuple[str, ...]


PRIMARY_ENTRIES: tuple[Stage1Entry, ...] = (
    Stage1Entry(
        1,
        "首页总览",
        "日常入口，让用户直接看到财务状态、数据健康、待处理事项和今日建议。",
        (
            "今日财务状态",
            "账户概览卡",
            "投资快照",
            "消费快照",
            "现金流压力",
            "数据健康快照",
            "今日建议 Top N",
            "待处理事项",
            "最近变化",
            "快捷操作",
        ),
        ("净资产", "账户地图", "投资快照", "消费快照", "数据健康", "今日建议"),
    ),
    Stage1Entry(
        2,
        "账户与资产",
        "表达钱在哪里、资产是什么、负债在哪里，并与数据源分离。",
        (
            "全部账户",
            "投资账户",
            "日常账户",
            "现金账户",
            "资产账户",
            "负债账户",
            "跨币种视图",
            "账户分组",
            "账户对账",
            "账户生命周期",
        ),
        ("DataSource != Account", "Account != AssetInstrument", "账户对账", "跨币种"),
    ),
    Stage1Entry(
        3,
        "账本流水",
        "所有投资、消费、转账、退款、费用、税费、汇率和估值事件的事实层。",
        (
            "全部流水",
            "待分类流水",
            "转账匹配",
            "投资事件",
            "消费事件",
            "退款/冲正",
            "手续费/税费",
            "汇率事件",
            "估值快照",
            "原始证据链",
        ),
        ("消费", "投资", "转账", "退款", "费用", "估值", "汇率", "证据链"),
    ),
    Stage1Entry(
        4,
        "投资管理",
        "多平台投资账户管理、投资行为分析、投资建议、PFI 策略回测、盘感训练和大数据模拟器。",
        (
            "投资总览",
            "持仓管理",
            "投资账户明细",
            "交易记录",
            "收益归因",
            "风险分析",
            "行为复盘",
            "基金分析",
            "贵金属分析",
            "PFI 策略实验室",
            "PFI 大数据模拟器",
            "盘感训练",
            "投资目标",
            "投资建议",
        ),
        ("Moomoo", "支付宝基金", "中国券商", "ABC Bullion", "策略实验室", "盘感训练", "大数据模拟器"),
    ),
    Stage1Entry(
        5,
        "消费管理",
        "多平台日常开支管理、消费行为分析、预算控制、成本优化和消费复盘。",
        (
            "消费总览",
            "日常账户",
            "分类分析",
            "商户/对象分析",
            "预算控制",
            "订阅管理",
            "异常消费",
            "现金流预测",
            "消费行为复盘",
            "生活目标",
            "消费建议",
        ),
        ("支付宝", "微信", "CBA", "银行卡", "信用卡", "订阅", "转账不计消费"),
    ),
    Stage1Entry(
        6,
        "数据源与同步",
        "低操作自动化核心，管理数据源、凭证引用、导入、同步、对账、待复核和只读出口。",
        (
            "数据源列表",
            "连接与凭证",
            "同步控制台",
            "自动采集器",
            "导入收件箱",
            "导入历史",
            "解析器管理",
            "对账中心",
            "待复核队列",
            "新增数据源向导",
            "数据新鲜度",
            "数据质量评分",
            "外部只读接口",
        ),
        ("数据源列表", "凭证", "同步", "导入", "对账", "待复核", "外部只读接口"),
    ),
    Stage1Entry(
        7,
        "建议与复盘",
        "投资、消费、现金流和数据修复建议的证据、动作、状态、复盘生命周期。",
        (
            "建议 Inbox",
            "投资建议",
            "消费建议",
            "现金流建议",
            "数据修复建议",
            "证据与置信度",
            "动作状态",
            "复盘记录",
            "建议失效条件",
        ),
        ("证据", "动作", "状态", "复盘", "失效条件"),
    ),
    Stage1Entry(
        8,
        "报告与洞察",
        "月度、投资、消费、数据质量和只读 context export 报告的证据链出口。",
        (
            "月度报告",
            "投资报告",
            "消费报告",
            "现金流报告",
            "数据质量报告",
            "建议复盘报告",
            "证据链索引",
            "PFI Context Export",
            "报告历史",
        ),
        ("月度", "投资", "消费", "数据质量", "Context Export", "证据链"),
    ),
)

FORBIDDEN_PRIMARY_ENTRY_MARKERS = (
    "Alpha",
    "System",
    "Development",
    "系统与开发",
    "R-prefixed Alpha variant",
)

LEGACY_COMPATIBILITY_ENTRY = {
    "existing_path": "QBVS",
    "current_root": "CodexProject/QBVS",
    "target_location": "独立系统：CodexProject/QBVS",
    "runtime_path": "QBVS/qbvs",
    "policy": "QBVS is independent from PFI. PFI may link to or read handoff evidence, but PFI investment management must not own or cover QBVS.",
}

V01_COMPATIBILITY_ENTRIES: tuple[str, ...] = (
    "首页",
    "市场",
    "研究",
    "持仓",
    "策略实验室",
    "数据与系统",
)


def primary_entry_labels() -> tuple[str, ...]:
    return tuple(entry.label for entry in PRIMARY_ENTRIES)


def v01_compatibility_entry_labels() -> tuple[str, ...]:
    return V01_COMPATIBILITY_ENTRIES


def build_stage1_ia_contract() -> dict[str, object]:
    return {
        "schema": "PFIV02Stage1IAContractV1",
        "project_root": "CodexProject/PFI",
        "primary_entries": [asdict(entry) for entry in PRIMARY_ENTRIES],
        "v01_compatibility_entries": V01_COMPATIBILITY_ENTRIES,
        "forbidden_primary_entry_markers": FORBIDDEN_PRIMARY_ENTRY_MARKERS,
        "legacy_compatibility_entry": LEGACY_COMPATIBILITY_ENTRY,
        "non_execution_boundary": (
            "PFI Stage 1 defines shared facts and contracts only; no trading password, "
            "no broker submission, no payment action, and no automatic real-money order."
        ),
    }
