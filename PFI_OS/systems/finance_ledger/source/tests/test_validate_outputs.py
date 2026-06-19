from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.validate_outputs import REQUIRED_HTML, REQUIRED_REPORTS, has_failures, validate_all


def write_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-" + b"0" * 25_000)


def write_html(path: Path) -> None:
    dashboard_markers = ""
    explorer_markers = ""
    behavior_markers = ""
    tag_library_markers = ""
    review_markers = ""
    reference_lab_markers = ""
    portal_markers = ""
    operations_markers = ""
    data_access_markers = ""
    acceptance_markers = ""
    if path.name == "index.html":
        portal_markers = """
        <section id="questionConsole">自定义问题查询控制台 本地记账分析系统 本地检索 · 证据回答 FACT INFERENCE OBSERVATION</section>
        <a id="dataAccessHubLink">数据接入与回测入口</a>
        <input id="customQuestionInput">
        <div id="questionHistory"></div>
        <div id="answerEvidence"></div>
        <div id="reportCenter"></div>
        <input id="reportFilterKeyword">
        <select id="reportPeriodFilter"></select>
        <select id="reportThemeFilter"></select>
        <select id="reportEvidenceFilter"></select>
        <div id="selectedReportList"></div>
        <div id="questionButtons"></div>
        <div id="questionAnswer"></div>
        <a target="_blank" rel="noopener"></a>
        <script>
          const DATA = {question_templates:[], qa_index:[]};
          function answerCustomQuestion() {}
          function renderReportCenter() {}
          function renderSelectedReports() {}
          function renderQuestion() {}
          function renderQuestionConsole() {}
        </script>
        """
    if path.name == "operations_center.html":
        operations_markers = """
        <h1>经济放血运行控制台</h1>
        <section id="workflowMap">当前运行状态</section>
        <svg id="workflowVisual"></svg>
        <div id="workflowSummary"></div>
        <div id="reviewPressureBar"></div>
        <h2>下一步选项</h2>
        <div id="stepButtons">每周更新 大额复核 用户验收 浏览器验收 打包前必跑 交付打包 只读 API</div>
        <pre id="actionCommand"></pre>
        <table id="reviewStatus"></table>
        <script>
          function selectAction() {}
          function copyCommand() {}
          function renderWorkflowVisual() {}
        </script>
        """
    if path.name == "data_access_hub.html":
        data_access_markers = """
        <h1>数据接入与回测入口</h1>
        <p>PFIOS 量化回测 ResearchBus SQLite 数据库 只读 API</p>
        <table id="viewTable">v_mart_daily_cashflow v_fact_expense_allocations v_data_trust_transactions v_reconciliation_checks</table>
        <table id="consumerTable"></table>
        <pre id="apiCommand"></pre>
        <script>
          function copyText() {}
        </script>
        """
    if path.name == "acceptance_workbench.html":
        acceptance_markers = """
        <h1>用户验收工作台</h1>
        <section id="acceptanceMatrix">验收选择矩阵 ChatGPT 对照文件</section>
        <table id="acceptanceSummary"></table>
        <div id="progressBar"></div>
        <div id="acceptanceScore"></div>
        <pre id="nextCommand">下一步选项 A/B/C</pre>
        <p id="exportStatus">复制验收 JSON</p>
        <textarea id="acceptanceJsonPreview">套用：1-8 A，最后 B</textarea>
        <div id="refinementGuide"></div>
        <input id="chatgptReferenceFile">
        <textarea id="chatgptReferenceText">ChatGPT 对照文件</textarea>
        <pre id="chatgptAuditCommand">导出对照文件 localStorage</pre>
        <script>
          function selectChoice() {}
          function downloadJson() {}
          function copyAcceptanceJson() {}
          function applyUserStatedChoices() {}
          function downloadCsv() {}
          function loadChatGPTReferenceFile() {}
          function saveReferenceDraft() {}
          function downloadChatGPTReference() {}
        </script>
        """
    if path.name == "reference_model_lab.html":
        reference_lab_markers = """
        <h1>开源参考模型工作台</h1>
        <input id="modelSearch">
        <select id="licenseFilter"></select>
        <select id="coverageFilter"></select>
        <svg id="referenceCoverageChart">吸收度对比</svg>
        <svg id="referenceFeatureDonut"></svg>
        <div id="referenceModelMatrix">GitHub 不复制外部代码或 UI</div>
        <div id="referenceUIPatternMatrix">UI/布局模式吸收矩阵</div>
        <table id="referenceGapTable">差距与边界</table>
        <script>
          function applyReferenceFilters() {}
          function renderReferenceModelLab() {}
          function renderUIPatternMatrix() {}
          function downloadReferenceCsv() {}
        </script>
        """
    if path.name == "dashboard.html":
        dashboard_markers = """
        <svg id="monthlyCashflowChart" aria-label="月度现金流折线图"></svg>
        <svg id="categoryShareChart" aria-label="主类占比环形图"></svg>
        <script>
          function renderMonthlyChart() {}
          function renderCategoryDonut() {}
          function renderCounterpartyConcentration() {}
          function renderTimeHeatmap() {}
          function renderMechanismBars() {}
          function renderRiskControlMatrix() {}
          function renderBehaviorBuckets() {}
          function renderMonthlyCategoryHeatmap() {}
          function renderCumulativeCashflow() {}
          function renderSourceHealth() {}
          function renderReviewStatus() {}
          function renderBudgetPressureRadar() {}
        </script>
        <div id="counterpartyConcentration">交易对方集中度</div>
        <div id="timeHeatmap">时间行为热力矩阵</div>
        <div id="mechanismBars">经济放血机制图谱</div>
        <table id="riskControlMatrix">风险控制矩阵</table>
        <div id="behaviorBuckets">行为桶支出对照</div>
        <div id="monthlyCategoryHeatmap">主类月度热力矩阵</div>
        <div id="cumulativeCashflow">累计净现金流轨迹</div>
        <div id="sourcePlatformBars">数据源平台分布与导入健康</div>
        <div id="sourceHealthCards"></div>
        <table id="sourceHealthTable"></table>
        <div id="reviewStatusBars">大额复核闭环状态</div>
        <table id="reviewStatusTable"></table>
        <svg id="budgetPressureRadar" aria-label="预算压力雷达"></svg>
        <div id="budgetPressureBars">预算压力雷达</div>
        """
    if path.name == "transaction_explorer.html":
        explorer_markers = """
        <script>
          function selectedTags() {}
          function applyTagPreset() {}
          function fuzzySearchMatch() {}
          function renderSearchFeedback() {}
          function toggleDetails() {}
          function renderDrilldown() {}
          function renderMiniBars() {}
        </script>
        <select id="tagPreset"><option>标签任一命中</option><option>标签全部命中</option></select>
        <select id="tagMatchMode"></select>
        <div id="tagCombo"></div>
        <div id="searchFeedback">搜索反馈</div>
        <section id="detailPanel"><button id="detailToggle">折叠明细</button></section>
        <div id="explorerCategoryBars">筛选主类分布</div>
        <div id="explorerRiskBars">筛选风险标签</div>
        <div id="explorerMonthTrend">筛选月份趋势</div>
        <div id="explorerCounterpartyBars">筛选对手方排行</div>
        """
    if path.name == "behavior_analysis.html":
        behavior_markers = """
        <h1>交易行为分析</h1>
        <select id="chartType"><option>折线图</option><option>直方图</option><option>环形图</option><option>金额分布图</option></select>
        <select id="matchMode"></select>
        <div id="tagGrid"></div>
        <svg id="behaviorChart"></svg>
        <script>
          function applyPreset() {}
          function renderChart() {}
          function amountBuckets() {}
        </script>
        """
    if path.name == "tag_library.html":
        tag_library_markers = """
        <h1>标签库编辑</h1>
        <table id="tagTable"></table>
        <div id="presetGrid"></div>
        <button>新增筛选组合</button>
        <span>tag_library_custom.json</span>
        <code>--tag-library</code>
        <script type="application/json">{"filter_presets":[]}</script>
        <script>
          function downloadJson() {}
          function addTag() {}
          function addPreset() {}
          function updateTag() {}
          function updatePreset() {}
          function updatePresetTags() {}
        </script>
        """
    if path.name == "review_workbench.html":
        review_markers = """
        <script>
          function decisionOptions() {}
          function categoryPresetOptions() {}
          function filteredPendingRows() {}
          function groupedRows() {}
          function renderGroupMatrix() {}
          function applyGroupAction() {}
          function applyCandidate() {}
          function applyCandidatesToVisible() {}
          function applyAllCandidates() {}
          function applyBatchToVisible() {}
          function setPrimaryCategory() {}
          function setPrimaryRiskTags() {}
          function changeCategoryPreset() {}
        </script>
        <input id="reviewSearch">
        <select id="filterCategory"></select>
        <select id="filterDecision"></select>
        <select id="batchCategory"></select>
        <select id="batchRisk"></select>
        <select id="groupMode"></select>
        <div id="candidateCount"></div>
        <div id="impactPreview"></div>
        <div id="reviewGroupMatrix">分组矩阵 套用批量栏 套用当前筛选候选</div>
        <select>复核决定</select>
        <select>主类/子类</select>
        <select>风险标签</select>
        <button>应用到当前筛选</button>
        <span>review_decisions_confirmed.csv</span>
        """
    global_nav_markers = """
    <nav id="globalNav">返回主菜单 数据接入 报告中心 交易明细 行为分析 标签库 大额复核 <button id="usageGuideToggle"></button></nav>
    <aside id="usageGuidePanel">使用说明与专业术语 推荐操作路径 专业术语 生产口径 待复核隔离 Data Trust Reconciliation</aside>
    <div id="usageGuideBackdrop"></div>
    <script>function openUsageGuide() {} function closeUsageGuide() {}</script>
    """
    path.write_text("<html><body><script>const ok = true;</script>" + global_nav_markers + portal_markers + operations_markers + data_access_markers + acceptance_markers + reference_lab_markers + dashboard_markers + explorer_markers + behavior_markers + tag_library_markers + review_markers + ("x" * 6_000) + "</body></html>", encoding="utf-8")


def write_report_md(path: Path) -> None:
    if path.name == "delivery_acceptance_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 交付验收报告",
                    "## 目标对照",
                    "## 数据规模",
                    "## 正式交付物",
                    "## 开源参考吸收矩阵",
                    "## 验收命令",
                    "## 待确认事项",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "classification_rulebook_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 分类规则手册",
                    "## 主类/子类体系",
                    "## 资金口径",
                    "## 趋势公式",
                    "## 风险标签",
                    "## 特殊确认规则",
                    "## 规则执行顺序",
                    "## 默认规则",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "reference_model_benchmark_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 开源参考对标报告",
                    "## 对标原则",
                    "## 参考项目功能矩阵",
                    "来源",
                    "证据摘要",
                    "## 功能吸收矩阵",
                    "## UI/布局模式吸收矩阵",
                    "## 本系统增强项",
                    "## 仍未覆盖的边界",
                    "## 验收证据",
                    "reference_source_log.json",
                    "reference_source_log.csv",
                    "reference_ui_patterns.json",
                    "reference_ui_patterns.csv",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "chatgpt_reference_intake_report.md":
        path.write_text(
            "\n".join(
                [
                    "# ChatGPT 对照文件接入审计报告",
                    "## 审计结论",
                    "## 候选文件清单",
                    "## 差距矩阵",
                    "## 接入规则",
                    "不伪造来源",
                    "chatgpt_reference_gap_matrix.csv",
                    "## 后续动作",
                    "ChatGPT",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "visual_quality_acceptance_report.md":
        path.write_text(
            "\n".join(
                [
                    "# UI 与可视化质量验收报告",
                    "## 页面矩阵",
                    "## 可视化矩阵",
                    "## 布局与颜色规则",
                    "## 交互验收",
                    "## 验收证据",
                    "report_visual_inventory.json",
                    "## 后续精修队列",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "report_visual_inventory_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 报告可视化覆盖审计报告",
                    "## 覆盖总览",
                    "all_period_pdf_reports_require_visual_sections",
                    "## 周期报告矩阵",
                    "## 图表类型矩阵",
                    "## 验收规则",
                    "## 验收证据",
                    "report_visual_inventory.json",
                    "report_visual_inventory.csv",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "user_manual_report.md":
        path.write_text(
            "\n".join(
                [
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
            ),
            encoding="utf-8",
        )
        return
    if path.name == "requirements_traceability_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 需求追踪验收报告",
                    "## 验收总览",
                    "## 需求追踪矩阵",
                    "大额 >= 10000 先复核不自动入账",
                    "固定问题模板查询",
                    "交付 ZIP 包",
                    "## 当前明确边界",
                    "## 关键入口",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "completion_audit_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 最终完成审计报告",
                    "## 目标拆解",
                    "## 证据矩阵",
                    "## 验收结果",
                    "## 剩余边界",
                    "## 完成判断",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "goal_completion_audit_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 目标完成度机器审计报告",
                    "## 审计总览",
                    "机器可验证完成度",
                    "evidence_required_no_subjective_completion",
                    "## 逐项矩阵",
                    "needs_user_input",
                    "## 状态口径",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "user_acceptance_matrix_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 用户验收矩阵报告",
                    "## 当前进度判断",
                    "ChatGPT 对照文件",
                    "## 验收选择矩阵",
                    "## 下一步选项",
                    "## 免打扰执行规则",
                    "## 证据入口",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "manual_review_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 大额复核清单",
                    "## 复核总览",
                    "## 处理原则",
                    "## 当前建议分类汇总",
                    "## 交易对方 Top 20",
                    "## 待复核明细",
                    "## 回灌命令",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "manual_review_queue_audit_report.md":
        path.write_text(
            "\n".join(
                [
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
            ),
            encoding="utf-8",
        )
        return
    if path.name == "entity_registry_report.md":
        path.write_text(
            "\n".join(
                [
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
            ),
            encoding="utf-8",
        )
        return
    if path.name == "evidence_decision_matrix_report.md":
        path.write_text(
            "\n".join(
                [
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
            ),
            encoding="utf-8",
        )
        return
    if path.name == "spending_control_action_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 消费控制行动计划",
                    "## 行动总览",
                    "## 优先级动作",
                    "## 风险暴露",
                    "## 主类控制线",
                    "## 下期执行规则",
                    "## 复盘流程",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "reconciliation_audit_report.md":
        path.write_text(
            "\n".join(
                [
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
            ),
            encoding="utf-8",
        )
        return
    if path.name == "data_trust_audit_report.md":
        path.write_text(
            "\n".join(
                [
                    "# Data Trust Layer 审计报告",
                    "## 状态定义",
                    "RAW_IMPORTED",
                    "PARSED_CANDIDATE",
                    "NEEDS_REVIEW",
                    "USER_CONFIRMED",
                    "RECONCILED",
                    "ARCHIVED",
                    "REJECTED",
                    "## 当前分布",
                    "## 口径说明",
                    "production_expense_allocations",
                ]
            ),
            encoding="utf-8",
        )
        return
    if path.name == "finance_ledger_system_improvement_report.md":
        path.write_text(
            "\n".join(
                [
                    "# 记账分析系统 V2 优化改进报告",
                    "## 执行摘要",
                    "FACT",
                    "INFERENCE",
                    "OBSERVATION",
                    "## 信息来源表",
                    "## 参考项目 / 案例 / 竞品对比表",
                    "## 可复用模块",
                    "## 差距分析",
                    "## 改进方案",
                    "## 实施路线图",
                    "## 风险与限制",
                    "## 验收标准",
                    "## 下一步行动建议",
                ]
            ),
            encoding="utf-8",
        )
        return
    trend_markers = {
        "weekly_report.md": "### 周期支出趋势\n\n趋势公式：周报环比：本周 vs 上周；周报同比：本周 vs 去年同 ISO 周。\n\n## 主类/子类趋势\n",
        "monthly_report.md": "### 周期支出趋势\n\n趋势公式：月报环比：本月 vs 上月；月报同比：本月 vs 去年同月。\n\n## 主类/子类趋势\n",
        "quarterly_report.md": "### 周期支出趋势\n\n趋势公式：季报环比：本季 vs 上季；季报同比：本季 vs 去年同季。\n\n## 主类/子类趋势\n",
        "half_year_report.md": "### 周期支出趋势\n\n趋势公式：半年报环比：本半年 vs 上半年；半年报同比：本半年 vs 去年同期半年。\n\n## 主类/子类趋势\n",
        "yearly_report.md": "### 周期支出趋势\n\n趋势公式：年报同比：本年 vs 上年。\n\n## 主类/子类趋势\n",
    }
    path.write_text(
        "\n".join(
            [
                "# Report",
                "## 可视化图表",
                "### 现金流视图",
                "### 累计净现金流轨迹",
                "### 行为桶支出对照",
                "### 预算压力雷达",
                "| 项目 | 金额 | 图表 |",
                "| 支出 | ¥1.00 | █░ |",
                "### 主类支出占比",
                "### 风险标签金额排行",
                "### 经济放血机制图谱",
                "### 风险控制矩阵",
                "### 交易对方集中度",
                "### 时间行为热力图",
                "### 主类月度热力矩阵",
                trend_markers.get(path.name, ""),
                "## 主类/子类金额",
                "| 主类 | 子类 | 金额 | 笔数 | 主类占总支出 | 子类占主类 |",
            ]
        ),
        encoding="utf-8",
    )


def make_output(root: Path) -> None:
    reports = root / "reports"
    reports.mkdir(parents=True)
    for report in REQUIRED_REPORTS:
        write_pdf(reports / report)
        write_report_md(reports / report.replace(".pdf", ".md"))
    for html in REQUIRED_HTML:
        write_html(reports / html)
    audit = root / "audit"
    audit.mkdir()
    manifest_reports = {f"pdf_{idx}": str(reports / report) for idx, report in enumerate(REQUIRED_REPORTS)}
    manifest_reports.update({f"html_{idx}": str(reports / html) for idx, html in enumerate(REQUIRED_HTML)})
    (audit / "report_manifest.json").write_text('{"reports":' + repr(manifest_reports).replace("'", '"') + "}", encoding="utf-8")
    reference_source_rows = [
        {
            "project": f"project-{idx}",
            "url": f"https://example.com/project-{idx}",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "MIT",
            "reference_feature_count": 4,
            "incorporated_feature_count": 4,
            "evidence_summary": "verified evidence",
            "remaining_gap": "none",
            "reuse_boundary": "functional reference only",
        }
        for idx in range(5)
    ]
    (audit / "reference_models.json").write_text(json.dumps(reference_source_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "reference_source_log.json").write_text(json.dumps(reference_source_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "reference_source_log.csv").write_text(
        "project,url,source_type,verified_at,license,reference_feature_count,incorporated_feature_count,evidence_summary,remaining_gap,reuse_boundary\n"
        + "\n".join(
            f"{row['project']},{row['url']},{row['source_type']},{row['verified_at']},{row['license']},{row['reference_feature_count']},{row['incorporated_feature_count']},{row['evidence_summary']},{row['remaining_gap']},{row['reuse_boundary']}"
            for row in reference_source_rows
        ),
        encoding="utf-8",
    )
    reference_ui_pattern_rows = [
        {
            "pattern_id": "demo",
            "pattern": "UI/布局模式",
            "reference_projects": "project-1",
            "source_signal": "dashboard",
            "applied_in": "dashboard.html",
            "implementation_evidence": "verified",
            "ui_boundary": "functional reference only",
        }
    ]
    (audit / "reference_ui_patterns.json").write_text(json.dumps(reference_ui_pattern_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "reference_ui_patterns.csv").write_text(
        "pattern_id,pattern,reference_projects,source_signal,applied_in,implementation_evidence,ui_boundary\n"
        "demo,UI/布局模式,project-1,dashboard,dashboard.html,verified,functional reference only\n",
        encoding="utf-8",
    )
    visual_reports = [
        {
            "report": name,
            "markdown_file": f"{idx}.md",
            "pdf_file": f"{idx}.pdf",
            "required_visuals": 14,
            "present_visuals": 14,
            "coverage_pct": "100.00%",
            "has_visual_bars": "yes",
            "pdf_ok": "yes",
            "status": "pass",
            "missing_visuals": "",
        }
        for idx, name in enumerate(["周报", "月报", "季报", "半年报", "年报", "账期年报"], 1)
    ]
    visual_rows = [
        {
            "report": row["report"],
            "markdown_file": row["markdown_file"],
            "visual_id": f"visual_{idx}",
            "visual_name": "现金流视图",
            "purpose": "demo",
            "present": "yes",
            "evidence": "demo",
        }
        for row in visual_reports
        for idx in range(12)
    ]
    (audit / "report_visual_inventory.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-06-05T00:00:00",
                "policy": "all_period_pdf_reports_require_visual_sections",
                "summary": {"report_count": 6, "pass_count": 6, "gap_count": 0, "required_visuals_per_report": 14, "coverage_pct": 100.0},
                "reports": visual_reports,
                "visual_rows": visual_rows,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (audit / "report_visual_inventory.csv").write_text(
        "report,markdown_file,pdf_file,required_visuals,present_visuals,coverage_pct,has_visual_bars,pdf_ok,status,missing_visuals\n"
        + "\n".join(f"{row['report']},{row['markdown_file']},{row['pdf_file']},14,14,100.00%,yes,yes,pass," for row in visual_reports)
        + "\n",
        encoding="utf-8",
    )
    chatgpt_payload = {
        "generated_at": "2026-06-05T09:10:00",
        "status": "missing",
        "candidate_count": 0,
        "scan_dirs": ["chatgpt_reference", "requirements", "docs"],
        "inputs": [],
        "rows": [],
        "gap_rows": [
            {
                "requirement_id": "pdf_reports",
                "requirement": "正式 PDF 周/月/季/半年/年报",
                "source_hits": 0,
                "implementation_status": "blocked_missing_chatgpt_source",
                "evidence": "reports/weekly_report.pdf",
                "next_action": "provide source",
            }
        ],
        "gap_summary": {"blocked_missing_chatgpt_source": 1},
        "policy": "fail_closed_no_reference_fabrication",
    }
    (audit / "chatgpt_reference_audit.json").write_text(json.dumps(chatgpt_payload, ensure_ascii=False), encoding="utf-8")
    (audit / "chatgpt_reference_audit.csv").write_text("path,status,reason,suffix,size_bytes,modified_at,sha256\n", encoding="utf-8")
    (audit / "chatgpt_reference_gap_matrix.csv").write_text("requirement_id,requirement,source_hits,implementation_status,evidence,next_action\n", encoding="utf-8")
    goal_payload = {
        "generated_at": "2026-06-05T10:10:00",
        "summary": {
            "total": 8,
            "counts": {"met": 6, "needs_user_input": 2},
            "machine_verifiable_total": 6,
            "machine_verifiable_met": 6,
            "machine_verifiable_pct": 100.0,
            "goal_complete": False,
        },
        "rows": [
            {
                "requirement_id": f"item_{idx}",
                "requirement": "requirement",
                "status": "met" if idx < 6 else "needs_user_input",
                "evidence": "reports/index.html",
                "detail": "detail",
                "next_action": "next",
            }
            for idx in range(8)
        ],
        "policy": "evidence_required_no_subjective_completion",
    }
    (audit / "goal_completion_audit.json").write_text(json.dumps(goal_payload, ensure_ascii=False), encoding="utf-8")
    (audit / "goal_completion_audit.csv").write_text("requirement_id,requirement,status,evidence,detail,next_action\n", encoding="utf-8")
    reconciliation_rows = [
        {
            "check_id": "demo",
            "layer": "test",
            "status": "pass",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "expected": "ok",
            "actual": "ok",
            "formula": "demo",
            "evidence_path": "test",
            "detail": "demo",
            "next_action": "none",
            "generated_at": "2026-06-05T00:00:00",
            "schema_version": "test",
        }
    ]
    (audit / "reconciliation_checks.json").write_text(json.dumps(reconciliation_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "reconciliation_checks.csv").write_text(
        "check_id,layer,status,evidence_classification,decision_grade,expected,actual,formula,evidence_path,detail,next_action,generated_at,schema_version\n"
        "demo,test,pass,FACT,Actionable,ok,ok,demo,test,demo,none,2026-06-05T00:00:00,test\n",
        encoding="utf-8",
    )
    manual_review_audit_rows = [
        {
            "review_key": "r1",
            "queue_status": "PENDING_REVIEW",
            "priority": "P1",
            "evidence_classification": "OBSERVATION",
            "decision_grade": "Watch",
            "ledger_effect": "blocked_until_manual_review",
            "next_action": "manual review",
            "amount": "20000.00",
            "schema_version": "test",
        }
    ]
    (audit / "manual_review_queue_audit.json").write_text(json.dumps(manual_review_audit_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "manual_review_queue_audit.csv").write_text(
        "review_key,queue_status,priority,evidence_classification,decision_grade,ledger_effect,next_action,amount,schema_version\n"
        "r1,PENDING_REVIEW,P1,OBSERVATION,Watch,blocked_until_manual_review,manual review,20000.00,test\n",
        encoding="utf-8",
    )
    entity_rows = [
        {
            "entity_id": "counterparty_1",
            "entity_type": "counterparty",
            "canonical_name": "测试商户",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "schema_version": "test",
        }
    ]
    alias_rows = [
        {
            "alias_id": "alias_1",
            "entity_type": "counterparty",
            "alias_value": "测试商户",
            "alias_normalized": "测试商户",
            "canonical_entity_id": "counterparty_1",
            "collision_status": "unique",
            "decision_grade": "Actionable",
            "schema_version": "test",
        }
    ]
    summary_rows = [
        {
            "entity_type": "counterparty",
            "entity_count": "1",
            "alias_count": "1",
            "alias_conflict_count": "0",
            "review_required_count": "0",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "schema_version": "test",
        }
    ]
    (audit / "entity_registry.json").write_text(json.dumps(entity_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "entity_registry.csv").write_text(
        "entity_id,entity_type,canonical_name,evidence_classification,decision_grade,schema_version\n"
        "counterparty_1,counterparty,测试商户,FACT,Actionable,test\n",
        encoding="utf-8",
    )
    (audit / "alias_map.json").write_text(json.dumps(alias_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "alias_map.csv").write_text(
        "alias_id,entity_type,alias_value,alias_normalized,canonical_entity_id,collision_status,decision_grade,schema_version\n"
        "alias_1,counterparty,测试商户,测试商户,counterparty_1,unique,Actionable,test\n",
        encoding="utf-8",
    )
    (audit / "entity_registry_summary.json").write_text(json.dumps(summary_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "entity_registry_summary.csv").write_text(
        "entity_type,entity_count,alias_count,alias_conflict_count,review_required_count,evidence_classification,decision_grade,schema_version\n"
        "counterparty,1,1,0,0,FACT,Actionable,test\n",
        encoding="utf-8",
    )
    evidence_rows = [
        {
            "evidence_id": "e1",
            "layer": "DataTrust",
            "subject_type": "transaction",
            "subject_id": "tx-1",
            "subject_name": "测试商户",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "status": "RECONCILED",
            "risk_level": "P3",
            "conclusion": "production matched",
            "source_table": "data_trust_transactions",
            "evidence_path": "data/data_trust_transactions.csv",
            "next_action": "keep",
            "generated_at": "2026-06-05T00:00:00",
            "schema_version": "evidence_decision_matrix.v1",
        }
    ]
    evidence_summary_rows = [
        {
            "layer": "DataTrust",
            "evidence_classification": "FACT",
            "decision_grade": "Actionable",
            "status": "RECONCILED",
            "count": "1",
            "schema_version": "evidence_decision_matrix.v1",
            "generated_at": "2026-06-05T00:00:00",
        }
    ]
    (audit / "evidence_decision_matrix.json").write_text(json.dumps(evidence_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "evidence_decision_matrix.csv").write_text(
        "evidence_id,layer,subject_type,subject_id,subject_name,evidence_classification,decision_grade,status,risk_level,conclusion,source_table,evidence_path,next_action,generated_at,schema_version\n"
        "e1,DataTrust,transaction,tx-1,测试商户,FACT,Actionable,RECONCILED,P3,production matched,data_trust_transactions,data/data_trust_transactions.csv,keep,2026-06-05T00:00:00,evidence_decision_matrix.v1\n",
        encoding="utf-8",
    )
    (audit / "evidence_decision_summary.json").write_text(json.dumps(evidence_summary_rows, ensure_ascii=False), encoding="utf-8")
    (audit / "evidence_decision_summary.csv").write_text(
        "layer,evidence_classification,decision_grade,status,count,schema_version,generated_at\n"
        "DataTrust,FACT,Actionable,RECONCILED,1,evidence_decision_matrix.v1,2026-06-05T00:00:00\n",
        encoding="utf-8",
    )
    (audit / "finance_ledger_system_improvement_source_log.json").write_text(
        json.dumps([{"source": "Actual Budget", "credibility": "高", "relevance": "高"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (audit / "finance_ledger_system_improvement_source_log.csv").write_text("source,credibility,relevance\nActual Budget,高,高\n", encoding="utf-8")
    (audit / "system_improvement_gap_matrix.csv").write_text("gap,evidence,improvement,priority,status\nfixed,portal,custom query,P0,planned\n", encoding="utf-8")
    (audit / "question_answer_index.json").write_text(
        json.dumps([{"question": "本月最该优化哪类支出", "answer_policy": "demo", "sources": ["summary_by_month"]}], ensure_ascii=False),
        encoding="utf-8",
    )
    (audit / "finance_ledger_system_improvement_source_log.json").write_text(
        json.dumps([{"source": "test", "evidence": "fixture"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (audit / "finance_ledger_system_improvement_source_log.csv").write_text("source,evidence\ntest,fixture\n", encoding="utf-8")
    (audit / "system_improvement_gap_matrix.csv").write_text("requirement,status,evidence\nfixture,met,test\n", encoding="utf-8")
    (audit / "question_answer_index.json").write_text(
        json.dumps({"questions": [{"id": "fixture", "answer": "test"}]}, ensure_ascii=False),
        encoding="utf-8",
    )


def make_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("create table classified_transactions_audit (id text)")
        conn.executemany("insert into classified_transactions_audit values (?)", [("a",), ("b",)])
        conn.execute("create table production_expense_allocations (review_key text, allocated_amount_cents text)")
        conn.execute("insert into production_expense_allocations values ('p1','10000')")
        conn.execute("create table manual_review_queue (order_id text, transaction_time text, counterparty text, amount_cents text, description text)")
        conn.execute("insert into manual_review_queue values ('r1','2026-01-01','x','2000000','review')")
        conn.execute("create table manual_review_status_summary (status text)")
        conn.execute("create table manual_review_decision_candidates (status text)")
        conn.execute("create table manual_review_decision_candidate_groups (status text)")
        conn.execute("create table manual_review_queue_audit (review_key text, queue_status text, priority text)")
        conn.execute("insert into manual_review_queue_audit values ('r1','PENDING_REVIEW','P1')")
        conn.execute("create table manual_review_queue_audit_summary (queue_status text, priority text, count text)")
        conn.execute("insert into manual_review_queue_audit_summary values ('PENDING_REVIEW','P1','1')")
        conn.execute("create table summary_by_category (id text)")
        conn.execute("create table summary_by_risk_tag (id text)")
        conn.execute("create table spending_control_plan (id text)")
        conn.execute("create table budget_pressure_radar (id text)")
        conn.execute("create table source_platform_summary (id text)")
        conn.execute("create table data_trust_transactions (data_trust_status text)")
        conn.executemany("insert into data_trust_transactions values (?)", [("RECONCILED",), ("NEEDS_REVIEW",)])
        conn.execute("create table reconciliation_checks (check_id text, status text)")
        conn.executemany("insert into reconciliation_checks values (?,?)", [("demo", "pass")])
        conn.execute("create table entity_registry (entity_id text, entity_type text, canonical_name text)")
        conn.execute("insert into entity_registry values ('counterparty_1','counterparty','测试商户')")
        conn.execute("create table alias_map (alias_id text, entity_type text, alias_normalized text, canonical_entity_id text, collision_status text)")
        conn.execute("insert into alias_map values ('alias_1','counterparty','测试商户','counterparty_1','unique')")
        conn.execute("create table entity_registry_summary (entity_type text, entity_count text, alias_count text)")
        conn.execute("insert into entity_registry_summary values ('counterparty','1','1')")
        conn.execute(
            "create table evidence_decision_matrix (evidence_id text, evidence_classification text, decision_grade text, layer text, status text)"
        )
        conn.execute("insert into evidence_decision_matrix values ('e1','FACT','Actionable','DataTrust','RECONCILED')")
        conn.execute("create table evidence_decision_summary (layer text, evidence_classification text, decision_grade text, status text, count text)")
        conn.execute("insert into evidence_decision_summary values ('DataTrust','FACT','Actionable','RECONCILED','1')")
        conn.execute("create table tag_library (id text)")
        conn.execute("create table tag_filter_presets (id text)")
        for table in ["summary_by_week", "summary_by_quarter", "summary_by_half", "summary_by_year"]:
            conn.execute(f"create table {table} (id text)")
        conn.execute("create table summary_by_month (total_expense text)")
        conn.execute("insert into summary_by_month values ('100.00')")
        conn.execute("create table ledger_metadata (key text, value text)")
        conn.executemany("insert into ledger_metadata values (?,?)", [(str(i), str(i)) for i in range(5)])
        conn.execute("create table source_archives (id text)")
        conn.execute("insert into source_archives values ('s1')")
        for view, table in [
            ("v_production_transactions", "production_expense_allocations"),
            ("v_classified_transactions_audit", "classified_transactions_audit"),
            ("v_pending_large_review", "manual_review_queue"),
            ("v_review_status_summary", "manual_review_status_summary"),
            ("v_review_decision_candidates", "manual_review_decision_candidates"),
            ("v_review_decision_candidate_groups", "manual_review_decision_candidate_groups"),
            ("v_manual_review_queue_audit", "manual_review_queue_audit"),
            ("v_manual_review_queue_blockers", "manual_review_queue_audit"),
            ("v_manual_review_queue_summary", "manual_review_queue_audit_summary"),
            ("v_cashflow_monthly", "summary_by_month"),
            ("v_cashflow_yearly", "summary_by_year"),
            ("v_category_summary", "summary_by_category"),
            ("v_risk_summary", "summary_by_risk_tag"),
            ("v_control_plan", "spending_control_plan"),
            ("v_budget_pressure_radar", "budget_pressure_radar"),
            ("v_source_platform_summary", "source_platform_summary"),
            ("v_data_trust_transactions", "data_trust_transactions"),
            ("v_data_trust_sources", "source_archives"),
            ("v_data_trust_summary", "data_trust_transactions"),
            ("v_reconciliation_checks", "reconciliation_checks"),
            ("v_reconciliation_failures", "reconciliation_checks"),
            ("v_reconciliation_summary", "reconciliation_checks"),
            ("v_entity_registry", "entity_registry"),
            ("v_alias_map", "alias_map"),
            ("v_entity_registry_summary", "entity_registry_summary"),
            ("v_entity_alias_conflicts", "alias_map"),
            ("v_evidence_decision_matrix", "evidence_decision_matrix"),
            ("v_evidence_decision_actionable", "evidence_decision_matrix"),
            ("v_evidence_decision_watchlist", "evidence_decision_matrix"),
            ("v_evidence_decision_summary", "evidence_decision_summary"),
            ("v_tag_library", "tag_library"),
            ("v_tag_filter_presets", "tag_filter_presets"),
            ("v_fact_expense_allocations", "production_expense_allocations"),
            ("v_fact_transactions_audit", "classified_transactions_audit"),
            ("v_fact_pending_large_review", "manual_review_queue"),
            ("v_mart_daily_cashflow", "summary_by_month"),
            ("v_mart_counterparty_monthly", "production_expense_allocations"),
            ("v_mart_risk_monthly", "production_expense_allocations"),
        ]:
            conn.execute(f"create view {view} as select * from {table}")
        conn.commit()


class ValidateOutputsTests(unittest.TestCase):
    def test_valid_outputs_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            make_output(root)
            db = Path(tmp) / "ledger.sqlite"
            make_db(db)
            results = validate_all(root, db, require_ledger=True)
            self.assertFalse(has_failures(results), [item.to_dict() for item in results if item.status == "fail"])

    def test_missing_pdf_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            make_output(root)
            (root / "reports" / "monthly_report.pdf").unlink()
            db = Path(tmp) / "ledger.sqlite"
            make_db(db)
            results = validate_all(root, db, require_ledger=True)
            self.assertTrue(has_failures(results))
            self.assertIn("pdf:monthly_report.pdf", {item.name for item in results if item.status == "fail"})


if __name__ == "__main__":
    unittest.main()
