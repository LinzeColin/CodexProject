from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class V02PrimaryEntry:
    index: int
    label: str
    purpose: str


@dataclass(frozen=True)
class CompatibilityEntry:
    existing_entry: str
    keep_accessible: bool
    current_location: str
    v02_location: str
    compatibility_action: str
    status: str


V02_TARGET_PRIMARY_ENTRIES: tuple[V02PrimaryEntry, ...] = (
    V02PrimaryEntry(1, "首页总览", "日常总入口：财务状态、数据健康、待处理事项和今日建议。"),
    V02PrimaryEntry(2, "账户与资产", "统一查看账户、资产、负债、币种和账户对账状态。"),
    V02PrimaryEntry(3, "账本流水", "统一承接消费、投资、转账、费用、退款、估值和汇率事件。"),
    V02PrimaryEntry(4, "投资管理", "承接持仓、市场观察、策略回测、盘感训练、策略实验室和大数据模拟器。"),
    V02PrimaryEntry(5, "消费管理", "承接日常支出、订阅、预算、异常消费和消费复盘。"),
    V02PrimaryEntry(6, "数据源与同步", "承接数据源、凭证引用、同步、导入、对账、待复核和状态解释。"),
    V02PrimaryEntry(7, "建议与复盘", "承接投资、消费、现金流和数据修复建议的生命周期与复盘。"),
    V02PrimaryEntry(8, "报告与洞察", "承接月度、投资、消费、数据质量、证据链和 PFI context export。"),
)

CURRENT_SIX_WORKSPACE_COMPATIBILITY: tuple[CompatibilityEntry, ...] = (
    CompatibilityEntry("首页", True, "web/index.html side-nav: home", "首页总览", "保留旧按钮；Stage 1 后作为别名或跳转。", "Mapped"),
    CompatibilityEntry("市场", True, "web/index.html side-nav: market", "投资管理 > 市场观察", "保留旧按钮；归入投资管理下的市场观察能力。", "Mapped"),
    CompatibilityEntry("研究", True, "web/index.html side-nav: research", "报告与洞察", "保留旧按钮；研究证据和报告清单归入报告与洞察。", "Mapped"),
    CompatibilityEntry("持仓", True, "web/index.html side-nav: portfolio", "账户与资产 / 投资管理", "保留旧按钮；账户事实归入账户与资产，投资复核归入投资管理。", "Mapped"),
    CompatibilityEntry("策略实验室", True, "web/index.html side-nav: strategy", "投资管理 > 策略实验室", "保留旧按钮；作为投资管理下的核心兼容入口。", "Mapped"),
    CompatibilityEntry("数据与系统", True, "web/index.html side-nav: data", "数据源与同步", "保留旧按钮；系统诊断只作为内部状态，不作为产品一级入口。", "Mapped"),
)

ACTIVE_VIEW_COMPATIBILITY: tuple[CompatibilityEntry, ...] = (
    CompatibilityEntry("首页｜总控驾驶舱", True, "ACTIVE_PFI_VIEW_OPTIONS: command", "首页总览", "保留当前入口；迁移为首页总览默认视图。", "Mapped"),
    CompatibilityEntry("市场｜热点分析", True, "ACTIVE_PFI_VIEW_OPTIONS: hotspots", "投资管理 > 市场观察", "保留当前入口；作为投资管理市场观察视图。", "Mapped"),
    CompatibilityEntry("市场｜情绪分析", True, "ACTIVE_PFI_VIEW_OPTIONS: sentiment", "投资管理 > 市场观察", "保留当前入口；作为市场情绪视图。", "Mapped"),
    CompatibilityEntry("研究｜政策雷达", True, "ACTIVE_PFI_VIEW_OPTIONS: policy", "报告与洞察 > 政策证据", "保留当前入口；作为证据和报告能力。", "Mapped"),
    CompatibilityEntry("研究｜报告中心", True, "ACTIVE_PFI_VIEW_OPTIONS: reports", "报告与洞察", "保留当前入口；作为报告与洞察主视图。", "Mapped"),
    CompatibilityEntry("持仓｜持仓复核", True, "ACTIVE_PFI_VIEW_OPTIONS: holdings", "投资管理 > 持仓复核", "保留当前入口；只读复核，不自动下单。", "Mapped"),
    CompatibilityEntry("持仓｜个人画像", True, "ACTIVE_PFI_VIEW_OPTIONS: profile", "建议与复盘 > 行为画像", "保留当前入口；作为复盘输入。", "Mapped"),
    CompatibilityEntry("策略实验室｜单标的回测", True, "ACTIVE_PFI_VIEW_OPTIONS: single", "投资管理 > 策略实验室 / 回测", "保留当前入口；策略回测保持核心化。", "Mapped"),
    CompatibilityEntry("策略实验室｜参数扫描", True, "ACTIVE_PFI_VIEW_OPTIONS: scan", "投资管理 > 策略实验室 / 参数扫描", "保留当前入口；作为策略实验室视图。", "Mapped"),
    CompatibilityEntry("策略实验室｜盘感训练", True, "ACTIVE_PFI_VIEW_OPTIONS: market_feel", "投资管理 > 策略实验室 / 盘感训练", "保留当前入口；隐藏未来答案并只做训练。", "Mapped"),
    CompatibilityEntry("策略实验室｜策略库", True, "ACTIVE_PFI_VIEW_OPTIONS: library", "投资管理 > 策略实验室 / 策略库", "保留当前入口；策略注册保持人工复核。", "Mapped"),
    CompatibilityEntry("数据与系统｜模拟实验", True, "ACTIVE_PFI_VIEW_OPTIONS: big_data", "投资管理 > 策略实验室 / 大数据模拟器", "保留当前入口；大数据模拟器归入策略实验室。", "Mapped"),
    CompatibilityEntry("数据与系统｜数据中心", True, "ACTIVE_PFI_VIEW_OPTIONS: tools", "数据源与同步", "保留当前入口；作为数据源与同步兼容入口。", "Mapped"),
)

PUBLIC_ASSUMPTION_COMPATIBILITY: tuple[CompatibilityEntry, ...] = (
    CompatibilityEntry("PFI/modules/qbvs_lab", True, "CodexProject/PFI/modules/qbvs_lab", "投资管理 > 策略实验室 / 大数据模拟器", "保留该路径和文档；作为新 IA 下的兼容入口。", "MappedPublicAssumption"),
    CompatibilityEntry("qbvs/ active runtime", True, "CodexProject/PFI/modules/qbvs_lab/qbvs", "投资管理 > 策略实验室 / 大数据模拟器", "禁止移动、改名或宽重构；Stage 4 只刷新入口和分析 read-model。", "BoundaryLocked"),
)

LOCAL_ACTIVE_RUNTIME_PATHS: tuple[str, ...] = (
    "src/pfi_os",
    "modules/qbvs_lab/qbvs",
    "web",
    "scripts",
    "tests",
    "$PFI_DATA_HOME/private/operational/pfi.sqlite",
)

ROOT_GOVERNANCE_PATHS: tuple[str, ...] = (
    "AGENTS.md",
    "README.md",
    "governance/projects.yaml",
)

LOCAL_PUBLIC_ASSUMPTION_GAPS: tuple[str, ...] = ()

FORBIDDEN_PRODUCT_PRIMARY_LABELS: tuple[str, ...] = (
    "Alpha",
    "System",
    "Development",
    "系统与开发",
    "R-prefixed Alpha variant",
)


def target_primary_labels() -> tuple[str, ...]:
    return tuple(entry.label for entry in V02_TARGET_PRIMARY_ENTRIES)


def all_compatibility_entries() -> tuple[CompatibilityEntry, ...]:
    return CURRENT_SIX_WORKSPACE_COMPATIBILITY + ACTIVE_VIEW_COMPATIBILITY + PUBLIC_ASSUMPTION_COMPATIBILITY


def build_stage0_contract() -> dict[str, object]:
    return {
        "schema": "PFIV02Stage0CompatibilityContractV1",
        "stage": "Stage 0",
        "target_primary_entries": [asdict(entry) for entry in V02_TARGET_PRIMARY_ENTRIES],
        "compatibility_entries": [asdict(entry) for entry in all_compatibility_entries()],
        "local_active_runtime_paths": LOCAL_ACTIVE_RUNTIME_PATHS,
        "root_governance_paths": ROOT_GOVERNANCE_PATHS,
        "local_public_assumption_gaps": LOCAL_PUBLIC_ASSUMPTION_GAPS,
        "forbidden_product_primary_labels": FORBIDDEN_PRODUCT_PRIMARY_LABELS,
        "non_trading_boundary": "Research, backtesting, simulation, review, reporting, context export only; no trading password and no automatic real-money order submission.",
    }
