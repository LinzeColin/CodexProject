from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR, get_env_value
from pfi_os.system.pfi_identity import app_bundle_paths


@dataclass(frozen=True)
class HealthCheck:
    item_cn: str
    item_en: str
    status: str
    detail_cn: str
    detail_en: str


def collect_health_checks(project_root: Path | None = None, report_root: Path | None = None) -> list[HealthCheck]:
    root = project_root or PROJECT_ROOT
    reports = report_root or REPORT_ROOT_DIR
    app_paths = app_bundle_paths()
    return [
        _path_check("项目目录", "Project Directory", root, must_exist=True),
        _path_check("报告目录", "Report Directory", reports, must_exist=False),
        _path_check("桌面 PFI 入口", "Desktop PFI Launcher", app_paths["desktop"], must_exist=True),
        _path_check("下载目录 PFI 入口", "Downloads PFI Launcher", app_paths["downloads"], must_exist=True),
        _path_check("Applications PFI 入口", "Applications PFI Launcher", app_paths["applications"], must_exist=True),
        _path_check("项目内部启动文件", "Internal Start Launcher", root / "StartPFI.command", must_exist=True),
        _path_check("双击停止文件", "Double-Click Stopper", root / "StopPFI.command", must_exist=True),
        _path_check("启动脚本", "Start Script", root / "scripts" / "startPFI.sh", must_exist=True),
        _path_check("停止脚本", "Stop Script", root / "scripts" / "stopPFI.sh", must_exist=True),
        _path_check("状态脚本", "Status Script", root / "scripts" / "statusPFI.sh", must_exist=True),
        _path_check("验收脚本", "Verification Script", root / "scripts" / "verifyPFI.sh", must_exist=True),
        _path_check("测试脚本", "Test Script", root / "scripts" / "runTests.sh", must_exist=True),
        _path_check("数据源配置脚本", "Data Source Setup Script", root / "scripts" / "setupEnv.sh", must_exist=True),
        _path_check("样例报告脚本", "Sample Report Script", root / "scripts" / "createSampleReport.sh", must_exist=True),
        _path_check("文档索引", "Docs Index", root / "docs" / "Index.md", must_exist=True),
        _path_check("验收清单", "Acceptance Checklist", root / "docs" / "AcceptanceChecklist.md", must_exist=True),
        _path_check("发布说明", "Release Notes", root / "docs" / "ReleaseNotes.md", must_exist=True),
        _path_check("成熟度路线", "Maturity Roadmap", root / "docs" / "MaturityRoadmap.md", must_exist=True),
        _env_check("TuShare Token", "TUSHARE_TOKEN"),
        _env_check("Alpha Vantage API Key", "ALPHA_VANTAGE_API_KEY"),
        _env_check("Polygon API Key", "POLYGON_API_KEY"),
        _safety_check(root),
    ]


def _path_check(item_cn: str, item_en: str, path: Path, must_exist: bool) -> HealthCheck:
    exists = path.exists()
    if exists:
        return HealthCheck(item_cn, item_en, "Pass", f"已找到：{path}", f"Found: {path}")
    if must_exist:
        return HealthCheck(item_cn, item_en, "Review", f"未找到：{path}", f"Missing: {path}")
    return HealthCheck(item_cn, item_en, "Info", f"尚未创建，系统会在需要时创建：{path}", f"Not created yet; the system will create it when needed: {path}")


def _env_check(item_en: str, key: str) -> HealthCheck:
    configured = bool(get_env_value(key))
    if configured:
        return HealthCheck(item_en, item_en, "Pass", f"{key} 已配置。", f"{key} is configured.")
    return HealthCheck(item_en, item_en, "Info", f"{key} 未配置；对应真实数据源可能不可用。", f"{key} is not configured; the related real data provider may be unavailable.")


def _safety_check(root: Path) -> HealthCheck:
    readme = root / "README.md"
    if not readme.exists():
        return HealthCheck("安全边界", "Safety Boundary", "Review", "README 缺失，无法确认安全声明。", "README is missing, so the safety statement cannot be verified.")
    text = readme.read_text(encoding="utf-8")
    has_boundary = "禁止接入实盘交易" in text and "禁止真实下单" in text
    if has_boundary:
        return HealthCheck("安全边界", "Safety Boundary", "Pass", "已确认：系统禁止实盘交易和真实下单。", "Confirmed: live trading and real order submission are prohibited.")
    return HealthCheck("安全边界", "Safety Boundary", "Review", "未在 README 中找到完整安全声明。", "The complete safety statement was not found in README.")
