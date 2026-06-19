from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from econ_bleed_analyzer.reports import write_report_pdf
from econ_bleed_analyzer.validate_outputs import validate_all


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "finance_ledger_20220605_20260603"
LEDGER_DB = ROOT / "data" / "finance_ledger" / "finance_ledger.sqlite"
OUTPUT_REL = Path("outputs") / "finance_ledger_20220605_20260603"
LEDGER_REL = Path("data") / "finance_ledger" / "finance_ledger.sqlite"
PACKAGE_DIR = ROOT / "outputs" / "handoff" / "finance_ledger_handoff_20260615"
ZIP_PATH = ROOT / "outputs" / "handoff" / "finance_ledger_handoff_20260615.zip"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sqlite_count(conn: sqlite3.Connection, name: str) -> int | None:
    try:
        return int(conn.execute(f"select count(*) from {name}").fetchone()[0])
    except sqlite3.Error:
        return None


def latest_zip() -> str:
    zips = sorted((ROOT / "outputs" / "delivery").glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(zips[0].relative_to(ROOT)) if zips else "未发现正式交付 ZIP"


def validation_summary() -> dict[str, Any]:
    rows = validate_all(OUTPUT_REL, LEDGER_REL, require_ledger=True)
    counts = {"ok": 0, "warn": 0, "fail": 0}
    warnings: list[dict[str, str]] = []
    for row in rows:
        status = row.status
        counts[status] = counts.get(status, 0) + 1
        if status != "ok":
            warnings.append({"name": row.name, "status": row.status, "detail": row.detail})
    return {"counts": counts, "non_ok": warnings, "total": len(rows)}


def collect_evidence() -> dict[str, Any]:
    audit = OUTPUT_DIR / "audit"
    with sqlite3.connect(LEDGER_DB) as conn:
        db_counts = {
            name: sqlite_count(conn, name)
            for name in [
                "classified_transactions_audit",
                "production_expense_allocations",
                "manual_review_queue",
                "data_trust_transactions",
                "reconciliation_checks",
                "entity_registry",
                "alias_map",
                "evidence_decision_matrix",
                "tag_library",
                "tag_filter_presets",
                "weixin_intake_items",
            ]
        }
        object_counts = {
            "tables": conn.execute("select count(*) from sqlite_master where type='table'").fetchone()[0],
            "views": conn.execute("select count(*) from sqlite_master where type='view'").fetchone()[0],
        }

    browser = read_json(audit / "browser_visual_acceptance.json")
    goal = read_json(audit / "goal_completion_audit.json")
    app = read_json(audit / "app_launchers.json")
    reports = read_json(audit / "report_manifest.json")
    run = read_json(audit / "run_manifest.json")

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(ROOT),
        "output_dir": str(OUTPUT_DIR.relative_to(ROOT)),
        "ledger_db": str(LEDGER_DB.relative_to(ROOT)),
        "latest_delivery_zip": latest_zip(),
        "validation": validation_summary(),
        "database": {"counts": db_counts, "object_counts": object_counts},
        "audits": {
            "browser_visual_acceptance": {
                "generated_at": browser.get("generated_at"),
                "checked_count": browser.get("checked_count"),
                "failure_count": browser.get("failure_count"),
                "base_url": browser.get("base_url"),
            },
            "goal_completion": goal.get("summary", {}),
            "app_launchers": {
                "generated_at": app.get("generated_at"),
                "launcher_type": app.get("launcher_type"),
                "target_url": app.get("target_url"),
                "install_locations": app.get("install_locations", []),
            },
            "report_manifest": {
                "generated_at": reports.get("generated_at"),
                "report_count": len(reports.get("reports", [])),
            },
            "run_manifest": {
                "generated_at": run.get("generated_at"),
                "transaction_count": run.get("transaction_count"),
                "source_files": run.get("source_files"),
            },
        },
    }


FEATURES = [
    ("本地 App 入口", "已实现", "Desktop / Downloads / Applications 三处 .app", "普通使用者", "audit/app_launchers.json", "可双击打开本地 127.0.0.1 首页", "本地未签名 app，跨机器分发需重新安装/签名"),
    ("首页与全局导航", "已实现", "index.html", "普通使用者/新开发者", "reports/index.html", "所有模块可回主菜单", "静态站点，无多用户账户体系"),
    ("运营控制台", "已实现", "operations_center.html", "维护者", "reports/operations_center.html", "流程、报告、命令入口集中展示", "命令仍需本地运行"),
    ("Dashboard", "已实现", "dashboard.html", "普通使用者", "reports/dashboard.html", "现金流、分类、趋势可视化", "图表为静态生成，不是在线 BI"),
    ("交易明细探索", "已实现", "transaction_explorer.html", "普通使用者/复核者", "reports/transaction_explorer.html", "支持模糊搜索、筛选反馈、明细折叠", "超大数据量时页面体积较大"),
    ("消费行为分析", "已实现", "behavior_analysis.html", "普通使用者", "reports/behavior_analysis.html", "标签组合、图形切换、行为风险分析", "标签解释仍需持续由用户校准"),
    ("标签库编辑", "已实现", "tag_library.html + SQLite", "普通使用者/维护者", "tag_library / tag_filter_presets", "自定义标签和筛选组合可持久化", "需避免标签过度膨胀"),
    ("人工复核队列", "已实现", "review_workbench.html", "复核者", "manual_review_queue", "大额/歧义交易下拉选择并隔离生产统计", "待复核确认后才应回灌生产报表"),
    ("周期 PDF 报告", "已实现", "weekly/monthly/quarterly/half/year/annual PDF", "普通使用者/审计者", "report_manifest.json", "支持周/月/季/半年/年和账期年", "报告质量取决于分类与复核输入"),
    ("分类规则与经济放血机制", "已实现", "classifier.py / reports.py", "维护者/ChatGPT 审核", "classification_rulebook_report.pdf", "主类、子类、百分比口径和趋势公式固定", "规则需随真实使用继续版本化"),
    ("数据可信层", "已实现", "data_trust_transactions", "新开发者/下游系统", "data_trust_audit_report.pdf", "每笔交易有可信状态", "不替代人工判断"),
    ("对账层", "已实现", "reconciliation_checks", "新开发者/审计者", "reconciliation_audit_report.pdf", "来源、生产分摊、月度汇总一致性检查", "异常时必须 fail-closed"),
    ("实体注册与别名", "已实现", "entity_registry / alias_map", "下游系统", "entity_registry_report.pdf", "统一交易对方、类别、标签实体", "别名规则还可接入人工别名治理"),
    ("证据决策矩阵", "已实现", "evidence_decision_matrix", "ChatGPT 审核/下游系统", "evidence_decision_matrix_report.pdf", "FACT/INFERENCE/OBSERVATION/OPINION 与决策等级", "矩阵体积较大，外发包只给摘要和索引"),
    ("数据接入与回测入口", "已实现", "data_access_hub.html", "PFIOS/ResearchBus/新开发者", "docs/finance_ledger_data_contract.md", "只读视图和 API 命令明确", "本系统不主导回测/行研 schema"),
    ("自定义问题查询控制台", "已实现", "index.html", "普通使用者", "question_answer_index.json", "可按本地证据回答常见问题", "不是通用大模型对话"),
    ("微信接入契约", "部分实现", "docs/weixin_ingestion_contract.md / scripts/weixin_alipay_fund_ingest.py", "跨系统维护者", "docs/weixin_ingestion_contract.md", "定义候选入箱和复用微信 API 边界", "当前 SQLite 未发现 weixin_intake_items 表"),
    ("正式交付打包", "已实现", "scripts/package_delivery.py / outputs/delivery", "维护者", "outputs/delivery/*.zip", "已有正式 ZIP", "本次审核包不重复包含原始账单数据"),
]


TASKS = [
    ("1", "账单来源归档", "已完成", "四年支付宝源文件已入 sources/source_archives", "后续每周新增源文件后再运行 weekly_update"),
    ("2", "导入与清洗", "已完成", "classified_transactions_audit 8808 笔", "保留原始来源 hash 和导入审计"),
    ("3", "分类与分摊", "已完成", "production_expense_allocations 5414 行", "大额/歧义项不得静默进入生产统计"),
    ("4", "人工复核", "进行中", "manual_review_queue 92 行", "用户确认后回灌并重建报告"),
    ("5", "周期统计", "已完成", "周/月/季/半年/年/账期年报告", "趋势公式固定，需持续防回归"),
    ("6", "Dashboard 与 UI", "已完成", "首页、仪表盘、明细、行为、标签、复核、验收、数据接入", "继续优化要围绕使用路径，不做低价值扩张"),
    ("7", "数据可信/对账/证据层", "已完成", "Data Trust、Reconciliation、Entity、Evidence Matrix", "作为只读审计层供下游使用"),
    ("8", "本地 App 入口", "已完成", "三处 macOS .app 与图标", "如点击异常优先查 launcher 日志和端口"),
    ("9", "输出验证", "已完成", "validate_outputs 全 OK", "当前 goal audit 仍显示 1 gap"),
    ("10", "最终验收关闭", "未完成", "当前文件态 goal_complete=false, 88.89%", "需复查用户验收文件或重跑 final audit"),
]


def write_csv(path: Path, header: list[str], rows: list[tuple[str, ...]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def source_table_md() -> str:
    rows = [
        ("HANDOFF.md", "项目连续交接记录", "高", "高", "人工维护 + 当前文件", "可能滞后于最新审计文件"),
        ("AGENTS.md", "项目执行边界和标准命令", "高", "高", "项目规范", "不代表当前验收结果"),
        ("data/finance_ledger/finance_ledger.sqlite", "底层 SQLite 账本和只读视图", "高", "高", "本地数据库", "含敏感交易数据，本包不复制"),
        ("outputs/finance_ledger_20220605_20260603/audit/*.json", "机器审计与验收状态", "高", "高", "机器生成审计", "可能需要按最新 UI 重新刷新"),
        ("outputs/finance_ledger_20220605_20260603/reports/*.pdf", "正式报告", "高", "高", "PDF 产物", "质量依赖分类和复核输入"),
        ("scripts/*.py / src/econ_bleed_analyzer/*.py", "可重复运行工程实现", "高", "高", "源码", "外部评审需进入本地仓库查看"),
        ("tests/*.py", "回归测试", "高", "高", "自动化测试", "不覆盖所有人工体验"),
        ("outputs/delivery/*.zip", "正式交付 ZIP", "中高", "中", "打包产物", "可能早于本次审核包"),
    ]
    lines = ["| 来源 | 用途 | 可信度 | 相关性 | 证据类型 | 不确定性 |", "|---|---|---:|---:|---|---|"]
    lines.extend(f"| `{a}` | {b} | {c} | {d} | {e} | {g} |" for a, b, c, d, e, g in rows)
    return "\n".join(lines)


def build_main_report(evidence: dict[str, Any]) -> str:
    counts = evidence["database"]["counts"]
    validation = evidence["validation"]["counts"]
    goal = evidence["audits"]["goal_completion"]
    browser = evidence["audits"]["browser_visual_acceptance"]
    app = evidence["audits"]["app_launchers"]
    report_count = evidence["audits"]["report_manifest"]["report_count"]
    return f"""# 本地记账分析系统开发进度与交接审核报告

生成时间：{evidence['generated_at']}

项目根目录：`{evidence['project_root']}`

## 1. 执行摘要

- FACT：当前系统是本地优先的记账分析系统，由静态 HTML UI、SQLite 账本、可选本机只读 HTTP API、PDF 报告和 macOS `.app` 启动入口组成，不是线上部署的 SaaS。
- FACT：当前账本审计交易 `{counts['classified_transactions_audit']}` 笔，生产分摊 `{counts['production_expense_allocations']}` 行，待复核队列 `{counts['manual_review_queue']}` 行。
- FACT：数据库当前包含 `{evidence['database']['object_counts']['tables']}` 张表和 `{evidence['database']['object_counts']['views']}` 个视图，覆盖数据可信、对账、实体、标签、证据决策和周期汇总。
- FACT：输出验证当前为 `{validation.get('ok', 0)}` ok / `{validation.get('warn', 0)}` warn / `{validation.get('fail', 0)}` fail。
- FACT：浏览器视觉验收最近记录为 `{browser.get('checked_count')}` checked / `{browser.get('failure_count')}` failures，生成时间 `{browser.get('generated_at')}`。
- OBSERVATION：当前 `goal_completion_audit.json` 显示 `goal_complete={goal.get('goal_complete')}`，完成度 `{goal.get('machine_verifiable_pct')}%`，仍有 `{goal.get('counts', {}).get('gap')}` 个 gap；这与历史 HANDOFF 中“全 A”记录存在漂移，下一轮应优先复核验收文件和最终审计。
- INFERENCE：系统已达到“可本地使用、可复核、可重复生成报告、可供下游只读读取”的工程基线，但还不应被描述为在线产品或无人值守真实资金系统。

## 2. 信息来源表

{source_table_md()}

## 3. 功能清单

详见 `feature_inventory.csv`。摘要如下：

| 模块 | 状态 | 入口/位置 | 主要用户 | 剩余风险 |
|---|---|---|---|---|
""" + "\n".join(
        f"| {module} | {status} | `{entry}` | {user} | {risk} |"
        for module, status, entry, user, _evidence, _validation, risk in FEATURES
    ) + f"""

## 4. 任务清单与步骤环节

详见 `task_checklist.csv`。当前最高优先级不是继续扩张 UI，而是关闭当前审计漂移：

1. 复查 `audit/user_acceptance_decisions.json` 与 `audit/goal_completion_audit.json`。
2. 如用户确认为全 A，重跑 `scripts/audit_goal_completion.py` 或完整 `scripts/finalize_delivery.py`。
3. 如仍有 gap，按 `goal_completion_audit_report.pdf` 指向的缺口修复。
4. 完成后重跑 `validate_outputs.py`、浏览器验收和 package_delivery。

## 5. 架构与数据流

```mermaid
flowchart LR
  A["用户账单源文件"] --> B["导入与清洗"]
  B --> C["分类规则与经济放血机制"]
  C --> D["人工复核隔离"]
  D --> E["生产分摊与周期汇总"]
  E --> F["PDF 报告与 Dashboard"]
  E --> G["只读 SQLite 视图 / 本地 API"]
  B --> H["Data Trust"]
  E --> I["Reconciliation"]
  C --> J["Entity / Alias"]
  H --> K["Evidence Decision Matrix"]
  I --> K
  J --> K
```

## 6. 可复用模块

- `src/econ_bleed_analyzer/classifier.py`：主类、子类、风险标签、特殊对手方规则。
- `src/econ_bleed_analyzer/ledger.py`：SQLite schema、表、视图、生产统计与只读数据集市。
- `src/econ_bleed_analyzer/reports.py`：HTML UI、PDF 报告、报告中心、导航和可视化。
- `src/econ_bleed_analyzer/data_trust.py`：逐笔可信状态。
- `src/econ_bleed_analyzer/reconciliation.py`：对账检查。
- `src/econ_bleed_analyzer/entity_registry.py`：实体注册与别名映射。
- `src/econ_bleed_analyzer/evidence_decision.py`：证据分类与决策等级。
- `scripts/weekly_update.py`：每周增量重建主入口。
- `scripts/validate_outputs.py`：输出和数据库验收。
- `scripts/finalize_delivery.py`：最终交付门禁与打包前检查。

## 7. 差距分析

- FACT：`weixin_intake_items` 表当前未在 SQLite 中发现；微信接入目前应视为“契约和脚本能力存在，但本库未落候选表”。
- FACT：当前审核包不复制原始 SQLite、CSV 源账单或交易明细，避免对外审核时泄露个人财务数据。
- OBSERVATION：`transaction_explorer.html` 和 `behavior_analysis.html` 文件体积较大，静态内嵌数据带来离线易用性，但会影响加载和外发体积。
- INFERENCE：下一阶段最有价值的工程工作是把验收漂移、复核回灌、数据接入契约和用户操作路径进一步稳定，而不是新增更多页面。

## 8. 改进方案

| 行动 | 预期价值 | 难度 | 风险 | 所需输入 | 验证方式 | 失效条件 |
|---|---:|---:|---|---|---|---|
| 关闭 goal audit 漂移 | 高 | 低 | 错误宣布完成 | 用户最终验收 JSON | `audit_goal_completion.py` + `validate_outputs.py` | 仍出现 gap |
| 完成 92 条待复核分类 | 高 | 中 | 错分真实支出 | 用户下拉复核结果 | 重建报告后 expense reconciliation | 复核证据不足 |
| 将微信候选入箱落表 | 中高 | 中 | 与其他系统重复建设 | 微信 API 输出契约 | `weixin_intake_items` 表 + 测试 | 上游 API 不稳定 |
| 减小静态明细页面体积 | 中 | 中 | 影响离线可用 | 用户是否接受分页/API | 页面性能和浏览器验收 | 用户仍要求纯离线全量 |
| 建立只读下游访问包 | 中高 | 中 | 泄露隐私 | 字段脱敏规则 | 数据契约测试 | 下游需要原始明细 |

## 9. 验收标准

- `PYTHONPATH=src python3 -m pytest tests -q` 通过。
- `PYTHONPATH=src python3 scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger --json` 无 fail。
- 浏览器视觉验收 `failure_count=0`，且验收文件晚于最新 HTML。
- `goal_completion_audit.json` 中 `goal_complete=true`。
- 待复核交易不进入生产统计，除非用户确认。
- 对外审核包不包含原始账单、SQLite 私密数据或可泄露真实交易明细的文件。

## 10. 下一步行动建议

默认推荐：先关闭 goal audit 漂移，再做复核回灌。理由是这是当前最小、最高 ROI、最能提升“外部可审核性”的动作。

"""


def write_text_files(evidence: dict[str, Any]) -> None:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    report_md = build_main_report(evidence)
    (PACKAGE_DIR / "finance_ledger_development_progress_report.md").write_text(report_md, encoding="utf-8")
    write_report_pdf(report_md, PACKAGE_DIR / "finance_ledger_development_progress_report.pdf")

    write_csv(
        PACKAGE_DIR / "feature_inventory.csv",
        ["module", "status", "entry", "primary_users", "evidence_path", "validation", "remaining_risk"],
        FEATURES,
    )
    write_csv(
        PACKAGE_DIR / "task_checklist.csv",
        ["step", "task", "status", "evidence", "next_action"],
        TASKS,
    )

    (PACKAGE_DIR / "system_evidence_index.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    (PACKAGE_DIR / "handoff_for_chatgpt.md").write_text(
        """# 给 ChatGPT / 外部审核者的审核说明

请基于本包文件进行审查，不要假设你可以访问用户原始账单。原始 SQLite 和账单明细因隐私未包含在本包中。

重点审核：

1. 当前系统是否符合“本地记账分析系统”的定位，而不是误判为线上 SaaS。
2. 功能清单是否覆盖账单导入、分类、人工复核、周期报告、Dashboard、标签库、行为分析、数据可信、对账和只读下游访问。
3. `goal_completion_audit` 当前仍有 1 个 gap 的原因，是否需要重跑最终验收。
4. 当前风险：隐私外发、待复核交易、微信候选入箱未落表、静态页面体积、下游系统边界。
5. 请把结论标为 FACT / INFERENCE / OBSERVATION / OPINION，并注明证据文件。
""",
        encoding="utf-8",
    )
    (PACKAGE_DIR / "developer_onboarding.md").write_text(
        """# 新开发者上手

## 运行定位

这是本地系统：静态 HTML + SQLite + 可选本机只读 API + macOS app launcher。不要默认部署到公网。

## 常用命令

```bash
PYTHONPATH=src python3 scripts/weekly_update.py \\
  --input data/finance_ledger/sources \\
  --ledger-db data/finance_ledger/finance_ledger.sqlite \\
  --output outputs/finance_ledger_20220605_20260603

PYTHONPATH=src python3 scripts/validate_outputs.py \\
  --output outputs/finance_ledger_20220605_20260603 \\
  --db data/finance_ledger/finance_ledger.sqlite \\
  --require-ledger

PYTHONPATH=src python3 -m pytest tests -q
```

## 开发边界

- 不执行支付、转账、交易或真实资金操作。
- 不把本地 HTTP 服务暴露到公网。
- 不静默修改分类规则、金额公式、复核决策或生产统计口径。
- 大额、歧义、高风险记录必须保留可复核状态。
""",
        encoding="utf-8",
    )
    (PACKAGE_DIR / "user_quick_start.md").write_text(
        """# 用户快速使用说明

1. 双击 `本地记账分析系统.app`，或打开 `http://127.0.0.1:8765/index.html`。
2. 先看首页和右侧“使用说明 / 术语”。
3. 看总览用 `Dashboard`。
4. 查单笔交易用 `交易明细探索`，支持模糊搜索和折叠。
5. 看消费行为用 `消费行为分析`，可按标签组合和图表类型筛选。
6. 调整标签用 `标签库`。
7. 处理大额/歧义交易用 `人工复核工作台`。
8. 查看 PDF 用首页报告中心，默认新标签页打开。
""",
        encoding="utf-8",
    )
    (PACKAGE_DIR / "review_questions_for_chatgpt.md").write_text(
        """# 建议让 ChatGPT 审核的问题

1. 这个系统当前最像什么：本地账本分析工具、BI dashboard、还是线上产品？证据是什么？
2. 目前功能是否足以支撑每周账单更新、人工复核和周期 PDF 生成？
3. 分类体系是否足够简洁？是否存在主类、子类、风险标签职责混乱？
4. Data Trust、Reconciliation、Entity Registry、Evidence Decision 是否构成可信审计链？
5. 当前最大工程风险是什么？请按严重度排序。
6. 哪些功能应该暂停，哪些应该优先做？
7. 如果交给新开发者，最小安全修改路径是什么？
""",
        encoding="utf-8",
    )
    (PACKAGE_DIR / "README.md").write_text(
        f"""# Finance Ledger Handoff Package

这是用于发给 ChatGPT、外部审核者、新开发者和新使用者的交接审核包。

主报告：

- `finance_ledger_development_progress_report.pdf`
- `finance_ledger_development_progress_report.md`

辅助文件：

- `feature_inventory.csv`
- `task_checklist.csv`
- `system_evidence_index.json`
- `handoff_for_chatgpt.md`
- `developer_onboarding.md`
- `user_quick_start.md`
- `review_questions_for_chatgpt.md`

隐私说明：本包不包含原始账单、SQLite 数据库或交易明细，只包含摘要、证据索引和工程交接材料。

最新正式交付 ZIP 参考：`{evidence['latest_delivery_zip']}`
""",
        encoding="utf-8",
    )


def write_zip() -> None:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(PACKAGE_DIR.parent))


def main() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    evidence = collect_evidence()
    write_text_files(evidence)
    write_zip()
    print(json.dumps({"package_dir": str(PACKAGE_DIR), "zip_path": str(ZIP_PATH), "files": len(list(PACKAGE_DIR.rglob('*')))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
