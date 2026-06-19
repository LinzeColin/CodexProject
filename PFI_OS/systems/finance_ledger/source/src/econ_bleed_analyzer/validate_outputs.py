from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_REPORTS = [
    "weekly_report.pdf",
    "monthly_report.pdf",
    "quarterly_report.pdf",
    "half_year_report.pdf",
    "yearly_report.pdf",
    "annual_bill_cycle_report.pdf",
    "delivery_acceptance_report.pdf",
    "report_visual_inventory_report.pdf",
    "visual_quality_acceptance_report.pdf",
    "reference_model_benchmark_report.pdf",
    "chatgpt_reference_intake_report.pdf",
    "classification_rulebook_report.pdf",
    "user_manual_report.pdf",
    "requirements_traceability_report.pdf",
    "completion_audit_report.pdf",
    "goal_completion_audit_report.pdf",
    "user_acceptance_matrix_report.pdf",
    "spending_control_action_report.pdf",
    "manual_review_report.pdf",
    "manual_review_queue_audit_report.pdf",
    "entity_registry_report.pdf",
    "evidence_decision_matrix_report.pdf",
    "reconciliation_audit_report.pdf",
    "data_trust_audit_report.pdf",
    "finance_ledger_system_improvement_report.pdf",
]
REQUIRED_HTML = ["index.html", "dashboard.html", "operations_center.html", "data_access_hub.html", "acceptance_workbench.html", "reference_model_lab.html", "transaction_explorer.html", "behavior_analysis.html", "tag_library.html", "review_workbench.html"]
REQUIRED_AUDIT_FILES = [
    "reference_models.json",
    "reference_source_log.json",
    "reference_source_log.csv",
    "reference_ui_patterns.json",
    "reference_ui_patterns.csv",
    "report_visual_inventory.json",
    "report_visual_inventory.csv",
    "chatgpt_reference_audit.json",
    "chatgpt_reference_audit.csv",
    "chatgpt_reference_gap_matrix.csv",
    "goal_completion_audit.json",
    "goal_completion_audit.csv",
    "reconciliation_checks.json",
    "reconciliation_checks.csv",
    "manual_review_queue_audit.json",
    "manual_review_queue_audit.csv",
    "entity_registry.json",
    "entity_registry.csv",
    "alias_map.json",
    "alias_map.csv",
    "entity_registry_summary.json",
    "entity_registry_summary.csv",
    "evidence_decision_matrix.json",
    "evidence_decision_matrix.csv",
    "evidence_decision_summary.json",
    "evidence_decision_summary.csv",
    "finance_ledger_system_improvement_source_log.json",
    "finance_ledger_system_improvement_source_log.csv",
    "system_improvement_gap_matrix.csv",
    "question_answer_index.json",
]
GLOBAL_NAV_CONTENT_MARKERS = [
    'id="globalNav"',
    'id="usageGuideToggle"',
    'id="usageGuidePanel"',
    'id="usageGuideBackdrop"',
    "返回主菜单",
    "数据接入",
    "报告中心",
    "交易明细",
    "行为分析",
    "标签库",
    "大额复核",
    "使用说明与专业术语",
    "推荐操作路径",
    "专业术语",
    "生产口径",
    "待复核隔离",
    "Data Trust",
    "Reconciliation",
    "function openUsageGuide",
    "function closeUsageGuide",
]
PORTAL_CONTENT_MARKERS = [
    'id="questionConsole"',
    'id="customQuestionInput"',
    'id="questionHistory"',
    'id="answerEvidence"',
    'id="reportCenter"',
    'id="reportFilterKeyword"',
    'id="reportPeriodFilter"',
    'id="reportThemeFilter"',
    'id="reportEvidenceFilter"',
    'id="selectedReportList"',
    'id="questionButtons"',
    'id="questionAnswer"',
    "qa_index",
    "question_templates",
    "function answerCustomQuestion",
    "function renderReportCenter",
    "function renderSelectedReports",
    'target="_blank"',
    'rel="noopener"',
    "本地记账分析系统",
    "数据接入与回测入口",
    "自定义问题查询控制台",
    "本地检索 · 证据回答",
    "FACT",
    "INFERENCE",
    "OBSERVATION",
    "function renderQuestion",
    "function renderQuestionConsole",
]
OPERATIONS_CENTER_CONTENT_MARKERS = [
    'id="stepButtons"',
    'id="actionCommand"',
    'id="reviewStatus"',
    'id="workflowMap"',
    'id="workflowVisual"',
    'id="workflowSummary"',
    'id="reviewPressureBar"',
    "function selectAction",
    "function copyCommand",
    "function renderWorkflowVisual",
    "经济放血运行控制台",
    "下一步选项",
    "当前运行状态",
    "每周更新",
    "大额复核",
    "用户验收",
    "浏览器验收",
    "打包前必跑",
    "交付打包",
    "只读 API",
]
DATA_ACCESS_HUB_CONTENT_MARKERS = [
    "数据接入与回测入口",
    "PFIOS",
    "量化回测",
    "ResearchBus",
    "SQLite 数据库",
    "只读 API",
    "v_mart_daily_cashflow",
    "v_fact_expense_allocations",
    "v_data_trust_transactions",
    "v_reconciliation_checks",
    'id="viewTable"',
    'id="consumerTable"',
    'id="apiCommand"',
    "function copyText",
]
ACCEPTANCE_WORKBENCH_CONTENT_MARKERS = [
    'id="acceptanceMatrix"',
    'id="acceptanceSummary"',
    'id="progressBar"',
    'id="acceptanceScore"',
    'id="nextCommand"',
    'id="exportStatus"',
    'id="acceptanceJsonPreview"',
    'id="refinementGuide"',
    'id="chatgptReferenceFile"',
    'id="chatgptReferenceText"',
    'id="chatgptAuditCommand"',
    "function selectChoice",
    "function downloadJson",
    "function copyAcceptanceJson",
    "function applyUserStatedChoices",
    "function downloadCsv",
    "function loadChatGPTReferenceFile",
    "function saveReferenceDraft",
    "function downloadChatGPTReference",
    "套用：1-8 A，最后 B",
    "复制验收 JSON",
    "localStorage",
    "用户验收工作台",
    "验收选择矩阵",
    "下一步选项 A/B/C",
    "ChatGPT 对照文件",
    "导出对照文件",
]
REFERENCE_MODEL_LAB_CONTENT_MARKERS = [
    'id="referenceCoverageChart"',
    'id="referenceFeatureDonut"',
    'id="referenceModelMatrix"',
    'id="referenceUIPatternMatrix"',
    'id="referenceGapTable"',
    'id="modelSearch"',
    'id="licenseFilter"',
    'id="coverageFilter"',
    "function applyReferenceFilters",
    "function renderReferenceModelLab",
    "function renderUIPatternMatrix",
    "function downloadReferenceCsv",
    "开源参考模型工作台",
    "GitHub",
    "吸收度对比",
    "差距与边界",
    "UI/布局模式吸收矩阵",
    "不复制外部代码或 UI",
]
DASHBOARD_CONTENT_MARKERS = [
    'id="monthlyCashflowChart"',
    'id="categoryShareChart"',
    'id="counterpartyConcentration"',
    'id="timeHeatmap"',
    'id="mechanismBars"',
    'id="riskControlMatrix"',
    'id="behaviorBuckets"',
    'id="monthlyCategoryHeatmap"',
    'id="cumulativeCashflow"',
    'id="sourcePlatformBars"',
    'id="sourceHealthTable"',
    'id="sourceHealthCards"',
    'id="reviewStatusBars"',
    'id="reviewStatusTable"',
    'id="budgetPressureRadar"',
    'id="budgetPressureBars"',
    "function renderMonthlyChart",
    "function renderCategoryDonut",
    "function renderCounterpartyConcentration",
    "function renderTimeHeatmap",
    "function renderMechanismBars",
    "function renderRiskControlMatrix",
    "function renderBehaviorBuckets",
    "function renderMonthlyCategoryHeatmap",
    "function renderCumulativeCashflow",
    "function renderSourceHealth",
    "function renderReviewStatus",
    "function renderBudgetPressureRadar",
    "月度现金流折线图",
    "主类占比环形图",
    "交易对方集中度",
    "时间行为热力矩阵",
    "经济放血机制图谱",
    "风险控制矩阵",
    "行为桶支出对照",
    "主类月度热力矩阵",
    "累计净现金流轨迹",
    "数据源平台分布与导入健康",
    "大额复核闭环状态",
    "预算压力雷达",
]
TRANSACTION_EXPLORER_CONTENT_MARKERS = [
    'id="explorerCategoryBars"',
    'id="explorerRiskBars"',
    'id="explorerMonthTrend"',
    'id="explorerCounterpartyBars"',
    'id="tagCombo"',
    'id="tagPreset"',
    'id="tagMatchMode"',
    'id="searchFeedback"',
    'id="detailPanel"',
    'id="detailToggle"',
    "function selectedTags",
    "function applyTagPreset",
    "function fuzzySearchMatch",
    "function renderSearchFeedback",
    "function toggleDetails",
    "function renderDrilldown",
    "function renderMiniBars",
    "标签任一命中",
    "标签全部命中",
    "搜索反馈",
    "折叠明细",
    "筛选主类分布",
    "筛选风险标签",
    "筛选月份趋势",
    "筛选对手方排行",
]
BEHAVIOR_ANALYSIS_CONTENT_MARKERS = [
    'id="behaviorChart"',
    'id="tagGrid"',
    'id="chartType"',
    'id="matchMode"',
    "function applyPreset",
    "function renderChart",
    "function amountBuckets",
    "折线图",
    "直方图",
    "环形图",
    "金额分布图",
    "交易行为分析",
]
TAG_LIBRARY_CONTENT_MARKERS = [
    'id="tagTable"',
    'id="presetGrid"',
    "function downloadJson",
    "function addTag",
    "function addPreset",
    "function updateTag",
    "function updatePreset",
    "function updatePresetTags",
    "filter_presets",
    "tag_library_custom.json",
    "--tag-library",
    "标签库编辑",
    "新增筛选组合",
]
REVIEW_WORKBENCH_CONTENT_MARKERS = [
    "复核决定",
    "主类/子类",
    "风险标签",
    'id="reviewSearch"',
    'id="filterCategory"',
    'id="filterDecision"',
    'id="batchCategory"',
    'id="batchRisk"',
    'id="groupMode"',
    'id="impactPreview"',
    'id="reviewGroupMatrix"',
    'id="candidateCount"',
    "function decisionOptions",
    "function categoryPresetOptions",
    "function filteredPendingRows",
    "function groupedRows",
    "function renderGroupMatrix",
    "function applyGroupAction",
    "function applyCandidate",
    "function applyCandidatesToVisible",
    "function applyAllCandidates",
    "function applyBatchToVisible",
    "function setPrimaryCategory",
    "function setPrimaryRiskTags",
    "function changeCategoryPreset",
    "应用到当前筛选",
    "分组矩阵",
    "套用批量栏",
    "套用当前筛选候选",
    "review_decisions_confirmed.csv",
]
REPORT_CONTENT_MARKERS = [
    "## 可视化图表",
    "### 现金流视图",
    "### 累计净现金流轨迹",
    "### 行为桶支出对照",
    "### 预算压力雷达",
    "### 主类支出占比",
    "### 风险标签金额排行",
    "### 经济放血机制图谱",
    "### 风险控制矩阵",
    "### 交易对方集中度",
    "### 时间行为热力图",
    "### 主类月度热力矩阵",
    "## 主类/子类金额",
    "| 主类 | 子类 | 金额 | 笔数 | 主类占总支出 | 子类占主类 |",
    "█",
]
ACCEPTANCE_REPORT_CONTENT_MARKERS = [
    "# 交付验收报告",
    "## 目标对照",
    "## 数据规模",
    "## 正式交付物",
    "## 开源参考吸收矩阵",
    "## 验收命令",
    "## 待确认事项",
]
VISUAL_QUALITY_ACCEPTANCE_CONTENT_MARKERS = [
    "# UI 与可视化质量验收报告",
    "## 页面矩阵",
    "## 可视化矩阵",
    "## 布局与颜色规则",
    "## 交互验收",
    "## 验收证据",
    "## 后续精修队列",
    "report_visual_inventory.json",
]
REPORT_VISUAL_INVENTORY_CONTENT_MARKERS = [
    "# 报告可视化覆盖审计报告",
    "## 覆盖总览",
    "## 周期报告矩阵",
    "## 图表类型矩阵",
    "## 验收规则",
    "## 验收证据",
    "all_period_pdf_reports_require_visual_sections",
    "report_visual_inventory.json",
    "report_visual_inventory.csv",
]
REFERENCE_MODEL_BENCHMARK_CONTENT_MARKERS = [
    "# 开源参考对标报告",
    "## 对标原则",
    "## 参考项目功能矩阵",
    "## 功能吸收矩阵",
    "## UI/布局模式吸收矩阵",
    "## 本系统增强项",
    "## 仍未覆盖的边界",
    "## 验收证据",
    "来源",
    "证据摘要",
    "reference_source_log.json",
    "reference_source_log.csv",
    "reference_ui_patterns.json",
    "reference_ui_patterns.csv",
]
CHATGPT_REFERENCE_INTAKE_CONTENT_MARKERS = [
    "# ChatGPT 对照文件接入审计报告",
    "## 审计结论",
    "## 候选文件清单",
    "## 差距矩阵",
    "## 接入规则",
    "## 后续动作",
    "不伪造来源",
    "chatgpt_reference_gap_matrix.csv",
    "ChatGPT",
]
RULEBOOK_REPORT_CONTENT_MARKERS = [
    "# 分类规则手册",
    "## 主类/子类体系",
    "## 资金口径",
    "## 趋势公式",
    "## 风险标签",
    "## 特殊确认规则",
    "## 规则执行顺序",
    "## 默认规则",
]
USER_MANUAL_CONTENT_MARKERS = [
    "# 使用手册",
    "## 每周更新流程",
    "## 标准周更命令",
    "## 带复核结果重建",
    "## 必跑验收命令",
    "## 报告入口",
    "## 大额复核规则",
    "## 只读查询命令",
    "## 交付打包",
    "## 下游系统接入",
    "## 维护原则",
]
REQUIREMENTS_TRACEABILITY_CONTENT_MARKERS = [
    "# 需求追踪验收报告",
    "## 验收总览",
    "## 需求追踪矩阵",
    "## 当前明确边界",
    "## 关键入口",
    "大额 >= 10000 先复核不自动入账",
    "固定问题模板查询",
    "交付 ZIP 包",
]
COMPLETION_AUDIT_CONTENT_MARKERS = [
    "# 最终完成审计报告",
    "## 目标拆解",
    "## 证据矩阵",
    "## 验收结果",
    "## 剩余边界",
    "## 完成判断",
]
GOAL_COMPLETION_AUDIT_CONTENT_MARKERS = [
    "# 目标完成度机器审计报告",
    "## 审计总览",
    "## 逐项矩阵",
    "## 状态口径",
    "机器可验证完成度",
    "needs_user_input",
    "evidence_required_no_subjective_completion",
]
USER_ACCEPTANCE_MATRIX_CONTENT_MARKERS = [
    "# 用户验收矩阵报告",
    "## 当前进度判断",
    "## 验收选择矩阵",
    "## 下一步选项",
    "## 免打扰执行规则",
    "## 证据入口",
    "ChatGPT 对照文件",
]
MANUAL_REVIEW_REPORT_CONTENT_MARKERS = [
    "# 大额复核清单",
    "## 复核总览",
    "## 处理原则",
    "## 当前建议分类汇总",
    "## 交易对方 Top 20",
    "## 待复核明细",
    "## 回灌命令",
]
MANUAL_REVIEW_AUDIT_REPORT_CONTENT_MARKERS = [
    "# Manual Review Queue 人工复核队列审计报告",
    "## 审计总览",
    "## 证据分层与决策等级",
    "## 队列摘要",
    "## 优先复核明细",
    "audit/manual_review_queue_audit.csv",
    "audit/manual_review_queue_audit.json",
    "v_manual_review_queue_audit",
    "v_manual_review_queue_blockers",
    "v_manual_review_queue_summary",
]
ENTITY_REGISTRY_REPORT_CONTENT_MARKERS = [
    "# Entity Registry / Alias Map 实体注册与别名映射报告",
    "## 假设与边界",
    "## 实体摘要",
    "## 需复核实体",
    "## 高频交易对方实体",
    "## 别名冲突",
    "audit/entity_registry.csv",
    "audit/alias_map.csv",
    "v_entity_registry",
    "v_alias_map",
    "v_entity_alias_conflicts",
]
EVIDENCE_DECISION_REPORT_CONTENT_MARKERS = [
    "# Evidence Decision Matrix 证据分层与决策等级矩阵报告",
    "## 状态口径",
    "## 执行摘要",
    "## 分层摘要",
    "## 优先复核 / 拒绝项",
    "audit/evidence_decision_matrix.csv",
    "audit/evidence_decision_matrix.json",
    "v_evidence_decision_matrix",
    "v_evidence_decision_actionable",
    "v_evidence_decision_watchlist",
    "v_evidence_decision_summary",
]
RECONCILIATION_REPORT_CONTENT_MARKERS = [
    "# Reconciliation Layer 自动对账报告",
    "## 审计总览",
    "## 对账公式与假设",
    "## 检查矩阵",
    "audit/reconciliation_checks.csv",
    "audit/reconciliation_checks.json",
    "v_reconciliation_checks",
    "v_reconciliation_failures",
    "v_reconciliation_summary",
]
DATA_TRUST_REPORT_CONTENT_MARKERS = [
    "# Data Trust Layer 审计报告",
    "## 状态定义",
    "## 当前分布",
    "## 口径说明",
    "RAW_IMPORTED",
    "PARSED_CANDIDATE",
    "NEEDS_REVIEW",
    "USER_CONFIRMED",
    "RECONCILED",
    "ARCHIVED",
    "REJECTED",
    "production_expense_allocations",
]
SYSTEM_IMPROVEMENT_REPORT_CONTENT_MARKERS = [
    "# 记账分析系统 V2 优化改进报告",
    "## 执行摘要",
    "## 信息来源表",
    "## 参考项目 / 案例 / 竞品对比表",
    "## 可复用模块",
    "## 差距分析",
    "## 改进方案",
    "## 实施路线图",
    "## 风险与限制",
    "## 验收标准",
    "## 下一步行动建议",
    "FACT",
    "INFERENCE",
    "OBSERVATION",
]
SPENDING_CONTROL_ACTION_CONTENT_MARKERS = [
    "# 消费控制行动计划",
    "## 行动总览",
    "## 优先级动作",
    "## 风险暴露",
    "## 主类控制线",
    "## 下期执行规则",
    "## 复盘流程",
]
TREND_REPORTS = {
    "weekly_report.md": ["### 周期支出趋势", "## 主类/子类趋势", "周报环比：本周 vs 上周", "周报同比：本周 vs 去年同 ISO 周"],
    "monthly_report.md": ["### 周期支出趋势", "## 主类/子类趋势", "月报环比：本月 vs 上月", "月报同比：本月 vs 去年同月"],
    "quarterly_report.md": ["### 周期支出趋势", "## 主类/子类趋势", "季报环比：本季 vs 上季", "季报同比：本季 vs 去年同季"],
    "half_year_report.md": ["### 周期支出趋势", "## 主类/子类趋势", "半年报环比：本半年 vs 上半年", "半年报同比：本半年 vs 去年同期半年"],
    "yearly_report.md": ["### 周期支出趋势", "## 主类/子类趋势", "年报同比：本年 vs 上年"],
}
REQUIRED_TABLES = [
    "classified_transactions_audit",
    "production_expense_allocations",
    "summary_by_category",
    "summary_by_risk_tag",
    "spending_control_plan",
    "budget_pressure_radar",
    "source_platform_summary",
    "data_trust_transactions",
    "reconciliation_checks",
    "tag_library",
    "tag_filter_presets",
    "manual_review_queue",
    "manual_review_status_summary",
    "manual_review_decision_candidates",
    "manual_review_decision_candidate_groups",
    "manual_review_queue_audit",
    "manual_review_queue_audit_summary",
    "entity_registry",
    "alias_map",
    "entity_registry_summary",
    "evidence_decision_matrix",
    "evidence_decision_summary",
    "summary_by_week",
    "summary_by_month",
    "summary_by_quarter",
    "summary_by_half",
    "summary_by_year",
]
REQUIRED_LEDGER_VIEWS = [
    "v_production_transactions",
    "v_classified_transactions_audit",
    "v_pending_large_review",
    "v_review_status_summary",
    "v_review_decision_candidates",
    "v_review_decision_candidate_groups",
    "v_manual_review_queue_audit",
    "v_manual_review_queue_blockers",
    "v_manual_review_queue_summary",
    "v_entity_registry",
    "v_alias_map",
    "v_entity_registry_summary",
    "v_entity_alias_conflicts",
    "v_evidence_decision_matrix",
    "v_evidence_decision_actionable",
    "v_evidence_decision_watchlist",
    "v_evidence_decision_summary",
    "v_cashflow_monthly",
    "v_cashflow_yearly",
    "v_category_summary",
    "v_risk_summary",
    "v_control_plan",
    "v_budget_pressure_radar",
    "v_source_platform_summary",
    "v_data_trust_transactions",
    "v_data_trust_sources",
    "v_data_trust_summary",
    "v_reconciliation_checks",
    "v_reconciliation_failures",
    "v_reconciliation_summary",
    "v_tag_library",
    "v_tag_filter_presets",
    "v_fact_expense_allocations",
    "v_fact_transactions_audit",
    "v_fact_pending_large_review",
    "v_mart_daily_cashflow",
    "v_mart_counterparty_monthly",
    "v_mart_risk_monthly",
]


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _ok(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "ok", detail)


def _fail(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "fail", detail)


def _warn(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "warn", detail)


def _pdf_is_nonempty(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return len(data) > 20_000 and data[:5] == b"%PDF-"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def validate_reports(output_dir: str | Path) -> list[CheckResult]:
    out = Path(output_dir)
    reports_dir = out / "reports"
    checks: list[CheckResult] = []
    checks.append(_ok("output_dir", str(out)) if out.exists() else _fail("output_dir", f"missing: {out}"))
    checks.append(_ok("reports_dir", str(reports_dir)) if reports_dir.exists() else _fail("reports_dir", f"missing: {reports_dir}"))
    for filename in REQUIRED_REPORTS:
        path = reports_dir / filename
        if _pdf_is_nonempty(path):
            checks.append(_ok(f"pdf:{filename}", f"{path.stat().st_size} bytes"))
        else:
            checks.append(_fail(f"pdf:{filename}", "missing, empty, or not a PDF"))

        md_path = reports_dir / filename.replace(".pdf", ".md")
        if not md_path.exists():
            checks.append(_fail(f"report_content:{md_path.name}", "missing Markdown source"))
            continue
        content = md_path.read_text(encoding="utf-8", errors="ignore")
        if md_path.name == "delivery_acceptance_report.md":
            missing_markers = [marker for marker in ACCEPTANCE_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "report_visual_inventory_report.md":
            missing_markers = [marker for marker in REPORT_VISUAL_INVENTORY_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "visual_quality_acceptance_report.md":
            missing_markers = [marker for marker in VISUAL_QUALITY_ACCEPTANCE_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "reference_model_benchmark_report.md":
            missing_markers = [marker for marker in REFERENCE_MODEL_BENCHMARK_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "chatgpt_reference_intake_report.md":
            missing_markers = [marker for marker in CHATGPT_REFERENCE_INTAKE_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "classification_rulebook_report.md":
            missing_markers = [marker for marker in RULEBOOK_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "user_manual_report.md":
            missing_markers = [marker for marker in USER_MANUAL_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "requirements_traceability_report.md":
            missing_markers = [marker for marker in REQUIREMENTS_TRACEABILITY_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "completion_audit_report.md":
            missing_markers = [marker for marker in COMPLETION_AUDIT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "goal_completion_audit_report.md":
            missing_markers = [marker for marker in GOAL_COMPLETION_AUDIT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "user_acceptance_matrix_report.md":
            missing_markers = [marker for marker in USER_ACCEPTANCE_MATRIX_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "spending_control_action_report.md":
            missing_markers = [marker for marker in SPENDING_CONTROL_ACTION_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "manual_review_report.md":
            missing_markers = [marker for marker in MANUAL_REVIEW_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "manual_review_queue_audit_report.md":
            missing_markers = [marker for marker in MANUAL_REVIEW_AUDIT_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "entity_registry_report.md":
            missing_markers = [marker for marker in ENTITY_REGISTRY_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "evidence_decision_matrix_report.md":
            missing_markers = [marker for marker in EVIDENCE_DECISION_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "reconciliation_audit_report.md":
            missing_markers = [marker for marker in RECONCILIATION_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "data_trust_audit_report.md":
            missing_markers = [marker for marker in DATA_TRUST_REPORT_CONTENT_MARKERS if marker not in content]
        elif md_path.name == "finance_ledger_system_improvement_report.md":
            missing_markers = [marker for marker in SYSTEM_IMPROVEMENT_REPORT_CONTENT_MARKERS if marker not in content]
        else:
            missing_markers = [marker for marker in REPORT_CONTENT_MARKERS if marker not in content]
            trend_markers = TREND_REPORTS.get(md_path.name, [])
            missing_markers.extend(marker for marker in trend_markers if marker not in content)
        if "| 层级 |" in content or "层级 |" in content:
            missing_markers.append("no visible 层级 column")
        if missing_markers:
            checks.append(_fail(f"report_content:{md_path.name}", "missing/invalid: " + ", ".join(missing_markers)))
        else:
            if md_path.name == "delivery_acceptance_report.md":
                detail = "delivery acceptance matrix verified"
            elif md_path.name == "report_visual_inventory_report.md":
                detail = "period PDF visual coverage inventory verified"
            elif md_path.name == "visual_quality_acceptance_report.md":
                detail = "UI and visualization quality acceptance verified"
            elif md_path.name == "reference_model_benchmark_report.md":
                detail = "reference model benchmark verified"
            elif md_path.name == "chatgpt_reference_intake_report.md":
                detail = "ChatGPT reference intake verified"
            elif md_path.name == "classification_rulebook_report.md":
                detail = "classification rulebook verified"
            elif md_path.name == "user_manual_report.md":
                detail = "user manual verified"
            elif md_path.name == "requirements_traceability_report.md":
                detail = "requirements traceability verified"
            elif md_path.name == "completion_audit_report.md":
                detail = "completion audit verified"
            elif md_path.name == "goal_completion_audit_report.md":
                detail = "machine-readable goal completion audit verified"
            elif md_path.name == "user_acceptance_matrix_report.md":
                detail = "user acceptance matrix verified"
            elif md_path.name == "spending_control_action_report.md":
                detail = "spending control action plan verified"
            elif md_path.name == "manual_review_report.md":
                detail = "manual review report verified"
            elif md_path.name == "manual_review_queue_audit_report.md":
                detail = "manual review queue audit verified"
            elif md_path.name == "entity_registry_report.md":
                detail = "entity registry and alias map verified"
            elif md_path.name == "evidence_decision_matrix_report.md":
                detail = "evidence classification and decision grade matrix verified"
            elif md_path.name == "reconciliation_audit_report.md":
                detail = "reconciliation layer audit verified"
            elif md_path.name == "data_trust_audit_report.md":
                detail = "data trust layer audit verified"
            elif md_path.name == "finance_ledger_system_improvement_report.md":
                detail = "finance ledger system improvement report verified"
            else:
                detail = "visuals, trend formulas, and category table verified"
            checks.append(_ok(f"report_content:{md_path.name}", detail))
    for filename in REQUIRED_HTML:
        path = reports_dir / filename
        content = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        if path.exists() and path.stat().st_size > 5_000 and "<script>" in content:
            checks.append(_ok(f"html:{filename}", f"{path.stat().st_size} bytes"))
        else:
            checks.append(_fail(f"html:{filename}", "missing, too small, or missing script"))
        if path.exists():
            missing_global_nav = [marker for marker in GLOBAL_NAV_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok(f"global_nav:{filename}", "shared navigation and main-menu return verified")
                if not missing_global_nav
                else _fail(f"global_nav:{filename}", "missing: " + ", ".join(missing_global_nav))
            )
        if filename == "index.html" and path.exists():
            missing_portal = [marker for marker in PORTAL_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("portal_question_console", "custom local question console and report center verified")
                if not missing_portal
                else _fail("portal_question_console", "missing: " + ", ".join(missing_portal))
            )
        if filename == "operations_center.html" and path.exists():
            missing_operations = [marker for marker in OPERATIONS_CENTER_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("operations_center_workflow", "weekly update and review workflow console verified")
                if not missing_operations
                else _fail("operations_center_workflow", "missing: " + ", ".join(missing_operations))
            )
        if filename == "data_access_hub.html" and path.exists():
            missing_data_access = [marker for marker in DATA_ACCESS_HUB_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("data_access_hub", "downstream data access and backtest-style entry verified")
                if not missing_data_access
                else _fail("data_access_hub", "missing: " + ", ".join(missing_data_access))
            )
        if filename == "acceptance_workbench.html" and path.exists():
            missing_acceptance = [marker for marker in ACCEPTANCE_WORKBENCH_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("acceptance_workbench", "button-first user acceptance matrix verified")
                if not missing_acceptance
                else _fail("acceptance_workbench", "missing: " + ", ".join(missing_acceptance))
            )
        if filename == "reference_model_lab.html" and path.exists():
            missing_reference_lab = [marker for marker in REFERENCE_MODEL_LAB_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("reference_model_lab", "interactive open-source reference model lab verified")
                if not missing_reference_lab
                else _fail("reference_model_lab", "missing: " + ", ".join(missing_reference_lab))
            )
        if filename == "dashboard.html" and path.exists():
            missing_dashboard = [marker for marker in DASHBOARD_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("dashboard_visuals", "SVG cashflow and category charts verified")
                if not missing_dashboard
                else _fail("dashboard_visuals", "missing: " + ", ".join(missing_dashboard))
            )
        if filename == "transaction_explorer.html" and path.exists():
            missing_explorer = [marker for marker in TRANSACTION_EXPLORER_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("transaction_explorer_drilldown", "multi-dimensional drilldown panels verified")
                if not missing_explorer
                else _fail("transaction_explorer_drilldown", "missing: " + ", ".join(missing_explorer))
            )
        if filename == "behavior_analysis.html" and path.exists():
            missing_behavior = [marker for marker in BEHAVIOR_ANALYSIS_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("behavior_analysis", "custom tag-combination charts verified")
                if not missing_behavior
                else _fail("behavior_analysis", "missing: " + ", ".join(missing_behavior))
            )
        if filename == "tag_library.html" and path.exists():
            missing_tags = [marker for marker in TAG_LIBRARY_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("tag_library_editor", "persistent tag library editor verified")
                if not missing_tags
                else _fail("tag_library_editor", "missing: " + ", ".join(missing_tags))
            )
        if filename == "review_workbench.html" and path.exists():
            missing_review = [marker for marker in REVIEW_WORKBENCH_CONTENT_MARKERS if marker not in content]
            checks.append(
                _ok("review_workbench_dropdowns", "dropdown-first manual review workflow verified")
                if not missing_review
                else _fail("review_workbench_dropdowns", "missing: " + ", ".join(missing_review))
            )

    manifest = out / "audit" / "report_manifest.json"
    if manifest.exists():
        payload = _read_json(manifest)
        report_values = set(payload.get("reports", {}).values())
        missing = [str(reports_dir / name) for name in REQUIRED_REPORTS if str(reports_dir / name) not in report_values]
        missing.extend(str(reports_dir / name) for name in REQUIRED_HTML if str(reports_dir / name) not in report_values)
        checks.append(_ok("report_manifest", "all required reports registered") if not missing else _fail("report_manifest", "missing: " + ", ".join(missing)))
    else:
        checks.append(_fail("report_manifest", f"missing: {manifest}"))
    audit_dir = out / "audit"
    for filename in REQUIRED_AUDIT_FILES:
        path = audit_dir / filename
        if path.exists() and path.stat().st_size > 20:
            checks.append(_ok(f"audit:{filename}", f"{path.stat().st_size} bytes"))
        else:
            checks.append(_fail(f"audit:{filename}", "missing or empty"))
    source_log_json = audit_dir / "reference_source_log.json"
    if source_log_json.exists():
        try:
            payload = _read_json(source_log_json)
        except Exception as exc:  # pragma: no cover - defensive parse detail
            checks.append(_fail("reference_source_log_schema", f"invalid json: {exc}"))
        else:
            required_keys = {"project", "url", "source_type", "verified_at", "evidence_summary", "reuse_boundary"}
            rows_ok = isinstance(payload, list) and len(payload) >= 5 and all(required_keys <= set(item) for item in payload if isinstance(item, dict))
            checks.append(_ok("reference_source_log_schema", f"{len(payload) if isinstance(payload, list) else 0} rows") if rows_ok else _fail("reference_source_log_schema", "missing required source evidence fields"))
    visual_inventory_json = audit_dir / "report_visual_inventory.json"
    if visual_inventory_json.exists():
        try:
            payload = _read_json(visual_inventory_json)
        except Exception as exc:  # pragma: no cover - defensive parse detail
            checks.append(_fail("report_visual_inventory_schema", f"invalid json: {exc}"))
        else:
            required_keys = {"generated_at", "policy", "summary", "reports", "visual_rows"}
            summary = payload.get("summary", {})
            reports = payload.get("reports", [])
            visual_rows = payload.get("visual_rows", [])
            summary_ok = isinstance(summary, dict) and summary.get("report_count") == 6 and summary.get("gap_count") == 0 and summary.get("pass_count") == 6
            reports_ok = isinstance(reports, list) and len(reports) == 6 and all(row.get("status") == "pass" and row.get("has_visual_bars") == "yes" and row.get("pdf_ok") == "yes" for row in reports if isinstance(row, dict))
            visuals_ok = isinstance(visual_rows, list) and len(visual_rows) >= 6 * 10 and all({"report", "visual_id", "visual_name", "present"} <= set(row) for row in visual_rows if isinstance(row, dict))
            checks.append(
                _ok("report_visual_inventory_schema", f"reports={summary.get('report_count')}, pass={summary.get('pass_count')}")
                if required_keys <= set(payload) and payload.get("policy") == "all_period_pdf_reports_require_visual_sections" and summary_ok and reports_ok and visuals_ok
                else _fail("report_visual_inventory_schema", "missing required fields or visual coverage gaps")
            )
    chatgpt_audit_json = audit_dir / "chatgpt_reference_audit.json"
    if chatgpt_audit_json.exists():
        try:
            payload = _read_json(chatgpt_audit_json)
        except Exception as exc:  # pragma: no cover - defensive parse detail
            checks.append(_fail("chatgpt_reference_audit_schema", f"invalid json: {exc}"))
        else:
            required_keys = {"generated_at", "status", "candidate_count", "scan_dirs", "rows", "gap_rows", "gap_summary", "policy"}
            rows = payload.get("rows", [])
            gap_rows = payload.get("gap_rows", [])
            status_ok = payload.get("status") in {"found", "missing"}
            rows_ok = isinstance(rows, list)
            gap_rows_ok = isinstance(gap_rows, list) and all({"requirement_id", "implementation_status", "evidence"} <= set(row) for row in gap_rows if isinstance(row, dict))
            policy_ok = payload.get("policy") == "fail_closed_no_reference_fabrication"
            checks.append(
                _ok("chatgpt_reference_audit_schema", f"status={payload.get('status')}, candidates={payload.get('candidate_count')}")
                if required_keys <= set(payload) and status_ok and rows_ok and gap_rows_ok and isinstance(payload.get("gap_summary"), dict) and policy_ok
                else _fail("chatgpt_reference_audit_schema", "missing required fields or fail-closed policy")
            )
    goal_audit_json = audit_dir / "goal_completion_audit.json"
    if goal_audit_json.exists():
        try:
            payload = _read_json(goal_audit_json)
        except Exception as exc:  # pragma: no cover - defensive parse detail
            checks.append(_fail("goal_completion_audit_schema", f"invalid json: {exc}"))
        else:
            required_keys = {"generated_at", "summary", "rows", "policy"}
            rows = payload.get("rows", [])
            summary = payload.get("summary", {})
            rows_ok = isinstance(rows, list) and len(rows) >= 8 and all(
                {"requirement_id", "requirement", "status", "evidence", "next_action"} <= set(row)
                for row in rows
                if isinstance(row, dict)
            )
            summary_ok = isinstance(summary, dict) and {"total", "counts", "machine_verifiable_pct", "goal_complete"} <= set(summary)
            policy_ok = payload.get("policy") == "evidence_required_no_subjective_completion"
            checks.append(
                _ok("goal_completion_audit_schema", f"goal_complete={summary.get('goal_complete')}, pct={summary.get('machine_verifiable_pct')}")
                if required_keys <= set(payload) and rows_ok and summary_ok and policy_ok
                else _fail("goal_completion_audit_schema", "missing required fields or evidence policy")
            )
    return checks


def validate_sqlite(db_path: str | Path, *, require_ledger: bool = False) -> list[CheckResult]:
    db = Path(db_path)
    checks: list[CheckResult] = []
    if not db.exists():
        return [_fail("sqlite", f"missing: {db}")]
    checks.append(_ok("sqlite", f"{db} ({db.stat().st_size} bytes)"))
    with _connect(db) as conn:
        names = {row[0] for row in conn.execute("select name from sqlite_master where type in ('table','view')")}
        for table in REQUIRED_TABLES:
            checks.append(_ok(f"table:{table}", "present") if table in names else _fail(f"table:{table}", "missing"))
        if require_ledger:
            for view in REQUIRED_LEDGER_VIEWS:
                checks.append(_ok(f"view:{view}", "present") if view in names else _fail(f"view:{view}", "missing"))
            metadata_count = conn.execute("select count(*) from ledger_metadata").fetchone()[0] if "ledger_metadata" in names else 0
            source_count = conn.execute("select count(*) from source_archives").fetchone()[0] if "source_archives" in names else 0
            checks.append(_ok("ledger_metadata", f"{metadata_count} rows") if metadata_count >= 5 else _fail("ledger_metadata", "missing or incomplete"))
            checks.append(_ok("source_archives", f"{source_count} rows") if source_count >= 1 else _fail("source_archives", "missing sources"))

        classified = conn.execute("select count(*) from classified_transactions_audit").fetchone()[0]
        data_trust = conn.execute("select count(*) from data_trust_transactions").fetchone()[0]
        production = conn.execute("select count(*) from production_expense_allocations").fetchone()[0]
        pending = conn.execute("select count(*) from manual_review_queue").fetchone()[0]
        months = conn.execute("select count(*) from summary_by_month").fetchone()[0]
        checks.append(_ok("classified_count", str(classified)) if classified > 0 else _fail("classified_count", "no rows"))
        checks.append(_ok("data_trust_count", str(data_trust)) if data_trust == classified and data_trust > 0 else _fail("data_trust_count", f"data_trust={data_trust}, classified={classified}"))
        reconciliation_count = conn.execute("select count(*) from reconciliation_checks").fetchone()[0]
        reconciliation_failures = conn.execute("select count(*) from reconciliation_checks where status = 'fail'").fetchone()[0]
        manual_review_audit_count = conn.execute("select count(*) from manual_review_queue_audit").fetchone()[0]
        entity_count = conn.execute("select count(*) from entity_registry").fetchone()[0]
        alias_count = conn.execute("select count(*) from alias_map").fetchone()[0]
        evidence_count = conn.execute("select count(*) from evidence_decision_matrix").fetchone()[0]
        evidence_summary_count = conn.execute("select count(*) from evidence_decision_summary").fetchone()[0]
        checks.append(_ok("reconciliation_check_count", str(reconciliation_count)) if reconciliation_count > 0 else _fail("reconciliation_check_count", "no reconciliation checks"))
        checks.append(
            _ok("reconciliation_failure_count", "0")
            if reconciliation_failures == 0
            else _fail("reconciliation_failure_count", f"{reconciliation_failures} reconciliation checks failed")
        )
        checks.append(_ok("production_count", str(production)) if production > 0 else _fail("production_count", "no production rows"))
        checks.append(_ok("month_count", str(months)) if months > 0 else _fail("month_count", "no month summaries"))
        checks.append(_ok("pending_review_count", str(pending)) if pending >= 0 else _fail("pending_review_count", "invalid"))
        checks.append(_ok("manual_review_audit_count", str(manual_review_audit_count)) if manual_review_audit_count > 0 else _fail("manual_review_audit_count", "no manual review audit rows"))
        checks.append(_ok("entity_registry_count", str(entity_count)) if entity_count > 0 else _fail("entity_registry_count", "no entity registry rows"))
        checks.append(_ok("alias_map_count", str(alias_count)) if alias_count >= entity_count else _fail("alias_map_count", f"aliases={alias_count}, entities={entity_count}"))
        checks.append(_ok("evidence_decision_count", str(evidence_count)) if evidence_count > 0 else _fail("evidence_decision_count", "no evidence decision rows"))
        checks.append(_ok("evidence_decision_summary_count", str(evidence_summary_count)) if evidence_summary_count > 0 else _fail("evidence_decision_summary_count", "no evidence decision summary rows"))
        invalid_evidence = conn.execute(
            "select count(*) from evidence_decision_matrix where evidence_classification not in ('FACT','INFERENCE','OPINION','OBSERVATION')"
        ).fetchone()[0]
        invalid_decisions = conn.execute(
            "select count(*) from evidence_decision_matrix where decision_grade not in ('Actionable','Watch','Observe','Reject')"
        ).fetchone()[0]
        checks.append(_ok("evidence_classification_values", "valid") if invalid_evidence == 0 else _fail("evidence_classification_values", f"{invalid_evidence} invalid evidence classifications"))
        checks.append(_ok("decision_grade_values", "valid") if invalid_decisions == 0 else _fail("decision_grade_values", f"{invalid_decisions} invalid decision grades"))

        total_expense = float(conn.execute("select coalesce(sum(cast(allocated_amount_cents as real)),0) / 100.0 from production_expense_allocations").fetchone()[0])
        summary_total = float(conn.execute("select coalesce(sum(cast(total_expense as real)),0) from summary_by_month").fetchone()[0])
        if abs(total_expense - summary_total) <= 0.05:
            checks.append(_ok("expense_reconciliation", f"production={total_expense:.2f}, monthly={summary_total:.2f}"))
        else:
            checks.append(_fail("expense_reconciliation", f"production={total_expense:.2f}, monthly={summary_total:.2f}"))

        pending_keys = {
            row[0]
            for row in conn.execute(
                "select coalesce(order_id, transaction_time || '|' || counterparty || '|' || amount_cents || '|' || description) from manual_review_queue"
            )
        }
        production_keys = {row[0] for row in conn.execute("select review_key from production_expense_allocations")}
        overlap = pending_keys & production_keys
        checks.append(_ok("pending_not_in_production", "no overlap") if not overlap else _fail("pending_not_in_production", f"{len(overlap)} overlapping review keys"))
    return checks


def validate_all(output_dir: str | Path, db_path: str | Path, *, require_ledger: bool = False) -> list[CheckResult]:
    return validate_reports(output_dir) + validate_sqlite(db_path, require_ledger=require_ledger)


def _print_results(results: list[CheckResult]) -> None:
    width = max(len(item.name) for item in results) if results else 10
    for item in results:
        print(f"{item.status.upper():4}  {item.name.ljust(width)}  {item.detail}")


def has_failures(results: list[CheckResult]) -> bool:
    return any(item.status == "fail" for item in results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate generated economic bleed reports and SQLite outputs.")
    parser.add_argument("--output", default="outputs/finance_ledger_20220605_20260603", help="Generated analysis output directory.")
    parser.add_argument("--db", default="data/finance_ledger/finance_ledger.sqlite", help="SQLite database to validate.")
    parser.add_argument("--require-ledger", action="store_true", help="Require master ledger metadata and stable views.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = validate_all(args.output, args.db, require_ledger=args.require_ledger)
    if args.json:
        print(json.dumps([item.to_dict() for item in results], ensure_ascii=False, indent=2))
    else:
        _print_results(results)
    return 1 if has_failures(results) else 0
