from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


version = "v0.2.3"

official_nav = [
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

deprecated_constraints = [
    "9 个一级入口",
    "市场与研究不得作为一级入口",
    "暗色 AI 控制台风格",
    "演示数据可用于验收",
    "README/docs 写完成即可 closeout",
]

retained_governance_rules = [
    "一轮只执行一个 Stage",
    "未经过用户验收不得进入下一 Stage",
    "禁止文档声明冒充完成",
    "禁止关键词测试冒充真实交互",
    "每个 Stage 必须生成 Evidence Pack",
]

v01_compatibility_routes = {
    "首页": "首页总览",
    "市场": "市场与研究",
    "研究": "市场与研究",
    "持仓": "投资管理",
    "策略实验室": "市场与研究 / 投资管理共享同一状态",
    "数据与系统": "设置",
}

forbidden_financial_data_terms = [
    "mock",
    "sample",
    "synthetic",
    "fixture",
    "demo",
    "fake",
    "测试样例",
    "自动生成流水",
    "自动生成持仓",
    "写死趋势线",
]

metric_data_statuses = [
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
]

no_mock_financial_data = True
one_stage_per_run = True
requires_user_acceptance = True
no_auto_closeout = True
light_theme_required = True
human_product_experience_priority = True
stage0_only = True


@dataclass(frozen=True)
class V023EvidenceCommand:
    command: str
    required: bool


@dataclass(frozen=True)
class V023Stage0Contract:
    version: str
    stage: str
    stage_name: str
    official_nav: tuple[str, ...]
    deprecated_constraints: tuple[str, ...]
    retained_governance_rules: tuple[str, ...]
    v01_compatibility_routes: dict[str, str]
    forbidden_financial_data_terms: tuple[str, ...]
    metric_data_statuses: tuple[str, ...]
    no_mock_financial_data: bool
    one_stage_per_run: bool
    requires_user_acceptance: bool
    no_auto_closeout: bool
    light_theme_required: bool
    human_product_experience_priority: bool
    stage0_only: bool
    allowed_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]
    validation_commands: tuple[V023EvidenceCommand, ...]
    evidence_files: tuple[str, ...]


def build_stage0_contract() -> dict[str, Any]:
    contract = V023Stage0Contract(
        version=version,
        stage="Stage 0",
        stage_name="需求锁定、历史约束废弃、证据基线建立",
        official_nav=tuple(official_nav),
        deprecated_constraints=tuple(deprecated_constraints),
        retained_governance_rules=tuple(retained_governance_rules),
        v01_compatibility_routes=dict(v01_compatibility_routes),
        forbidden_financial_data_terms=tuple(forbidden_financial_data_terms),
        metric_data_statuses=tuple(metric_data_statuses),
        no_mock_financial_data=no_mock_financial_data,
        one_stage_per_run=one_stage_per_run,
        requires_user_acceptance=requires_user_acceptance,
        no_auto_closeout=no_auto_closeout,
        light_theme_required=light_theme_required,
        human_product_experience_priority=human_product_experience_priority,
        stage0_only=stage0_only,
        allowed_files=(
            "PFI/docs/pfi_v023/*",
            "PFI/src/pfi_v02/stage_v023_contract.py",
            "PFI/tests/test_v023_stage0_contract.py",
            "PFI/reports/pfi_v023/stage_0/*",
        ),
        explicitly_not_done=(
            "Stage 1 app/localhost/frontend bundle consistency",
            "UI visual rebuild",
            "route implementation",
            "data computation or read-model changes",
            "report generation implementation",
            "app bundle reinstall",
        ),
        validation_commands=(
            V023EvidenceCommand("node --check PFI/web/app/shell.js", True),
            V023EvidenceCommand("python3 -m py_compile PFI/src/pfi_v02/stage_v023_contract.py", True),
            V023EvidenceCommand("python3 -m py_compile PFI/tests/test_v023_stage0_contract.py", True),
            V023EvidenceCommand("python3 -m pytest PFI/tests/test_v023_stage0_contract.py -q", True),
            V023EvidenceCommand("git diff --check -- PFI", True),
        ),
        evidence_files=(
            "PFI/reports/pfi_v023/stage_0/evidence.json",
            "PFI/reports/pfi_v023/stage_0/terminal.log",
            "PFI/reports/pfi_v023/stage_0/changed_files.txt",
        ),
    )
    payload = asdict(contract)
    payload["validation_commands"] = [asdict(item) for item in contract.validation_commands]
    return payload


def current_stage0_baseline(root: Path | None = None) -> dict[str, Any]:
    project_root = root or Path(__file__).resolve().parents[2]
    web_index = project_root / "web" / "index.html"
    shell_js = project_root / "web" / "app" / "shell.js"
    index_text = web_index.read_text(encoding="utf-8")
    shell_text = shell_js.read_text(encoding="utf-8")
    return {
        "web_index_exists": web_index.exists(),
        "shell_js_exists": shell_js.exists(),
        "web_index_primary_entry_count_marker": 'data-primary-workspaces="10"' in index_text,
        "web_index_has_market_research": "市场与研究" in index_text,
        "shell_has_market_research": "市场与研究" in shell_text,
        "shell_has_strategy_lab_keyword": "策略实验室" in shell_text,
        "stage0_modifies_ui": False,
    }
