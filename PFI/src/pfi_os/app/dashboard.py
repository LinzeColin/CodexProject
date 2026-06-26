from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class QuickAction:
    title_cn: str
    title_en: str
    description_cn: str
    description_en: str
    target_cn: str
    target_en: str
    target_key: str


@dataclass(frozen=True)
class WorkflowStep:
    step_cn: str
    step_en: str
    detail_cn: str
    detail_en: str


@dataclass(frozen=True)
class DailyRunbookItem:
    phase_cn: str
    phase_en: str
    action_cn: str
    action_en: str
    pass_rule_cn: str
    pass_rule_en: str


@dataclass(frozen=True)
class ResultJudgement:
    status: str
    title_cn: str
    title_en: str
    detail_cn: str
    detail_en: str


@dataclass(frozen=True)
class UsageGuideSection:
    title: str
    target_key: str
    purpose: str
    best_for: str
    steps: tuple[str, ...]
    checks: tuple[str, ...]
    outputs: tuple[str, ...]
    risks: tuple[str, ...]


def workspace_shell_summary(
    workspace_payload: dict,
    registry: pd.DataFrame | None = None,
    state: pd.DataFrame | None = None,
) -> dict:
    systems = [item for item in workspace_payload.get("systems", []) if isinstance(item, dict)]
    registry_map = _row_map(registry, "system_name")
    state_map = _row_map(state, "system_name")
    rows = []
    for item in systems:
        system_id = str(item.get("system_id", ""))
        registry_row = registry_map.get(system_id, {})
        state_row = state_map.get(system_id, {})
        rows.append(
            {
                "系统": system_id,
                "名称": str(item.get("display_name", "")),
                "Adapter": str(item.get("adapter_status", "")),
                "ResearchBus": str(registry_row.get("status") or state_row.get("status") or "NotRegistered"),
                "迁移阶段": str(item.get("migration_phase", "")),
                "样本文件": int(item.get("sample_file_count", 0) or 0),
                "源码根": str(item.get("source_root", "")),
                "下一步": _first_text(item.get("next_actions", [])),
            }
        )
    registered_count = sum(1 for row in rows if row["ResearchBus"] != "NotRegistered")
    ready_count = sum(1 for row in rows if row["Adapter"] == "Ready" and row["ResearchBus"] == "Ready")
    review_count = len(rows) - ready_count
    return {
        "schema": "WorkspaceShellSummaryV1",
        "status": "Ready" if rows and review_count == 0 else "Review",
        "cards": [
            {"label": "Workspace 系统", "value": len(rows), "detail": "canonical manifests"},
            {"label": "Adapter Ready", "value": int(workspace_payload.get("ready_count", ready_count) or 0), "detail": "compact summaries"},
            {"label": "ResearchBus Ready", "value": registered_count, "detail": "registered canonical systems"},
            {"label": "需复核", "value": review_count, "detail": "adapter or bus state"},
        ],
        "rows": rows,
        "token_policy": "UI reads compact manifest summaries and ResearchBus state; it does not scan subsystem source trees.",
        "commands": [
            "scripts/syncWorkspaceSystemSummaries.sh --check --json",
            "scripts/orchestrateSystems.sh register --json",
            "scripts/syncResearchBus.sh --mode status --json",
        ],
    }


def vectorized_research_shell_summary(payload: dict | None) -> dict:
    if not payload or payload.get("schema") != "PFIOSVectorizedResearchBatchV1":
        return {
            "schema": "VectorizedResearchShellSummaryV1",
            "status": "Missing",
            "cards": [
                {"label": "Vectorized 状态", "value": "Missing", "detail": "latest summary not found"},
                {"label": "扫描运行", "value": "0/0", "detail": "scan runs / parameter runs"},
                {"label": "最佳 Sharpe", "value": "0.00", "detail": "best run"},
                {"label": "稳定性", "value": "Missing", "detail": "parameter stability"},
            ],
            "rows": [],
            "chart_rows": [],
            "token_policy": "UI reads only data/vectorized/VectorizedResearch_latest.json compact summary; it does not reload replay records or rerun scans.",
            "commands": ["scripts/vectorizedResearch.sh --symbol SPY --market US --interval 1d --param short_window=2,3 --param long_window=4,5"],
            "safety_policy": "Read-only vectorized summary display; no market refresh, broker calls, orders, or holdings mutation.",
        }
    summary_rows = [row for row in payload.get("summary_rows", []) if isinstance(row, dict)]
    best = payload.get("best_run", {}) if isinstance(payload.get("best_run", {}), dict) else {}
    stability = payload.get("stability", {}) if isinstance(payload.get("stability", {}), dict) else {}
    rows = [_vectorized_row(row) for row in summary_rows[:10]]
    chart_rows = [
        {
            "参数": row["参数"],
            "Sharpe": row["Sharpe"],
            "总收益%": row["总收益%"],
            "最大回撤%": row["最大回撤%"],
        }
        for row in rows
    ]
    return {
        "schema": "VectorizedResearchShellSummaryV1",
        "status": str(payload.get("status", "")) or "Missing",
        "cards": [
            {"label": "Vectorized 状态", "value": str(payload.get("status", "")), "detail": f"replay={payload.get('replay_status', '')}"},
            {"label": "扫描运行", "value": f"{int(payload.get('scan_run_count', 0) or 0)}/{int(payload.get('parameter_run_count', 0) or 0)}", "detail": "scan runs / parameter runs"},
            {"label": "最佳 Sharpe", "value": f"{_number(best.get('sharpe')):.2f}", "detail": str(best.get("run_id", ""))},
            {"label": "稳定性", "value": str(stability.get("stability_status", "")), "detail": f"coverage={_number(stability.get('parameter_coverage')):.2f}"},
        ],
        "rows": rows,
        "chart_rows": chart_rows,
        "token_policy": "UI reads only data/vectorized/VectorizedResearch_latest.json compact summary_rows; it does not reload EventReplay records or rerun parameter scans.",
        "commands": ["scripts/vectorizedResearch.sh --symbol SPY --market US --interval 1d --param short_window=2,3 --param long_window=4,5"],
        "safety_policy": str(payload.get("safety_boundary", "")) or "Read-only vectorized summary display; no market refresh, broker calls, orders, or holdings mutation.",
        "window": f"{payload.get('first_datetime', '')} -> {payload.get('last_datetime', '')}",
        "selected_symbol": str(payload.get("selected_symbol", "")),
        "strategy_id": str(payload.get("strategy_id", "")),
        "outputs": payload.get("outputs", {}),
    }


def macos_runtime_evidence_summary(payload: dict | None) -> dict:
    if not payload or payload.get("schema") != "PFIOSMacOSRuntimeAcceptanceV1":
        return {
            "schema": "MacOSRuntimeEvidenceSummaryV1",
            "status": "Missing",
            "cards": [
                {"label": "Runtime 证据", "value": "Missing", "detail": "latest JSON not found"},
                {"label": "检查通过", "value": "0/0", "detail": "pass / total checks"},
                {"label": "最近运行", "value": "Missing", "detail": "no generated_at"},
                {"label": "启动方式", "value": "Missing", "detail": "script or app"},
            ],
            "rows": [],
            "commands": [
                "scripts/macosRuntimeAcceptance.sh --summary-json",
                "scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI.app --summary-json",
            ],
            "token_policy": "UI reads only the sanitized Operational Store runtime evidence model derived from data/systemAudit/MacOSRuntimeAcceptance_latest.json; it does not start or stop services.",
            "safety_policy": "Read-only runtime evidence display; runtime acceptance remains Terminal-only and is not allowlisted in the UI.",
            "next_action": "Run runtime acceptance from Terminal after confirming no active workbench session is in use.",
        }
    summary = payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {}
    checks = [row for row in payload.get("checks", []) if isinstance(row, dict)]
    failed_rows = [_runtime_evidence_row(row) for row in checks if row.get("status") == "Fail"]
    status = str(payload.get("status") or "Missing")
    generated_at = str(payload.get("generated_at") or "")
    age = _runtime_age_label(generated_at)
    launch_method = str(payload.get("launch_method") or "Missing")
    pass_count = int(summary.get("pass", 0) or 0)
    fail_count = int(summary.get("fail", 0) or 0)
    total_count = int(summary.get("total", len(checks)) or 0)
    pre_ports = payload.get("pre_existing_healthy_ports", [])
    post_ports = payload.get("post_healthy_ports", [])
    return {
        "schema": "MacOSRuntimeEvidenceSummaryV1",
        "status": status,
        "cards": [
            {"label": "Runtime 证据", "value": status, "detail": f"started_by_acceptance={bool(payload.get('started_by_acceptance'))}"},
            {"label": "检查通过", "value": f"{pass_count}/{total_count}", "detail": f"fail={fail_count}"},
            {"label": "最近运行", "value": age, "detail": generated_at or "missing generated_at"},
            {"label": "启动方式", "value": launch_method, "detail": f"pre={_port_label(pre_ports)} post={_port_label(post_ports)}"},
        ],
        "rows": failed_rows,
        "commands": [
            "scripts/macosRuntimeAcceptance.sh --summary-json",
            "scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI.app --summary-json",
        ],
        "token_policy": "UI reads only the sanitized Operational Store runtime evidence model derived from data/systemAudit/MacOSRuntimeAcceptance_latest.json; it does not start or stop services.",
        "safety_policy": str(payload.get("safety_boundary", "")) or "Read-only runtime evidence display; no market refresh, broker calls, orders, or holdings mutation.",
        "heavy_smoke_policy": str(payload.get("heavy_smoke_policy", "")),
        "next_action": str(payload.get("next_action", "")) or "If missing or stale, run runtime acceptance from Terminal.",
    }


def macos_lifecycle_summary(
    *,
    is_running: bool,
    app_paths: tuple[str, ...] | None = None,
) -> dict:
    app_paths = app_paths or (
        "~/Desktop/PFI.app",
        "~/Downloads/PFI.app",
        "/Applications/PFI.app",
    )
    actions = [
        _lifecycle_action(
            "日常验收",
            "Daily Acceptance",
            "scripts/macosAcceptance.sh",
            True,
            "推荐默认入口：合并开发就绪和 GitHub-safe 公开验收摘要；不运行完整 smoke。",
            "Recommended default entry: combines dev readiness and GitHub-safe public acceptance summary; no full smoke.",
        ),
        _lifecycle_action(
            "状态检查",
            "Status Check",
            "scripts/statusPFI.sh",
            True,
            "只读检查当前 8501-8510 端口和本地 PFI 进程。",
            "Read-only port and local PFI process check.",
        ),
        _lifecycle_action(
            "开发检查",
            "Dev Ready Check",
            "scripts/devReadyCheck.sh",
            True,
            "日常开发默认 gate：检查入口脚本、语法、状态、缓存 dry-run 和 git 状态；不运行完整 smoke。",
            "Default daily development gate for entry scripts, syntax, status, cache dry-run, and git status; no full smoke.",
        ),
        _lifecycle_action(
            "启动工作台",
            "Start Workbench",
            "scripts/startPFI.sh",
            not is_running,
            "从终端或 PFI app 启动；当前页面内不自启动新服务，避免重复进程。",
            "Start from Terminal or PFI app; the running page does not start another service.",
            disabled_reason="服务已在运行" if is_running else "",
        ),
        _lifecycle_action(
            "停止服务",
            "Stop Service",
            "scripts/stopPFI.sh",
            is_running,
            "仅停止当前项目的 Streamlit 服务；不会触发交易、抓取或写入研究数据。",
            "Stops only this project's Streamlit service; no trading, scraping, or research writes.",
            disabled_reason="" if is_running else "服务未运行",
        ),
        _lifecycle_action(
            "清理缓存",
            "Clean Cache",
            "scripts/cleanCache.sh",
            not is_running,
            "清理 pycache、pytest cache 和 .DS_Store；服务运行时保持禁用。",
            "Cleans pycache, pytest cache, and .DS_Store; disabled while the service is running.",
            disabled_reason="先停止服务再清理缓存" if is_running else "",
        ),
        _lifecycle_action(
            "轻量验收",
            "Lite Acceptance",
            "scripts/macosAppAcceptanceLite.sh",
            True,
            "只读检查 App 入口、签名、project binding、launcher dry-run 和状态脚本；不运行完整 smoke。",
            "Read-only app-entry, signature, project binding, launcher dry-run, and status-script check; no full smoke.",
        ),
        _lifecycle_action(
            "生命周期验收",
            "Lifecycle Readiness",
            "scripts/macosLifecycleReadiness.sh",
            True,
            "只读检查启动、停止、heartbeat 自动关闭、缓存清理保护、UI allowlist 和 App 入口验收；不运行完整 smoke。",
            "Read-only start, stop, heartbeat shutdown, cache-clean guard, UI allowlist, and app-entry readiness; no full smoke.",
        ),
        _lifecycle_action(
            "运行时验收",
            "Runtime Acceptance",
            "scripts/macosRuntimeAcceptance.sh --summary-json",
            not is_running,
            "受控启动本地服务、验证 health、运行中缓存清理拒绝、停止服务并复核；必须在 Terminal 运行。",
            "Controlled local start, health, cache-guard, stop, and post-stop check; run from Terminal.",
            disabled_reason="服务已在运行，避免误停当前会话" if is_running else "",
        ),
        _lifecycle_action(
            "App 打开验收",
            "App Open Acceptance",
            "scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI.app --summary-json",
            not is_running,
            "真实打开 Downloads 的 PFI app，验证 health、缓存保护和停止闭环；可能打开默认浏览器，必须在 Terminal 运行。",
            "Opens the Downloads PFI app, then verifies health, cache guard, and stop loop; may open the default browser, run from Terminal.",
            disabled_reason="服务已在运行，避免误停当前会话" if is_running else "",
        ),
        _lifecycle_action(
            "最终验收",
            "Final Acceptance",
            "scripts/finalAcceptanceCheck.sh",
            True,
            "完整本地验收，耗时较长；建议在终端运行并保留输出。",
            "Full local acceptance; run from Terminal and keep the output.",
        ),
    ]
    return {
        "schema": "MacOSLifecycleSummaryV1",
        "status": "Running" if is_running else "Stopped",
        "cards": [
            {"label": "运行状态", "value": "Running" if is_running else "Stopped", "detail": "Streamlit local service"},
            {"label": "App 入口", "value": len(app_paths), "detail": "Desktop / Downloads / Applications"},
            {"label": "可执行动作", "value": sum(1 for item in actions if item["enabled"]), "detail": "safe lifecycle actions"},
            {"label": "需终端执行", "value": sum(1 for item in actions if item["ui_mode"] == "Terminal"), "detail": "long or start actions"},
        ],
        "app_paths": list(app_paths),
        "actions": actions,
        "safety_policy": "Lifecycle controls only manage the local PFI app process and caches; they do not refresh market data, place orders, or send broker instructions.",
    }


def _lifecycle_action(
    title_cn: str,
    title_en: str,
    command: str,
    enabled: bool,
    detail_cn: str,
    detail_en: str,
    *,
    disabled_reason: str = "",
) -> dict:
    ui_mode = (
        "UI"
        if command
        in {
            "scripts/statusPFI.sh",
            "scripts/stopPFI.sh",
            "scripts/macosAcceptance.sh",
            "scripts/devReadyCheck.sh",
            "scripts/macosAppAcceptanceLite.sh",
            "scripts/macosLifecycleReadiness.sh",
        }
        else "Terminal"
    )
    return {
        "动作": title_cn,
        "Action": title_en,
        "命令": command,
        "enabled": bool(enabled),
        "ui_mode": ui_mode,
        "禁用原因": disabled_reason,
        "说明": detail_cn,
        "Detail": detail_en,
    }


def _row_map(frame: pd.DataFrame | None, key: str) -> dict[str, dict]:
    if frame is None or frame.empty or key not in frame.columns:
        return {}
    return {str(row.get(key, "")): dict(row) for row in frame.to_dict("records")}


def _first_text(value) -> str:
    if isinstance(value, (list, tuple)) and value:
        return str(value[0])
    return ""


def _runtime_evidence_row(row: dict) -> dict:
    return {
        "target": str(row.get("target", "")),
        "check": str(row.get("check", "")),
        "status": str(row.get("status", "")),
        "evidence": _public_text(str(row.get("evidence", "")))[:240],
    }


def _runtime_age_label(value: str) -> str:
    if not value:
        return "Missing"
    try:
        generated = datetime.fromisoformat(value)
    except ValueError:
        return "Unknown"
    elapsed = datetime.now(generated.tzinfo) - generated
    days = max(elapsed.days, 0)
    if days == 0:
        return "Today"
    if days <= 7:
        return f"{days}d"
    return f"Stale {days}d"


def _port_label(value) -> str:
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value) or "-"
    return "-"


def _public_text(value: str) -> str:
    return value.replace("/Users/linzezhang/", "~/")


def _vectorized_row(row: dict) -> dict:
    params = []
    for key, value in row.items():
        if str(key).startswith("param_"):
            params.append(f"{str(key).replace('param_', '', 1)}={value}")
    return {
        "Run": str(row.get("run_id", "")),
        "策略": str(row.get("strategy_id", "")),
        "参数": ", ".join(params),
        "总收益%": round(_number(row.get("total_return")) * 100, 2),
        "Sharpe": round(_number(row.get("sharpe")), 2),
        "最大回撤%": round(_number(row.get("max_drawdown")) * 100, 2),
        "交易数": int(_number(row.get("trade_count"))),
        "成本": round(_number(row.get("cost_total")), 2),
    }


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def quick_actions() -> list[QuickAction]:
    return [
        QuickAction(
            "查看总控驾驶舱",
            "Executive Command Center",
            "先看 PFI 是否可继续研究：就绪检查、集成审计、业务子系统、最新报告和行动队列。",
            "Check whether PFI is ready for research: readiness, integration audit, business subsystems, latest report, and action queue.",
            "总控驾驶舱",
            "Executive Command Center",
            "command",
        ),
        QuickAction(
            "复核公司现金流",
            "Company CashFlow Command",
            "录入余额快照、收入、支出、应收和应付，按证据口径查看 runway 和现金流行动项。",
            "Record balance snapshots, inflow, outflow, receivable, and payable evidence, then review runway and cashflow actions.",
            "现金流",
            "Company CashFlow Command",
            "cashflow",
        ),
        QuickAction(
            "复核政策机会",
            "Policy Intelligence Radar",
            "登记政策来源、影响行业、机会类型和行动要求，按权威来源与证据状态决定是否进入机会队列。",
            "Record policy sources, affected sectors, opportunity types, and required actions, then gate promotion by authority and evidence.",
            "政策雷达",
            "Policy Intelligence Radar",
            "policy",
        ),
        QuickAction(
            "检查消费守卫",
            "Consumption Guard",
            "登记消费证据、冲动风险、固定成本和可投资现金流压力，防止非必要支出吞噬投资现金流。",
            "Record consumption evidence, impulse risk, fixed costs, and investable cashflow pressure before spending patterns damage capital discipline.",
            "消费守卫",
            "Consumption Guard",
            "consumption",
        ),
        QuickAction(
            "快速验证单个标的",
            "Validate One Symbol",
            "用样例数据或真实数据运行单标的回测，先看收益、回撤、交易和 Word 报告。",
            "Run a single-symbol backtest with sample or real data, then review return, drawdown, trades, and the Word report.",
            "单标的回测",
            "Single Backtest",
            "single",
        ),
        QuickAction(
            "观察市场情绪",
            "Market Sentiment",
            "查看大盘、自选对象和持仓对象的情绪分、RSI、趋势、波动和回撤。",
            "Review sentiment score, RSI, trend, volatility, and drawdown for market, watchlist, and holdings.",
            "情绪分析",
            "Sentiment Analysis",
            "sentiment",
        ),
        QuickAction(
            "查看大盘热点",
            "Market Hotspots",
            "用热力图、气泡图和时间切片观察大盘、行业、风格和避险资产的强弱扩散。",
            "Review market, sector, style, and defensive-asset strength with heatmap, bubble chart, and time slices.",
            "热点分析",
            "Market Hotspots",
            "hotspots",
        ),
        QuickAction(
            "训练技术盘感",
            "Technical Market Feel",
            "用 MA、RSI、MACD、Bollinger、ATR 和成交量练习读图，获得讲解、分析和研究结论。",
            "Train chart reading with MA, RSI, MACD, Bollinger, ATR, and volume, then review explanation and research conclusion.",
            "盘感训练",
            "Technical Market Feel",
            "market_feel",
        ),
        QuickAction(
            "同步当前持仓",
            "Sync Holdings",
            "读取行研、消费分析、支付宝账本和 PFI 导入文件，形成正式持仓簿。",
            "Read industry research, consumer analytics, Alipay ledger, and PFI import files into a canonical holdings book.",
            "持仓",
            "Holdings",
            "holdings",
        ),
        QuickAction(
            "查找历史报告",
            "Find Reports",
            "按类型、日期和关键词搜索 Word 报告、元数据、数据质量文件和实验记录。",
            "Search Word reports, metadata, data quality files, and experiment records by type, date, and keyword.",
            "报告中心",
            "Report Center",
            "reports",
        ),
        QuickAction(
            "运行大数据模拟",
            "Run Big Data Simulation",
            "调用独立验证系统生成百万、千万、亿级或十亿级分片测试记录，验证系统能否承接大规模数据任务。",
            "Create million-to-billion-row independent validation shard records through the shared research bus.",
            "大数据模拟",
            "Big Data Simulation",
            "big_data",
        ),
    ]


def command_center_next_actions(payload: dict | None = None) -> dict:
    payload = payload or {}
    queue = [item for item in payload.get("action_queue", []) if isinstance(item, dict)]
    status = str(payload.get("command_status") or "NeedsReview")
    p0_count = sum(1 for item in queue if str(item.get("priority")) == "P0")
    p1_count = sum(1 for item in queue if str(item.get("priority")) == "P1")
    latest_missing = any(str(item.get("source")) == "Report Evidence" for item in queue)
    rows: list[dict[str, str]] = []

    if p0_count:
        rows.append(
            _route_row(
                "P0",
                "先处理阻断项",
                "总控驾驶舱",
                "command",
                f"行动队列存在 {p0_count} 个 P0，先闭合阻断项再进入研究流程。",
                "行动队列",
            )
        )
    elif latest_missing:
        rows.append(
            _route_row(
                "P1",
                "补齐报告证据",
                "报告中心",
                "reports",
                "当前缺少可追溯 Word 研究报告，先补证据再使用结论。",
                "证据索引 / 验证任务",
            )
        )
    elif status != "ReadyForResearch" or p1_count:
        rows.append(
            _route_row(
                "P1",
                "复核总控状态",
                "总控驾驶舱",
                "command",
                "总控仍需复核，先处理行动队列和风险闸门。",
                "核心状态 / 风控闸门",
            )
        )
    else:
        rows.append(
            _route_row(
                "P2",
                "开始日常研究",
                "热点分析",
                "hotspots",
                "系统状态可继续研究，先用热点快速预检观察市场结构。",
                "热点快速预检",
            )
        )

    rows.extend(
        [
            _route_row(
                "P2",
                "热点快速预检",
                "热点分析",
                "hotspots",
                "适合先看对象规模、缓存状态和预计计算量，避免直接触发慢生成。",
                "热点快速预检",
            ),
            _route_row(
                "P2",
                "参数扫描预检",
                "参数扫描",
                "scan",
                "适合先看参数组合数、上限占用和网格错误，再决定是否运行回测。",
                "参数扫描预检",
            ),
            _route_row(
                "P2",
                "报告验证",
                "报告中心",
                "reports",
                "适合集中查看证据索引、验证任务、实验记录和历史 Word 报告。",
                "证据索引 / 验证任务",
            ),
            _route_row(
                "P2",
                "macOS 日常验收",
                "总控驾驶舱",
                "command",
                "准备交付或本机状态变化后，按命令运行轻量验收而不是完整 smoke。",
                "scripts/macosAcceptance.sh",
            ),
        ]
    )
    rows = _dedupe_route_rows(rows)[:5]
    router_status = "Blocked" if p0_count else "NeedsReview" if p1_count or status != "ReadyForResearch" else "Ready"
    return {
        "schema": "PFIOSCommandCenterActionRouterV1",
        "status": router_status,
        "cards": [
            {"label": "推荐入口", "value": rows[0]["入口"] if rows else "-", "detail": rows[0]["建议"] if rows else ""},
            {"label": "P0", "value": p0_count, "detail": "blocking action count"},
            {"label": "P1", "value": p1_count, "detail": "review action count"},
            {"label": "路由数", "value": len(rows), "detail": "deduped next actions"},
        ],
        "rows": rows,
        "token_policy": "Action Router reads only the compact command-center payload and static route metadata; it does not scan reports, load market data, run backtests, or call lifecycle scripts.",
        "safety_boundary": "Navigation guidance only; no browser automation, market refresh, broker calls, orders, payments, holdings mutation, or cache deletion.",
    }


def _route_row(priority: str, title: str, target: str, target_key: str, reason: str, checkpoint: str) -> dict[str, str]:
    return {
        "优先级": priority,
        "建议": title,
        "入口": target,
        "view": target_key,
        "链接": f"?view={target_key}",
        "先看检查点": checkpoint,
        "原因": reason,
    }


def _dedupe_route_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    for row in rows:
        key = (row.get("建议", ""), row.get("view", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def usage_guide_sections() -> list[UsageGuideSection]:
    return [
        UsageGuideSection(
            title="总控驾驶舱",
            target_key="command",
            purpose="作为 PFI 日常入口，集中判断当前系统能否继续研究，哪些证据缺失，哪些事项必须先处理。",
            best_for="每天第一次打开系统、准备生成报告、准备使用回测结论前，先做一次总控复核。",
            steps=(
                "先看总控状态。可继续研究表示核心证据闭合；需要复核表示存在缺失证据；阻断表示不应继续使用下游结论。",
                "查看核心状态表，确认 Daily Readiness、Integration Audit、Risk Gates、业务子系统和 Latest Report 是否通过。",
                "查看行动队列，优先处理 P0，再处理 P1，P2 通常是价值量化或长期完善事项。",
                "查看证据来源，确认 Daily Readiness、Integration Audit、Data Trust、业务子系统和最新报告是否都有实际文件路径。",
                "查看风控闸门，确认 DataTrust、IntegrationAudit、NoLiveTradingBoundary、ReportEvidence 和 LatestWordReport 是否闭合。",
                "需要留档时点击生成总控报告，系统会输出 JSON、Markdown 和 PDF，并保存 latest 版本。",
            ),
            checks=(
                "总控状态是否为可继续研究；如果不是，先不要把研究结论用于交易前参考。",
                "行动队列是否存在 P0；P0 必须优先处理。",
                "证据来源是否缺失；缺失时说明结论不可追溯。",
            ),
            outputs=(
                "页面总览：总控状态、待处理事项、子系统复核、证据来源和最新报告。",
                "正式产物：`data/commandCenter/PFICommandCenter_DDMMYYYY.json/md/pdf`。",
                "最新指针：`data/commandCenter/PFICommandCenter_latest.json/md/pdf`。",
            ),
            risks=(
                "总控驾驶舱是证据聚合器，不证明策略盈利能力。",
                "如果底层审计文件过期，状态只能代表本地最近一次证据，不代表实时市场状态。",
                "该页面不刷新行情、不启动 OpenD、不连接实盘、不生成下单指令。",
            ),
        ),
        UsageGuideSection(
            title="现金流",
            target_key="cashflow",
            purpose="把公司经营现金余额、收入、支出、应收和应付整理成可复核证据，形成 runway、净现金流和行动队列。",
            best_for="每周经营复盘、付款前检查、订阅/固定支出控制、收入到账复核和判断短期现金安全边界。",
            steps=(
                "先看现金流状态、最新余额、近 30 天净现金流、Runway 天数和待复核数量。",
                "如果状态是 MissingBalance，先录入一条 BalanceSnapshot，并附上银行截图、账本或其他可复核证据。",
                "录入收入时选择 Inflow，录入支出时选择 Outflow；尚未到账的收入用 Receivable，尚未支付的支出用 Payable。",
                "为每条记录选择分类，例如 SalesRevenue、Tax、Salary、Vendor、Software 或 Marketing。",
                "填写证据链接或本地证据路径；没有证据的记录即使标记 Reviewed，也不会进入现金流汇总。",
                "保持 PendingReview 直到金额、日期、方向、分类和证据都确认，再升级为 Reviewed。",
                "点击生成现金流快照，输出 JSON、CSV、Markdown 和 PDF，供后续总控和经营复盘引用。",
            ),
            checks=(
                "最新余额是否来自 Reviewed + evidence 的 BalanceSnapshot。",
                "近 30 天净现金流是否为负；如果为负，优先检查固定成本和收入到账。",
                "Runway 是否低于 30 天；低于 14 天应视为经营现金 P0 风险。",
                "PendingReview 和 Reviewed 但缺证据的记录是否仍未进入汇总。",
            ),
            outputs=(
                "现金流台账：private Operational Store `company_cashflow` reviewed-input ledger。",
                "正式快照：`$PFI_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_DDMMYYYY.json/csv/md/pdf`。",
                "最新指针：`$PFI_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_latest.json/csv/md/pdf`。",
                "页面输出：状态指标、行动队列、分类汇总和现金流台账。",
            ),
            risks=(
                "本页不连接银行、支付、税务、工资或会计系统；所有金额都来自人工录入。",
                "Receivable 和 Payable 只是经营预期，不是已到账或已支付现金。",
                "Runway 是按近期支出速度估算的安全边界，不是融资、付款或投资建议。",
            ),
        ),
        UsageGuideSection(
            title="政策雷达",
            target_key="policy",
            purpose="把政策来源、影响行业、机会类型、权威证据、影响评分和下一步行动整理成可复核机会台账。",
            best_for="政策报告、政府公告、监管变化、产业支持、税务优惠、合规风险和项目申报机会进入 PFI 前的第一层证据整理。",
            steps=(
                "先看政策状态、机会数量、Actionable、Watch 和缺证据数量，判断当前政策机会是否可进入人工复核。",
                "录入政策标题、来源名称、来源类型和发布日期；来源类型优先选择 Official、Regulator、Government 或 Exchange。",
                "填写 source_url 或 evidence_path；没有来源证据的机会只能停留在 NeedsEvidence。",
                "填写地区、政策层级、机会类型、影响行业和影响对象，便于后续映射到标的、项目或验证任务。",
                "写清影响摘要和下一步行动，例如核验资格、找原文、拆验证任务或跟踪截止日期。",
                "给出权威分、相关分、紧急分和可执行分；系统会计算影响评分用于排序。",
                "确认来源权威和证据后再把复核状态设为 Reviewed；点击生成政策雷达快照保存正式产物。",
            ),
            checks=(
                "Actionable 是否同时满足 Reviewed、权威来源类型、source_url/evidence_path 和足够影响评分。",
                "News、Research 或 Manual 来源是否已回溯到官方、监管、政府或交易所来源。",
                "影响行业和影响对象是否具体到可验证项目、标的、产业链或业务动作。",
                "下一步行动是否仍是人工复核、验证或跟踪，而不是自动交易、付款或申报。",
            ),
            outputs=(
                "政策机会台账：private Operational Store `policy_radar` reviewed-input ledger。",
                "正式快照：`$PFI_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_DDMMYYYY.json/csv/md/pdf`。",
                "最新指针：`$PFI_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_latest.json/csv/md/pdf`。",
                "页面输出：政策状态、行动队列、行业暴露和政策机会表。",
            ),
            risks=(
                "本页不自动抓取实时政策，不证明政策覆盖完整。",
                "影响评分只是优先级，不是补贴可得、合规意见、项目通过率或投资收益预测。",
                "所有外部动作，包括申报、付款、交易和法律文件提交，都必须人工处理。",
            ),
        ),
        UsageGuideSection(
            title="消费守卫",
            target_key="consumption",
            purpose="把消费事件、账单证据、冲动风险、固定成本和可投资现金流压力整理成可复核台账，减少非必要支出对投资纪律的侵蚀。",
            best_for="每周消费复盘、订阅清理、冲动消费复盘、投资现金流压力检查和账单证据整理。",
            steps=(
                "先输入月可投资现金流预算；如果还没有明确预算，可以留 0，系统会显示压力缺预算。",
                "查看守卫状态、计入支出、冲动支出、固定成本和现金流压力，判断消费是否正在挤压投资现金流。",
                "录入消费事件时填写日期、事件类型、分类、金额、商户、支付方式和是否计划内。",
                "用必要性、冲动分和后悔分记录行为质量；系统会生成风险分和风险等级。",
                "填写账单、截图、导出 CSV 或可复核说明；没有证据的 Reviewed 记录不会进入汇总。",
                "保持 PendingReview 直到金额、证据和风险评分都确认，再升级为 Reviewed。",
                "点击生成消费守卫快照，输出 JSON、CSV、Markdown 和 PDF，供后续总控和复盘引用。",
            ),
            checks=(
                "计入支出是否只来自 Reviewed + evidence 的记录。",
                "高冲动消费是否集中在某类商户、时间段或情绪场景。",
                "固定成本是否存在长期不用的订阅或重复支出。",
                "非必要和冲动消费是否超过月可投资预算的 60%。",
            ),
            outputs=(
                "消费事件台账：private Operational Store `consumption_guard` reviewed-input ledger。",
                "正式快照：`$PFI_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_DDMMYYYY.json/csv/md/pdf`。",
                "最新指针：`$PFI_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_latest.json/csv/md/pdf`。",
                "页面输出：守卫状态、行动队列、分类汇总和消费事件表。",
            ),
            risks=(
                "本页不连接支付宝、银行、工资、税务、券商或支付系统；所有金额都来自人工录入。",
                "冲动风险评分是行为复盘工具，不是医学、心理、投资或财务诊断。",
                "页面只提供消费复盘和行动队列，不会执行付款、转账、退款、冻结账户或投资操作。",
            ),
        ),
        UsageGuideSection(
            title="单标的回测",
            target_key="single",
            purpose="用于研究一个股票、ETF 或指数在指定时间段内，某个策略相对买入持有是否有优势。",
            best_for="日常研究的第一入口；适合先验证一个标的、一个策略、一个时间周期。",
            steps=(
                "选择数据源。首次使用建议用 Sample；研究真实标的时优先用 Moomoo、AKShare、Yahoo Finance 等真实数据源。",
                "选择市场、输入标的并点击联网搜索；搜索不到时不要运行回测，先确认代码格式或到数据中心检查。",
                "选择周期和日期。日常研究先用 1d，短线研究再切换到 1min、5min、15min 等分钟级周期。",
                "选择运行模式。单策略回测用于看一个策略；双策略对比用于在同一数据和成本条件下比较两个策略。",
                "选择策略和参数。先跑默认参数，再逐个调整，避免一次改太多导致无法判断原因。",
                "设置初始资金、佣金率、滑点 bps、冲击成本 bps。成本不确定时宁可保守设置高一点。",
                "点击运行后先看目标走势、策略收益率、相对收益，再看核心指标、诊断、交易表和 Word 报告。",
                "如果报告、图表、交易表或数据质量提示异常，先不要把结果用于交易参考。",
            ),
            checks=(
                "总收益率和年化收益率是否同时优于买入持有。",
                "最大回撤是否可接受，且是否小于买入持有最大回撤。",
                "Sharpe 是否改善；如果收益高但 Sharpe 很差，说明波动代价可能过高。",
                "交易次数、买入次数、卖出次数是否合理，是否过度交易。",
                "交易摩擦占比是否过高；成本翻倍后三种指标是否仍能接受。",
                "Bootstrap 模拟是否显示结果过度依赖少数路径。",
            ),
            outputs=(
                "页面结果：走势图、收益率曲线、策略诊断、Bootstrap 鲁棒性、交易/持仓/信号表。",
                "Word 研究报告：默认保存到当前用户 `~/Downloads/量化回测分析/日期目录`，也可用报告根目录配置覆盖。",
                "数据质量报告：记录数据源、标的、周期、缺失值和异常。",
                "运行元数据：用于报告中心复盘历史实验。",
            ),
            risks=(
                "标的代码错误会导致研究对象不一致；必须确认搜索结果名称和代码。",
                "短周期数据更容易受数据源限制、滑点和噪声影响。",
                "策略收益如果只来自极少数交易，稳定性不足，需要参数扫描或更长区间验证。",
                "回测结果只作为实盘参考，不代表未来收益，也不连接实盘下单。",
            ),
        ),
        UsageGuideSection(
            title="情绪分析",
            target_key="sentiment",
            purpose="用于观察大盘、自选对象和持仓对象的短期情绪状态，辅助判断研究环境是否偏热、偏冷或中性。",
            best_for="日常开盘前、盘中或收盘后快速检查市场风险温度，不作为独立交易信号。",
            steps=(
                "选择数据源。首次检查可用 Sample；真实研究优先用 Moomoo、Yahoo Finance 或 AKShare。",
                "选择市场，US、CN、HK 会加载不同默认观察对象。",
                "选择分析范围：大盘默认用于宏观情绪，自选对象用于临时股票池，持仓对象用于读取持仓簿。",
                "设置开始日期和结束日期。情绪分析至少需要 30 个交易日，建议保留一年左右样本。",
                "自选对象模式下输入多个代码，用逗号、空格或换行分隔。",
                "点击刷新情绪分析，先看平均情绪分、偏热数量、偏冷数量和最新日期。",
                "查看情绪卡片，重点读 1 日涨跌、20 日涨跌、RSI、60 日最大回撤和研究解读。",
                "打开指标明细，检查失败对象和数据点数量，避免误用数据不足的对象。",
            ),
            checks=(
                "数据源是否真实可用，失败对象是否被列入错误明细。",
                "RSI 是否高于 70 或低于 30，是否存在短期拥挤或低迷。",
                "情绪分是否与 20 日趋势、回撤和波动相互印证。",
                "情绪判断是否只作为研究观察，而不是直接形成买卖动作。",
            ),
            outputs=(
                "情绪观察卡片。",
                "情绪分对比图。",
                "指标明细表和失败对象表。",
            ),
            risks=(
                "情绪分是技术状态摘要，不等于涨跌预测。",
                "VIX、黄金、债券等对象的解释方向不同，必须结合角色和研究场景。",
                "真实数据源不可用时，页面只能显示失败原因或样例数据。",
            ),
        ),
        UsageGuideSection(
            title="热点分析",
            target_key="hotspots",
            purpose="用热力图、气泡图和时间切片观察大盘、行业、风格、避险资产和持仓对象的强弱扩散。",
            best_for="盘前、盘中或收盘后快速判断市场强弱是否集中、扩散、分化或降温。",
            steps=(
                "选择数据源。真实研究优先用 Moomoo、Yahoo Finance 或 AKShare；Sample 只用于功能演示。",
                "选择市场和时间粒度。60min 用于小时级热点观察，1d 用于日线热点观察。",
                "勾选大盘热点、我的持仓或自选代码。大盘热点建议保留宽基、成长、周期、避险和波动对象。",
                "设置日期区间。小时级至少保留 30 个交易日，日线建议保留 6-12 个月。",
                "默认开启每小时自动刷新当前页；如果不想刷新，可以关闭并手动点击生成。",
                "点击生成热点分析后，先拖动时间切片，观察不同小时或日期的热点变化。",
                "先看热力图定位偏强和偏弱区域，再看气泡图区分短期异动和持续强弱。",
                "最后查看优先复核对象和热点明细，确认热度是否由趋势、波动、回撤或数据异常驱动。",
            ),
            checks=(
                "失败对象是否为 0；如果不为 0，先确认代码、数据源权限和时间粒度。",
                "偏强对象是否集中在一个板块，还是多个板块扩散。",
                "避险资产、波动率和权益资产是否发出互相矛盾的信号。",
                "热度变化是否持续多个时间切片，而不是单小时噪声。",
            ),
            outputs=(
                "热点总览：对象数量、平均热度、偏强对象、偏弱对象、领先板块和失败对象。",
                "热力图：按板块/对象查看热点热度。",
                "气泡图：按近1期和近5期涨跌查看异动强度。",
                "优先复核对象表、热点明细表和指标口径说明。",
            ),
            risks=(
                "热点热度是横向技术状态，不是涨跌预测和实盘操作建议。",
                "60min 数据受数据源权限、延迟和交易时段影响，失败时必须降级处理。",
                "短期热点可能来自新闻、资金流或外部冲击，必须结合基本面和数据质量复核。",
            ),
        ),
        UsageGuideSection(
            title="盘感训练",
            target_key="market_feel",
            purpose="用技术面指标训练读图能力，把价格结构拆成趋势、动能、风险和量价确认四个模块。",
            best_for="日常复盘、策略前检查、观察持仓和自选对象技术状态；用于训练判断，不作为独立交易信号。",
            steps=(
                "选择数据源。首次训练建议用 Sample；真实研究优先使用 Moomoo、Yahoo Finance 或 AKShare。",
                "选择市场，并勾选大盘对象、我的持仓或自选代码。",
                "设置开始日期和结束日期。盘感训练至少需要 60 个交易日，建议保留一年以上样本。",
                "选择训练场景：收盘复盘、盘中观察或策略前检查。",
                "点击生成盘感训练，先看盘感分、趋势、动能、风险和量价四个判断。",
                "选择图表对象，按价格、MA20/MA60、Bollinger、RSI 和 MACD 的顺序读图。",
                "查看指标讲解表，逐项理解每个指标为什么支持或削弱当前判断。",
                "阅读训练题，先自己给出判断，再对照讲解、分析和训练结论复核。",
            ),
            checks=(
                "价格是否在 MA20 和 MA60 上方，短期趋势和中期趋势是否一致。",
                "RSI 与 MACD 是否共振，还是一个偏强一个偏弱。",
                "Bollinger 位置是否接近上轨或下轨，是否存在拥挤或风险释放。",
                "ATR、波动和 60 日最大回撤是否提示风险升温。",
                "成交量是否确认价格方向，还是放量承压或缩量观望。",
            ),
            outputs=(
                "盘感训练卡片：盘感分、趋势判断、动能判断、风险判断、量价判断。",
                "技术图表：价格、MA20/MA60、Bollinger、RSI、MACD。",
                "指标讲解表、训练明细表、训练题和研究结论。",
            ),
            risks=(
                "技术面训练只能帮助识别结构和风险，不能单独证明未来涨跌。",
                "强趋势可能继续强，也可能高位拥挤；低迷状态可能反弹，也可能继续恶化。",
                "数据源、复权、成交量口径不同会影响指标读数，真实研究应回到数据中心交叉校验。",
            ),
        ),
        UsageGuideSection(
            title="持仓",
            target_key="holdings",
            purpose="统一读取、保存、同步和维护个人持仓，区分正式持仓、截图候选持仓和待确认订单。",
            best_for="把行研报告系统、消费行为分析系统、支付宝账本和 PFI 本地导入的持仓放到同一持仓簿。",
            steps=(
                "进入持仓页面后先点击同步持仓，系统会扫描已配置的持仓来源。",
                "查看顶部卡片，确认持仓总市值、正式持仓数量、最大单一权重、前三权重和待确认订单数量。",
                "在当前持仓页检查正式持仓表，确认代码、名称、市场、市值、权重和来源文件。",
                "查看暴露拆解，检查市场暴露和来源暴露是否符合真实账户情况。",
                "打开同步来源，确认支付宝账本、行研上传、消费分析系统和 PFI 导入目录是否 Ready。",
                "打开待确认订单，核对付款成功但未确认份额或净值的记录；这些记录不会计入正式持仓。",
                "需要补录时到手动维护页填写代码、名称、市场、数量、市值、成本和浮动盈亏。",
                "到质量检查页查看缺失市值、缺失市场、更新时间和集中度检查。",
            ),
            checks=(
                "正式持仓不能包含待确认订单或截图候选记录。",
                "持仓簿更新时间是否接近最近一次上传时间。",
                "市值和权重是否与真实账户口径一致。",
                "最大单一权重和前三权重是否触发集中度风险。",
            ),
            outputs=(
                "永久保存的 HoldingsBook.json。",
                "可导出的 HoldingsBook.csv。",
                "同步历史、来源状态、质量检查和待确认订单表。",
            ),
            risks=(
                "支付宝当前持仓文件为空时，只能显示待确认订单，不能假设正式持仓。",
                "不同系统的基金名称和代码可能不完全一致，需要人工复核。",
                "手动录入会覆盖同代码同市场的最新记录，保存前需确认口径。",
            ),
        ),
        UsageGuideSection(
            title="报告中心",
            target_key="reports",
            purpose="集中查看、筛选、下载和清理所有研究产物，形成可追溯的研究档案。",
            best_for="复盘历史回测、查找 Word 报告、比较不同日期和不同策略的研究记录。",
            steps=(
                "先看顶部资产卡片，确认 Word 报告、运行元数据、数据质量报告和实验记录数量。",
                "在总览页查看研究资产趋势、运行收益/回撤分布、最近运行趋势和策略表现汇总。",
                "在报告列表按报告类型、日期目录和关键词筛选，定位目标 Word 报告。",
                "下载最新 Word 报告或打开报告所在目录，进行人工复核和归档。",
                "进入运行判读，按状态筛选历史运行，重点比较收益、回撤、Sharpe、成本占比。",
                "进入实验记录，打开参数扫描或验证实验的详细页面。",
                "使用安全清理时只清理杂项文件，不会删除 Word、JSON、CSV 研究产物。",
            ),
            checks=(
                "最新报告日期是否与本次研究日期一致。",
                "报告名是否符合 `报告名称_DDMMYYYY` 规则。",
                "报告是否包含策略描述、数据质量、多源交叉校验、收益曲线和回撤图。",
                "运行元数据是否能解释这次结果由哪个策略、标的、时间区间和成本设置产生。",
            ),
            outputs=(
                "Word 报告清单、运行元数据清单、实验记录清单。",
                "可下载的最新 Word 报告。",
                "按日期分类的研究产物目录。",
            ),
            risks=(
                "只看报告结论不看数据质量，容易误用不完整行情。",
                "不同日期参数不同，不能只比较收益，必须同步比较成本和回撤。",
                "安全清理只用于杂项文件，研究产物不要手动误删。",
            ),
        ),
        UsageGuideSection(
            title="行研报告",
            target_key="industry",
            purpose="按日期检索本地行研报告，并把报告、验证任务、PFI 研究产物和回测元数据放到同一视图。",
            best_for="从盘前、盘中、盘后、K 线分析或行业研究报告出发，形成待验证问题并联动量化验证。",
            steps=(
                "确认行研报告目录。默认目录是当前用户 `~/Downloads/行研报告`，也可用 `PFI_INDUSTRY_REPORT_DIR` 覆盖。",
                "选择开始日期和结束日期，按报告日期筛选。",
                "输入关键词，按报告名称、类型、目录或路径搜索。",
                "在报告表格中查看报告日期、类型、区间目录、大小和路径。",
                "选择报告后可以打开报告或打开所在目录。",
                "查看最近 PFI Word 报告，把行研结论与回测验证报告对应起来。",
                "查看验证任务队列，把行研中的假设拆成待验证信号。",
            ),
            checks=(
                "报告日期是否与研究日期一致。",
                "报告类型是否符合本次研究目的，例如盘前、盘中、盘后或 K 线。",
                "是否已有对应 PFI 验证报告。",
                "验证任务是否记录了样本区间、成本假设和基准。",
            ),
            outputs=(
                "按日期筛选后的行研报告列表。",
                "行研报告路径和打开入口。",
                "最近 PFI 报告和验证任务联动表。",
            ),
            risks=(
                "PDF 内容当前主要按文件名和日期索引，正文深度解析需要后续接入 OCR 或 PDF 文本提取。",
                "行研结论不能直接升级为实盘操作，必须通过数据质量、回测和风险门禁验证。",
            ),
        ),
        UsageGuideSection(
            title="研究总线",
            target_key="research_bus",
            purpose="统一监控 PFI、行研系统、消费行为系统、持仓主数据和独立验证系统的输入、输出、请求、心跳和同步状态。",
            best_for="当你通过任意聊天框、投递箱、Webhook 或行研系统更新信息后，检查这些信息是否进入共享数据库并被对应系统处理。",
            steps=(
                "进入研究总线页面，先看顶部五个状态卡片：总线状态、待处理请求、失败请求、心跳过期和投递箱文件。",
                "如果投递箱文件大于 0，点击处理投递箱，把 `.txt`、`.md` 或 `.json` 对话输入写入 ResearchBus。",
                "如果待处理请求大于 0，点击处理请求，让 ResearchBus 执行同步、验证任务、独立验证或系统优化登记。",
                "点击同步一次，串行同步行研报告、PFI 回测结果、持仓主数据和消费行为系统状态。",
                "打开系统状态页，确认 PFI、AI-Research-System、ConsumptionAnalysisSystem、HoldingsMaster 和 ResearchBus 都是 Ready。",
                "打开请求页，检查 `Pending`、`Completed`、`Failed` 的请求类型和响应内容。",
                "打开对话输入页，确认输入来源、分类、关联请求和创建时间。",
                "打开心跳页，检查各系统最后同步时间和能力声明是否过期。",
            ),
            checks=(
                "失败请求数量是否为 0；如果不为 0，必须打开最近请求查看错误字段。",
                "心跳是否过期；过期说明对应系统的 watch、automation 或手动同步没有运行。",
                "投递箱文件是否被移动到 processed 或 failed，不能长期停留在根目录。",
                "同步后的验证任务数量、回测结果数量和消费行为状态数量是否符合预期。",
            ),
            outputs=(
                "ResearchBus.sqlite 共享数据库。",
                "ResearchBusSnapshot.json 审计快照。",
                "bus_api_requests、bus_chat_inputs、bus_heartbeats、system_state 等状态表。",
                "投递箱 processed/failed 文件和错误记录。",
            ),
            risks=(
                "本地 HTTP/Webhook 只允许绑定 127.0.0.1，不要暴露到公网。",
                "LaunchAgent 在 macOS Documents 路径下可能被 TCC 权限拦截，需要授权或使用手动同步脚本。",
                "系统优化请求只会登记为待评审任务，不会自动修改代码。",
            ),
        ),
        UsageGuideSection(
            title="大数据模拟",
            target_key="big_data",
            purpose="调用独立验证系统生成大规模数据测试计划、分片记录和 checksum 校验摘要，确认 PFI、行研系统和自动化入口能共享同一验证结果。",
            best_for="验证百万、千万、亿级到十亿级数据任务的调度能力、分片口径、审计输出和跨系统可见性。",
            steps=(
                "进入大数据模拟页面，先看共享库状态、运行次数、最新状态、最新规模和最新分片。",
                "选择模拟规模：百万行、千万行、一亿行、十亿行或自定义行数。",
                "选择分片大小。默认百万行适合日常检查；十亿级任务可用一亿行减少分片数量。",
                "选择验证模式。dry_run 只登记计划；checksum 会生成逐片校验摘要，但仍不会一次性加载完整大数据。",
                "填写自然语言备注，用于记录这次测试的来源、目的和上下文。",
                "点击运行大数据模拟，系统会把结果写入独立验证运行表和分片表。",
                "到最近运行表确认状态、模式、总行数、分片数、输出文件和更新时间。",
                "需要从其他聊天框或 automation 触发时，复制页面给出的 researchBusApi.sh 命令或把文本放入投递箱。",
            ),
            checks=(
                "总行数是否符合预期，例如百万行等于 1,000,000，十亿行等于 1,000,000,000。",
                "分片数是否合理，且没有把完整数据集一次性加载到内存。",
                "checksum 模式下每个分片状态是否为 Completed；失败时必须查看输出文件错误信息。",
                "ResearchBus 的请求表、对话输入表和独立验证运行表是否能看到同一任务。",
            ),
            outputs=(
                "independent_validation_runs 运行记录。",
                "independent_validation_shards 分片记录。",
                "data/independentValidation 下的 IndependentValidationRun JSON 输出文件。",
                "可被 PFI、AI-Research-System、automation 和其他 agent 读取的 ResearchBus 共享状态。",
            ),
            risks=(
                "dry_run 证明调度和审计链路可用，不证明真实源文件内容已经被逐行校验。",
                "checksum 对真实文件执行时，如果文件缺失、格式不支持或行数不足，会 fail-closed。",
                "亿级以上真实数据执行需要外部分布式或批处理执行器逐片消费，当前页面只负责登记和轻量校验。",
            ),
        ),
        UsageGuideSection(
            title="个人画像",
            target_key="profile",
            purpose="综合消费行为分析系统持仓、PFI 持仓、回测记录、复盘记录和验证任务，形成行为习惯、风险和优化方向。",
            best_for="日常复盘自己的研究纪律、风险暴露、证据习惯、情绪偏差和待验证积压。",
            steps=(
                "先看顶部持仓总市值、持仓数量、最大单一权重、前三权重和 HHI。",
                "打开数据连接状态，确认消费行为分析系统和 PFI 持仓数据是否 Ready。",
                "如果持仓数据缺失，把 CSV、XLSX 或 JSON 放入 `data/external/consumerHoldings` 或 `data/holdings`。",
                "查看持仓数据和来源/市场暴露，确认数据是否来自正确系统。",
                "查看行为习惯，理解研究频率、证据习惯、复盘纪律和验证队列。",
                "查看风险画像，优先识别持仓集中、证据链不完整、情绪冲动和纪律违反。",
                "查看行为优化，把建议转化为后续验证任务或复盘动作。",
            ),
            checks=(
                "持仓文件字段是否包含代码、市场、市值或权重。",
                "最大单一权重和前三权重是否过高。",
                "NeedsMoreEvidence 运行是否过多。",
                "复盘记录是否存在新闻冲动、情绪补仓、追高或纪律违反。",
            ),
            outputs=(
                "持仓汇总、来源暴露和市场暴露。",
                "行为习惯表、风险画像表和行为优化表。",
                "研究证据、复盘行为和验证任务明细。",
            ),
            risks=(
                "未配置持仓数据时，集中度和真实账户风险无法准确判断。",
                "行为画像基于已记录数据，记录越少，结论越应视为初步观察。",
                "页面只提供研究复盘，不输出实盘买卖或仓位建议。",
            ),
        ),
        UsageGuideSection(
            title="参数扫描",
            target_key="scan",
            purpose="系统比较一组参数组合，判断策略是否只依赖单个偶然参数。",
            best_for="优化已确认策略的参数网格，验证收益、Sharpe、回撤在参数邻域内是否稳定。",
            steps=(
                "选择数据源、标的、市场、周期、开始日期和结束日期。",
                "选择已确认策略。未确认的自定义策略需要先到策略库完成确认。",
                "填写参数网格，例如 short_window=10,20,30；自定义策略可用 indicator.parameter=... 覆盖策略库参数。",
                "控制最大组合数，先用小网格跑通，再逐步扩大范围。",
                "设置成本和初始资金，保持与单标的回测一致，便于对比。",
                "运行参数扫描，系统会生成所有有效参数组合的结果。",
                "先看热力图：总收益率、Sharpe、最大回撤是否在相邻参数区域表现一致。",
                "再看 Train-Test 和 Walk-Forward 验证，确认样本外没有明显失效。",
                "打开实验详情，检查最佳参数、稳定性说明、风险闸门和实验明细。",
            ),
            checks=(
                "最佳参数附近是否也有较好结果；如果只有一个孤岛，过拟合风险高。",
                "Train-Test 的测试期表现是否显著低于训练期。",
                "Walk-Forward 通过窗口数量是否足够。",
                "最佳收益是否以不可接受回撤为代价。",
            ),
            outputs=(
                "参数热力图和 Top N 参数组合图。",
                "实验摘要、实验明细和可导出的实验 Word 报告。",
                "稳定性、Train-Test、Walk-Forward 验证结果。",
            ),
            risks=(
                "参数扫描越多，越容易数据挖掘；必须用样本外验证约束。",
                "只按最高收益选参数不可靠，应同时看 Sharpe、回撤和成本。",
                "自定义策略扫描仍必须经过策略库确认；参数覆盖不代表策略假设已经成立。",
            ),
        ),
        UsageGuideSection(
            title="组合轮动",
            target_key="portfolio",
            purpose="研究多个标的之间的动量轮动效果，判断组合层面是否优于单标的。",
            best_for="ETF 轮动、多资产候选池、分散化研究和组合稳定性验证。",
            steps=(
                "输入股票池，多个标的用英文逗号分隔。",
                "选择数据源、市场、开始日期和结束日期。",
                "设置动量回看窗口和持有数量 Top N。",
                "设置成本和初始资金，成本要与单标的回测保持同口径。",
                "运行组合轮动后，先看组合核心指标和权益摩擦图。",
                "查看组合归因，确认收益来自哪些标的、权重是否过度集中。",
                "查看交易、持仓和信号表，确认没有异常换手或空仓逻辑。",
            ),
            checks=(
                "最大单标的权重是否过高。",
                "前三权重是否集中，是否违背分散化目标。",
                "换手是否过高导致交易摩擦吞噬收益。",
                "组合收益是否只是某一个标的贡献，而非轮动机制本身有效。",
            ),
            outputs=(
                "组合回测指标、权益与交易摩擦图。",
                "组合归因表、交易表、持仓表和信号表。",
                "各标的数据质量报告。",
            ),
            risks=(
                "标的池过小会让轮动结果不稳定。",
                "不同市场和货币混用时需要额外汇率处理；当前默认同币种研究。",
                "组合轮动不代表实盘调仓指令，只用于研究参考。",
            ),
        ),
        UsageGuideSection(
            title="数据中心",
            target_key="tools",
            purpose="检查数据源可用性、A 股代码格式和多源交叉校验，保证回测数据可验证。",
            best_for="真实数据接入前、标的搜索异常时、报告数据质量需要复核时。",
            steps=(
                "先看数据源状态，确认 Sample、CSV、Moomoo、AKShare、TuShare、Yahoo Finance 等是否可用。",
                "如果状态为 NeedsConfig，说明需要配置对应 API Key 或环境变量。",
                "使用代码格式示例确认 A 股、港股、美股代码输入规则。",
                "使用 A 股代码助手，把 000001、600000 等代码转换成 AKShare、TuShare 所需格式。",
                "运行多源交叉校验时至少选择两个数据源。",
                "设置校验日期和容忍差异，检查最大差异和平均差异。",
                "交叉校验通过后，再回到单标的回测使用该数据源。",
            ),
            checks=(
                "Moomoo 是否显示 NeedsOpenD；如果是，需要先启动并登录 OpenD。",
                "TuShare、Alpha Vantage、Polygon 是否配置 API Key。",
                "多源交叉校验差异是否在可接受阈值内。",
                "A 股代码后缀是否与目标数据源一致。",
            ),
            outputs=(
                "数据源状态表。",
                "A 股代码格式转换结果。",
                "多源交叉校验报告和交叉校验详情。",
            ),
            risks=(
                "不同数据源复权、时区、停牌处理可能不同。",
                "分钟级数据更容易受数据源权限限制。",
                "数据中心只能帮助发现差异，不能保证所有外部数据源永远准确。",
            ),
        ),
        UsageGuideSection(
            title="策略库",
            target_key="library",
            purpose="沉淀策略假设、收益来源、失效环境、参数设置和策略档案。",
            best_for="管理内置策略、创建自定义策略、编辑策略档案和建立可复用策略库。",
            steps=(
                "先查看内置策略列表，理解每个策略的类别、收益来源和研究假设。",
                "选择一个策略查看档案，重点读收益来源、长期存在理由、失效环境和默认参数设置。",
                "需要修改内置策略档案时，使用编辑内置策略档案；修改会持久保存，不覆盖源码。",
                "新增自定义策略时，输入中文名称，系统自动生成英文名称和策略编号。",
                "选择策略逻辑、指标组合和参数设置，系统自动推断类别、收益来源、研究假设和失效环境。",
                "生成策略模板后，检查 no-code 参数、策略文件、档案文件和确认记录。",
                "编辑自定义策略规格会生成新版本并提交确认，确认前不能作为正式策略运行。",
            ),
            checks=(
                "策略是否能回答赚的是什么钱、为什么长期存在、什么环境会失效。",
                "收益来源是否来自风险溢价、行为偏差、信息优势、结构性约束、执行优势或组合优势。",
                "参数设置是否可解释，是否避免过度复杂。",
                "策略修改是否产生新的确认记录。",
            ),
            outputs=(
                "内置策略档案和持久化覆盖文件。",
                "自定义策略规格、策略文件、策略档案和修改历史。",
                "待确认或已确认的策略记录。",
            ),
            risks=(
                "没有研究假设的策略不应进入正式回测。",
                "内置档案编辑不等于修改策略代码，只影响研究说明和档案。",
                "自定义策略必须确认后才可运行，避免未复核逻辑进入结果。",
            ),
        ),
    ]


def parameter_scan_term_rows() -> list[dict[str, str]]:
    return [
        {
            "术语": "参数扫描",
            "解释": "把同一个策略的多组参数逐一回测，比较哪一组更稳健，而不是只看单次回测结果。",
            "使用方法": "先设定一个合理参数范围，再看收益、Sharpe、回撤和样本外验证是否同时较好。",
            "风险提示": "参数越多越容易过拟合，不能只选择历史收益最高的一组。",
        },
        {
            "术语": "参数网格",
            "解释": "把策略参数组合成二维或多维组合表，每一个格子代表一次独立回测。",
            "使用方法": "每行使用 参数名=值1,值2；自定义策略使用 indicator.parameter=值1,值2 覆盖策略库参数。",
            "风险提示": "网格过细会增加数据挖掘风险，也会拖慢运行速度。",
        },
        {
            "术语": "已确认策略",
            "解释": "进入正式扫描前，策略必须在策略库里完成研究假设、参数和风险说明确认。",
            "使用方法": "如果自定义策略未出现在参数扫描下拉框，先回到策略库确认当前版本。",
            "风险提示": "未确认策略不能作为正式研究实验，避免把草稿逻辑误当成验证结果。",
        },
        {
            "术语": "短均线 MA",
            "解释": "较短窗口的移动平均线，用来更快反映价格近期变化。",
            "使用方法": "短均线常用于捕捉趋势启动，但要与长均线一起判断。",
            "风险提示": "窗口太短容易被噪声影响，可能导致频繁交易。",
        },
        {
            "术语": "长均线 MA",
            "解释": "较长窗口的移动平均线，用来表示中长期趋势基准。",
            "使用方法": "长均线通常作为趋势过滤器，短均线上穿长均线时代表趋势可能转强。",
            "风险提示": "窗口太长会反应迟钝，可能错过较早的趋势变化。",
        },
        {
            "术语": "总收益率",
            "解释": "从回测开始到结束，策略权益相对初始资金的累计涨跌幅。",
            "使用方法": "用于判断最终结果是否赚钱，但必须结合回撤和成本一起看。",
            "风险提示": "高总收益可能来自少数极端行情，不能单独作为选参依据。",
        },
        {
            "术语": "年化收益率",
            "解释": "把不同长度回测区间折算成每年平均收益，方便跨时间区间比较。",
            "使用方法": "比较不同周期实验时优先看年化收益率，而不是只看总收益率。",
            "风险提示": "短区间年化容易被放大，样本过短时参考价值下降。",
        },
        {
            "术语": "Sharpe",
            "解释": "衡量单位波动带来的收益，数值越高通常说明收益质量越好。",
            "使用方法": "在收益接近时，优先选择 Sharpe 更高且回撤更小的参数组合。",
            "风险提示": "Sharpe 假设收益分布较稳定，遇到极端亏损或非线性策略时需要结合回撤判断。",
        },
        {
            "术语": "最大回撤",
            "解释": "回测期间从历史最高权益跌到之后最低权益的最大跌幅。",
            "使用方法": "用于衡量最难承受的亏损深度，是选参时的核心风控指标。",
            "风险提示": "收益高但最大回撤过大，可能不适合真实交易参考。",
        },
        {
            "术语": "热力图",
            "解释": "用颜色展示不同参数组合的表现，颜色越明显代表该指标越突出。",
            "使用方法": "寻找一片连续表现较好的区域，而不是只寻找单个最好格子。",
            "风险提示": "如果只有一个孤立亮点，通常代表参数稳定性不足。",
        },
        {
            "术语": "Top N 参数组合",
            "解释": "按指标排序后展示表现靠前的 N 组参数。",
            "使用方法": "用于快速定位候选参数，但最终还要看稳定性、回撤和样本外验证。",
            "风险提示": "Top N 只是历史排序，不代表未来仍排在前列。",
        },
        {
            "术语": "参数稳定性",
            "解释": "判断最佳参数附近的其他参数是否也表现良好。",
            "使用方法": "优先选择一片区域都表现不错的参数，而不是一个尖峰参数。",
            "风险提示": "稳定性差说明策略可能只适配过去某段行情。",
        },
        {
            "术语": "前 20% 均值",
            "解释": "表现排名前 20% 参数组合的平均得分，用来判断优秀参数整体质量。",
            "使用方法": "如果前 20% 均值接近最佳分数，说明优秀区域较宽。",
            "风险提示": "如果最佳分数远高于前 20% 均值，可能是偶然尖峰。",
        },
        {
            "术语": "邻域均值",
            "解释": "最佳参数附近相邻参数组合的平均表现。",
            "使用方法": "用来判断最佳参数周围是否仍然有效。",
            "风险提示": "邻域均值很差时，不建议直接使用最佳参数作为交易参考。",
        },
        {
            "术语": "覆盖度",
            "解释": "参数扫描中有效参数组合占全部候选组合的比例。",
            "使用方法": "覆盖度越高，说明扫描结果越完整。",
            "风险提示": "覆盖度过低时，可能是参数设置无效或数据不足。",
        },
        {
            "术语": "Train-Test 验证",
            "解释": "把历史数据分成训练期和测试期，先在训练期选参数，再看测试期表现。",
            "使用方法": "测试期表现不能明显差于训练期，否则说明泛化能力不足。",
            "风险提示": "只在训练期好、测试期差，是典型过拟合信号。",
        },
        {
            "术语": "Walk-Forward 验证",
            "解释": "用多个滚动窗口重复训练和测试，模拟策略在时间推进中的稳定性。",
            "使用方法": "关注通过窗口数量、平均测试分数和平均泛化能力。",
            "风险提示": "通过窗口少，说明策略对市场环境变化敏感。",
        },
        {
            "术语": "泛化比率",
            "解释": "测试期表现相对训练期表现的比例，用来衡量参数从历史拟合到未知数据的延续性。",
            "使用方法": "泛化比率越接近或高于合理水平，说明样本外表现越稳。",
            "风险提示": "泛化比率过低说明历史参数可能不可复用。",
        },
        {
            "术语": "研究风险闸门",
            "解释": "系统对回测结果做的风险检查，包括收益、回撤、成本、稳定性和样本外表现。",
            "使用方法": "如果风险闸门提示复核，应先查原因，再决定是否继续研究该参数。",
            "风险提示": "风险闸门不是收益保证，只是帮助你排除明显不稳健的结果。",
        },
        {
            "术语": "过拟合",
            "解释": "策略参数过度适配历史数据，导致历史表现好但未来或样本外表现差。",
            "使用方法": "通过参数稳定性、Train-Test、Walk-Forward 和更长区间验证降低风险。",
            "风险提示": "参数扫描最常见的问题就是过拟合，必须主动防范。",
        },
        {
            "术语": "交易摩擦",
            "解释": "佣金、滑点和冲击成本等交易成本的合计影响。",
            "使用方法": "参数扫描时要使用与真实交易接近的成本设置，避免高频参数被低估成本。",
            "风险提示": "如果扣除交易摩擦后收益消失，策略不具备实际参考价值。",
        },
    ]


def single_backtest_steps() -> list[WorkflowStep]:
    return [
        WorkflowStep(
            "选择数据",
            "Choose Data",
            "先用 Sample 熟悉流程，再切换到真实数据源。",
            "Use Sample first to learn the workflow, then switch to a real provider.",
        ),
        WorkflowStep(
            "选择策略",
            "Choose Strategy",
            "先使用默认策略参数，跑通后再修改。",
            "Use default strategy parameters first, then adjust after the first run.",
        ),
        WorkflowStep(
            "运行回测",
            "Run Backtest",
            "运行后检查核心指标、图表、交易和 Word 报告。",
            "After running, review key metrics, charts, trades, and the Word report.",
        ),
        WorkflowStep(
            "复核风险",
            "Review Risk",
            "重点看最大回撤、成本、数据质量和报告中的风险闸门。",
            "Focus on max drawdown, costs, data quality, and the research risk gate in the report.",
        ),
    ]


def daily_runbook_items() -> list[DailyRunbookItem]:
    return [
        DailyRunbookItem(
            "启动前",
            "Before Start",
            "检查系统自检、报告目录和数据源配置。",
            "Check system health, report directory, and data provider configuration.",
            "没有 Review 项；未配置的数据源只作为 Info 处理。",
            "No Review items; unconfigured providers appear as Info only.",
        ),
        DailyRunbookItem(
            "首次运行",
            "First Run",
            "先用 Sample 数据和默认 MA Crossover 跑一份报告。",
            "Run one report with Sample data and default MA Crossover first.",
            "报告、图表、数据质量文件和运行元数据都能生成。",
            "Report, charts, data quality file, and run metadata are generated.",
        ),
        DailyRunbookItem(
            "真实数据",
            "Real Data",
            "切换到 AKShare、TuShare、Yahoo、Alpha Vantage 或 Polygon，并执行多源交叉校验。",
            "Switch to AKShare, TuShare, Yahoo, Alpha Vantage, or Polygon, then run cross-source validation.",
            "数据质量为 Pass 或 Info，交叉校验差异在可接受阈值内。",
            "Data quality is Pass or Info, and cross-source difference is within tolerance.",
        ),
        DailyRunbookItem(
            "研究决策",
            "Research Decision",
            "只使用经过策略库确认、成本后仍有效、回撤可接受的结果作为交易参考。",
            "Use only strategy-library-confirmed, cost-adjusted, drawdown-acceptable results as trading references.",
            "风险闸门不为 Block，且 Word 报告能解释收益来源和失效条件。",
            "Risk gate is not Block, and the Word report explains return source and failure conditions.",
        ),
    ]


def readiness_summary(pass_count: int, review_count: int, info_count: int) -> tuple[str, str]:
    if review_count > 0:
        return (
            "需要先处理 Review 项，再使用结果作为研究参考。",
            "Resolve Review items before using outputs as research references.",
        )
    if info_count > 0:
        return (
            "核心环境可用；未配置的数据源会显示为 Info。",
            "Core environment is ready; unconfigured data providers appear as Info.",
        )
    return (
        "系统自检全部通过，可以开始研究流程。",
        "All system checks passed; research workflow can start.",
    )


def buy_and_hold_metrics(data: pd.DataFrame, annualization: int = 252) -> dict[str, float]:
    if data.empty or "close" not in data.columns:
        return _empty_buy_hold_metrics()
    close = _ordered_close_series(data)
    if len(close) < 2:
        return _empty_buy_hold_metrics()
    start = float(close.iloc[0])
    if start <= 0:
        return _empty_buy_hold_metrics()
    end = float(close.iloc[-1])
    total_return = end / start - 1
    periods = max(len(close) - 1, 1)
    annualized = (1 + total_return) ** (annualization / periods) - 1 if total_return > -1 else -1.0
    returns = close.pct_change().fillna(0.0)
    volatility = returns.std() * annualization**0.5
    sharpe = (returns.mean() * annualization / volatility) if volatility else 0.0
    wealth = close / start
    drawdown = wealth / wealth.cummax() - 1
    return {
        "buy_hold_total_return": float(total_return),
        "buy_hold_annualized_return": float(annualized),
        "buy_hold_sharpe": float(sharpe),
        "buy_hold_volatility": float(volatility),
        "buy_hold_max_drawdown": float(drawdown.min()),
    }


def _empty_buy_hold_metrics() -> dict[str, float]:
    return {
        "buy_hold_total_return": 0.0,
        "buy_hold_annualized_return": 0.0,
        "buy_hold_sharpe": 0.0,
        "buy_hold_volatility": 0.0,
        "buy_hold_max_drawdown": 0.0,
    }


def _ordered_close_series(data: pd.DataFrame) -> pd.Series:
    frame = data.copy()
    if "datetime" in frame.columns:
        frame = frame.assign(_pfi_os_datetime=pd.to_datetime(frame["datetime"], errors="coerce"))
        frame = frame.sort_values("_pfi_os_datetime", kind="mergesort")
    elif isinstance(frame.index, pd.DatetimeIndex):
        frame = frame.sort_index(kind="mergesort")
    close = pd.to_numeric(frame["close"], errors="coerce").dropna()
    return close[close > 0]


def backtest_result_judgements(metrics: dict, buy_hold: dict[str, float]) -> list[ResultJudgement]:
    strategy_total = float(metrics.get("total_return", 0.0))
    strategy_annualized = float(metrics.get("annualized_return", 0.0))
    max_drawdown_value = float(metrics.get("max_drawdown", 0.0))
    cost_total = float(metrics.get("cost_total", 0.0))
    ending_equity = float(metrics.get("ending_equity", 0.0))
    buy_hold_total = float(buy_hold.get("buy_hold_total_return", 0.0))
    buy_hold_annualized = float(buy_hold.get("buy_hold_annualized_return", 0.0))
    buy_hold_drawdown = float(buy_hold.get("buy_hold_max_drawdown", 0.0))
    excess_total = strategy_total - buy_hold_total
    excess_annualized = strategy_annualized - buy_hold_annualized
    drawdown_difference = max_drawdown_value - buy_hold_drawdown
    cost_ratio = cost_total / ending_equity if ending_equity else 0.0

    return [
        ResultJudgement(
            _status_from_threshold(excess_total, pass_level=0.0, watch_level=-0.05),
            "相对买入持有",
            "Versus Buy And Hold",
            f"策略总收益比买入持有高 {excess_total:.2%}，年化差异 {excess_annualized:.2%}。",
            f"Strategy total return exceeds buy-and-hold by {excess_total:.2%}; annualized difference is {excess_annualized:.2%}.",
        ),
        ResultJudgement(
            _status_from_threshold(drawdown_difference, pass_level=0.0, watch_level=-0.05),
            "相对买入持有回撤",
            "Drawdown Versus Buy Hold",
            f"策略最大回撤相比买入持有最大回撤为 {drawdown_difference:.2%}。策略 {max_drawdown_value:.2%}，买入持有 {buy_hold_drawdown:.2%}；正数表示策略回撤更小。",
            f"Strategy max drawdown versus buy-and-hold max drawdown is {drawdown_difference:.2%}. Strategy is {max_drawdown_value:.2%}; buy-and-hold is {buy_hold_drawdown:.2%}; positive means the strategy drawdown is smaller.",
        ),
        ResultJudgement(
            _status_from_threshold(-cost_ratio, pass_level=-0.03, watch_level=-0.08),
            "交易摩擦",
            "Trading Friction",
            f"建模交易摩擦占期末权益 {cost_ratio:.2%}。",
            f"Modeled trading friction is {cost_ratio:.2%} of ending equity.",
        ),
    ]


def _status_from_threshold(value: float, pass_level: float, watch_level: float) -> str:
    if value >= pass_level:
        return "Pass"
    if value >= watch_level:
        return "Watch"
    return "Review"


def _drawdown_status(value: float) -> str:
    if value >= -0.15:
        return "Pass"
    if value >= -0.25:
        return "Watch"
    return "Review"
