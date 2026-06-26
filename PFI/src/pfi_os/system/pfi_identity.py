from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


MASTER_SYSTEM_ID = "PFI"
MASTER_DISPLAY_NAME = "PFI"
MASTER_CN_NAME = "证值智能中台"
MASTER_FULL_TITLE = f"{MASTER_SYSTEM_ID}｜{MASTER_CN_NAME}"
MASTER_SHORT_TITLE = f"{MASTER_DISPLAY_NAME}｜{MASTER_CN_NAME}"
MASTER_EXPANSION = "Personal Financial Intelligence Operating System"

APP_BUNDLE_NAME = "PFI"
APP_DISPLAY_NAME = MASTER_DISPLAY_NAME
LEGACY_APP_NAME = "量化回测系统"


@dataclass(frozen=True)
class PFISubsystem:
    order: int
    key: str
    name_en: str
    name_cn: str
    pfi_os_view: str
    p0_output: str


@dataclass(frozen=True)
class PFIFoundationLayer:
    key: str
    name_en: str
    name_cn: str
    rule: str


PFI_SUBSYSTEMS: tuple[PFISubsystem, ...] = (
    PFISubsystem(1, "executive_command_center", "Executive Command Center", "总控驾驶舱", "research_bus", "weekly_command_report"),
    PFISubsystem(2, "company_cashflow_command", "Company CashFlow Command", "公司经营现金流系统", "research_bus", "weekly_cashflow_report"),
    PFISubsystem(3, "pfi_os", "PFI", "量化研究与回测系统", "single", "backtest_report"),
    PFISubsystem(4, "policy_intelligence_radar", "Policy Intelligence Radar", "政策机会情报系统", "industry", "policy_brief"),
    PFISubsystem(5, "consumption_guard", "Consumption Guard", "个人消费止血系统", "profile", "monthly_guard_report"),
    PFISubsystem(6, "ai_research_engine", "AI Research Engine", "AI行业研究系统", "industry", "ai_research_weekly"),
    PFISubsystem(7, "sports_market_lab", "Sports Market Lab", "赛事市场分析系统", "research_bus", "calibration_report"),
    PFISubsystem(8, "codexforge_factory", "CodexForge Factory", "Codex工程交付工厂", "research_bus", "release_package"),
)

PFI_FOUNDATION_LAYERS: tuple[PFIFoundationLayer, ...] = (
    PFIFoundationLayer("evidence", "Evidence Layer", "证据层", "所有输入必须进入证据层。"),
    PFIFoundationLayer("data", "Data Layer", "数据层", "所有数据必须记录来源、时间、质量状态和限制条件。"),
    PFIFoundationLayer("decision", "Decision Layer", "决策层", "所有结论必须经过风控层并降级不足证据。"),
    PFIFoundationLayer("engineering", "Engineering Layer", "工程层", "所有系统必须经过 Codex 工程层和可复跑验收。"),
    PFIFoundationLayer("review", "Review Layer", "复核层", "所有行动建议必须进入人工复核队列。"),
)


def app_bundle_paths(home: Path | None = None, applications_dir: Path | None = None) -> dict[str, Path]:
    base_home = home or Path.home()
    apps = applications_dir or Path("/Applications")
    return {
        "desktop": base_home / "Desktop" / f"{APP_BUNDLE_NAME}.app",
        "downloads": base_home / "Downloads" / f"{APP_BUNDLE_NAME}.app",
        "applications": apps / f"{APP_BUNDLE_NAME}.app",
    }


def legacy_app_bundle_paths(home: Path | None = None, applications_dir: Path | None = None) -> dict[str, Path]:
    base_home = home or Path.home()
    apps = applications_dir or Path("/Applications")
    return {
        "desktop": base_home / "Desktop" / f"{LEGACY_APP_NAME}.app",
        "downloads": base_home / "Downloads" / f"{LEGACY_APP_NAME}.app",
        "applications": apps / f"{LEGACY_APP_NAME}.app",
    }


def pfi_manifest() -> dict[str, object]:
    return {
        "system_id": MASTER_SYSTEM_ID,
        "display_name": MASTER_DISPLAY_NAME,
        "cn_name": MASTER_CN_NAME,
        "full_title": MASTER_FULL_TITLE,
        "short_title": MASTER_SHORT_TITLE,
        "expansion": MASTER_EXPANSION,
        "entry_system": "PFI",
        "research_only": True,
        "no_live_trading": True,
        "subsystems": [asdict(item) for item in PFI_SUBSYSTEMS],
        "foundation_layers": [asdict(item) for item in PFI_FOUNDATION_LAYERS],
        "rules": [
            "所有输入必须进入证据层。",
            "所有结论必须经过风控层。",
            "所有系统必须经过 Codex 工程层。",
            "所有行动建议必须进入人工复核队列。",
        ],
    }
