from __future__ import annotations

import html
import hashlib
import json
import os
import re
import sys
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

try:
    import streamlit as st
    import streamlit.components.v1 as components
except (ModuleNotFoundError, ImportError, TypeError):  # pragma: no cover - enables logic-level imports without optional UI deps
    class _MissingStreamlit:
        def cache_data(self, *decorator_args, **decorator_kwargs):
            if decorator_args and callable(decorator_args[0]) and len(decorator_args) == 1 and not decorator_kwargs:
                return decorator_args[0]

            def _decorator(func):
                return func

            return _decorator

        def __getattr__(self, name):
            raise ModuleNotFoundError(
                "streamlit is required for the PFI UI runtime. "
                "Install optional app dependencies with `pip install -e .[app]`."
            )

    class _MissingComponents:
        def html(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "streamlit is required for embedded UI components. "
                "Install optional app dependencies with `pip install -e .[app]`."
            )

    st = _MissingStreamlit()
    components = _MissingComponents()

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ModuleNotFoundError:  # pragma: no cover
    go = None
    make_subplots = None

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

CASHFLOW_LEDGER = "company_cashflow"
POLICY_LEDGER = "policy_radar"
CONSUMPTION_LEDGER = "consumption_guard"
ALIPAY_IMPORT_STATUS_LABELS = {
    "Ready": "就绪",
    "Pass": "通过",
    "Review": "待复核",
    "PendingReview": "待复核",
    "Failed": "失败",
    "Error": "失败",
    "Skipped": "已跳过",
}

from pfi_os.approvals import StrategyApprovalRegistry
from pfi_os.application import (
    OperationalStore,
    build_command_center_read_model,
    build_macos_runtime_acceptance_read_model,
    build_vectorized_research_read_model,
    build_homepage_summary,
    empty_command_center_read_model,
    empty_macos_runtime_acceptance_read_model,
    empty_vectorized_research_read_model,
    empty_homepage_summary,
    append_private_reviewed_input_entry,
    default_data_home,
    ingest_command_center_cache,
    ingest_macos_runtime_acceptance_cache,
    ingest_vectorized_research_cache,
    load_private_reviewed_input_entries,
    private_reviewed_input_output_dir,
)
from pfi_os.analysis import (
    HOTSPOT_REFRESH_TTL_SECONDS,
    HOTSPOT_RUNTIME_SUMMARY_SCHEMA,
    SentimentInstrument,
    build_hotspot_evidence_gate_rows,
    build_hotspot_history,
    bootstrap_equity_robustness,
    build_strategy_diagnostics,
    default_hotspot_universe,
    default_sentiment_universe,
    hotspot_cache_directory_summary,
    hotspot_focus_rows,
    hotspot_persisted_cache_status,
    hotspot_request_trace_summary,
    invalidate_hotspot_persisted_cache,
    load_hotspot_persisted_cache,
    hotspot_runtime_cache_key,
    hotspot_runtime_summary,
    hotspot_summary,
    write_hotspot_persisted_cache,
    market_feel_chart_frame,
    market_feel_from_bars,
    market_feel_indicator_rows,
    market_feel_training_case,
    portfolio_attribution,
    portfolio_concentration_metrics,
    portfolio_exposure_breakdown,
    portfolio_single_symbol_loss,
    portfolio_stress_scenarios,
    robustness_summary_rows,
    sentiment_from_bars,
    sentiment_summary,
)
from pfi_os.app.dashboard import (
    backtest_result_judgements,
    buy_and_hold_metrics,
    command_center_next_actions,
    macos_lifecycle_summary,
    macos_runtime_evidence_summary,
    parameter_scan_term_rows,
    readiness_summary,
    single_backtest_steps,
    usage_guide_sections,
    vectorized_research_shell_summary,
    workspace_shell_summary,
)
from pfi_os.backtest import BacktestConfig, BacktestEngine, PortfolioBacktestEngine
from pfi_os.business import (
    CASHFLOW_CATEGORIES,
    CASHFLOW_DIRECTIONS,
    build_cashflow_command,
    build_cashflow_runtime_summary,
    create_cashflow_entry,
    write_cashflow_command,
)
from pfi_os.consumption import (
    CONSUMPTION_CATEGORIES,
    CONSUMPTION_EVENT_TYPES,
    build_consumption_guard,
    build_consumption_runtime_summary,
    create_consumption_event,
    write_consumption_guard,
)
from pfi_os.config import REPORT_ROOT_DIR
from pfi_os.executive import build_command_center, write_command_center
from pfi_v02.local_imports import (
    build_alipay_import_preview,
    discover_local_alipay_raw_files,
    payloads_from_paths,
    write_private_alipay_import,
)
from pfi_os.data import (
    DEFAULT_US_ETF_UNIVERSE,
    INTERVAL_OPTIONS,
    assess_bars,
    get_bars_with_interval_fallback,
    market_symbol_examples,
    normalize_a_share_symbol,
    provider_status_rows,
    save_cross_source_validation_result,
    save_quality_report,
    search_symbols,
    validate_close_across_sources,
)
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.factory import make_provider
from pfi_os.integrations import (
    HOLDINGS_BOOK_PATH,
    HOLDINGS_EXPORT_PATH,
    bus_api_requests_frame,
    bus_chat_inputs_frame,
    bus_heartbeats_frame,
    build_personal_profile,
    collect_industry_reports,
    confirm_holding_update_candidate,
    export_holdings_csv,
    external_system_status,
    filter_industry_reports,
    holdings_exposure_frame,
    holdings_quality_frame,
    holdings_summary,
    holdings_sync_history_frame,
    holdings_symbol_proxy_frame,
    holding_update_candidates_frame,
    independent_validation_runs_frame,
    load_candidate_holdings_frame,
    load_current_holdings,
    load_holdings_frame,
    load_pending_orders_frame,
    pending_bus_requests_frame,
    process_chat_dropbox,
    process_pending_bus_requests,
    research_bus_health_summary,
    research_bus_db_path,
    research_bus_status_frame,
    resolve_holding_symbol_proxy,
    scan_holding_sources,
    run_independent_validation,
    sync_all_research_bus,
    sync_holdings_book,
    system_registry_frame,
    upsert_manual_holding,
)
from pfi_os.integrations.workspace_systems import compact_workspace_system_payload
from pfi_os.integrations.site52etf import (
    SITE52ETF_URL,
    build_site52etf_hotspot_comparison,
    fetch_52etf_public_snapshot,
    load_site52etf_public_snapshot_latest,
    site52etf_comparison_rows,
    site52etf_summary_rows,
)
from pfi_os.policy import (
    POLICY_LEVELS,
    POLICY_OPPORTUNITY_TYPES,
    POLICY_SOURCE_TYPES,
    build_policy_radar,
    build_policy_runtime_summary,
    create_policy_opportunity,
    write_policy_radar,
)
from pfi_os.research import (
    ACTION_TYPES,
    ERROR_TYPES,
    RETURN_ATTRIBUTION_TYPES,
    VALIDATION_TASK_STATUSES,
    ExperimentRunner,
    append_report_gap_validation_tasks,
    create_trade_review_record,
    create_validation_task,
    error_profile_frame,
    review_dashboard_cards,
    save_trade_review_record,
    save_validation_task,
    trade_review_frame,
    validation_queue_cards,
    validation_priority_frame,
    validation_task_frame,
    write_validation_task_execution,
    write_validation_priority_plan,
)
from pfi_os.research.experiments import analyze_parameter_stability
from pfi_os.reports.catalog import (
    WORD_REPORT_TYPES,
    artifact_counts,
    cleanup_report_junk,
    experiment_summaries_frame,
    filter_report_artifacts_frame,
    latest_report_artifact,
    load_experiment_detail,
    report_activity_frame,
    report_artifacts_frame,
    report_dashboard_cards,
    run_metadata_summaries_frame,
    run_status_counts_frame,
    search_report_artifacts_frame,
    strategy_run_summary_frame,
)
from pfi_os.risk import evaluate_decision_quality, evaluate_research_risk_gates
from pfi_os.strategies import (
    AlipayStrategy,
    AlipayEnhancedStrategy,
    BollingerReversionStrategy,
    BreakoutStrategy,
    CustomNoCodeStrategy,
    MomentumRotationStrategy,
    MovingAverageCrossoverStrategy,
    DEFAULT_STRATEGY_ORDER,
    RETURN_SOURCE_TAXONOMY,
    RSIReversionStrategy,
    STRATEGY_PROFILES,
    built_in_strategy_parameter_rows,
    collect_strategy_code_quality_reports,
    collect_strategy_profile_candidates,
    collect_strategy_smoke_tests,
    custom_strategy_spec_history_rows,
    custom_strategy_spec_rows,
    create_strategy_template,
    editable_strategy_profile_payload,
    evaluate_strategy_readiness_gate,
    get_built_in_strategy_parameters,
    get_strategy_profile,
    load_custom_strategy_specs,
    move_strategy_order_item,
    next_strategy_version,
    normalize_strategy_id,
    ordered_strategy_ids,
    reset_built_in_strategy_parameters,
    save_custom_strategy_spec_revision,
    save_built_in_strategy_parameters,
    save_strategy_profile_override,
    save_strategy_order,
    strategy_profile_rows,
    write_custom_strategy_code_for_spec,
)
from pfi_os.system import MASTER_SHORT_TITLE, MASTER_DISPLAY_NAME, collect_health_checks
from pfi_os.system.cache_cleanup import build_cache_cleanup_report
from pfi_os.system.report_validation_hub import build_report_validation_hub, report_validation_hub_summary


BUILT_IN_STRATEGY_FACTORIES = {
    "ma_crossover": MovingAverageCrossoverStrategy,
    "rsi_reversion": RSIReversionStrategy,
    "bollinger_reversion": BollingerReversionStrategy,
    "breakout": BreakoutStrategy,
    "alipay": AlipayStrategy,
    "alipay_enhanced": AlipayEnhancedStrategy,
}

DATA_OPTIONS = ["Sample", "Moomoo", "CSV", "AKShare", "TuShare", "Yahoo Finance", "Alpha Vantage", "Polygon"]
SENTIMENT_WARMUP_DAYS = 260
HOTSPOT_DAILY_WARMUP_DAYS = 260
HOTSPOT_INTRADAY_WARMUP_DAYS = 120
HOTSPOT_MAX_DISPLAY_SNAPSHOTS = 720
HOTSPOT_WORKBENCH_PROFILES = {
    "快速预览": {
        "max_snapshots": 96,
        "object_limit": 12,
        "description": "默认模式，限制对象和切片数量，适合日常快速判断热点结构。",
    },
    "标准分析": {
        "max_snapshots": 240,
        "object_limit": 24,
        "description": "保留更多时间切片，适合盘中或盘后复核。",
    },
    "完整复盘": {
        "max_snapshots": HOTSPOT_MAX_DISPLAY_SNAPSHOTS,
        "object_limit": 60,
        "description": "尽量保留完整展示窗口，适合生成报告前复盘；运行会更慢。",
    },
}
SCAN_BUILT_IN_STRATEGY_IDS = {"ma_crossover", "rsi_reversion", "bollinger_reversion", "breakout"}
SCAN_DATA_OPTIONS = [option for option in DATA_OPTIONS if option != "CSV"]


def _operational_store() -> OperationalStore:
    store = OperationalStore()
    store.initialize()
    return store


def _load_private_reviewed_rows(ledger: str) -> list[dict]:
    try:
        return load_private_reviewed_input_entries(_operational_store(), ledger=ledger)
    except Exception:
        return []


def _append_private_reviewed_row(ledger: str, entry: dict, *, entry_id_key: str, as_of_key: str) -> dict:
    return append_private_reviewed_input_entry(
        _operational_store(),
        ledger=ledger,
        entry=entry,
        entry_id_key=entry_id_key,
        as_of_key=as_of_key,
    )


def _private_reviewed_output_dir(ledger: str) -> Path:
    return private_reviewed_input_output_dir(ledger)


def _private_runtime_upload_path(content: bytes, *, suffix: str = ".csv") -> Path:
    digest = hashlib.sha256(content).hexdigest()[:16]
    clean_suffix = suffix if suffix.startswith(".") and len(suffix) <= 12 else ".csv"
    return default_data_home() / "runtime" / "uploads" / f"market_bars_{digest}{clean_suffix}"


VIEW_OPTIONS = {
    "command": "总控驾驶舱",
    "cashflow": "现金流",
    "policy": "政策雷达",
    "consumption": "消费守卫",
    "single": "单标的回测",
    "sentiment": "情绪分析",
    "hotspots": "热点分析",
    "market_feel": "盘感训练",
    "holdings": "持仓",
    "reports": "报告中心",
    "industry": "行研报告",
    "research_bus": "研究总线",
    "big_data": "大数据模拟",
    "profile": "个人画像",
    "scan": "参数扫描",
    "portfolio": "组合轮动",
    "tools": "数据中心",
    "library": "策略库",
}

ACTIVE_PFI_VIEW_OPTIONS = {
    "command": "首页｜总控驾驶舱",
    "hotspots": "市场｜热点分析",
    "sentiment": "市场｜情绪分析",
    "policy": "研究｜政策雷达",
    "reports": "研究｜报告中心",
    "holdings": "持仓｜持仓复核",
    "profile": "持仓｜个人画像",
    "single": "策略实验室｜单标的回测",
    "scan": "策略实验室｜参数扫描",
    "market_feel": "策略实验室｜盘感训练",
    "library": "策略实验室｜策略库",
    "big_data": "数据与系统｜模拟实验",
    "tools": "数据与系统｜数据中心",
}

PFI_PRIMARY_NAV_LABELS = ("首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察")

TERM_HELP = {
    "数据源": "行情数据来源。真实研究优先使用已配置并可验证的数据源；Sample 只用于演示和功能检查。",
    "市场": "研究对象所属市场。CN 表示 A 股/中国内地相关标的，US 表示美股，HK 表示港股。",
    "对象来源": "分析对象来自默认大盘列表、当前持仓或手动输入的自选代码，可多选并自动去重。",
    "分析范围": "热点分析对象池。大盘热点用于市场横向结构，我的持仓用于组合相关对象，自选代码用于临时观察。",
    "时间粒度": "每根 K 线或数据 bar 覆盖的时间长度。60min 表示小时级，1d 表示日线。",
    "情绪分": "0-100 的技术状态摘要，综合短期涨跌、趋势、RSI、波动和回撤；只用于研究观察。",
    "偏热比例": "偏热或过热对象占成功计算对象的比例。比例高说明短期拥挤可能扩散。",
    "偏冷比例": "偏冷或极度低迷对象占成功计算对象的比例。比例高说明风险释放或趋势走弱更集中。",
    "热点热度": "页面默认显示平滑热度：先计算每个时间切片的即时技术热度，再用最近数个切片平滑。不同时间切片本身会变化，但同一切片不应因展示窗口改变而重算。",
    "即时热度": "单一时间切片的原始技术热度，结合近1期、近5期、近20期涨跌、RSI、波动和回撤；它可以快速变化。",
    "平滑热度": "对即时热度做短窗口平滑后的默认展示口径，并限制单个切片的显示跳变，更适合判断热点是否持续，不适合当作交易指令。",
    "热度变化": "当前平滑热度相对上一时间切片的变化。变化过大时优先检查数据源、时间粒度和异常行情。",
    "热点状态": "把热点热度翻译成强势扩散、局部偏强、中性轮动、局部偏弱或风险降温。",
    "时间切片": "选定某一个小时或日期，只观察该时点的横向热点结构。拖动它可以看热点如何变化。",
    "领先板块": "当前时间切片平均热点热度最高的板块或资产类别。",
    "失败对象": "因为代码、数据源权限、样本长度或网络问题未能成功计算的对象。",
    "热力图": "按对象和板块展示热点热度。红色偏强，绿色偏弱，白色接近中性。",
    "气泡图": "横轴看近1期涨跌，纵轴看近5期涨跌，气泡大小代表波动和异动程度。",
    "RSI14": "14 期相对强弱指标。高于 70 往往代表短期拥挤，低于 30 往往代表短期低迷。",
    "VIX": "美股波动率指数。通常 VIX 上升代表风险情绪升温，不等同于股票上涨。",
    "MA20": "20 期移动平均线，用于观察短期趋势基准。",
    "MA60": "60 期移动平均线，用于观察中期趋势基准。",
    "MACD": "动能指标，用于观察短中期趋势差和动能变化。",
    "Bollinger": "布林带，观察价格相对近期波动区间的位置。",
    "ATR14": "14 期平均真实波幅，用于衡量短期波动和交易噪声。",
    "最大回撤": "从阶段高点到后续低点的最大跌幅，用于衡量风险压力。",
    "盘感分": "0-100 的技术结构训练分，综合趋势、动能、支撑压力、风险和量价确认；不是涨跌预测。",
    "训练难度": "入门只判断方向；中等判断方向和收益区间；专家还要填写更精确的累计涨跌幅。",
    "判断周期": "答案区间覆盖的未来交易日数量。系统先隐藏这段未来数据，提交后再揭示。",
    "限时秒数": "盘感训练答题时间。页面会实时倒计时；提交时按开始时间和提交时间记录是否超时。",
    "收益区间判断": "判断答案周期内累计涨跌幅落在哪个区间，不是判断单日涨跌。",
    "预计区间涨跌幅": "专家模式填写的答案周期累计涨跌幅百分比。例如上涨 2.35% 填 2.35。",
    "20日支撑": "最近 20 个 bar 的低点区域，用于观察价格离近期需求区有多远。",
    "20日压力": "最近 20 个 bar 的高点区域，用于观察价格离近期供给区有多远。",
    "成交量比": "当前成交量相对近 20 期均量的比例，用于判断价格变化是否得到量能确认。",
    "证据闸门": "把数据源、失败率、样本长度、最新日期和情绪集中度拆成检查项；不通过时只作观察，不进入交易前参考。",
    "样本点": "用于计算指标的有效行情 bar 数量。样本太少时，RSI、波动率、回撤和趋势判断都不稳定。",
    "失败率": "未成功计算对象占全部请求对象的比例。失败率高说明数据源、代码或权限存在问题，需要先修正。",
    "数据新鲜度": "本次结果中最新行情日期。日期明显滞后时，情绪结论不能代表当前市场状态。",
    "情绪集中度": "偏热或偏冷对象是否集中出现。集中度过高代表环境可能拥挤或压力扩散，需要更严格复核。",
    "热点证据闸门": "热点分析专用验收表，检查数据源、对象覆盖、失败率、样本长度、时间切片、刷新粒度和热度集中度。",
    "数据覆盖率": "成功生成结果的对象占全部请求对象的比例。覆盖率低时，横向强弱对比会失真。",
    "刷新粒度": "热点时间轴相邻切片的典型间隔。60min 模式应接近小时级；间隔过大时只能按低频观察。",
    "热度集中度": "偏强或偏弱对象占成功对象的最高比例。过高说明市场可能单边拥挤或风险集中。",
    "热点工作台模式": "控制热点分析默认计算规模。快速预览限制对象和切片数量，标准分析适合盘中复核，完整复盘适合报告前使用。",
    "热点运行摘要": "热点按钮生成后的 compact 运行摘要，用于确认对象覆盖、切片数量、缓存 TTL 和证据状态，不重复保存原始行情明细。",
    "52ETF公开参考": "读取 52ETF 大盘云图公开页面的板块和交互提示，只作为市场云图参考，不作为行情、回测或交易证据。",
    "52ETF热点对照": "把 52ETF 公开 A 股云图板块与 PFI 当前热点对象做只读覆盖对照，用于检查 UI 和对象池，不作为交易信号。",
    "自定义时间查看": "输入日期、时间片段或完整时间戳，系统会自动定位到最接近的可用时间切片。",
    "热点扩散": "平均热度上升且偏强对象增加，代表横向强势从少数对象向更多对象扩散。",
    "强弱分化": "同一时间切片内偏强和偏弱对象同时存在，代表市场内部差异较大，需要分板块复核。",
    "研究观察": "系统只输出证据、解释和风险复核方向，不输出实盘买卖、下单或仓位指令。",
    "指标预热窗口": "系统会自动向展示开始日期之前多取历史数据，用于稳定 RSI、均线、波动和回撤等指标。",
    "展示窗口": "你在页面上选择要查看的日期范围。结束日期覆盖当天全天；展示窗口改变时，不应改变同一目标时间切片的指标计算历史。",
    "参数扫描": "用同一数据、同一成本假设批量测试多组参数，观察收益、回撤、Sharpe 和稳定性，不是寻找保证赚钱的参数。",
    "参数网格": "每一行用 参数名=值1,值2,值3。系统会组合所有参数值逐一回测，组合太多会变慢。",
    "Train-Test 验证": "先用训练期挑参数，再在测试期检验同一参数是否延续，帮助识别过拟合。",
    "Walk-Forward 验证": "用多个滚动训练/测试窗口重复检验参数，观察参数是否在不同市场阶段仍然有效。",
    "人工价值录入": "由用户手工登记真实收入、节省成本、避免损失、资产复用价值和证据链接；系统不会自动编造金额。",
    "复核状态": "PendingReview 表示待复核，Reviewed 表示可纳入已量化统计，Rejected 表示证据不足或口径不成立。",
    "价值状态": "只有已复核且存在真实金额字段的记录才会成为 Quantified；其他记录只保留为待复核证据。",
    "现金流": "公司经营现金进入和流出的证据化记录，用于判断 runway、固定支出压力、应收应付和短期现金安全。",
    "BalanceSnapshot": "人工录入的某日现金余额快照，必须附上银行截图、账本或其他可复核证据；系统不会连接银行账户。",
    "Runway": "按最近支出速度估算当前现金余额还能覆盖多少天，只是经营安全指标，不是融资或付款建议。",
    "应收应付": "Receivable 表示预计收入但尚未到账，Payable 表示预计支出但尚未支付；两者不等同于真实现金流。",
    "政策雷达": "把政策来源、影响行业、机会类型、影响评分和下一步行动放入可复核台账；不自动抓取或宣称实时覆盖。",
    "政策来源权威": "Official、Regulator、Government 或 Exchange 且有来源证据时才可进入 Actionable；新闻和手工来源必须回溯官方来源。",
    "影响评分": "按来源权威、相关性、紧急度和可执行性加权得到 0-100 的优先级分，不是收益预测或政策合规意见。",
    "政策机会状态": "Actionable 代表可进入人工机会复核队列；Watch/Observe 只作观察；NeedsEvidence 表示缺少权威来源或证据。",
    "消费守卫": "把消费事件、账单证据、冲动风险、固定成本和可投资现金流压力放到同一张可复核台账里。",
    "冲动风险": "综合冲动分、后悔分、必要性和是否计划消费得到的行为风险，不是医学或财务诊断。",
    "可投资现金流压力": "非必要和冲动消费占月可投资预算的比例，用来判断消费是否正在挤压投资现金流。",
    "固定成本": "周期性订阅、房租、水电、债务等重复支出，需要定期复核是否仍有必要。",
}


def term_badge(term: str, label: str | None = None) -> str:
    """Return an HTML badge with a native hover tooltip for key UI terms."""

    detail = TERM_HELP.get(term, "")
    safe_label = _escape_html(label or term)
    safe_detail = _escape_html(detail or term)
    return f'<span class="ql-term-inline" title="{safe_detail}">{safe_label}</span>'


def hotspot_workbench_profile(mode: str) -> dict[str, object]:
    profile = HOTSPOT_WORKBENCH_PROFILES.get(mode) or HOTSPOT_WORKBENCH_PROFILES["快速预览"]
    return dict(profile)


def limit_hotspot_instruments(
    instruments: list[SentimentInstrument],
    object_limit: int,
) -> tuple[list[SentimentInstrument], int]:
    if object_limit <= 0 or len(instruments) <= object_limit:
        return instruments, 0
    return instruments[:object_limit], len(instruments) - object_limit


def hotspot_quick_preflight(
    *,
    workbench_mode: str,
    requested_count: int,
    active_count: int,
    skipped_count: int,
    max_snapshots: int,
    request_cache_status: dict[str, object],
    directory_summary: dict[str, object],
    data_source: str,
    interval: str,
) -> dict[str, object]:
    cache_state = str(request_cache_status.get("state", "miss"))
    cache_hit = cache_state == "hit"
    estimated_cells = max(0, int(active_count)) * max(0, int(max_snapshots))
    provider_requests = 0 if cache_hit else max(0, int(active_count))
    if active_count <= 0:
        status = "NeedsInput"
        label = "需要选择对象"
        next_action = "先选择大盘热点、持仓对象或自选代码。"
    elif cache_hit:
        status = "CacheHit"
        label = "可复用缓存"
        next_action = "点击生成会优先读取本地派生缓存，通常不重新请求行情。"
    elif estimated_cells >= 6000 or workbench_mode == "完整复盘":
        status = "LargeRun"
        label = "可能较慢"
        next_action = "如只做日常观察，建议先切回快速预览；报告前复盘再使用完整复盘。"
    else:
        status = "Ready"
        label = "可快速生成"
        next_action = "当前规模适合直接生成；生成后先看热点运行摘要和证据闸门。"
    return {
        "schema": "PFIOSHotspotQuickPreflightV1",
        "status": status,
        "label": label,
        "workbench_mode": workbench_mode,
        "data_source": data_source,
        "interval": interval,
        "requested_count": int(requested_count),
        "active_count": int(active_count),
        "skipped_count": int(skipped_count),
        "max_snapshots": int(max_snapshots),
        "estimated_cells": int(estimated_cells),
        "expected_provider_requests": int(provider_requests),
        "cache_state": cache_state,
        "cache_hit": cache_hit,
        "cache_remaining_seconds": request_cache_status.get("remaining_seconds"),
        "cache_file_count": int(directory_summary.get("file_count", 0) or 0),
        "cache_total_kb": float(directory_summary.get("total_kb", 0.0) or 0.0),
        "next_action": next_action,
        "token_policy": "Preflight uses only selected objects, mode limits, and cache metadata; it does not load market bars or compute hotspot history.",
        "safety_boundary": "Read-only UI guidance; no market refresh, broker calls, orders, payments, or holdings mutation.",
    }


RESEARCH_CHART_MODEBAR_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "pfi_os_research_chart",
        "height": 720,
        "width": 1280,
        "scale": 2,
    },
}


def research_chart_config(filename: str = "pfi_os_research_chart") -> dict[str, object]:
    config = dict(RESEARCH_CHART_MODEBAR_CONFIG)
    image_options = dict(RESEARCH_CHART_MODEBAR_CONFIG["toImageButtonOptions"])
    image_options["filename"] = filename
    config["toImageButtonOptions"] = image_options
    return config


def apply_research_chart_ux(
    fig,
    *,
    height: int,
    hovermode: str = "x unified",
    dragmode: str = "pan",
    x_range_slider: bool = False,
    x_range_selector: bool = False,
):
    fig.update_layout(
        height=height,
        hovermode=hovermode,
        dragmode=dragmode,
        uirevision="pfi_os_research_chart_v1",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    xaxis_updates = {
        "showline": True,
        "linecolor": "#cbd5e1",
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikedash": "dot",
        "spikethickness": 1,
        "fixedrange": False,
    }
    if x_range_slider:
        xaxis_updates["rangeslider"] = {"visible": True}
    if x_range_selector:
        xaxis_updates["rangeselector"] = {
            "buttons": [
                {"count": 6, "label": "近6期", "step": "hour", "stepmode": "backward"},
                {"count": 24, "label": "近24期", "step": "hour", "stepmode": "backward"},
                {"count": 7, "label": "近7天", "step": "day", "stepmode": "backward"},
                {"step": "all", "label": "全部"},
            ]
        }
    fig.update_xaxes(**xaxis_updates)
    fig.update_yaxes(
        showline=True,
        linecolor="#cbd5e1",
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikethickness=1,
        fixedrange=False,
    )
    return fig

CUSTOM_LOGIC_OPTIONS = {
    "mean_reversion": ("均值回归", "Mean Reversion"),
    "trend_following": ("趋势跟随", "Trend Following"),
    "breakout": ("突破", "Breakout"),
    "momentum_rotation": ("动量轮动", "Momentum Rotation"),
}

CUSTOM_INDICATOR_OPTIONS = {
    "moving_average": ("均线", "Moving Average"),
    "rsi": ("RSI", "RSI"),
    "bollinger": ("布林带", "Bollinger Bands"),
    "breakout_channel": ("突破通道", "Breakout Channel"),
    "momentum": ("动量", "Momentum"),
    "volume_filter": ("成交量过滤", "Volume Filter"),
    "atr_risk": ("ATR 风险控制", "ATR Risk Control"),
}

RETURN_SOURCE_EN = {
    "风险溢价": "Risk Premium",
    "行为偏差": "Behavioral Bias",
    "信息优势": "Information Advantage",
    "结构性约束": "Structural Constraint",
    "执行优势": "Execution Advantage",
    "组合优势": "Portfolio Advantage",
}


def single_strategy_options() -> dict[str, dict[str, object]]:
    options: dict[str, dict[str, object]] = built_in_strategy_options()
    registry = StrategyApprovalRegistry()
    for spec in load_custom_strategy_specs():
        strategy = CustomNoCodeStrategy(spec)
        status = "已确认" if registry.is_approved(strategy) else "待确认"
        label = f"自定义：{spec.display_name} [{status}]"
        options[label] = {"kind": "custom", "spec": spec, "status": status}
    return options


def built_in_strategy_options(order_path=None) -> dict[str, dict[str, object]]:
    options: dict[str, dict[str, object]] = {}
    for strategy_id in ordered_strategy_ids(order_path) if order_path is not None else ordered_strategy_ids():
        factory = BUILT_IN_STRATEGY_FACTORIES.get(strategy_id)
        if factory is None:
            continue
        label = built_in_strategy_label(strategy_id)
        if label in options:
            label = f"{label} ({strategy_id})"
        options[label] = {"kind": "built_in", "factory": factory, "strategy_id": strategy_id}
    return options


def parameter_scan_strategy_options(strategy_options: dict[str, dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    source = strategy_options or single_strategy_options()
    registry = StrategyApprovalRegistry()
    options: dict[str, dict[str, object]] = {}
    for label, option in source.items():
        if option.get("kind") == "built_in" and option.get("strategy_id") in SCAN_BUILT_IN_STRATEGY_IDS:
            options[label] = option
        elif option.get("kind") == "custom":
            strategy = CustomNoCodeStrategy(option["spec"])
            if registry.is_approved(strategy):
                options[label] = option
    return options


def scan_strategy_id(option: dict[str, object]) -> str:
    if option.get("kind") == "custom":
        return str(option["spec"].strategy_id)
    return str(option.get("strategy_id", "strategy"))


def default_parameter_grid_text(option: dict[str, object]) -> str:
    if option.get("kind") == "custom":
        spec = option["spec"]
        example = _first_custom_scan_parameter(spec)
        lines = [
            "weight=0.50,0.75,1.00",
            "# 自定义策略可覆盖策略库参数，格式：indicator.parameter=值1,值2",
        ]
        if example:
            lines.append(f"# 示例：{example}")
        return "\n".join(lines)
    strategy_id = str(option.get("strategy_id", "ma_crossover"))
    if strategy_id == "ma_crossover":
        return "short_window=10,20,30\nlong_window=60,90,120"
    if strategy_id == "rsi_reversion":
        return "window=10,14,20\nentry=25,30,35\nexit=50,55,60"
    if strategy_id == "bollinger_reversion":
        return "window=15,20,30\nnum_std=1.50,2.00,2.50\nexit_z=-0.50,0.00,0.50"
    if strategy_id == "breakout":
        return "lookback=40,55,80\nexit_lookback=10,20,30"
    return ""


def parse_parameter_grid_text(text: str) -> dict[str, list[object]]:
    grid: dict[str, list[object]] = {}
    for line_number, raw_line in enumerate(str(text).splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"第 {line_number} 行缺少 '='。")
        key, raw_values = line.split("=", 1)
        key = key.strip()
        values = [_parse_scan_value(item) for item in raw_values.split(",") if item.strip()]
        if not key:
            raise ValueError(f"第 {line_number} 行参数名为空。")
        if not values:
            raise ValueError(f"第 {line_number} 行没有参数值。")
        if key in grid:
            raise ValueError(f"参数重复：{key}")
        grid[key] = values
    if not grid:
        raise ValueError("参数网格不能为空。")
    return grid


def clean_scan_param_grid(strategy_id: str, param_grid: dict[str, list[object]]) -> dict[str, list[object]]:
    cleaned = {key: list(values) for key, values in param_grid.items()}
    if strategy_id == "ma_crossover" and {"short_window", "long_window"}.issubset(cleaned):
        short_values = [int(value) for value in cleaned["short_window"]]
        long_values = [int(value) for value in cleaned["long_window"]]
        valid_long_values = [value for value in long_values if all(short < value for short in short_values)]
        if not valid_long_values:
            raise ValueError("MA 参数无效：所有 long_window 都必须大于 short_window。")
        cleaned["short_window"] = short_values
        cleaned["long_window"] = valid_long_values
    return cleaned


def parameter_grid_run_count(param_grid: dict[str, list[object]]) -> int:
    count = 1
    for values in param_grid.values():
        count *= max(len(values), 1)
    return count


def parameter_scan_preflight(
    *,
    strategy_id: str,
    strategy_kind: str,
    param_grid: dict[str, list[object]],
    max_runs: int,
    symbol_valid: bool = True,
    grid_error: str = "",
    data_source: str = "",
    interval: str = "",
) -> dict[str, object]:
    run_count = parameter_grid_run_count(param_grid) if param_grid else 0
    max_run_count = max(1, int(max_runs))
    if not symbol_valid:
        status = "Blocked"
        label = "标的无效"
        next_action = "先修正市场和标的代码，再运行参数扫描。"
    elif grid_error:
        status = "InvalidGrid"
        label = "网格需修正"
        next_action = f"先修正参数网格：{grid_error}"
    elif run_count <= 0:
        status = "InvalidGrid"
        label = "没有组合"
        next_action = "参数网格为空，先填写至少一个参数和值。"
    elif run_count > max_run_count:
        status = "TooMany"
        label = "组合过多"
        next_action = f"当前 {run_count} 组超过上限 {max_run_count}；先缩小网格或明确提高上限。"
    elif run_count >= max(12, int(max_run_count * 0.8)):
        status = "LargeRun"
        label = "接近上限"
        next_action = "建议先缩小网格做快速筛选；确认稳定区域后再扩大扫描。"
    else:
        status = "Ready"
        label = "可以运行"
        next_action = "当前规模适合运行；结果仍需看稳定性、Train-Test、Walk-Forward 和交易摩擦。"
    return {
        "schema": "PFIOSParameterScanPreflightV1",
        "status": status,
        "label": label,
        "strategy_id": str(strategy_id),
        "strategy_kind": str(strategy_kind),
        "data_source": str(data_source),
        "interval": str(interval),
        "parameter_count": len(param_grid),
        "run_count": int(run_count),
        "max_runs": int(max_run_count),
        "usage_ratio": round(float(run_count) / float(max_run_count), 4) if max_run_count else 0.0,
        "symbol_valid": bool(symbol_valid),
        "grid_error": str(grid_error),
        "next_action": next_action,
        "token_policy": "Preflight parses parameter grid and selection metadata only; it does not load market bars, run backtests, or generate reports.",
        "safety_boundary": "Research planning only; no market refresh, broker calls, orders, payments, or holdings mutation.",
    }


def make_scan_strategy_factory(option: dict[str, object], config: BacktestConfig):
    if option.get("kind") == "custom":
        spec = option["spec"]
        strategy = CustomNoCodeStrategy(spec)
        StrategyApprovalRegistry().require_approved(strategy)
        return _custom_scan_strategy_factory(spec)
    strategy_id = str(option.get("strategy_id", ""))
    factory = option["factory"]
    if strategy_id in {"alipay", "alipay_enhanced"}:
        return lambda **params: factory(**{**params, "initial_cash": config.initial_cash})
    return factory


def _custom_scan_strategy_factory(spec):
    def factory(**params):
        payload = spec.to_dict()
        settings = json.loads(json.dumps(payload.get("settings", {})))
        weight = float(params.pop("weight", 1.0))
        for key, value in params.items():
            if "." not in key:
                raise ValueError(f"自定义策略参数必须使用 indicator.parameter 格式：{key}")
            indicator_key, setting_key = key.split(".", 1)
            if indicator_key not in settings or setting_key not in settings[indicator_key]:
                raise ValueError(f"自定义策略不存在参数：{key}")
            original = settings[indicator_key][setting_key]
            settings[indicator_key][setting_key] = int(value) if isinstance(original, int) and not isinstance(original, bool) else float(value)
        payload["settings"] = settings
        return CustomNoCodeStrategy(payload, weight=weight)

    factory.strategy_id = spec.strategy_id
    factory.__name__ = f"{spec.strategy_id}_scan_factory"
    return factory


def _first_custom_scan_parameter(spec) -> str:
    for indicator_key, values in spec.settings.items():
        for setting_key, value in values.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if isinstance(value, int):
                    choices = sorted({max(1, value - 5), value, value + 5})
                else:
                    choices = sorted({round(max(0.0, value * 0.8), 4), round(value, 4), round(value * 1.2, 4)})
                return f"{indicator_key}.{setting_key}=" + ",".join(str(choice) for choice in choices)
    return ""


def _parse_scan_value(value: str) -> object:
    text = value.strip()
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(char in text for char in [".", "e", "E"]):
            return float(text)
        return int(text)
    except ValueError:
        return text


def built_in_strategy_label(strategy_id: str) -> str:
    profile = get_strategy_profile(strategy_id)
    if strategy_id == "ma_crossover":
        return profile.display_name if "MA" in profile.display_name.upper() else f"{profile.display_name} MA"
    if strategy_id == "rsi_reversion":
        return profile.display_name if "RSI" in profile.display_name.upper() else f"RSI {profile.display_name}"
    return profile.display_name


STRATEGY_OPTIONS = {
    label: option["factory"]
    for label, option in built_in_strategy_options().items()
}


def make_single_strategy(strategy_name: str, params: dict, options: dict[str, dict[str, object]]):
    option = options[strategy_name]
    if option["kind"] == "custom":
        return CustomNoCodeStrategy(option["spec"])
    return option["factory"](**params)


def strategy_needs_initial_cash(strategy_name: str, strategy_options: dict[str, dict[str, object]]) -> bool:
    return strategy_options.get(strategy_name, {}).get("strategy_id") in {"alipay", "alipay_enhanced"}


def run_backtest_for_strategy(
    data: pd.DataFrame,
    config: BacktestConfig,
    strategy_name: str,
    params: dict,
    strategy_options: dict[str, dict[str, object]],
):
    strategy_params_for_run = {**params, "initial_cash": config.initial_cash} if strategy_needs_initial_cash(strategy_name, strategy_options) else params
    strategy = make_single_strategy(strategy_name, strategy_params_for_run, strategy_options)
    return BacktestEngine(config).run(data, strategy)


def _pfi_ui_v2_enabled() -> bool:
    env_enabled = os.environ.get("PFI_UI_V2", "1") != "0"
    if not env_enabled:
        return False
    try:
        return st.query_params.get("pfi_legacy", "0") not in {"1", "true", "yes"}
    except Exception:
        return True


def _pfi_web_shell_html(home_summary: dict | None = None) -> str:
    try:
        from pfi_v02.stage_v021_runtime_api import ensure_v021_runtime_api_server

        runtime_api_base_url = ensure_v021_runtime_api_server()
    except Exception:
        runtime_api_base_url = "http://127.0.0.1:8766"
    shell_path = ROOT / "web" / "index.html"
    css_path = ROOT / "web" / "styles" / "tokens.css"
    js_path = ROOT / "web" / "app" / "shell.js"
    shell_html = shell_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")
    summary_payload = home_summary if isinstance(home_summary, dict) else empty_homepage_summary()
    summary_json = json.dumps(summary_payload, ensure_ascii=False).replace("</", "<\\/")
    runtime_json = json.dumps({"apiBaseUrl": runtime_api_base_url}, ensure_ascii=False).replace("</", "<\\/")
    shell_html = shell_html.replace('<link rel="stylesheet" href="./styles/tokens.css" />', f"<style>{css}</style>")
    shell_html = re.sub(
        r'<script type="application/json" id="pfi-runtime-config">.*?</script>',
        f'<script type="application/json" id="pfi-runtime-config">{runtime_json}</script>',
        shell_html,
        flags=re.DOTALL,
    )
    shell_html = re.sub(
        r'<script type="application/json" id="pfi-home-summary">.*?</script>',
        f'<script type="application/json" id="pfi-home-summary">{summary_json}</script>',
        shell_html,
        flags=re.DOTALL,
    )
    shell_html = shell_html.replace('<script src="./app/shell.js"></script>', f"<script>{js}</script>")
    return shell_html


def _render_html_frame(markup: str, *, height: int, width: object = None, scrolling: bool = False) -> None:
    components.html(markup, height=height, width=width, scrolling=scrolling)


def _render_pfi_native_shell_style() -> None:
    st.markdown(
        """
        <style>
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"] {
            background: #06111f !important;
        }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        header[data-testid="stHeader"],
        .stDeployButton {
            display: none !important;
        }
        .block-container {
            max-width: none !important;
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-bottom: 24px !important;
        }
        iframe {
            display: block;
            border: 0 !important;
        }
        [data-testid="stFileUploader"] {
            margin-top: 12px;
            padding: 16px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(102, 242, 221, 0.12), rgba(145, 197, 255, 0.08));
        }
        [data-testid="stFileUploader"] label {
            color: #f4f9ff !important;
            font-weight: 800 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            min-height: 148px;
            position: relative;
            overflow: hidden;
            border: 1px dashed rgba(102, 242, 221, 0.58) !important;
            border-radius: 8px !important;
            background: rgba(255, 255, 255, 0.06) !important;
        }
        [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"],
        [data-testid="stFileUploaderDropzoneInstructions"],
        [data-testid="stFileUploaderDropzone"] small {
            display: none !important;
        }
        [data-testid="stFileUploaderDropzone"]::before {
            content: "拖拽 CSV / ZIP 到这里";
            position: absolute;
            left: 24px;
            top: 28px;
            color: #f4f9ff;
            font-size: 18px;
            font-weight: 900;
        }
        [data-testid="stFileUploaderDropzone"]::after {
            content: "单文件上限 200MB · 支持 CSV、ZIP · 原始数据只写入本机私有账本";
            position: absolute;
            left: 24px;
            top: 62px;
            right: 24px;
            color: #a9bbcf;
            font-size: 13px;
            line-height: 1.5;
        }
        [data-testid="stFileUploaderDropzone"] button {
            position: absolute !important;
            right: 24px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            min-width: 112px !important;
            border-radius: 8px !important;
            border-color: rgba(102, 242, 221, 0.44) !important;
            background: linear-gradient(135deg, #66f2dd, #91c5ff) !important;
            color: #06111f !important;
            font-size: 0 !important;
            font-weight: 900 !important;
        }
        [data-testid="stFileUploaderDropzone"] button::after {
            content: "选择文件";
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_streamlit_upload_localizer() -> None:
    components.html(
        """
        <script>
        (() => {
          const parentDoc = window.parent && window.parent.document;
          if (!parentDoc) return;
          const dragText = ["Drag", "and drop files here"].join(" ");
          const browseText = ["Browse", "files"].join(" ");
          const limitPrefix = ["Limit", "200MB per file"].join(" ");
          const replacements = new Map([
            [dragText, "拖拽 CSV / ZIP 到这里"],
            [browseText, "选择文件"],
          ]);

          function localizeUploader() {
            parentDoc.querySelectorAll('[data-testid="stFileUploaderDropzone"]').forEach((dropzone) => {
              dropzone.setAttribute("aria-label", "选择支付宝原始账单 CSV 或 ZIP");
              dropzone.querySelectorAll("span, small, button").forEach((node) => {
                const text = (node.textContent || "").trim();
                if (replacements.has(text)) {
                  node.textContent = replacements.get(text);
                } else if (text.startsWith(limitPrefix)) {
                  node.textContent = "单文件上限 200MB · 支持 CSV、ZIP";
                }
              });
            });
          }

          localizeUploader();
          new MutationObserver(localizeUploader).observe(parentDoc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_pfi_local_data_upload_panel() -> None:
    st.markdown("## PFI 本机数据上传")
    st.caption("先把支付宝、微信、银行等原始账单导入本机私有目录，再进入账本、消费、投资和报告；按本轮授权同步备份到 GitHub 顶层 MetaDatabase。")
    latest = st.session_state.get("pfi_latest_alipay_import_manifest") or _load_existing_alipay_import_manifest()
    if latest:
        _render_alipay_import_summary(latest, title="当前 PFI 私有账本")
        st.caption("最近一次导入记录：已保存在本机私有数据目录，可由开发验收工具读取。")
        st.divider()

    uploaded_files = st.file_uploader(
        "上传支付宝原始账单 CSV / ZIP",
        type=["csv", "zip"],
        accept_multiple_files=True,
        key="pfi_alipay_bill_upload_v1",
        help="支持支付宝导出的带说明区 CSV，也支持包含 CSV 的 ZIP。可一次选择多份年度账单。",
    )
    _render_streamlit_upload_localizer()
    if uploaded_files:
        payloads = tuple((file.name, file.getvalue()) for file in uploaded_files)
        preview = build_alipay_import_preview(payloads)
        _render_alipay_import_summary(preview.as_dict(), title="上传预检结果")
        if st.button("保存上传账单到 PFI 私有账本", type="primary", key="save_uploaded_alipay_bills"):
            manifest = write_private_alipay_import(payloads, default_data_home())
            st.session_state["pfi_latest_alipay_import_manifest"] = manifest
            st.success("已保存到 PFI 私有数据目录，并同步到 MetaDatabase，标准化流水已生成。")
            _render_alipay_import_summary(manifest, title="已保存导入结果")

    discovered = discover_local_alipay_raw_files()
    if discovered:
        st.divider()
        st.markdown("### 已找到旧支付宝原始账单")
        st.caption("这些文件来自之前交接目录。点击按钮会复制到 PFI 本机私有上传目录，同步到 `MetaDatabase/PFI/alipay_daily`，并生成私有账本预览。")
        if latest:
            st.success("旧支付宝原始账单已经接入当前 PFI 私有账本；需要重建时可点击下方按钮。")
        elif st.button("预检已发现的旧支付宝账单", key="preview_discovered_alipay_bills"):
            discovered_preview = build_alipay_import_preview(payloads_from_paths(discovered))
            _render_alipay_import_summary(discovered_preview.as_dict(), title="旧数据预检结果")
        st.markdown("#### 查看已发现文件")
        st.dataframe(
            pd.DataFrame({"文件": [path.name for path in discovered], "本机路径": [str(path) for path in discovered]}),
            use_container_width=True,
            hide_index=True,
        )
        if st.button("接入已发现的支付宝三年原始账单", type="primary", key="import_discovered_alipay_bills"):
            manifest = write_private_alipay_import(payloads_from_paths(discovered), default_data_home())
            st.session_state["pfi_latest_alipay_import_manifest"] = manifest
            st.success("已接入旧支付宝原始账单，当前 PFI 私有账本和 MetaDatabase 备份已生成。")
            _render_alipay_import_summary(manifest, title="已接入旧数据")
    else:
        st.info("当前没有在历史交接目录发现支付宝原始账单；可以直接用上方上传控件导入。")


def _load_existing_alipay_import_manifest() -> dict | None:
    manifest_path = default_data_home() / "runtime" / "imports" / "alipay_daily" / "alipay_import_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _render_alipay_import_summary(summary: dict, *, title: str) -> None:
    st.markdown(f"#### {title}")
    cols = st.columns(6)
    cols[0].metric("文件", f"{summary.get('valid_file_count', 0)}/{summary.get('file_count', 0)}")
    cols[1].metric("原始记录", int(summary.get("raw_record_count", 0)))
    cols[2].metric("标准流水", int(summary.get("transaction_count", 0)))
    cols[3].metric("待复核", int(summary.get("review_count", 0)))
    cols[4].metric("起始", summary.get("date_start") or "待识别")
    cols[5].metric("结束", summary.get("date_end") or "待识别")

    file_summaries = summary.get("file_summaries") or []
    if file_summaries:
        file_summary_frame = pd.DataFrame(file_summaries)
        if "status" in file_summary_frame.columns:
            file_summary_frame["status"] = file_summary_frame["status"].map(
                lambda value: ALIPAY_IMPORT_STATUS_LABELS.get(str(value), str(value) or "待识别")
            )
        columns = [
            column
            for column in [
                "file_name",
                "status",
                "raw_record_count",
                "transaction_count",
                "review_count",
                "date_start",
                "date_end",
                "error",
            ]
            if column in file_summary_frame.columns
        ]
        st.dataframe(
            file_summary_frame[columns].rename(
                columns={
                    "file_name": "文件",
                    "status": "状态",
                    "raw_record_count": "原始记录",
                    "transaction_count": "标准流水",
                    "review_count": "待复核",
                    "date_start": "起始",
                    "date_end": "结束",
                    "error": "错误",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    if summary.get("private_transactions_path"):
        st.caption("标准化流水状态")
        st.success("已生成标准化流水，并保存在本机 PFI 私有数据目录。")


def install_streamlit_runtime_compat() -> None:
    marker = "_pfi_runtime_compat_installed"
    if getattr(st, "__dict__", {}).get(marker):
        return
    try:
        original_dataframe = st.dataframe
        original_plotly_chart = st.plotly_chart
    except Exception:
        return

    def dataframe_compat(*args, **kwargs):
        if kwargs.get("width") == "stretch":
            kwargs.pop("width")
            kwargs.setdefault("use_container_width", True)
        return original_dataframe(*args, **kwargs)

    def plotly_chart_compat(*args, **kwargs):
        if kwargs.get("width") == "stretch":
            kwargs.pop("width")
            kwargs.setdefault("use_container_width", True)
        return original_plotly_chart(*args, **kwargs)

    st.dataframe = dataframe_compat
    st.plotly_chart = plotly_chart_compat
    setattr(st, marker, True)


def _pfi_segmented_control(label: str, options: list[str], *, default: str, key: str) -> str:
    control = getattr(st, "segmented_control", None)
    if callable(control):
        return control(label, options, default=default, key=key)
    index = options.index(default) if default in options else 0
    return st.radio(label, options, index=index, key=key, horizontal=True)


def render_pfi_ui_v2_shell() -> None:
    _render_pfi_native_shell_style()
    store = OperationalStore()
    try:
        store.initialize()
        ingest_command_center_cache(store, project_root=ROOT)
        home_summary = build_homepage_summary(store)
    except Exception:
        home_summary = empty_homepage_summary()
    _render_html_frame(_pfi_web_shell_html(home_summary), height=1120, scrolling=True)
    st.markdown(
        """
        <section style="padding:0 24px 24px;color:#f5f9ff;">
          <div style="max-width:1200px;margin:0 auto 12px;padding:16px 18px;border:1px solid rgba(255,255,255,.14);border-radius:8px;background:rgba(255,255,255,.06);">
            <strong>本机真实上传与支付宝账本</strong>
            <span style="display:block;margin-top:6px;color:#a9bbcf;">这是本机原生上传能力，负责把真实 CSV / ZIP 写入 PFI 私有账本；上方工作台负责日常导航、预览和反馈。</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_pfi_local_data_upload_panel()


def main() -> None:
    st.set_page_config(page_title=MASTER_DISPLAY_NAME, page_icon=None, layout="wide", initial_sidebar_state="expanded")
    install_streamlit_runtime_compat()
    if _pfi_ui_v2_enabled():
        render_pfi_ui_v2_shell()
        return

    install_shutdown_heartbeat()
    apply_theme()
    workspace_header()
    selected_view = navigation_view()
    sidebar_usage_guide(selected_view)

    if selected_view == "command":
        executive_command_center_view()
    elif selected_view == "cashflow":
        cashflow_view()
    elif selected_view == "policy":
        policy_radar_view()
    elif selected_view == "consumption":
        consumption_guard_view()
    elif selected_view == "single":
        single_backtest_view()
    elif selected_view == "sentiment":
        sentiment_analysis_view()
    elif selected_view == "hotspots":
        market_hotspots_view()
    elif selected_view == "market_feel":
        market_feel_training_view()
    elif selected_view == "holdings":
        holdings_view()
    elif selected_view == "reports":
        report_center_view()
    elif selected_view == "industry":
        industry_research_view()
    elif selected_view == "research_bus":
        research_bus_monitor_view()
    elif selected_view == "big_data":
        big_data_simulation_view()
    elif selected_view == "profile":
        personal_profile_view()
    elif selected_view == "scan":
        parameter_scan_view()
    elif selected_view == "portfolio":
        portfolio_rotation_view()
    elif selected_view == "tools":
        data_tools_view()
    elif selected_view == "library":
        strategy_library_view()
    if selected_view in {"command", "tools"}:
        system_status_panel()


def install_shutdown_heartbeat() -> None:
    heartbeat_url = _safe_heartbeat_url(os.getenv("PFI_HEARTBEAT_URL", "").strip())
    if not heartbeat_url:
        return
    _render_html_frame(
        f"""
        <script>
        const heartbeatUrl = {json.dumps(heartbeat_url)};
        async function sendHeartbeat() {{
          try {{
            await fetch(heartbeatUrl, {{ method: "POST", mode: "no-cors", keepalive: true }});
          }} catch (e) {{}}
        }}
        sendHeartbeat();
        setInterval(sendHeartbeat, 3000);
        window.addEventListener("pagehide", sendHeartbeat);
        </script>
        """,
        height=0,
        width=0,
    )


def _safe_heartbeat_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme != "http":
        return ""
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        return ""
    return value


def render_auto_refresh_component(ttl_seconds: int) -> None:
    _render_html_frame(_auto_refresh_component_html(ttl_seconds), height=46, width=None)


def _auto_refresh_component_html(ttl_seconds: int) -> str:
    safe_ttl = max(60, int(ttl_seconds))
    safe_minutes = safe_ttl // 60
    return f"""
    <div id="ql-auto-refresh" role="timer" aria-live="polite" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#475467; font-size:13px;">
      1 小时缓存刷新规则：页面保持打开时自动倒计时，约 <strong>{safe_minutes}</strong> 分钟后刷新当前页。
      <br>
      距离下次刷新：<strong id="ql-auto-refresh-remaining">{safe_ttl}</strong> 秒
    </div>
    <script>
    (function() {{
      const ttlSeconds = {safe_ttl};
      const startedAt = Date.now();
      const remainingNode = document.getElementById("ql-auto-refresh-remaining");
      function tick() {{
        const elapsed = Math.floor((Date.now() - startedAt) / 1000);
        const remaining = Math.max(0, ttlSeconds - elapsed);
        remainingNode.textContent = String(remaining);
        if (remaining <= 0) {{
          window.parent.location.reload();
        }}
      }}
      tick();
      setInterval(tick, 1000);
    }})();
    </script>
    """


def render_countdown_component(component_key: str, started_at: float, time_limit_seconds: int) -> None:
    _render_html_frame(_countdown_component_html(component_key, started_at, time_limit_seconds), height=86, width=None)


def _countdown_component_html(component_key: str, started_at: float, time_limit_seconds: int) -> str:
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "", component_key)[:40] or "timer"
    safe_started = float(started_at)
    safe_limit = max(1, int(time_limit_seconds))
    return f"""
    <div id="ql-countdown-{safe_key}" class="ql-countdown-box" style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;border:1px solid #d9dee7;border-radius:8px;padding:10px 12px;background:#fff;" role="timer" aria-live="polite">
      <div style="display:flex;justify-content:space-between;gap:12px;color:#172033;font-weight:700;">
        <span>自动倒计时</span>
        <span id="ql-countdown-label-{safe_key}">{safe_limit} 秒</span>
      </div>
      <div style="height:8px;background:#eef2f6;border-radius:999px;overflow:hidden;margin-top:10px;">
        <div id="ql-countdown-bar-{safe_key}" style="height:8px;width:100%;background:#0ea5e9;border-radius:999px;"></div>
      </div>
      <div id="ql-countdown-note-{safe_key}" style="margin-top:7px;color:#667085;font-size:12px;">计时器实时运行；归零后仍可提交，但系统会记录为超时。</div>
    </div>
    <script>
    (function() {{
      const startedAtMs = {safe_started * 1000.0:.3f};
      const limitSeconds = {safe_limit};
      const label = document.getElementById("ql-countdown-label-{safe_key}");
      const bar = document.getElementById("ql-countdown-bar-{safe_key}");
      const note = document.getElementById("ql-countdown-note-{safe_key}");
      function tick() {{
        const elapsed = Math.max(0, (Date.now() - startedAtMs) / 1000);
        const remaining = Math.max(0, limitSeconds - elapsed);
        const ratio = Math.max(0, Math.min(1, remaining / Math.max(1, limitSeconds)));
        label.textContent = remaining.toFixed(1) + " 秒";
        bar.style.width = (ratio * 100).toFixed(1) + "%";
        if (remaining <= 0) {{
          bar.style.background = "#b42318";
          note.textContent = "已超时。提交后会在成绩里记录超时，不会按未超时计算。";
        }} else if (remaining <= Math.max(5, limitSeconds * 0.25)) {{
          bar.style.background = "#d97706";
          note.textContent = "临近超时，请先提交你的独立判断。";
        }} else {{
          bar.style.background = "#0ea5e9";
          note.textContent = "计时器实时运行；归零后仍可提交，但系统会记录为超时。";
        }}
      }}
      tick();
      setInterval(tick, 100);
    }})();
    </script>
    """


def navigation_view() -> str:
    requested = st.query_params.get("view", "command")
    if requested not in ACTIVE_PFI_VIEW_OPTIONS:
        requested = "command"
    keys = list(ACTIVE_PFI_VIEW_OPTIONS)
    with st.sidebar:
        st.markdown("### PFI V0.2 入口")
        st.caption("首页总览 / 账户与资产 / 账本流水 / 投资管理 / 消费管理 / 数据源与上传 / 建议与复盘 / 报告与洞察；旧研究和策略入口保持兼容。")
        selected_label = st.radio(
            "功能区",
            options=[ACTIVE_PFI_VIEW_OPTIONS[key] for key in keys],
            index=keys.index(requested),
            key="workspace_view",
            label_visibility="collapsed",
        )
    selected = next((key for key, label in ACTIVE_PFI_VIEW_OPTIONS.items() if label == selected_label), requested)
    st.query_params["view"] = selected
    return selected


def _view_key_from_target(target_en: str) -> str:
    normalized = target_en.lower()
    if "command" in normalized or "executive" in normalized:
        return "command"
    if "parameter" in normalized:
        return "scan"
    if "report" in normalized:
        return "reports"
    if "sentiment" in normalized or "emotion" in normalized:
        return "sentiment"
    if "feel" in normalized or "technical" in normalized or "indicator" in normalized:
        return "market_feel"
    if "holding" in normalized or "position" in normalized:
        return "holdings"
    if "industry" in normalized:
        return "industry"
    if "big" in normalized or "simulation" in normalized or "stress" in normalized:
        return "big_data"
    if "profile" in normalized:
        return "profile"
    if "library" in normalized:
        return "library"
    if "approval" in normalized:
        return "library"
    if "data" in normalized:
        return "tools"
    if "portfolio" in normalized:
        return "portfolio"
    return "single"


def executive_command_center_view() -> None:
    st.subheader("总控驾驶舱")
    st.caption("聚合就绪检查、总集成审计、现金流、政策、消费、最新报告和行动队列。仅用于研究管理，不连接实盘。")
    payload = _command_center_operational_payload()
    status = str(payload.get("command_status", "NeedsReview"))
    status_label = {
        "ReadyForResearch": "可继续研究",
        "NeedsReview": "需要复核",
        "Blocked": "阻断",
    }.get(status, status)
    action_count = len(payload.get("action_queue", []))
    latest_report = payload.get("latest_report", {})
    business_summary = payload.get("business_system_summary", [])
    business_review_count = sum(1 for row in business_summary if row.get("status") != "Pass")

    metric_cols = st.columns(5)
    metric_cols[0].metric("总控状态", status_label)
    metric_cols[1].metric("待处理事项", action_count)
    metric_cols[2].metric("子系统复核", business_review_count)
    metric_cols[3].metric("证据来源", len(payload.get("evidence_sources", [])))
    metric_cols[4].metric("最新报告", latest_report.get("name") or "缺失")

    st.info(str(payload.get("status_reason", "")))
    render_command_center_action_router(payload)
    scorecards = pd.DataFrame(payload.get("scorecards", []))
    if not scorecards.empty:
        st.markdown("#### 核心状态")
        st.dataframe(scorecards, use_container_width=True, hide_index=True)

    business_frame = pd.DataFrame(business_summary)
    if not business_frame.empty:
        st.markdown("#### 业务子系统")
        st.dataframe(business_frame, use_container_width=True, hide_index=True)

    left, right = st.columns([1.2, 1.0], gap="large")
    with left:
        st.markdown("#### 行动队列")
        actions = pd.DataFrame(payload.get("action_queue", []))
        if actions.empty:
            st.success("当前没有阻断项。")
        else:
            st.dataframe(actions, use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### 证据来源")
        evidence = pd.DataFrame(payload.get("evidence_sources", []))
        st.dataframe(evidence, use_container_width=True, hide_index=True)

    st.markdown("#### 风控闸门")
    gates = pd.DataFrame(payload.get("risk_gates", []))
    st.dataframe(gates, use_container_width=True, hide_index=True)

    if st.button("生成总控报告", type="primary", use_container_width=False):
        saved = write_command_center(project_root=ROOT, report_root=REPORT_ROOT_DIR, output_dir=ROOT / "data" / "commandCenter")
        st.success("已生成总控报告。")
        st.json(saved.get("outputs", {}), expanded=False)


def _command_center_operational_payload() -> dict:
    store = OperationalStore()
    try:
        store.initialize()
        ingest_command_center_cache(store, project_root=ROOT)
        return build_command_center_read_model(store)
    except Exception:
        return empty_command_center_read_model()


def render_command_center_action_router(payload: dict) -> None:
    router = command_center_next_actions(payload)
    st.markdown("#### 统一下一步")
    st.caption(str(router.get("token_policy", "")))
    cards = list(router.get("cards", []))
    card_cols = st.columns(len(cards))
    for column, card in zip(card_cols, cards):
        column.metric(str(card["label"]), card["value"], help=str(card["detail"]))
    rows = [row for row in router.get("rows", []) if isinstance(row, dict)]
    if not rows:
        st.info("暂无推荐下一步。")
    else:
        shortcut_cols = st.columns(min(4, len(rows)))
        for column, row in zip(shortcut_cols, rows[:4]):
            column.markdown(f"**{row.get('建议', '')}**")
            column.caption(f"{row.get('原因', '')} 先看：{row.get('先看检查点', '')}")
            column.link_button(f"打开{row.get('入口', '')}", str(row.get("链接", "")), use_container_width=True)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(str(router.get("safety_boundary", "")))


def _money_label(value: object) -> str:
    if value is None or value == "":
        return "缺失"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "缺失"


def _roi_label(value: object) -> str:
    if value is None or value == "":
        return "未量化"
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "未量化"


def _number_label(value: object) -> str:
    if value is None or value == "":
        return "缺失"
    try:
        return f"{float(value):,.1f}"
    except (TypeError, ValueError):
        return "缺失"


def cashflow_view() -> None:
    st.subheader("现金流")
    st.caption("Company CashFlow Command：录入、复核和导出公司经营现金流证据。所有金额必须来自人工证据，不连接银行或支付账户。")
    cashflow_entries = _load_private_reviewed_rows(CASHFLOW_LEDGER)
    payload = build_cashflow_command(project_root=ROOT, entries=cashflow_entries)
    runtime_summary = payload.get("runtime_summary") or build_cashflow_runtime_summary(payload)
    summary = payload.get("summary", {})

    metric_cols = st.columns(5)
    metric_cols[0].metric("现金流状态", str(payload.get("cashflow_status", "MissingBalance")))
    metric_cols[1].metric("最新余额", _money_label(summary.get("latest_balance")))
    metric_cols[2].metric("近30天净现金流", _money_label(summary.get("net_cashflow", 0.0)))
    metric_cols[3].metric("Runway天数", _number_label(summary.get("runway_days")))
    metric_cols[4].metric("待复核", int(summary.get("pending_review_records", 0) or 0))

    runtime_cols = st.columns(5)
    runtime_cols[0].metric("运行状态", str(runtime_summary.get("status", "Unknown")))
    runtime_cols[1].metric("计入记录", int(runtime_summary.get("counted_records", 0) or 0))
    runtime_cols[2].metric("缺证据", int(runtime_summary.get("reviewed_missing_evidence_records", 0) or 0))
    runtime_cols[3].metric("应收", _money_label(runtime_summary.get("receivable", 0.0)))
    runtime_cols[4].metric("应付", _money_label(runtime_summary.get("payable", 0.0)))

    with st.expander("运行摘要与证据闸门", expanded=True):
        st.caption(str(runtime_summary.get("token_policy", "")))
        gate_frame = pd.DataFrame(runtime_summary.get("evidence_gate", []))
        if gate_frame.empty:
            st.info("暂无现金流运行摘要。")
        else:
            st.dataframe(gate_frame, use_container_width=True, hide_index=True)
        st.caption(str(runtime_summary.get("safety_boundary", "")))

    st.markdown("#### 经营检查")
    action_queue = pd.DataFrame(payload.get("action_queue", []))
    if not action_queue.empty:
        st.dataframe(action_queue, use_container_width=True, hide_index=True)
    else:
        st.success("当前没有现金流行动项。")

    with st.expander("现金流口径", expanded=True):
        st.markdown(
            "- 只有 `review_status=Reviewed` 且 `evidence_status=Pass` 的记录会计入余额、收入、支出、应收、应付和 Runway。\n"
            "- `BalanceSnapshot` 是人工录入的余额证据，不是银行 API。\n"
            "- `Receivable` 和 `Payable` 只进入应收应付视图，不等同于已到账现金。\n"
            "- 页面不会付款、转账、连接银行、连接支付账户或修改真实账本。"
        )

    st.markdown("#### 录入现金流证据")
    with st.form("company_cashflow_entry"):
        top_cols = st.columns([1, 1, 1, 1])
        entry_date = top_cols[0].date_input("日期", value=pd.Timestamp.today().date(), key="cashflow_entry_date")
        direction = top_cols[1].selectbox("方向", list(CASHFLOW_DIRECTIONS), index=0, help=TERM_HELP["现金流"])
        category = top_cols[2].selectbox("分类", list(CASHFLOW_CATEGORIES), index=list(CASHFLOW_CATEGORIES).index("Other"))
        review_status = top_cols[3].selectbox("复核状态", ["PendingReview", "Reviewed", "Rejected"], index=0)
        amount_cols = st.columns([1, 1, 1])
        amount = amount_cols[0].number_input("金额", min_value=0.0, value=0.0, step=100.0)
        currency = amount_cols[1].text_input("币种", value="AUD", max_chars=8)
        recurring = amount_cols[2].checkbox("周期性", value=False)
        account = st.text_input("账户/钱包", placeholder="例如：Business account / Cash reserve")
        counterparty = st.text_input("交易对方", placeholder="客户、供应商、平台或税务机构")
        description = st.text_input("说明", placeholder="这笔现金流对应的业务事实")
        evidence_link = st.text_input("证据链接/说明", placeholder="发票、账单、银行截图、Notion 页或可复核说明")
        evidence_path = st.text_input("本地证据路径", placeholder="可选：截图、CSV、PDF、账本导出路径")
        notes = st.text_area("复核备注", placeholder="记录分类口径、税务口径、应收应付限制或待确认事项")
        submitted = st.form_submit_button("保存现金流证据", type="primary")
        if submitted:
            try:
                entry = create_cashflow_entry(
                    entry_date=entry_date.isoformat(),
                    direction=direction,
                    category=category,
                    amount=float(amount),
                    currency=currency,
                    account=account,
                    counterparty=counterparty,
                    description=description,
                    evidence_link=evidence_link,
                    evidence_path=evidence_path,
                    review_status=review_status,
                    recurring=bool(recurring),
                    notes=notes,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                _append_private_reviewed_row(CASHFLOW_LEDGER, entry, entry_id_key="entry_id", as_of_key="entry_date")
                st.success("已保存现金流证据。")
                st.json({"entry_id": entry["entry_id"], "review_status": entry["review_status"], "evidence_status": entry["evidence_status"]}, expanded=False)

    action_cols = st.columns([1, 2])
    if action_cols[0].button("生成现金流快照", type="primary"):
        saved = write_cashflow_command(
            project_root=ROOT,
            entries=_load_private_reviewed_rows(CASHFLOW_LEDGER),
            output_dir=_private_reviewed_output_dir(CASHFLOW_LEDGER),
        )
        action_cols[1].success("已生成 Company CashFlow Command 快照。")
        action_cols[1].json(saved.get("outputs", {}), expanded=False)

    category_totals = pd.DataFrame(payload.get("category_totals", []))
    if not category_totals.empty:
        st.markdown("#### 分类汇总")
        st.dataframe(category_totals, use_container_width=True, hide_index=True)

    entries = pd.DataFrame(_load_private_reviewed_rows(CASHFLOW_LEDGER))
    st.markdown("#### 现金流台账")
    if entries.empty:
        st.info("暂无现金流记录。建议先录入一条 Reviewed + evidence 的 BalanceSnapshot。")
    else:
        columns = ["entry_date", "direction", "category", "amount", "currency", "review_status", "evidence_status", "counterparty", "description", "next_action"]
        st.dataframe(entries[[column for column in columns if column in entries.columns]], use_container_width=True, hide_index=True)


def policy_radar_view() -> None:
    st.subheader("政策雷达")
    st.caption("Policy Intelligence Radar：登记政策来源、影响行业、机会类型、影响评分和人工行动队列。缺少权威来源时 fail-closed。")
    policy_opportunities = _load_private_reviewed_rows(POLICY_LEDGER)
    payload = build_policy_radar(project_root=ROOT, opportunities=policy_opportunities)
    summary = payload.get("summary", {})
    runtime_summary = payload.get("runtime_summary") or build_policy_runtime_summary(payload)

    metric_cols = st.columns(5)
    metric_cols[0].metric("政策状态", str(payload.get("policy_status", "MissingPolicyEvidence")))
    metric_cols[1].metric("机会数量", int(payload.get("opportunity_count", 0) or 0))
    metric_cols[2].metric("Actionable", int(summary.get("actionable_count", 0) or 0))
    metric_cols[3].metric("Watch", int(summary.get("watch_count", 0) or 0))
    metric_cols[4].metric("缺证据", int(summary.get("missing_evidence_count", 0) or 0))

    runtime_cols = st.columns(5)
    runtime_cols[0].metric("运行状态", str(runtime_summary.get("status", "Unknown")))
    runtime_cols[1].metric("权威来源", int(runtime_summary.get("authoritative_source_records", 0) or 0))
    runtime_cols[2].metric("待溯源", int(runtime_summary.get("needs_authority_review_records", 0) or 0))
    runtime_cols[3].metric("待复核", int(runtime_summary.get("pending_review_count", 0) or 0))
    runtime_cols[4].metric("最高影响分", float(runtime_summary.get("max_impact_score", 0.0) or 0.0))

    with st.expander("运行摘要与证据闸门", expanded=True):
        st.caption(str(runtime_summary.get("token_policy", "")))
        gate_frame = pd.DataFrame(runtime_summary.get("evidence_gate", []))
        if gate_frame.empty:
            st.info("暂无政策运行摘要。")
        else:
            st.dataframe(gate_frame, use_container_width=True, hide_index=True)
        st.caption(str(runtime_summary.get("safety_boundary", "")))

    with st.expander("政策雷达口径", expanded=True):
        st.markdown(
            "- 只有 `Reviewed`、权威来源类型、并带 `source_url` 或 `evidence_path` 的机会才可能进入 `Actionable`。\n"
            "- `Research`、`News`、`Manual` 来源只能作为 Watch/Observe 线索，必须回溯官方、监管、政府或交易所来源。\n"
            "- 影响评分用于排序，不代表政策确定落地、补贴可得、合规意见或投资收益。\n"
            "- 页面不抓取实时政策、不提交申请、不登录政府平台、不生成交易动作。"
        )

    st.markdown("#### 行动队列")
    action_queue = pd.DataFrame(payload.get("action_queue", []))
    if action_queue.empty:
        st.success("当前没有政策行动项。")
    else:
        st.dataframe(action_queue, use_container_width=True, hide_index=True)

    st.markdown("#### 录入政策机会")
    with st.form("policy_radar_entry"):
        top_cols = st.columns([1, 1, 1, 1])
        published_date = top_cols[0].date_input("发布日期", value=pd.Timestamp.today().date(), key="policy_published_date")
        source_type = top_cols[1].selectbox("来源类型", list(POLICY_SOURCE_TYPES), index=0, help=TERM_HELP["政策来源权威"])
        policy_level = top_cols[2].selectbox("政策层级", list(POLICY_LEVELS), index=list(POLICY_LEVELS).index("Unknown"))
        review_status = top_cols[3].selectbox("复核状态", ["PendingReview", "Reviewed", "Rejected"], index=0, key="policy_review_status")
        title = st.text_input("政策标题", placeholder="政策、通知、办法或公开文件标题")
        source_name = st.text_input("来源名称", placeholder="政府部门、监管机构、交易所、研究机构或新闻来源")
        source_url = st.text_input("来源URL", placeholder="官方页面、监管公告、交易所公告或政策 PDF URL")
        evidence_path = st.text_input("本地证据路径", placeholder="可选：PDF、截图、政策系统报告或来源登记文件")
        detail_cols = st.columns([1, 1, 1])
        jurisdiction = detail_cols[0].text_input("地区/辖区", value="Unknown")
        opportunity_type = detail_cols[1].selectbox("机会类型", list(POLICY_OPPORTUNITY_TYPES), index=list(POLICY_OPPORTUNITY_TYPES).index("Other"))
        sectors = detail_cols[2].text_input("影响行业", placeholder="AI, 半导体, 能源")
        affected_entities = st.text_input("影响对象", placeholder="公司、产业链、客户、资产类别或项目")
        impact_summary = st.text_area("影响摘要", placeholder="政策可能改变什么，影响路径是什么，限制条件是什么")
        required_action = st.text_input("下一步行动", placeholder="例如：核验资格、找原文、拆验证任务、跟踪截止日期")
        score_cols = st.columns(4)
        authority_score = score_cols[0].slider("权威分", 0, 100, 0, help=TERM_HELP["政策来源权威"])
        relevance_score = score_cols[1].slider("相关分", 0, 100, 0)
        urgency_score = score_cols[2].slider("紧急分", 0, 100, 0)
        feasibility_score = score_cols[3].slider("可执行分", 0, 100, 0)
        notes = st.text_area("备注", placeholder="记录证据缺口、反方观点、适用限制或等待事项")
        submitted = st.form_submit_button("保存政策机会", type="primary")
        if submitted:
            try:
                entry = create_policy_opportunity(
                    published_date=published_date.isoformat(),
                    title=title,
                    source_name=source_name,
                    source_type=source_type,
                    source_url=source_url,
                    evidence_path=evidence_path,
                    jurisdiction=jurisdiction,
                    policy_level=policy_level,
                    opportunity_type=opportunity_type,
                    sectors=sectors,
                    affected_entities=affected_entities,
                    impact_summary=impact_summary,
                    required_action=required_action,
                    authority_score=float(authority_score),
                    relevance_score=float(relevance_score),
                    urgency_score=float(urgency_score),
                    feasibility_score=float(feasibility_score),
                    review_status=review_status,
                    notes=notes,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                _append_private_reviewed_row(POLICY_LEDGER, entry, entry_id_key="policy_id", as_of_key="published_date")
                st.success("已保存政策机会。")
                st.json({"policy_id": entry["policy_id"], "impact_score": entry["impact_score"], "opportunity_status": entry["opportunity_status"]}, expanded=False)

    action_cols = st.columns([1, 2])
    if action_cols[0].button("生成政策雷达快照", type="primary"):
        saved = write_policy_radar(
            project_root=ROOT,
            opportunities=_load_private_reviewed_rows(POLICY_LEDGER),
            output_dir=_private_reviewed_output_dir(POLICY_LEDGER),
        )
        action_cols[1].success("已生成 Policy Intelligence Radar 快照。")
        action_cols[1].json(saved.get("outputs", {}), expanded=False)

    sector_exposure = pd.DataFrame(payload.get("sector_exposure", []))
    if not sector_exposure.empty:
        st.markdown("#### 行业暴露")
        st.dataframe(sector_exposure, use_container_width=True, hide_index=True)

    st.markdown("#### 政策机会台账")
    opportunities = pd.DataFrame(_load_private_reviewed_rows(POLICY_LEDGER))
    if opportunities.empty:
        st.info("暂无政策机会。建议先录入一条带官方或监管来源的 PendingReview 记录。")
    else:
        columns = ["published_date", "title", "source_type", "evidence_status", "review_status", "sectors", "impact_score", "opportunity_status", "required_action", "next_action"]
        st.dataframe(opportunities[[column for column in columns if column in opportunities.columns]], use_container_width=True, hide_index=True)


def consumption_guard_view() -> None:
    st.subheader("消费守卫")
    st.caption("Consumption Guard：登记消费证据、识别冲动风险、固定成本和可投资现金流压力。不会连接支付宝、银行或支付账户。")
    budget = st.number_input("月可投资现金流预算", min_value=0.0, value=0.0, step=100.0, help=TERM_HELP["可投资现金流压力"])
    consumption_events = _load_private_reviewed_rows(CONSUMPTION_LEDGER)
    payload = build_consumption_guard(project_root=ROOT, events=consumption_events, monthly_investable_budget=float(budget))
    summary = payload.get("summary", {})
    runtime_summary = payload.get("runtime_summary") or build_consumption_runtime_summary(payload)

    metric_cols = st.columns(5)
    metric_cols[0].metric("守卫状态", str(payload.get("guard_status", "MissingConsumptionEvidence")))
    metric_cols[1].metric("计入支出", _money_label(summary.get("counted_spend", 0.0)))
    metric_cols[2].metric("冲动支出", _money_label(summary.get("impulse_spend", 0.0)))
    metric_cols[3].metric("固定成本", _money_label(summary.get("fixed_cost", 0.0)))
    pressure = summary.get("investable_cashflow_pressure")
    metric_cols[4].metric("现金流压力", "缺预算" if pressure is None else f"{float(pressure):.2%}")

    runtime_cols = st.columns(5)
    runtime_cols[0].metric("运行状态", str(runtime_summary.get("status", "Unknown")))
    runtime_cols[1].metric("计入记录", int(runtime_summary.get("counted_records", 0) or 0))
    runtime_cols[2].metric("缺证据", int(runtime_summary.get("reviewed_missing_evidence_records", 0) or 0))
    runtime_cols[3].metric("待复核", int(runtime_summary.get("pending_review_records", 0) or 0))
    runtime_cols[4].metric("高风险", int(runtime_summary.get("high_risk_event_count", 0) or 0))

    with st.expander("运行摘要与证据闸门", expanded=True):
        st.caption(str(runtime_summary.get("token_policy", "")))
        gate_frame = pd.DataFrame(runtime_summary.get("evidence_gate", []))
        if gate_frame.empty:
            st.info("暂无消费运行摘要。")
        else:
            st.dataframe(gate_frame, use_container_width=True, hide_index=True)
        st.caption(str(runtime_summary.get("safety_boundary", "")))

    with st.expander("消费守卫口径", expanded=True):
        st.markdown(
            "- 只有 `review_status=Reviewed` 且带 `evidence_link` 或 `evidence_path` 的消费事件才会进入支出、冲动风险、固定成本和压力汇总。\n"
            "- `PendingReview`、`Rejected` 或缺证据记录只保留在台账中，不污染指标。\n"
            "- 月可投资预算是你手工输入的计划值，不来自银行、工资、支付宝、税务或券商系统。\n"
            "- 页面不会付款、转账、下单、冻结账户或修改外部账本。"
        )

    st.markdown("#### 行动队列")
    actions = pd.DataFrame(payload.get("action_queue", []))
    if actions.empty:
        st.success("当前没有消费守卫行动项。")
    else:
        st.dataframe(actions, use_container_width=True, hide_index=True)

    st.markdown("#### 录入消费事件")
    with st.form("consumption_guard_event"):
        top_cols = st.columns([1, 1, 1, 1])
        event_date = top_cols[0].date_input("日期", value=pd.Timestamp.today().date(), key="consumption_event_date")
        event_type = top_cols[1].selectbox("事件类型", list(CONSUMPTION_EVENT_TYPES), index=list(CONSUMPTION_EVENT_TYPES).index("Discretionary"))
        category = top_cols[2].selectbox("分类", list(CONSUMPTION_CATEGORIES), index=list(CONSUMPTION_CATEGORIES).index("Other"))
        review_status = top_cols[3].selectbox("复核状态", ["PendingReview", "Reviewed", "Rejected"], index=0, key="consumption_review_status")
        amount_cols = st.columns([1, 1, 1, 1])
        amount = amount_cols[0].number_input("金额", min_value=0.0, value=0.0, step=10.0, key="consumption_amount")
        currency = amount_cols[1].text_input("币种", value="AUD", max_chars=8, key="consumption_currency")
        planned = amount_cols[2].checkbox("计划内", value=False, key="consumption_planned")
        recurring = amount_cols[3].checkbox("周期性", value=False, help=TERM_HELP["固定成本"], key="consumption_recurring")
        merchant = st.text_input("商户/对象", placeholder="商户、平台、服务或消费对象")
        payment_method = st.text_input("支付方式", placeholder="现金、信用卡、支付宝、银行卡等，仅作文本记录")
        score_cols = st.columns(3)
        necessity_score = score_cols[0].slider("必要性", 0, 100, 0)
        impulse_score = score_cols[1].slider("冲动分", 0, 100, 0, help=TERM_HELP["冲动风险"])
        regret_score = score_cols[2].slider("后悔分", 0, 100, 0)
        evidence_link = st.text_input("证据链接/说明", placeholder="账单、截图、导出 CSV、Notion 记录或可复核说明")
        evidence_path = st.text_input("本地证据路径", placeholder="可选：账单文件、截图、CSV、PDF")
        notes = st.text_area("复核备注", placeholder="记录触发场景、是否可避免、下次规则或预算影响")
        submitted = st.form_submit_button("保存消费事件", type="primary")
        if submitted:
            try:
                event = create_consumption_event(
                    event_date=event_date.isoformat(),
                    event_type=event_type,
                    category=category,
                    amount=float(amount),
                    currency=currency,
                    merchant=merchant,
                    payment_method=payment_method,
                    planned=bool(planned),
                    recurring=bool(recurring),
                    necessity_score=float(necessity_score),
                    impulse_score=float(impulse_score),
                    regret_score=float(regret_score),
                    evidence_link=evidence_link,
                    evidence_path=evidence_path,
                    review_status=review_status,
                    notes=notes,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                _append_private_reviewed_row(CONSUMPTION_LEDGER, event, entry_id_key="event_id", as_of_key="event_date")
                st.success("已保存消费事件。")
                st.json({"event_id": event["event_id"], "risk_score": event["risk_score"], "risk_level": event["risk_level"]}, expanded=False)

    action_cols = st.columns([1, 2])
    if action_cols[0].button("生成消费守卫快照", type="primary"):
        saved = write_consumption_guard(
            project_root=ROOT,
            events=_load_private_reviewed_rows(CONSUMPTION_LEDGER),
            output_dir=_private_reviewed_output_dir(CONSUMPTION_LEDGER),
            monthly_investable_budget=float(budget),
        )
        action_cols[1].success("已生成 Consumption Guard 快照。")
        action_cols[1].json(saved.get("outputs", {}), expanded=False)

    category_totals = pd.DataFrame(payload.get("category_totals", []))
    if not category_totals.empty:
        st.markdown("#### 分类汇总")
        st.dataframe(category_totals, use_container_width=True, hide_index=True)

    st.markdown("#### 消费事件台账")
    events = pd.DataFrame(_load_private_reviewed_rows(CONSUMPTION_LEDGER))
    if events.empty:
        st.info("暂无消费事件。建议先录入一条带账单证据的 PendingReview 记录。")
    else:
        columns = ["event_date", "event_type", "category", "amount", "risk_score", "risk_level", "review_status", "evidence_status", "merchant", "next_action"]
        st.dataframe(events[[column for column in columns if column in events.columns]], use_container_width=True, hide_index=True)


def sidebar_usage_guide(selected_view: str) -> None:
    sections = [section for section in usage_guide_sections() if section.target_key in ACTIVE_PFI_VIEW_OPTIONS]
    section_by_key = {section.target_key: section for section in sections}
    current = section_by_key.get(selected_view) or sections[0]
    with st.sidebar:
        st.divider()
        st.markdown("### 使用指导")
        st.caption("边看边操作；先按步骤做，再按检查点复核。术语旁有悬停说明。")
        labels = [section.title for section in sections]
        default_index = labels.index(current.title) if current.title in labels else 0
        selected_title = st.selectbox(
            "指导功能区",
            labels,
            index=default_index,
            key="sidebar_guide_section",
            help="切换这里不会改变主页面，只切换侧栏说明。",
        )
        section = next((item for item in sections if item.title == selected_title), current)
        shortest_steps = "".join(f"<li>{_escape_html(step)}</li>" for step in section.steps[:3])
        first_checks = "".join(f"<li>{_escape_html(item)}</li>" for item in section.checks[:2])
        st.markdown(f"#### {section.title}")
        st.markdown(
            f"""
            <div class="ql-sidebar-guide-card">
              <div class="ql-sidebar-guide-label">用途</div>
              <div>{_escape_html(section.purpose)}</div>
              <div class="ql-sidebar-guide-label">适用场景</div>
              <div>{_escape_html(section.best_for)}</div>
              <div class="ql-sidebar-guide-label">最短操作路径</div>
              <ol class="ql-sidebar-mini-list">{shortest_steps}</ol>
              <div class="ql-sidebar-guide-label">先看这两个检查点</div>
              <ul class="ql-sidebar-mini-list">{first_checks}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("手把手步骤", expanded=True):
            for index, step in enumerate(section.steps, start=1):
                st.markdown(f"{index}. {step}")
        with st.expander("关键检查点", expanded=False):
            for item in section.checks:
                st.markdown(f"- {item}")
        with st.expander("产出与保存", expanded=False):
            for item in section.outputs:
                st.markdown(f"- {item}")
        with st.expander("风险与处理", expanded=False):
            for item in section.risks:
                st.markdown(f"- {item}")
        with st.expander("常用术语悬停说明", expanded=False):
            for term, detail in TERM_HELP.items():
                st.markdown(f'<span class="ql-term" title="{_escape_html(detail)}">{_escape_html(term)}</span>', unsafe_allow_html=True)


def workspace_header() -> None:
    st.markdown(
        f"""
        <div class="ql-hero">
          <div>
            <div class="ql-eyebrow">本地优先 / 证据驱动 / 价值转化</div>
            <h1>{_escape_html(MASTER_SHORT_TITLE)}</h1>
            <p class="ql-hero-cn">PFI 是主入口；内置量化研究、策略回测和盘感训练能力，继续承接研究总线、持仓复核和跨系统证据流。</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def system_status_panel() -> None:
    checks = collect_health_checks()
    pass_count = sum(1 for check in checks if check.status == "Pass")
    review_count = sum(1 for check in checks if check.status == "Review")
    info_count = sum(1 for check in checks if check.status == "Info")
    summary_cn, summary_en = readiness_summary(pass_count, review_count, info_count)
    st.subheader("工作台状态")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2.2])
    col1.metric("正常", pass_count)
    col2.metric("需检查", review_count)
    col3.metric("提示", info_count)
    col4.info(summary_cn)
    with st.expander("系统自检", expanded=review_count > 0):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "项目": check.item_cn,
                        "状态": check.status,
                        "说明": check.detail_cn,
                    }
                    for check in checks
                ]
            ),
            width="stretch",
            hide_index=True,
        )
    render_workspace_shell_status()


def render_workspace_shell_status() -> None:
    try:
        shell = workspace_shell_summary(
            compact_workspace_system_payload(),
            registry=system_registry_frame(),
            state=research_bus_status_frame(),
        )
    except Exception as exc:
        st.warning(f"统一 Workspace 状态暂不可用：{exc}")
        return
    st.markdown("#### 统一 Workspace Shell")
    st.caption(shell["token_policy"])
    card_cols = st.columns(len(shell["cards"]))
    for column, card in zip(card_cols, shell["cards"]):
        column.metric(str(card["label"]), card["value"], help=str(card["detail"]))
    rows = pd.DataFrame(shell["rows"])
    if rows.empty:
        st.info("暂无 workspace 系统摘要。")
    else:
        st.dataframe(rows, width="stretch", hide_index=True)
    with st.expander("验收命令", expanded=False):
        st.code("\n".join(shell["commands"]))
    render_vectorized_research_panel()
    render_macos_lifecycle_panel()


def render_vectorized_research_panel() -> None:
    payload = _vectorized_research_operational_payload()
    summary = vectorized_research_shell_summary(payload)
    st.markdown("#### Vectorized Research")
    st.caption(summary["token_policy"])
    cols = st.columns(len(summary["cards"]))
    for column, card in zip(cols, summary["cards"]):
        column.metric(str(card["label"]), card["value"], help=str(card["detail"]))
    if summary["status"] == "Missing":
        st.info("尚未生成 Vectorized Research latest 产物。")
    else:
        st.caption(f"{summary['selected_symbol']} / {summary['strategy_id']} / {summary['window']}")
        rows = pd.DataFrame(summary["rows"])
        chart_rows = pd.DataFrame(summary["chart_rows"])
        if not chart_rows.empty and go is not None:
            fig = go.Figure()
            fig.add_bar(x=chart_rows["参数"], y=chart_rows["Sharpe"], name="Sharpe")
            fig.add_scatter(x=chart_rows["参数"], y=chart_rows["总收益%"], mode="lines+markers", name="总收益%")
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            apply_research_chart_ux(fig, height=280, hovermode="x unified", dragmode="pan")
            st.plotly_chart(fig, width="stretch", config=research_chart_config("pfi_os_vectorized_research"))
        if not rows.empty:
            st.dataframe(rows, width="stretch", hide_index=True)
    with st.expander("Vectorized 输出与命令", expanded=False):
        outputs = summary.get("outputs", {})
        if isinstance(outputs, dict) and outputs:
            st.code("\n".join(f"{key}: {value}" for key, value in outputs.items()), language="text")
        st.code("\n".join(summary["commands"]), language="text")
    st.caption(summary["safety_policy"])


def _vectorized_research_operational_payload() -> dict:
    # VectorizedResearch_latest.json is ingested into the Operational Store before UI reads it.
    store = OperationalStore()
    try:
        store.initialize()
        ingest_vectorized_research_cache(store, project_root=ROOT)
        return build_vectorized_research_read_model(store)
    except Exception:
        return empty_vectorized_research_read_model()


LIFECYCLE_SCRIPT_ALLOWLIST = {
    "scripts/statusPFI.sh": 8,
    "scripts/stopPFI.sh": 20,
    "scripts/macosAcceptance.sh": 70,
    "scripts/devReadyCheck.sh": 45,
    "scripts/cleanCache.sh": 60,
    "scripts/macosAppAcceptanceLite.sh": 30,
    "scripts/macosLifecycleReadiness.sh": 40,
}


def _macos_runtime_operational_payload() -> dict:
    # MacOSRuntimeAcceptance_latest.json is local-only raw evidence; the UI reads its sanitized Operational Store model.
    store = OperationalStore()
    try:
        store.initialize()
        ingest_macos_runtime_acceptance_cache(store, project_root=ROOT)
        return build_macos_runtime_acceptance_read_model(store)
    except Exception:
        return empty_macos_runtime_acceptance_read_model()


def render_macos_lifecycle_panel() -> None:
    runtime = _run_lifecycle_script("scripts/statusPFI.sh")
    is_running = "PFI 正在运行" in runtime["stdout"] or "PFIOS running:" in runtime["stdout"]
    lifecycle = macos_lifecycle_summary(is_running=is_running)
    st.markdown("#### macOS 生命周期")
    st.caption(lifecycle["safety_policy"])
    cols = st.columns(len(lifecycle["cards"]))
    for column, card in zip(cols, lifecycle["cards"]):
        column.metric(str(card["label"]), card["value"], help=str(card["detail"]))
    actions = pd.DataFrame(lifecycle["actions"])
    st.dataframe(
        actions[["动作", "命令", "enabled", "ui_mode", "禁用原因", "说明"]],
        width="stretch",
        hide_index=True,
    )
    with st.expander("本机 App 入口", expanded=False):
        st.code("\n".join(lifecycle["app_paths"]), language="text")
    with st.expander("生命周期命令", expanded=False):
        st.code("\n".join(str(item["命令"]) for item in lifecycle["actions"]), language="text")
    runtime_evidence = macos_runtime_evidence_summary(_macos_runtime_operational_payload())
    st.markdown("##### 运行时验收证据")
    st.caption(runtime_evidence["token_policy"])
    evidence_cols = st.columns(len(runtime_evidence["cards"]))
    for column, card in zip(evidence_cols, runtime_evidence["cards"]):
        column.metric(str(card["label"]), card["value"], help=str(card["detail"]))
    if runtime_evidence["rows"]:
        st.dataframe(pd.DataFrame(runtime_evidence["rows"]), width="stretch", hide_index=True)
    else:
        st.caption("没有失败检查记录；如果状态为 Missing，请在 Terminal 运行运行时验收命令生成 latest JSON。")
    with st.expander("运行时验收命令", expanded=False):
        st.code("\n".join(runtime_evidence["commands"]), language="text")
    st.caption(runtime_evidence["safety_policy"])
    cache_preview = build_cache_cleanup_report(ROOT, dry_run=True)
    st.caption(
        "缓存预览："
        f"{cache_preview['candidate_count']} 个候选路径，"
        f"{cache_preview['candidate_file_count']} 个文件，"
        f"{cache_preview['candidate_kb']} KB；仅覆盖 pycache、pytest/tool cache、.DS_Store 和根 data/cache 运行日志。"
    )
    control_cols = st.columns([1, 1, 1, 1, 1, 2])
    if control_cols[0].button("刷新状态", key="macos_lifecycle_status"):
        refreshed = _run_lifecycle_script("scripts/statusPFI.sh")
        st.code(_command_output(refreshed), language="text")
    confirm_stop = control_cols[1].checkbox("确认停止", value=False, key="macos_lifecycle_confirm_stop", disabled=not is_running)
    if control_cols[1].button("停止服务", key="macos_lifecycle_stop", disabled=not (is_running and confirm_stop)):
        result = _run_lifecycle_script("scripts/stopPFI.sh")
        st.code(_command_output(result), language="text")
        st.warning("如果当前页面断开，说明本地 Streamlit 服务已停止。重新打开 PFI app 即可启动。")
    confirm_clean = control_cols[2].checkbox("确认清理", value=False, key="macos_lifecycle_confirm_clean", disabled=is_running)
    if control_cols[2].button("清理缓存", key="macos_lifecycle_clean", disabled=is_running or not confirm_clean):
        result = _run_lifecycle_script("scripts/cleanCache.sh")
        st.code(_command_output(result), language="text")
    if control_cols[3].button("日常验收", key="macos_lifecycle_daily_acceptance"):
        result = _run_lifecycle_script("scripts/macosAcceptance.sh")
        st.code(_command_output(result), language="text")
    control_cols[4].info("优先使用日常验收；单项验收保留在高级入口。缓存清理会在服务运行时自动拒绝。")
    with st.expander("高级单项验收", expanded=False):
        advanced_cols = st.columns(3)
        if advanced_cols[0].button("开发检查", key="macos_lifecycle_dev_ready"):
            result = _run_lifecycle_script("scripts/devReadyCheck.sh")
            st.code(_command_output(result), language="text")
        if advanced_cols[1].button("轻量验收", key="macos_lifecycle_acceptance_lite"):
            result = _run_lifecycle_script("scripts/macosAppAcceptanceLite.sh")
            st.code(_command_output(result), language="text")
        if advanced_cols[2].button("生命周期验收", key="macos_lifecycle_readiness"):
            result = _run_lifecycle_script("scripts/macosLifecycleReadiness.sh")
            st.code(_command_output(result), language="text")


def _run_lifecycle_script(script_name: str) -> dict[str, object]:
    if script_name not in LIFECYCLE_SCRIPT_ALLOWLIST:
        return {"returncode": 2, "stdout": "", "stderr": f"Lifecycle script not allowed: {script_name}"}
    script_path = ROOT / script_name
    try:
        completed = subprocess.run(
            [str(script_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=LIFECYCLE_SCRIPT_ALLOWLIST[script_name],
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": "Lifecycle command timed out."}
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def _read_json_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _command_output(result: dict[str, object]) -> str:
    stdout = str(result.get("stdout", "") or "").strip()
    stderr = str(result.get("stderr", "") or "").strip()
    parts = [f"exit={result.get('returncode')}"]
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(stderr)
    return "\n".join(parts)


def single_backtest_view() -> None:
    st.subheader("单标的研究工作流")
    render_workflow_steps(single_backtest_steps())
    col_controls, col_body = st.columns([0.30, 0.70], gap="large")
    with col_controls:
        st.markdown("#### 1. 数据")
        data_mode = st.selectbox("数据源", DATA_OPTIONS, index=0, key="single_data")
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="single_market")
        symbol = symbol_search_input(market, default="AAPL", key_prefix="single")
        interval = st.selectbox("周期", INTERVAL_OPTIONS, index=5, key="single_interval")
        start = st.date_input("开始日期", value=pd.Timestamp("2020-01-01"), key="single_start")
        end = date_input_with_today("结束日期", key="single_end", default=pd.Timestamp("2024-12-31"))
        csv_file = st.file_uploader("CSV 行情", type=["csv"], key="single_csv") if data_mode == "CSV" else None
        st.markdown("#### 2. 运行模式")
        run_mode = _pfi_segmented_control("运行模式", ["单策略回测", "双策略对比"], default="单策略回测", key="single_run_mode")
        strategy_options = single_strategy_options()
        params: dict = {}
        params_a: dict = {}
        params_b: dict = {}
        strategy_name = ""
        strategy_a = ""
        strategy_b = ""
        if run_mode == "单策略回测":
            st.markdown("#### 3. 策略")
            strategy_name = st.selectbox("策略", list(strategy_options), index=0, key="single_strategy")
            with st.expander("策略参数", expanded=False):
                params = strategy_params(strategy_name, prefix="single", strategy_options=strategy_options)
        else:
            st.markdown("#### 3. 策略对比")
            option_names = list(strategy_options)
            default_b = 1 if len(option_names) > 1 else 0
            strategy_a = st.selectbox("策略一", option_names, index=0, key="compare_strategy_a")
            strategy_b = st.selectbox("策略二", option_names, index=default_b, key="compare_strategy_b")
            if strategy_a == strategy_b:
                st.warning("当前选择了同一策略，结果会完全或高度接近；建议选择两个不同策略。")
            with st.expander("策略一参数", expanded=False):
                params_a = strategy_params(strategy_a, prefix="compare_a", strategy_options=strategy_options)
            with st.expander("策略二参数", expanded=False):
                params_b = strategy_params(strategy_b, prefix="compare_b", strategy_options=strategy_options)
        with st.expander("成本和资金", expanded=False):
            config = backtest_config(prefix="single")
            st.caption("当前系统不支持做空；持仓权重会被限制在 0 到 100%。")
        run_label = "运行回测" if run_mode == "单策略回测" else "运行策略对比"
        run = st.button(run_label, type="primary")
        st.caption("建议先用默认参数跑通，再逐项调整。")

    with col_body:
        if not run:
            show_single_backtest_empty_state(run_mode)
            return
        if not st.session_state.get("single_symbol_valid", True):
            st.error("未找到匹配标的，已阻止回测。")
            return
        try:
            data, quality_path, quality = load_data(data_mode, csv_file, symbol, market, interval, start, end)
        except Exception as exc:
            st.error(f"数据获取失败：{exc}")
            return
        symbol_name = st.session_state.get("single_symbol_name", "")
        buy_hold = buy_and_hold_metrics(data, annualization=config.annualization)
        st.markdown(f"#### 目标标的：{symbol}" + (f" - {symbol_name}" if symbol_name else ""))
        if run_mode == "双策略对比":
            try:
                result_a = run_backtest_for_strategy(data, config, strategy_a, params_a, strategy_options)
                result_b = run_backtest_for_strategy(data, config, strategy_b, params_b, strategy_options)
            except PermissionError as exc:
                st.error(f"策略未确认，不能运行回测。请先到策略库确认当前版本和风险说明。\n\n{exc}")
                return
            except Exception as exc:
                st.error(f"策略对比失败：{exc}")
                return
            st.success("策略对比完成")
            show_strategy_comparison(result_a, result_b, data, buy_hold, strategy_a, strategy_b)
            with st.expander("策略一交易明细", expanded=False):
                show_tables(result_a)
            with st.expander("策略二交易明细", expanded=False):
                show_tables(result_b)
            return
        try:
            result = run_backtest_for_strategy(data, config, strategy_name, params, strategy_options)
        except PermissionError as exc:
            st.error(f"策略未确认，不能运行回测。请先到策略库确认当前版本和风险说明。\n\n{exc}")
            return
        except Exception as exc:
            st.error(f"回测失败：{exc}")
            return
        st.success("回测完成")
        cross_validation_result = st.session_state.get("latest_cross_validation_result")
        risk_gate = evaluate_research_risk_gates(
            metrics=result.metrics,
            data_quality_status=getattr(quality, "quality_status", None),
        )
        decision_quality = evaluate_decision_quality(
            result=result,
            risk_gate=risk_gate,
            data_quality_status=getattr(quality, "quality_status", None),
            cross_validation_status=getattr(cross_validation_result, "status", None),
        )
        show_result_judgement(result.metrics, buy_hold)
        show_decision_quality(decision_quality)
        show_metric_comparison_table(result.metrics, buy_hold)
        show_strategy_diagnostics(result)
        show_strategy_performance_chart(data, result, strategy_name)
        show_equity_friction_chart(result, data=data)
        show_bootstrap_robustness(result, target_return=buy_hold.get("buy_hold_total_return", 0.0))
        show_tables(result)
        from pfi_os.reports import export_backtest_docx

        report_path = export_backtest_docx(
            result,
            data_quality_report=quality,
            cross_validation_result=cross_validation_result,
        )
        show_output_paths(report_path, quality_path)


def render_workflow_steps(steps) -> None:
    cols = st.columns(len(steps))
    for index, (col, step) in enumerate(zip(cols, steps), start=1):
        with col:
            st.markdown(
                f"""
                <div class="ql-step">
                  <div class="ql-step-index">{index}</div>
                  <div class="ql-step-title">{step.step_cn}</div>
                  <div class="ql-step-body">{step.detail_cn}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def symbol_search_input(market: str, default: str, key_prefix: str) -> str:
    query = st.text_input("标的搜索", value=default, key=f"{key_prefix}_symbol_query")
    col_a, col_b = st.columns([0.42, 0.58])
    with col_a:
        search_clicked = st.button("联网搜索", key=f"{key_prefix}_symbol_search")
    if search_clicked and query.strip():
        results = search_symbols(query, market)
        st.session_state[f"{key_prefix}_symbol_results"] = results
        st.session_state[f"{key_prefix}_symbol_search_done"] = True
    results = st.session_state.get(f"{key_prefix}_symbol_results", [])
    if results:
        labels = [item.label() for item in results]
        with col_b:
            selected_label = st.selectbox("搜索结果", labels, key=f"{key_prefix}_symbol_select")
        selected = next((item.symbol for item in results if item.label() == selected_label), query)
        selected_name = next((item.name for item in results if item.label() == selected_label), "")
        st.session_state[f"{key_prefix}_symbol_name"] = selected_name
        st.session_state[f"{key_prefix}_symbol_valid"] = True
        st.caption("搜索会优先联网；失败时使用内置常见标的兜底。")
        return selected
    if st.session_state.get(f"{key_prefix}_symbol_search_done"):
        st.session_state[f"{key_prefix}_symbol_valid"] = False
        st.warning("未找到匹配标的，不能开始回测。")
        return query.strip()
    st.session_state[f"{key_prefix}_symbol_valid"] = True
    st.session_state[f"{key_prefix}_symbol_name"] = ""
    st.caption("可输入 A、1 等前缀或片段后点击搜索。")
    return query.strip() or default


def date_input_with_today(label: str, key: str, default) -> object:
    if key not in st.session_state:
        st.session_state[key] = pd.Timestamp(default).date()
    col_date, col_button = st.columns([0.68, 0.32])
    with col_button:
        if st.button("今天", key=f"{key}_today"):
            st.session_state[key] = pd.Timestamp.today().date()
            st.rerun()
    with col_date:
        return st.date_input(label, key=key)


def show_single_backtest_empty_state(run_mode: str = "单策略回测") -> None:
    action = "运行策略对比" if run_mode == "双策略对比" else "运行回测"
    st.info(f"按左侧步骤选择数据、模式和策略，然后点击「{action}」。")
    st.markdown(
        """
        <div class="ql-empty-panel">
          <strong>运行后你会看到</strong>
          <ul>
            <li>核心指标：总收益率、年化收益率、Sharpe、最大回撤、胜率、交易次数。</li>
            <li>图表：价格走势、买卖点、收益曲线、回撤曲线、交易摩擦。</li>
            <li>明细：交易、持仓和信号。</li>
            <li>文件：Word 研究报告和数据质量报告。</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_result_judgement(metrics: dict, buy_hold: dict[str, float]) -> None:
    st.markdown("#### 结果判读")
    cols = st.columns(3)
    for col, judgement in zip(cols, backtest_result_judgements(metrics, buy_hold)):
        with col:
            st.markdown(
                f"""
                <div class="ql-judgement ql-judgement-{judgement.status.lower()}">
                  <div class="ql-judgement-status">{judgement.status}</div>
                  <div class="ql-judgement-title">{judgement.title_cn}</div>
                  <div class="ql-judgement-body">{judgement.detail_cn}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_decision_quality(decision_quality) -> None:
    st.markdown("#### 决策质量门禁 Decision Quality Score")
    cols = st.columns(4)
    cols[0].metric("研究状态", decision_quality.status)
    cols[1].metric("质量分数", f"{decision_quality.score}/100")
    cols[2].metric("缺失证据", str(len(decision_quality.missing_evidence)))
    cols[3].metric("风险提示", str(len(decision_quality.warnings)))
    if decision_quality.status == "ContinueResearch":
        st.success("当前结果可继续研究，但仍不构成个人金融建议或真实操作指令。")
    elif decision_quality.status == "WatchOnly":
        st.info("当前结果仅适合作为观察线索，后续需要更多证据。")
    elif decision_quality.status == "NeedsMoreEvidence":
        st.warning("关键证据不足，只能用于研究复盘，不能升级为高置信参考。")
    else:
        st.error("风险门禁未通过，暂停使用该研究结论。")

    dimension_rows = [
        {
            "维度": item.label,
            "分数": item.score,
            "状态": item.status,
            "证据": item.evidence,
        }
        for item in decision_quality.dimensions
    ]
    st.dataframe(pd.DataFrame(dimension_rows), width="stretch", hide_index=True)

    exposure = decision_quality.simulated_exposure
    exposure_rows = [
        {"项目": "历史模拟增加暴露金额", "数值": _format_metric_value(exposure.get("simulated_exposure_increase_amount", 0.0), "currency")},
        {"项目": "历史模拟增加暴露比例", "数值": _format_metric_value(exposure.get("simulated_exposure_increase_ratio", 0.0), "percent")},
        {"项目": "历史模拟降低暴露金额", "数值": _format_metric_value(exposure.get("simulated_exposure_reduction_amount", 0.0), "currency")},
        {"项目": "历史模拟降低暴露比例", "数值": _format_metric_value(exposure.get("simulated_exposure_reduction_ratio", 0.0), "percent")},
        {"项目": "期末持仓金额", "数值": _format_metric_value(exposure.get("ending_position_value", 0.0), "currency")},
        {"项目": "期末持仓暴露比例", "数值": _format_metric_value(exposure.get("ending_exposure_ratio", 0.0), "percent")},
    ]
    with st.expander("历史模拟暴露统计", expanded=False):
        st.dataframe(pd.DataFrame(exposure_rows), width="stretch", hide_index=True)
        if decision_quality.missing_evidence:
            st.write("缺失证据")
            st.dataframe(pd.DataFrame({"项目": decision_quality.missing_evidence}), width="stretch", hide_index=True)
        if decision_quality.research_actions:
            st.write("下一步研究动作")
            st.dataframe(pd.DataFrame({"动作": decision_quality.research_actions}), width="stretch", hide_index=True)


def show_output_paths(report_path, quality_path: str) -> None:
    st.markdown("#### 输出文件")
    st.dataframe(
        pd.DataFrame(
            [
                {"文件": "Word 研究报告", "路径": str(report_path)},
                {"文件": "数据质量报告", "路径": str(quality_path)},
            ]
        ),
        width="stretch",
        hide_index=True,
    )


def portfolio_rotation_view() -> None:
    col_controls, col_body = st.columns([0.32, 0.68], gap="large")
    with col_controls:
        st.subheader("股票池")
        symbols_text = st.text_area("标的列表", value=", ".join(DEFAULT_US_ETF_UNIVERSE.symbols), height=88)
        symbols = [s.strip().upper() for s in symbols_text.split(",") if s.strip()]
        data_mode = st.selectbox("数据源", ["Sample", "Moomoo", "Yahoo Finance", "AKShare", "TuShare", "Alpha Vantage", "Polygon"], index=0, key="portfolio_data")
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="portfolio_market")
        start = st.date_input("开始日期", value=pd.Timestamp("2020-01-01"), key="portfolio_start")
        end = date_input_with_today("结束日期", key="portfolio_end", default=pd.Timestamp("2024-12-31"))
        lookback = st.number_input("动量回看", min_value=20, value=126, step=10)
        top_n = st.number_input("持有数量 Top N", min_value=1, max_value=max(len(symbols), 1), value=min(2, max(len(symbols), 1)), step=1)
        config = backtest_config(prefix="portfolio")
        run = st.button("运行组合轮动", type="primary")

    with col_body:
        if not run:
            st.info("运行多标的动量轮动组合回测。")
            return
        try:
            data, quality_paths = load_universe_data(data_mode, symbols, market, "1d", start, end)
        except Exception as exc:
            st.error(f"数据获取失败：{exc}")
            return
        strategy = MomentumRotationStrategy(lookback=int(lookback), top_n=int(top_n))
        result = PortfolioBacktestEngine(config).run(data, strategy)
        show_metrics(result.metrics)
        show_equity_friction_chart(result)
        show_portfolio_attribution(result)
        show_portfolio_risk_view(result)
        show_tables(result)
        st.caption("数据质量报告：" + ", ".join(str(path) for path in quality_paths))


def parameter_scan_view() -> None:
    col_controls, col_body = st.columns([0.32, 0.68], gap="large")
    with col_controls:
        st.subheader("参数扫描工作台")
        st.caption("先用小网格找稳定区域，再看样本外和滚动验证；不要只挑最高收益的单点参数。")
        data_mode = st.selectbox("数据源", SCAN_DATA_OPTIONS, index=0, key="scan_data")
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="scan_market")
        symbol = symbol_search_input(market, default="AAPL", key_prefix="scan")
        interval = st.selectbox("周期", ["1d", "1w", "1m"], index=0, key="scan_interval")
        start = st.date_input("开始日期", value=pd.Timestamp("2020-01-01"), key="scan_start")
        end = date_input_with_today("结束日期", key="scan_end", default=pd.Timestamp("2024-12-31"))
        scan_options = parameter_scan_strategy_options()
        if not scan_options:
            st.error("当前没有可扫描策略。请先在策略库确认至少一个自定义策略，或恢复内置策略配置。")
            return
        strategy_name = st.selectbox("策略", list(scan_options), index=0, key="scan_strategy")
        strategy_option = scan_options[strategy_name]
        strategy_id = scan_strategy_id(strategy_option)
        st.caption("未确认的自定义策略不会出现在这里；请先到策略库补全档案和确认状态。")
        grid_text = st.text_area(
            "参数网格",
            value=default_parameter_grid_text(strategy_option),
            height=130,
            key=f"scan_grid_{strategy_id}",
            help=TERM_HELP["参数网格"],
        )
        max_runs = st.number_input("最大组合数", min_value=1, max_value=200, value=36, step=1, key="scan_max_runs")
        config = backtest_config(prefix="scan")
        run = st.button("运行参数扫描", type="primary")

    with col_body:
        st.markdown("#### 扫描目的")
        st.info("参数扫描用于判断策略是否存在一片相对稳定的可用参数区域。结果仍需结合交易成本、最大回撤、Train-Test 和 Walk-Forward 验证。")
        param_grid: dict[str, list[object]] = {}
        grid_error = ""
        try:
            param_grid = clean_scan_param_grid(strategy_id, parse_parameter_grid_text(grid_text))
        except Exception as exc:
            grid_error = str(exc)
        preflight = parameter_scan_preflight(
            strategy_id=strategy_id,
            strategy_kind=str(strategy_option.get("kind", "")),
            param_grid=param_grid,
            max_runs=int(max_runs),
            symbol_valid=bool(st.session_state.get("scan_symbol_valid", True)),
            grid_error=grid_error,
            data_source=data_mode,
            interval=interval,
        )
        render_parameter_scan_preflight(preflight, param_grid)
        if not run:
            if param_grid:
                st.markdown("#### 当前参数网格")
                st.dataframe(pd.DataFrame([{"参数": key, "候选值": ", ".join(map(str, values))} for key, values in param_grid.items()]), width="stretch", hide_index=True)
            else:
                st.warning(f"参数网格需要修正：{grid_error}")
            parameter_scan_terms_panel()
            return
        if not st.session_state.get("scan_symbol_valid", True):
            st.error("未找到匹配标的，已阻止参数扫描。")
            return
        if grid_error:
            st.error(f"参数网格无效：{grid_error}")
            return
        run_count = int(preflight.get("run_count", 0) or 0)
        if run_count > int(max_runs):
            st.error(f"当前参数组合数为 {run_count}，超过最大组合数 {int(max_runs)}。请缩小网格或提高上限。")
            return
        try:
            data, _, _ = load_data(data_mode, None, symbol, market, interval, start, end)
        except Exception as exc:
            st.error(f"数据获取失败：{exc}")
            return
        try:
            strategy_factory = make_scan_strategy_factory(strategy_option, config)
        except PermissionError as exc:
            st.error(f"策略未确认，不能运行参数扫描。请先到策略库确认当前版本和风险说明。\n\n{exc}")
            return
        except Exception as exc:
            st.error(f"策略初始化失败：{exc}")
            return
        experiment_name = f"{strategy_id}_scan_{symbol}_{int(time.time())}"
        runner = ExperimentRunner(config=config)
        try:
            summary, _ = runner.run_grid(data, strategy_factory, param_grid, experiment_name=experiment_name)
            validation = runner.run_train_test_validation(data, strategy_factory, param_grid, experiment_name=experiment_name)
            walk_forward = runner.run_walk_forward_validation(data, strategy_factory, param_grid, experiment_name=experiment_name)
        except Exception as exc:
            st.error(f"参数扫描失败：{exc}")
            return
        st.caption(f"实验目录：{runner.output_dir}")
        st.success(f"参数扫描完成：{run_count} 组参数，策略 {strategy_id}。")
        show_parameter_stability(analyze_parameter_stability(summary))
        show_train_test_validation(validation)
        show_walk_forward_validation(walk_forward)
        st.dataframe(summary, width="stretch")
        if go is not None and not summary.empty:
            show_scan_chart(summary)
    parameter_scan_terms_panel()


def render_parameter_scan_preflight(preflight: dict[str, object], param_grid: dict[str, list[object]]) -> None:
    st.markdown("#### 参数扫描预检")
    cols = st.columns(5)
    cols[0].metric("建议状态", str(preflight.get("label", "")), help=str(preflight.get("status", "")))
    cols[1].metric("组合数", int(preflight.get("run_count", 0) or 0), help=f"上限 {int(preflight.get('max_runs', 0) or 0)}")
    cols[2].metric("参数数", int(preflight.get("parameter_count", 0) or 0))
    cols[3].metric("上限占用", f"{float(preflight.get('usage_ratio', 0.0) or 0.0):.2%}")
    cols[4].metric("策略类型", str(preflight.get("strategy_kind", "")))
    status = str(preflight.get("status", ""))
    message = str(preflight.get("next_action", ""))
    if status in {"Blocked", "InvalidGrid", "TooMany"}:
        st.warning(message)
    elif status == "LargeRun":
        st.warning(message)
    else:
        st.info(message)
    if param_grid:
        st.caption("预检只解析参数网格和选择项，不读取行情、不运行回测；真正扫描会额外执行稳定性、Train-Test 和 Walk-Forward 验证。")
    st.caption(str(preflight.get("token_policy", "")))


def parameter_scan_terms_panel() -> None:
    st.divider()
    st.markdown("#### 参数扫描专业术语说明")
    st.caption("这些解释用于帮助你理解参数扫描结果。实际选参时不要只看单一指标，应同时检查收益、回撤、Sharpe、稳定性、样本外验证和交易摩擦。")
    st.dataframe(pd.DataFrame(parameter_scan_term_rows()), width="stretch", hide_index=True)


def industry_research_view() -> None:
    st.subheader("行研报告")
    st.caption("按日期检索本地行研报告，并通过统一研究数据总线同步验证任务、回测结果和持仓主数据。")
    status = external_system_status()
    reports = collect_industry_reports()

    cols = st.columns(4)
    cols[0].metric("报告数量", str(len(reports)))
    cols[1].metric("可用系统", str(int((status["status"] == "Ready").sum())) if not status.empty else "0")
    latest_date = reports["report_date"].max() if not reports.empty else "N/A"
    cols[2].metric("最新报告日期", str(latest_date))
    cols[3].metric("验证任务", str(len(validation_task_frame())))

    sync_col, snapshot_col = st.columns([0.25, 0.75])
    if sync_col.button("同步研究数据总线", type="primary"):
        try:
            result = sync_all_research_bus(push_validation_queue=True)
            st.session_state["research_bus_sync_message"] = {
                "status": "success",
                "text": (
                    f"同步完成：行研报告 {result.reports} 份，验证任务 {result.validation_tasks} 条，"
                    f"PFI 结果 {result.pfi_os_results} 条，持仓 {result.holdings} 条。"
                ),
                "snapshot": result.snapshot_path,
                "warnings": list(result.warnings),
            }
        except Exception as exc:
            st.session_state["research_bus_sync_message"] = {"status": "error", "text": f"同步失败：{exc}", "snapshot": "", "warnings": []}
    sync_message = st.session_state.pop("research_bus_sync_message", None)
    if sync_message:
        if sync_message["status"] == "success":
            snapshot_col.success(sync_message["text"])
            if sync_message.get("snapshot"):
                snapshot_col.caption(f"快照文件：{sync_message['snapshot']}")
            for warning in sync_message.get("warnings", []):
                snapshot_col.warning(warning)
        else:
            snapshot_col.error(sync_message["text"])

    with st.expander("统一研究数据总线状态", expanded=False):
        bus_status = research_bus_status_frame()
        display_bus = bus_status.copy()
        if not display_bus.empty:
            display_bus = display_bus.rename(
                columns={
                    "system_name": "系统",
                    "status": "状态",
                    "root_path": "路径",
                    "last_sync_at": "最后同步",
                    "summary_json": "摘要",
                }
            )
        st.dataframe(display_bus, width="stretch", hide_index=True)

    with st.expander("外部系统连接状态", expanded=False):
        st.dataframe(
            status.rename(columns={"system": "系统", "status": "状态", "path": "路径", "expected": "期望数据"}),
            width="stretch",
            hide_index=True,
        )

    if reports.empty:
        st.warning("未找到行研报告。默认目录为当前用户 `~/Downloads/行研报告`；也可以通过环境变量 `PFI_INDUSTRY_REPORT_DIR` 指定。")

    parsed_dates = pd.to_datetime(reports["report_date"], errors="coerce").dropna()
    default_start = (parsed_dates.min().date() if not parsed_dates.empty else (pd.Timestamp.today() - pd.Timedelta(days=30)).date())
    default_end = (parsed_dates.max().date() if not parsed_dates.empty else pd.Timestamp.today().date())
    filter_col1, filter_col2, filter_col3 = st.columns([0.25, 0.25, 0.50])
    start_date = filter_col1.date_input("开始日期", value=default_start, key="industry_start")
    end_date = filter_col2.date_input("结束日期", value=default_end, key="industry_end")
    query = filter_col3.text_input("关键词", value="", placeholder="报告名、类型、目录或路径")
    filtered = filter_industry_reports(reports, start_date, end_date, query)
    st.caption(f"当前显示：{len(filtered)} / {len(reports)}")

    display = filtered.copy()
    if not display.empty:
        st.dataframe(
            display.rename(
                columns={
                    "name": "报告名称",
                    "report_date": "报告日期",
                    "category": "类型",
                    "period": "区间目录",
                    "size_kb": "大小 KB",
                    "modified_time": "修改时间",
                    "path": "路径",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        selected_path = st.selectbox("选择报告", list(display["path"]), format_func=lambda path: Path(str(path)).name)
        open_col, folder_col = st.columns(2)
        if open_col.button("打开报告"):
            _open_local_path(Path(str(selected_path)))
        if folder_col.button("打开所在目录"):
            _open_local_path(Path(str(selected_path)).parent)

    st.markdown("#### 量化验证联动")
    artifacts = report_artifacts_frame(REPORT_ROOT_DIR)
    runs = run_metadata_summaries_frame(REPORT_ROOT_DIR)
    tasks = validation_task_frame()
    linked_col1, linked_col2 = st.columns(2)
    with linked_col1:
        st.write("最近 PFI 报告")
        latest_reports = artifacts[artifacts["artifact_type"].isin(WORD_REPORT_TYPES)].head(10) if not artifacts.empty else pd.DataFrame()
        if latest_reports.empty:
            st.info("暂无 PFI Word 报告。")
        else:
            st.dataframe(_display_artifacts_frame(latest_reports), width="stretch", hide_index=True)
    with linked_col2:
        st.write("验证任务队列")
        if tasks.empty:
            st.info("暂无验证任务。可在报告中心的“验证任务”页签新增。")
        else:
            st.dataframe(tasks[["created_at", "research_topic", "symbol", "market", "status", "validation_report_path"]], width="stretch", hide_index=True)

    if not runs.empty:
        st.write("最近研究门禁状态")
        visible = [column for column in ["date_folder", "strategy_id", "research_status", "decision_quality_score", "missing_evidence_count", "metadata_path"] if column in runs.columns]
        st.dataframe(runs[visible].head(20), width="stretch", hide_index=True)


def research_bus_monitor_view() -> None:
    st.subheader("研究总线")
    st.caption("集中查看 PFI、行研系统、消费行为系统、持仓主数据和独立验证系统的互通状态。")
    health = research_bus_health_summary()
    counts = health.get("request_counts", {})
    cols = st.columns(5)
    cols[0].metric("总线状态", str(health.get("status", "")))
    cols[1].metric("待处理请求", str(health.get("pending_request_count", 0)))
    cols[2].metric("失败请求", str(health.get("failed_request_count", 0)))
    cols[3].metric("心跳过期", str(health.get("heartbeat_stale_count", 0)))
    cols[4].metric("投递箱文件", str(health.get("chat_inbox_pending_files", 0)))

    action_cols = st.columns(4)
    if action_cols[0].button("处理投递箱", type="primary"):
        try:
            result = process_chat_dropbox(min_age_seconds=0)
            st.success(f"投递箱处理完成：成功 {result['processed_count']} 个，失败 {result['failed_count']} 个。")
        except Exception as exc:
            st.error(f"投递箱处理失败：{exc}")
    if action_cols[1].button("处理请求"):
        try:
            result = process_pending_bus_requests(system_name="ResearchBus", limit=100)
            st.success(f"请求处理完成：成功 {result['processed']} 个，失败 {result['failed']} 个。")
        except Exception as exc:
            st.error(f"请求处理失败：{exc}")
    if action_cols[2].button("同步一次"):
        try:
            result = sync_all_research_bus(push_validation_queue=True)
            st.success(f"同步完成：报告 {result.reports}，验证任务 {result.validation_tasks}，回测结果 {result.pfi_os_results}，持仓 {result.holdings}。")
            for warning in result.warnings:
                st.warning(warning)
        except Exception as exc:
            st.error(f"同步失败：{exc}")
    if action_cols[3].button("刷新状态"):
        st.rerun()

    st.markdown("#### 输入入口")
    st.code(str(health.get("chat_inbox_dir", "")))
    st.caption("本地 HTTP 入口默认监听 `127.0.0.1:8765`；可用 `scripts/researchBusWebhook.sh` 启动。")

    tab_status, tab_requests, tab_candidates, tab_chats, tab_heartbeats = st.tabs(["系统状态", "请求", "持仓候选", "对话输入", "心跳"])
    with tab_status:
        st.dataframe(research_bus_status_frame(), width="stretch", hide_index=True)
        st.dataframe(pd.DataFrame([{"状态": key, "数量": value} for key, value in counts.items()]), width="stretch", hide_index=True)
    with tab_requests:
        st.dataframe(pending_bus_requests_frame(target_system="ResearchBus", limit=200), width="stretch", hide_index=True)
        with st.expander("最近请求", expanded=False):
            st.dataframe(bus_api_requests_frame(limit=200), width="stretch", hide_index=True)
    with tab_candidates:
        candidates = holding_update_candidates_frame(limit=200)
        if candidates.empty:
            st.info("暂无待复核持仓候选。")
        else:
            visible_columns = [
                "updated_at",
                "source_system",
                "account",
                "candidate_type",
                "status",
                "quality_status",
                "parser_status",
                "structured_holding_count",
                "structured_transaction_count",
                "content_text",
                "attachments_json",
                "extracted_symbols_json",
                "source_request_id",
            ]
            st.dataframe(candidates[[column for column in visible_columns if column in candidates.columns]], width="stretch", hide_index=True)
            pending_candidates = candidates[candidates["status"].astype(str).isin(["PendingReview", "NeedsStructuredData"])] if "status" in candidates.columns else candidates
            candidate_ids = pending_candidates["candidate_id"].astype(str).tolist() if "candidate_id" in pending_candidates.columns else []
            if candidate_ids:
                with st.form("confirm_holding_candidate_form"):
                    selected_candidate_id = st.selectbox("候选编号", candidate_ids)
                    confirm_clicked = st.form_submit_button("确认结构化候选")
                if confirm_clicked:
                    try:
                        result = confirm_holding_update_candidate(selected_candidate_id)
                        if result.get("status") == "Applied":
                            st.success(
                                f"确认完成：持仓 {result.get('confirmed_holding_count', 0)} 条，"
                                f"交易 {result.get('confirmed_transaction_count', 0)} 条。"
                            )
                        else:
                            st.warning(str(result.get("message", result)))
                    except Exception as exc:
                        st.error(f"确认失败：{exc}")
    with tab_chats:
        st.dataframe(bus_chat_inputs_frame(limit=200), width="stretch", hide_index=True)
    with tab_heartbeats:
        st.dataframe(bus_heartbeats_frame(), width="stretch", hide_index=True)


def big_data_simulation_view() -> None:
    st.subheader("大数据模拟")
    st.caption("通过 ResearchBus 调用独立验证系统，生成百万、千万、亿级到十亿级数据测试计划或 checksum 校验记录；只用于研究验证，不接实盘。")

    runs = independent_validation_runs_frame()
    latest = runs.iloc[0].to_dict() if not runs.empty else {}
    metric_cols = st.columns(5)
    metric_cols[0].metric("共享库", "Ready" if research_bus_db_path().exists() else "Missing")
    metric_cols[1].metric("运行次数", str(len(runs)))
    metric_cols[2].metric("最新状态", str(latest.get("status", "N/A")))
    metric_cols[3].metric("最新规模", _format_big_number(latest.get("total_rows", 0)))
    metric_cols[4].metric("最新分片", _format_big_number(latest.get("shard_count", 0)))

    st.markdown("#### 新建模拟")
    scale_options = {
        "百万行": 1_000_000,
        "千万行": 10_000_000,
        "一亿行": 100_000_000,
        "十亿行": 1_000_000_000,
        "自定义": 0,
    }
    shard_options = {
        "十万行": 100_000,
        "百万行": 1_000_000,
        "千万行": 10_000_000,
        "一亿行": 100_000_000,
    }
    with st.form("big_data_simulation_form"):
        col_scale, col_shard, col_mode = st.columns(3)
        scale_label = col_scale.selectbox("模拟规模", list(scale_options), index=2)
        shard_label = col_shard.selectbox("分片大小", list(shard_options), index=1)
        mode_label = col_mode.selectbox("验证模式", ["dry_run 计划登记", "checksum 流式校验"], index=0)
        custom_rows = 0
        if scale_label == "自定义":
            custom_rows = int(
                st.number_input(
                    "自定义行数",
                    min_value=1_000,
                    max_value=1_000_000_000_000,
                    value=100_000_000,
                    step=1_000_000,
                )
            )
        prompt = st.text_area(
            "自然语言备注",
            value=f"请运行{scale_label.replace('自定义', '自定义规模')}独立验证，每片{shard_label}",
            height=72,
        )
        submitted = st.form_submit_button("运行大数据模拟")

    if submitted:
        synthetic_rows = custom_rows if scale_label == "自定义" else scale_options[scale_label]
        rows_per_shard = shard_options[shard_label]
        mode = "checksum" if "checksum" in mode_label else "dry_run"
        try:
            result = run_independent_validation(
                db_path=research_bus_db_path(),
                synthetic_rows=int(synthetic_rows),
                rows_per_shard=int(rows_per_shard),
                mode=mode,
            )
            st.success(
                f"已写入独立验证系统：状态 {result.status}，总行数 {_format_big_number(result.total_rows)}，"
                f"分片 {result.shard_count} 个。"
            )
            st.caption(f"备注：{prompt}")
            st.caption(f"输出文件：{result.output_path}")
        except Exception as exc:
            st.error(f"大数据模拟失败：{exc}")

    st.markdown("#### 输入入口")
    st.dataframe(
        pd.DataFrame(
            [
                {"入口": "本页按钮", "用途": "直接生成独立验证运行记录和分片计划。"},
                {"入口": "任意聊天框文本", "用途": "写入 ResearchBus 投递箱或调用 researchBusApi.sh submit-chat 后处理请求。"},
                {"入口": "本地 Webhook", "用途": "通过 127.0.0.1:8765 接收 JSON 或文本，不暴露公网。"},
                {"入口": "automation", "用途": "定时处理投递箱、请求和系统同步。"},
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    st.code(
        "scripts/researchBusApi.sh submit-chat --text \"请运行千万行独立验证 checksum 校验，每片100万行\" --json\n"
        "scripts/researchBusApi.sh process --system-name ResearchBus --json\n"
        "scripts/runIndependentValidation.sh --synthetic-rows 1000000000 --rows-per-shard 100000000 --mode dry_run --json",
        language="bash",
    )
    st.caption(f"共享数据库：{research_bus_db_path()}")

    st.markdown("#### 最近运行")
    if runs.empty:
        st.info("暂无独立验证运行记录。")
    else:
        display = runs.copy()
        display["total_rows"] = display["total_rows"].map(_format_big_number)
        display["shard_count"] = display["shard_count"].map(_format_big_number)
        st.dataframe(
            display.rename(
                columns={
                    "run_id": "运行编号",
                    "status": "状态",
                    "mode": "模式",
                    "manifest_path": "Manifest",
                    "total_rows": "总行数",
                    "shard_count": "分片数",
                    "started_at": "开始时间",
                    "completed_at": "完成时间",
                    "output_path": "输出文件",
                    "updated_at": "更新时间",
                }
            ),
            width="stretch",
            hide_index=True,
        )


def _format_big_number(value: object) -> str:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return "0"
    return f"{number:,}"


def holdings_view() -> None:
    st.subheader("持仓")
    st.caption("读取、保存并同步 PFI、行研报告系统、消费行为分析系统和支付宝账本中的持仓数据；待确认订单不会计入正式持仓。")
    sources = scan_holding_sources()
    holdings = load_current_holdings()
    pending_orders = load_pending_orders_frame()
    candidate_holdings = load_candidate_holdings_frame()
    summary = holdings_summary(holdings)

    action_cols = st.columns([0.18, 0.18, 0.18, 0.46])
    if action_cols[0].button("同步持仓", type="primary"):
        try:
            result = sync_holdings_book()
            st.session_state["holdings_sync_message"] = {"status": "success", "text": f"同步完成：正式持仓 {result.canonical_row_count} 条，源文件 {result.source_file_count} 个。", "warnings": list(result.warnings)}
        except Exception as exc:
            st.session_state["holdings_sync_message"] = {"status": "error", "text": f"同步失败：{exc}", "warnings": []}
        st.rerun()
    sync_message = st.session_state.pop("holdings_sync_message", None)
    if isinstance(sync_message, dict):
        if sync_message.get("status") == "error":
            st.error(str(sync_message.get("text", "")))
        else:
            st.success(str(sync_message.get("text", "")))
            if sync_message.get("warnings"):
                st.warning("；".join(str(item) for item in sync_message["warnings"]))
    if action_cols[1].button("导出 CSV"):
        export_path = export_holdings_csv(holdings)
        st.success(f"已导出：{export_path}")
    if action_cols[2].button("打开持仓簿"):
        _open_local_path(HOLDINGS_BOOK_PATH)
    action_cols[3].info("正式持仓只来自确认数据；截图候选和待确认订单单独显示，用于复核，不进入权重和风险计算。")

    metric_cols = st.columns(6)
    metric_cols[0].metric("持仓总市值", _format_metric_value(summary["total_position_value"], "currency"))
    metric_cols[1].metric("正式持仓", str(summary["holding_count"]))
    metric_cols[2].metric("最大单一权重", _format_metric_value(summary["top1_weight"], "percent"))
    metric_cols[3].metric("前三权重", _format_metric_value(summary["top3_weight"], "percent"))
    metric_cols[4].metric("市场数量", str(summary["market_count"]))
    metric_cols[5].metric("待确认订单", str(len(pending_orders)))

    tab_current, tab_sources, tab_pending, tab_manual, tab_quality = st.tabs(["当前持仓", "同步来源", "待确认订单", "手动维护", "质量检查"])
    with tab_current:
        if holdings.empty:
            st.warning("当前没有正式持仓。可点击“同步持仓”，或把 CSV/XLSX/JSON 放入持仓导入目录。")
            st.code(
                "data/holdings/imports\n"
                "data/external/consumerHoldings\n"
                "~/Downloads/行研报告，或通过 PFI_INDUSTRY_REPORT_DIR 指定",
                language="text",
            )
        else:
            st.dataframe(_display_holdings_frame(holdings), width="stretch", hide_index=True)
            exposure = holdings_exposure_frame(holdings)
            if not exposure.empty:
                st.markdown("#### 暴露拆解")
                display_exposure = exposure.copy()
                display_exposure["市值"] = display_exposure["市值"].map(lambda value: f"{float(value):,.2f}")
                display_exposure["权重"] = display_exposure["权重"].map(lambda value: f"{float(value):.2%}")
                st.dataframe(display_exposure, width="stretch", hide_index=True)
        if not candidate_holdings.empty:
            with st.expander("截图候选持仓，需人工确认", expanded=False):
                st.dataframe(_display_holdings_frame(candidate_holdings), width="stretch", hide_index=True)

    with tab_sources:
        st.dataframe(
            sources.rename(
                columns={
                    "source_system": "来源系统",
                    "status": "状态",
                    "file_count": "文件数",
                    "latest_modified_time": "最近修改",
                    "paths": "扫描路径",
                    "description": "说明",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        history = holdings_sync_history_frame()
        st.markdown("#### 同步历史")
        if history.empty:
            st.info("暂无同步历史。")
        else:
            st.dataframe(history.head(20), width="stretch", hide_index=True)

    with tab_pending:
        if pending_orders.empty:
            st.info("未读取到待确认订单。")
        else:
            display_pending = pending_orders.copy()
            for column in ["order_amount", "confirmed_amount", "confirmed_units", "confirmed_nav", "fee"]:
                if column in display_pending.columns:
                    display_pending[column] = pd.to_numeric(display_pending[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):,.2f}")
            st.dataframe(display_pending, width="stretch", hide_index=True)
            st.caption("这些订单来自支付宝账本的 pending_orders.csv。确认份额、确认净值或订单状态前，不计入正式持仓。")

    with tab_manual:
        st.markdown("#### 手动新增或更新持仓")
        with st.form("manual_holding_form"):
            col_a, col_b, col_c = st.columns(3)
            symbol = col_a.text_input("代码", value="")
            name = col_b.text_input("名称", value="")
            market = col_c.selectbox("市场", ["CN", "US", "HK", "OTHER"], index=0)
            col_d, col_e, col_f = st.columns(3)
            quantity = col_d.number_input("数量/份额", min_value=0.0, value=0.0, step=1.0)
            position_value = col_e.number_input("持仓金额/市值", min_value=0.0, value=0.0, step=100.0)
            cost_basis = col_f.number_input("成本价/成本", min_value=0.0, value=0.0, step=0.01)
            col_g, col_h = st.columns(2)
            unrealized_pnl = col_g.number_input("浮动盈亏", value=0.0, step=10.0)
            updated_at = col_h.date_input("更新时间", value=pd.Timestamp.today().date(), key="manual_holding_updated_at")
            submitted = st.form_submit_button("保存到持仓簿")
        if submitted:
            if not symbol.strip() and not name.strip():
                st.error("代码和名称至少填写一个。")
            elif position_value <= 0 and quantity <= 0:
                st.error("持仓金额或数量至少需要一个大于 0。")
            else:
                updated = upsert_manual_holding(
                    {
                        "symbol": symbol,
                        "name": name,
                        "market": market,
                        "quantity": quantity,
                        "cost_basis": cost_basis,
                        "position_value": position_value,
                        "unrealized_pnl": unrealized_pnl,
                        "updated_at": str(updated_at),
                    }
                )
                st.success(f"已保存，当前正式持仓 {len(updated)} 条。")
                st.rerun()
        st.caption(f"持仓簿永久保存到：{HOLDINGS_BOOK_PATH}")
        st.caption(f"CSV 导出默认保存到：{HOLDINGS_EXPORT_PATH}")

    with tab_quality:
        quality = holdings_quality_frame(holdings)
        st.dataframe(quality, width="stretch", hide_index=True)
        st.markdown("#### 字段口径")
        st.dataframe(
            pd.DataFrame(
                [
                    {"字段": "代码", "说明": "股票、ETF、基金或指数代码；缺失时用名称作为临时身份键。"},
                    {"字段": "市场", "说明": "CN、US、HK 或 OTHER，用于组合暴露和情绪分析联动。"},
                    {"字段": "持仓金额/市值", "说明": "当前正式持仓金额；如果来源文件有权重但无金额，集中度只能按权重初步判断。"},
                    {"字段": "权重", "说明": "当存在有效市值时系统按市值重新计算；否则使用来源文件权重。"},
                    {"字段": "待确认订单", "说明": "付款成功但未确认份额、净值或订单状态的记录，不计入正式持仓。"},
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def sentiment_analysis_view() -> None:
    st.subheader("情绪分析")
    st.caption("先选市场，再勾选大盘对象、我的持仓或自选代码；系统生成情绪观察分，仅用于研究观察，不输出实盘买卖指令。")
    st.markdown(
        f"先看 {term_badge('证据闸门')}，再看 {term_badge('情绪分')}、{term_badge('偏热比例')} 和 {term_badge('偏冷比例')}。鼠标悬停在术语上可查看解释。",
        unsafe_allow_html=True,
    )
    control_col, body_col = st.columns([0.26, 0.74], gap="large")
    with control_col:
        data_source = st.selectbox("数据源", ["Sample", "Moomoo", "Yahoo Finance", "AKShare"], index=0, key="sentiment_data", help=TERM_HELP["数据源"])
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="sentiment_market", help=TERM_HELP["市场"])
        object_sources = st.multiselect(
            "对象来源",
            ["大盘对象", "我的持仓", "自选代码"],
            default=["大盘对象"],
            key="sentiment_object_sources",
            help=TERM_HELP["对象来源"],
        )
        market_options = {_sentiment_option_label(item): item for item in default_sentiment_universe(market)}
        selected_market_labels: list[str] = []
        if "大盘对象" in object_sources:
            selected_market_labels = st.multiselect(
                "大盘对象",
                list(market_options),
                default=list(market_options),
                key="sentiment_market_objects",
            )
        holding_options: dict[str, SentimentInstrument] = {}
        selected_holding_labels: list[str] = []
        if "我的持仓" in object_sources:
            current_holdings = load_current_holdings()
            holding_options = {_sentiment_option_label(item, include_weight=True): item for item in _holding_sentiment_options(current_holdings, market)}
            proxy_frame = holdings_symbol_proxy_frame(current_holdings, market)
            if holding_options:
                selected_holding_labels = st.multiselect(
                    "我的持仓",
                    list(holding_options),
                    default=list(holding_options)[:10],
                    key="sentiment_holding_objects",
                )
                with st.expander("持仓行情代理说明", expanded=False):
                    st.caption("缺少真实代码的基金会使用本地代理规则匹配 ETF、指数或行业代理；代理只用于情绪观察，不代表基金本身。")
                    st.dataframe(_display_holding_symbol_proxy_frame(proxy_frame), width="stretch", hide_index=True)
            elif not current_holdings.empty:
                st.warning("当前持仓已读取，但缺少可用于拉取行情的代码。请在持仓页补充代码，或在自选代码中输入对应 ETF/基金/指数代码。")
                preview = _display_holdings_frame(current_holdings)
                visible_preview = [column for column in ["名称", "市场", "持仓金额", "持有收益", "持有收益率", "权重"] if column in preview.columns]
                st.dataframe(preview[visible_preview].head(20), width="stretch", hide_index=True)
            else:
                st.info("当前没有可用于情绪分析的正式持仓；可到持仓页面同步或手动维护。")
        start = st.date_input("展示开始日期", value=(pd.Timestamp.today() - pd.Timedelta(days=420)).date(), key="sentiment_start", help=TERM_HELP["展示窗口"])
        end = date_input_with_today("结束日期", key="sentiment_end", default=pd.Timestamp.today())
        sentiment_warmup_start = indicator_warmup_start(end, "1d")
        st.caption(
            "情绪分按结束日期计算；开始日期不应改变同一结束日期的分数。"
            f"实际请求从 {sentiment_warmup_start.date().isoformat()} 开始，展示从 {pd.Timestamp(start).date().isoformat()} 开始。"
        )
        custom_symbols = ""
        if "自选代码" in object_sources:
            custom_symbols = st.text_area("自选代码", value="SPY, QQQ, GLD" if market == "US" else "000001, 510300, 518880", height=90)
            st.caption("多个代码用逗号、空格或换行分隔。")
        instruments = _sentiment_instruments_from_selection(
            market=market,
            market_options=market_options,
            selected_market_labels=selected_market_labels,
            holding_options=holding_options,
            selected_holding_labels=selected_holding_labels,
            custom_symbols=custom_symbols,
        )
        run = st.button("生成情绪观察", type="primary", help="生成后先看总体摘要，再看极端偏热/偏冷对象和失败对象。")
        st.caption("真实数据依赖对应数据源权限；失败对象会列入错误明细，不会阻断其他对象。")

    with body_col:
        st.markdown("#### 已选择对象")
        if instruments:
            st.dataframe(pd.DataFrame([instrument.__dict__ for instrument in instruments]), width="stretch", hide_index=True)
        else:
            st.info("请选择至少一个大盘对象、持仓对象或自选代码。")
        if not run:
            st.info("确认对象列表后点击“生成情绪观察”。")
            sentiment_terms_panel()
            return
        if not instruments:
            st.error("没有可分析对象。请勾选大盘对象、持仓对象，或输入自选代码。")
            return
        rows, errors = fetch_sentiment_rows(data_source, market, instruments, start, end)
        if rows.empty:
            st.error("没有生成情绪结果。请检查数据源、代码格式或时间区间。")
            if errors:
                st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
            return
        render_sentiment_overview(rows, errors, data_source)
        show_sentiment_distribution_chart(rows)
        render_sentiment_cards(rows)
        show_sentiment_score_chart(rows)
        render_sentiment_priority_table(rows)
        st.markdown("#### 指标明细")
        st.dataframe(_display_sentiment_frame(rows), width="stretch", hide_index=True)
        if errors:
            with st.expander("未成功对象", expanded=True):
                st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
        sentiment_terms_panel()


def market_hotspots_view() -> None:
    st.subheader("大盘热点分析")
    st.caption("用热力图和气泡图观察大盘、行业、风格和持仓对象的短期强弱扩散。数据至少按 1 小时缓存刷新；结果只用于研究观察。")
    st.markdown(
        f"标准读法：先看 {term_badge('热点证据闸门')}，再看 {term_badge('时间切片')} 和时间轴，最后用 {term_badge('热力图')} 与 {term_badge('气泡图')} 复核异动强度。",
        unsafe_allow_html=True,
    )
    control_col, body_col = st.columns([0.26, 0.74], gap="large")
    with control_col:
        data_source = st.selectbox("数据源", ["Sample", "Moomoo", "Yahoo Finance", "AKShare"], index=0, key="hotspot_data", help=TERM_HELP["数据源"])
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="hotspot_market", help=TERM_HELP["市场"])
        interval = st.selectbox(
            "时间粒度",
            ["60min", "1d"],
            index=0,
            key="hotspot_interval",
            help="60min 用于小时级热点观察；如果数据源不支持，会在失败对象中显示原因或由底层数据源兜底。",
        )
        workbench_mode = st.selectbox(
            "工作台模式",
            list(HOTSPOT_WORKBENCH_PROFILES),
            index=0,
            key="hotspot_workbench_mode",
            help=TERM_HELP["热点工作台模式"],
        )
        workbench_profile = hotspot_workbench_profile(workbench_mode)
        st.caption(str(workbench_profile["description"]))
        show_52etf_reference = st.checkbox(
            "显示 52ETF 公开参考",
            value=False,
            key="hotspot_52etf_reference",
            help=TERM_HELP["52ETF公开参考"],
        )
        object_sources = st.multiselect(
            "分析范围",
            ["大盘热点", "我的持仓", "自选代码"],
            default=["大盘热点"],
            key="hotspot_object_sources",
            help=TERM_HELP["分析范围"],
        )
        market_options = {_sentiment_option_label(item): item for item in default_hotspot_universe(market)}
        selected_market_labels: list[str] = []
        if "大盘热点" in object_sources:
            selected_market_labels = st.multiselect(
                "大盘热点对象",
                list(market_options),
                default=list(market_options),
                key="hotspot_market_objects",
                help="建议保留宽基、成长、周期、避险和波动对象，便于观察横向扩散。",
            )
        holding_options: dict[str, SentimentInstrument] = {}
        selected_holding_labels: list[str] = []
        if "我的持仓" in object_sources:
            current_holdings = load_current_holdings()
            holding_options = {_sentiment_option_label(item, include_weight=True): item for item in _holding_sentiment_options(current_holdings, market)}
            if holding_options:
                selected_holding_labels = st.multiselect(
                    "我的持仓对象",
                    list(holding_options),
                    default=list(holding_options)[:12],
                    key="hotspot_holding_objects",
                    help="持仓缺少证券代码时会使用本地代理规则。代理只用于观察，不代表基金本身。",
                )
            else:
                st.info("当前没有可用于热点分析的正式持仓代码。")
        custom_symbols = ""
        if "自选代码" in object_sources:
            custom_symbols = st.text_area("自选代码", value="SPY, QQQ, SMH, GLD" if market == "US" else "000001, 399006, 512760, 518880", height=90, key="hotspot_custom")
            st.caption("多个代码用逗号、空格或换行分隔。")
        start = st.date_input("展示开始日期", value=(pd.Timestamp.today() - pd.Timedelta(days=45)).date(), key="hotspot_start", help=f"{TERM_HELP['展示窗口']} 小时级热点建议至少保留 30 个交易日；日线热点建议保留 6-12 个月。")
        end = date_input_with_today("结束日期", key="hotspot_end", default=pd.Timestamp.today())
        hotspot_warmup_start = indicator_warmup_start(start, interval)
        st.caption(f"指标会自动向前取预热数据：实际请求从 {hotspot_warmup_start.date().isoformat()} 开始，展示从 {pd.Timestamp(start).date().isoformat()} 开始。")
        enable_hourly_refresh = st.checkbox(
            "每小时自动刷新当前页",
            value=True,
            key="hotspot_hourly_refresh",
            help="页面保持打开时，每 1 小时刷新一次，以触发缓存失效后的重新读取。关闭后可手动点击生成。",
        )
        run = st.button("生成热点分析", type="primary", help="生成后先看时间切片，再看热力图、气泡图、优先复核对象和明细。")
        st.caption(f"缓存刷新间隔：{HOTSPOT_REFRESH_TTL_SECONDS // 60} 分钟。真实更新速度取决于数据源权限和行情延迟。")

    instruments = _sentiment_instruments_from_selection(
        market=market,
        market_options=market_options,
        selected_market_labels=selected_market_labels,
        holding_options=holding_options,
        selected_holding_labels=selected_holding_labels,
        custom_symbols=custom_symbols,
    )
    active_instruments, skipped_instrument_count = limit_hotspot_instruments(instruments, int(workbench_profile["object_limit"]))
    start_iso = pd.Timestamp(start).date().isoformat()
    end_iso = pd.Timestamp(end).date().isoformat()
    max_snapshots = int(workbench_profile["max_snapshots"])
    request_key = hotspot_runtime_cache_key(
        data_source=data_source,
        market=market,
        interval=interval,
        instruments=active_instruments,
        display_start=start_iso,
        display_end=end_iso,
        max_snapshots=max_snapshots,
    )
    hotspot_cache_root = ROOT / "data" / "cache" / "hotspots"
    request_cache_status = hotspot_persisted_cache_status(hotspot_cache_root, request_key=request_key)
    cache_directory_summary = hotspot_cache_directory_summary(hotspot_cache_root)
    hotspot_preflight = hotspot_quick_preflight(
        workbench_mode=workbench_mode,
        requested_count=len(instruments),
        active_count=len(active_instruments),
        skipped_count=skipped_instrument_count,
        max_snapshots=max_snapshots,
        request_cache_status=request_cache_status,
        directory_summary=cache_directory_summary,
        data_source=data_source,
        interval=interval,
    )

    with body_col:
        site52etf_snapshot: dict[str, object] | None = None
        render_hotspot_preflight(hotspot_preflight)
        with st.expander("高级缓存与清理", expanded=False):
            render_hotspot_cache_controls(request_cache_status, cache_directory_summary, hotspot_cache_root, request_key)
        if show_52etf_reference:
            site52etf_snapshot = render_site52etf_public_reference()
        if enable_hourly_refresh:
            render_auto_refresh_component(HOTSPOT_REFRESH_TTL_SECONDS)
        st.markdown("#### 分析对象")
        if active_instruments:
            if skipped_instrument_count:
                st.warning(f"{workbench_mode} 已限制分析对象数量，本次先计算 {len(active_instruments)} 个对象，跳过 {skipped_instrument_count} 个。切到“标准分析”或“完整复盘”可扩大范围。")
            st.dataframe(pd.DataFrame([instrument.__dict__ for instrument in active_instruments]), width="stretch", hide_index=True)
            st.caption(f"运行请求：{request_key}；同一数据源、对象、日期、粒度和工作台模式在 {HOTSPOT_REFRESH_TTL_SECONDS // 60} 分钟内复用缓存。")
        else:
            st.info("请选择至少一个大盘热点对象、持仓对象或自选代码。")
        if not run:
            st.info("确认对象列表后点击“生成热点分析”。")
            hotspot_terms_panel()
            return
        if not active_instruments:
            st.error("没有可分析对象。请勾选大盘热点、持仓对象，或输入自选代码。")
            return
        history, errors, cache_meta = fetch_hotspot_history_cached(
            data_source=data_source,
            market=market,
            interval=interval,
            instrument_payloads=_sentiment_payloads(active_instruments),
            start_iso=start_iso,
            end_iso=end_iso,
            max_snapshots=max_snapshots,
            request_key=request_key,
        )
        if history.empty:
            st.error("没有生成热点结果。请检查数据源、代码格式、时间粒度或时间区间。")
            if errors:
                st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
            return
        runtime = hotspot_runtime_summary(
            history,
            errors,
            data_source=data_source,
            market=market,
            interval=interval,
            requested_count=len(active_instruments),
            max_snapshots=max_snapshots,
            request_key=request_key,
            cache_source=str(cache_meta.get("source", "computed")),
            persisted_cache_age_seconds=cache_meta.get("age_seconds"),
            request_trace=cache_meta.get("request_trace", []),
        )
        render_hotspot_runtime_summary(runtime)
        render_hotspot_request_trace(runtime.get("request_trace", {}))
        show_hotspot_timeline(history)
        snapshot_options = list(history["snapshot_time"].drop_duplicates().astype(str))
        selected_snapshot = st.select_slider(
            "时间切片",
            options=snapshot_options,
            value=snapshot_options[-1],
            key="hotspot_snapshot",
            help=TERM_HELP["时间切片"],
        )
        requested_snapshot = st.text_input(
            "自定义时间查看",
            value=selected_snapshot,
            key="hotspot_snapshot_query",
            help="可输入完整时间、日期片段或近似时间；系统会匹配最近的可用时间切片。",
        )
        resolved_snapshot = resolve_hotspot_snapshot(snapshot_options, requested_snapshot, fallback=selected_snapshot)
        if resolved_snapshot != selected_snapshot:
            st.caption(f"已定位到可用时间切片：{resolved_snapshot}")
        selected_snapshot = resolved_snapshot
        render_hotspot_overview(history, selected_snapshot, errors)
        render_hotspot_evidence_gate(history, errors, data_source, interval, requested_count=len(active_instruments))
        if show_52etf_reference:
            render_site52etf_hotspot_comparison(site52etf_snapshot or fetch_site52etf_public_snapshot_cached(), history, market, selected_snapshot)
        show_hotspot_heatmap(history, selected_snapshot)
        show_hotspot_bubble_chart(history, selected_snapshot)
        st.markdown("#### 优先复核对象")
        st.caption("优先复核最偏强和最偏弱的对象，确认是否由趋势、波动、避险资产或数据异常驱动。")
        st.dataframe(_display_hotspot_frame(hotspot_focus_rows(history, selected_snapshot, n=8)), width="stretch", hide_index=True)
        st.markdown("#### 热点明细")
        current = history[history["snapshot_time"].astype(str).eq(str(selected_snapshot))]
        st.dataframe(_display_hotspot_frame(current), width="stretch", hide_index=True)
        if errors:
            with st.expander("未成功对象", expanded=True):
                st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
        hotspot_terms_panel()


def render_hotspot_preflight(preflight: dict[str, object]) -> None:
    st.markdown("#### 热点快速预检")
    cols = st.columns(5)
    cols[0].metric("建议状态", str(preflight.get("label", "")), help=str(preflight.get("status", "")))
    cols[1].metric("对象", f"{int(preflight.get('active_count', 0) or 0)}/{int(preflight.get('requested_count', 0) or 0)}")
    cols[2].metric("切片上限", int(preflight.get("max_snapshots", 0) or 0))
    cols[3].metric("预计请求", int(preflight.get("expected_provider_requests", 0) or 0), help="缓存命中时通常为 0；缓存未命中时约等于对象数。")
    cols[4].metric("缓存", "Hit" if preflight.get("cache_hit") else str(preflight.get("cache_state", "miss")))
    status = str(preflight.get("status", ""))
    message = str(preflight.get("next_action", ""))
    if status == "NeedsInput":
        st.warning(message)
    elif status == "CacheHit":
        st.success(message)
    elif status == "LargeRun":
        st.warning(message)
    else:
        st.info(message)
    skipped = int(preflight.get("skipped_count", 0) or 0)
    if skipped:
        st.caption(f"当前模式已自动跳过 {skipped} 个对象，避免一次请求过慢；切换到更高模式可扩大范围。")
    st.caption(str(preflight.get("token_policy", "")))


@st.cache_data(ttl=HOTSPOT_REFRESH_TTL_SECONDS, show_spinner=False)
def fetch_hotspot_history_cached(
    data_source: str,
    market: str,
    interval: str,
    instrument_payloads: tuple[tuple[str, str, str, str], ...],
    start_iso: str,
    end_iso: str,
    max_snapshots: int = HOTSPOT_MAX_DISPLAY_SNAPSHOTS,
    request_key: str = "",
) -> tuple[pd.DataFrame, list[dict[str, str]], dict[str, object]]:
    instruments = _payloads_to_sentiment_instruments(instrument_payloads)
    cache_root = ROOT / "data" / "cache" / "hotspots"
    request_key = request_key or hotspot_runtime_cache_key(
        data_source=data_source,
        market=market,
        interval=interval,
        instruments=instruments,
        display_start=start_iso,
        display_end=end_iso,
        max_snapshots=max_snapshots,
    )
    persisted = load_hotspot_persisted_cache(cache_root, request_key=request_key)
    if persisted:
        return (
            persisted["history"],
            persisted["errors"],
            {
                "source": "persisted",
                "path": persisted.get("path", ""),
                "age_seconds": persisted.get("age_seconds"),
                "request_key": request_key,
                "request_trace": persisted.get("request_trace", []),
            },
        )
    request_start_iso = indicator_warmup_start(start_iso, interval).date().isoformat()
    frames: dict[str, pd.DataFrame] = {}
    errors: list[dict[str, str]] = []
    request_trace: list[dict[str, object]] = []
    try:
        provider = make_provider(data_source)
    except Exception as exc:
        return pd.DataFrame(), [{"代码": "", "名称": "", "错误": f"数据源不可用：{exc}"}], {"source": "computed", "request_key": request_key, "request_trace": request_trace}
    for instrument in instruments:
        provider_symbol = _sentiment_symbol_for_provider(instrument.symbol, instrument.market or market, data_source)
        started_at = time.perf_counter()
        try:
            request = BarDataRequest(
                symbol=provider_symbol,
                market=instrument.market or market,
                interval=interval,
                start=request_start_iso,
                end=end_iso,
                adjustment="auto",
            )
            bars, _fallback = get_bars_with_interval_fallback(provider, request)
            frames[instrument.symbol] = bars
            request_trace.append(
                _hotspot_trace_row(
                    instrument,
                    provider_symbol=provider_symbol,
                    status="Pass",
                    elapsed_ms=(time.perf_counter() - started_at) * 1000,
                    row_count=len(bars),
                    fallback=str(_fallback or ""),
                )
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            errors.append({"代码": instrument.symbol, "名称": instrument.name, "错误": str(exc)})
            request_trace.append(
                _hotspot_trace_row(
                    instrument,
                    provider_symbol=provider_symbol,
                    status="Fail",
                    elapsed_ms=elapsed_ms,
                    row_count=0,
                    error=str(exc),
                )
            )
    history = build_hotspot_history(
        frames,
        instruments,
        data_source=data_source,
        max_snapshots=max_snapshots,
        display_start=start_iso,
        display_end=end_iso,
    )
    cache_meta: dict[str, object] = {"source": "computed", "request_key": request_key}
    if not history.empty:
        summary = hotspot_runtime_summary(
            history,
            errors,
            data_source=data_source,
            market=market,
            interval=interval,
            requested_count=len(instruments),
            max_snapshots=max_snapshots,
            request_key=request_key,
            cache_source="computed",
            request_trace=request_trace,
        )
        try:
            write_result = write_hotspot_persisted_cache(
                cache_root,
                request_key=request_key,
                history=history,
                errors=errors,
                summary=summary,
                request_trace=request_trace,
            )
            cache_meta["persist_write_status"] = write_result.get("status", "")
            cache_meta["persist_path"] = write_result.get("path", "")
        except OSError as exc:
            cache_meta["persist_write_status"] = "Failed"
            cache_meta["persist_write_error"] = str(exc)
    cache_meta["request_trace"] = request_trace
    return history, errors, cache_meta


@st.cache_data(ttl=HOTSPOT_REFRESH_TTL_SECONDS, show_spinner=False)
def fetch_site52etf_public_snapshot_cached() -> dict[str, object]:
    latest = load_site52etf_public_snapshot_latest(project_root=ROOT)
    if latest:
        latest["snapshot_source"] = "local_latest"
        return latest
    return fetch_52etf_public_snapshot().to_dict()


def render_site52etf_public_reference() -> dict[str, object]:
    st.markdown("#### 52ETF 大盘云图公开参考")
    snapshot = fetch_site52etf_public_snapshot_cached()
    rows = site52etf_summary_rows(snapshot)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.markdown(f"[打开 52ETF 大盘云图]({SITE52ETF_URL})")
    if snapshot.get("snapshot_source") == "local_latest":
        st.caption("当前使用本地 52ETF latest snapshot；可运行 `scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf` 刷新。")
    if snapshot.get("status") == "Unavailable":
        st.warning("52ETF 公开参考暂不可用；PFI 本地热点分析仍可继续运行。")
    else:
        st.caption("该参考源只用于学习市场云图表达和对照对象池，不写入回测、不触发交易、不替代本地数据质量闸门。")
    return snapshot


def render_site52etf_hotspot_comparison(snapshot: dict[str, object], history: pd.DataFrame, market: str, snapshot_time: str) -> None:
    comparison = build_site52etf_hotspot_comparison(snapshot, history, market=market, snapshot_time=snapshot_time)
    st.markdown(f'<h4 title="{_escape_html(TERM_HELP["52ETF热点对照"])}">52ETF 与 PFI 热点对照</h4>', unsafe_allow_html=True)
    st.caption("只读对照公开 A 股云图板块和 PFI 当前热点对象池；用于检查覆盖与交互口径，不进入回测、不触发交易。")
    st.dataframe(pd.DataFrame(site52etf_comparison_rows(comparison)), width="stretch", hide_index=True)
    if comparison.get("status") != "Pass":
        st.caption("当前对照为 Review：可能是 52ETF 不可用、市场不是 CN，或 PFI 对象池与公开云图板块映射不足。")


def _sentiment_payloads(instruments: list[SentimentInstrument]) -> tuple[tuple[str, str, str, str], ...]:
    return tuple((item.symbol, item.name, item.market, item.role) for item in instruments)


def _payloads_to_sentiment_instruments(payloads: tuple[tuple[str, str, str, str], ...]) -> list[SentimentInstrument]:
    return [SentimentInstrument(symbol=symbol, name=name, market=market, role=role) for symbol, name, market, role in payloads]


def indicator_warmup_start(start, interval: str = "1d") -> pd.Timestamp:
    start_ts = pd.Timestamp(start)
    days = HOTSPOT_INTRADAY_WARMUP_DAYS if str(interval).lower() in {"1min", "5min", "15min", "30min", "60min"} else HOTSPOT_DAILY_WARMUP_DAYS
    if str(interval).lower() == "1d":
        days = SENTIMENT_WARMUP_DAYS
    return start_ts - pd.Timedelta(days=days)


def render_hotspot_runtime_summary(summary: dict[str, object]) -> None:
    if summary.get("schema") != HOTSPOT_RUNTIME_SUMMARY_SCHEMA:
        return
    st.markdown(f'<h4 title="{_escape_html(TERM_HELP["热点运行摘要"])}">热点运行摘要</h4>', unsafe_allow_html=True)
    cards = [card for card in summary.get("cards", []) if isinstance(card, dict)]
    cols = st.columns(4)
    for index, card in enumerate(cards[:4]):
        cols[index].metric(
            str(card.get("label", "")),
            str(card.get("value", "")),
            help=str(card.get("detail", "")),
        )
    st.caption(
        f"请求指纹：{summary.get('request_key', '') or '未生成'}；"
        f"窗口：{summary.get('first_snapshot', '') or '无'} -> {summary.get('latest_snapshot', '') or '无'}；"
        f"{summary.get('token_policy', '')}"
    )


def render_hotspot_request_trace(trace_summary: dict[str, object] | object) -> None:
    if not isinstance(trace_summary, dict) or trace_summary.get("schema") != "PFIOSHotspotRequestTraceV1":
        trace_summary = hotspot_request_trace_summary([])
    if int(trace_summary.get("request_count", 0) or 0) <= 0:
        return
    st.markdown("#### 数据请求耗时")
    cols = st.columns(4)
    cols[0].metric("请求对象", str(trace_summary.get("request_count", 0)))
    cols[1].metric("成功/失败", f"{trace_summary.get('success_count', 0)}/{trace_summary.get('failed_count', 0)}")
    cols[2].metric("总耗时", _format_ms_compact(trace_summary.get("total_elapsed_ms")))
    cols[3].metric("最慢对象", _format_ms_compact(trace_summary.get("slowest_elapsed_ms")))
    slowest = trace_summary.get("slowest", [])
    if isinstance(slowest, list) and slowest:
        st.dataframe(_display_hotspot_trace_rows(slowest), width="stretch", hide_index=True)
    st.caption("这里只显示每个对象的 compact 请求耗时和错误摘要，不保存原始行情帧、不触发下单或持仓修改。")


def _display_hotspot_trace_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    display_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        display_rows.append(
            {
                "代码": row.get("symbol", ""),
                "名称": row.get("name", ""),
                "Provider代码": row.get("provider_symbol", ""),
                "状态": row.get("status", ""),
                "耗时": _format_ms_compact(row.get("elapsed_ms")),
                "行数": row.get("row_count", 0),
                "兜底": row.get("fallback", ""),
                "错误": row.get("error", ""),
            }
        )
    return pd.DataFrame(display_rows)


def _format_ms_compact(value: object) -> str:
    try:
        ms = max(0.0, float(value))
    except (TypeError, ValueError):
        return "0ms"
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms / 1000:.2f}s"


def render_hotspot_cache_controls(
    request_status: dict[str, object],
    directory_summary: dict[str, object],
    cache_root: Path,
    request_key: str,
) -> None:
    st.markdown("#### 热点缓存")
    state = str(request_status.get("state", "miss"))
    state_label = {
        "hit": "可复用",
        "miss": "未生成",
        "expired": "已过期",
        "corrupt": "需清理",
        "mismatch": "需清理",
    }.get(state, "需复核")
    remaining = request_status.get("remaining_seconds")
    age = request_status.get("age_seconds")
    cols = st.columns(4)
    cols[0].metric("当前请求", state_label, help=f"request_key={request_key}")
    cols[1].metric("缓存年龄", _format_seconds_compact(age), help="当前请求缓存写入后经过的时间。")
    cols[2].metric("剩余有效期", _format_seconds_compact(remaining), help=f"TTL={HOTSPOT_REFRESH_TTL_SECONDS // 60} 分钟。")
    cols[3].metric("缓存目录", f"{directory_summary.get('file_count', 0)} 个", help=f"{directory_summary.get('total_kb', 0.0)} KB")
    if state == "hit":
        st.caption("当前请求已有有效派生缓存，点击生成会优先复用，不重新读取行情。")
    elif state == "expired":
        st.caption("当前请求缓存已超过 TTL，下一次生成会重新计算并覆盖派生缓存。")
    else:
        st.caption("当前请求暂无有效派生缓存，第一次生成可能较慢；生成后同一请求会复用本地缓存。")
    clear_disabled = not bool(request_status.get("exists"))
    if st.button("清除当前热点缓存", key=f"hotspot_clear_cache_{request_key}", disabled=clear_disabled, help="只删除当前请求指纹对应的派生热点缓存。"):
        result = invalidate_hotspot_persisted_cache(cache_root, request_key=request_key)
        clear_func = getattr(fetch_hotspot_history_cached, "clear", None)
        if callable(clear_func):
            clear_func()
        st.success(f"缓存处理完成：{result.get('status')}")
        st.rerun()


def _format_seconds_compact(value: object) -> str:
    if value is None:
        return "不适用"
    try:
        seconds = max(0.0, float(value))
    except (TypeError, ValueError):
        return "不适用"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60:.1f}h"


def _hotspot_trace_row(
    instrument: SentimentInstrument,
    *,
    provider_symbol: str,
    status: str,
    elapsed_ms: float,
    row_count: int,
    fallback: str = "",
    error: str = "",
) -> dict[str, object]:
    return {
        "symbol": instrument.symbol,
        "name": instrument.name,
        "market": instrument.market,
        "provider_symbol": provider_symbol,
        "status": status,
        "elapsed_ms": round(float(elapsed_ms), 2),
        "row_count": int(row_count),
        "fallback": fallback,
        "error": error,
    }


def render_hotspot_overview(history: pd.DataFrame, snapshot_time: str, errors: list[dict[str, str]]) -> None:
    summary = hotspot_summary(history, snapshot_time)
    timeline_state = hotspot_timeline_state(hotspot_timeline_frame(history))
    st.markdown("#### 热点总览")
    cols = st.columns([1, 1, 1, 1, 1.15, 1, 1.15])
    cols[0].metric("对象数量", str(summary.object_count), help="该时间切片成功计算的热点对象数量。")
    cols[1].metric("平均平滑热度", f"{summary.average_heat_score:.2f}", help=TERM_HELP["平滑热度"])
    cols[2].metric("偏强对象", str(summary.strong_count), help="热点状态为强势扩散或局部偏强的对象数量。")
    cols[3].metric("偏弱对象", str(summary.weak_count), help="热点状态为局部偏弱或风险降温的对象数量。")
    cols[4].metric("领先板块", summary.leading_sector or "无", help=TERM_HELP["领先板块"])
    cols[5].metric("失败对象", str(len(errors)), help=TERM_HELP["失败对象"])
    cols[6].metric("热点状态", timeline_state["状态"], help=TERM_HELP["热点状态"])
    st.caption(f"时间切片：{summary.snapshot_time}；落后板块：{summary.lagging_sector or '无'}。{timeline_state['说明']} 即时热度用于发现异动，平滑热度用于判断持续性。")


def render_hotspot_evidence_gate(history: pd.DataFrame, errors: list[dict[str, str]], data_source: str, interval: str, requested_count: int | None = None) -> None:
    rows = hotspot_evidence_gate_rows(history, errors, data_source, interval, requested_count=requested_count)
    if not rows:
        return
    st.markdown(f'<h4 title="{_escape_html(TERM_HELP["热点证据闸门"])}">热点证据闸门</h4>', unsafe_allow_html=True)
    st.caption("先看闸门，再看图表。只要出现 Review 或 Block，热点结果只能作为观察线索，需要补充数据或降低结论强度。")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def hotspot_evidence_gate_rows(history: pd.DataFrame, errors: list[dict[str, str]], data_source: str, interval: str, requested_count: int | None = None) -> list[dict[str, str]]:
    return build_hotspot_evidence_gate_rows(
        history,
        errors,
        data_source=data_source,
        interval=interval,
        requested_count=requested_count,
    )


def hotspot_timeline_frame(history: pd.DataFrame) -> pd.DataFrame:
    columns = ["snapshot_time", "平均热度", "平均即时热度", "偏强对象", "偏弱对象", "对象数量"]
    if history.empty or "snapshot_time" not in history.columns:
        return pd.DataFrame(columns=columns)
    frame = history.copy()
    frame["heat_score"] = pd.to_numeric(frame.get("heat_score", 50.0), errors="coerce").fillna(50.0)
    frame["instant_heat_score"] = pd.to_numeric(frame.get("instant_heat_score", frame["heat_score"]), errors="coerce").fillna(50.0)
    frame["_strong"] = frame.get("hotspot_state", "").isin(["强势扩散", "局部偏强"]).astype(int)
    frame["_weak"] = frame.get("hotspot_state", "").isin(["局部偏弱", "风险降温"]).astype(int)
    timeline = (
        frame.groupby("snapshot_time", dropna=False)
        .agg(
            平均热度=("heat_score", "mean"),
            平均即时热度=("instant_heat_score", "mean"),
            偏强对象=("_strong", "sum"),
            偏弱对象=("_weak", "sum"),
            对象数量=("symbol", "count"),
        )
        .reset_index()
    )
    timeline["_sort_time"] = pd.to_datetime(timeline["snapshot_time"], errors="coerce")
    timeline = timeline.sort_values(["_sort_time", "snapshot_time"], kind="mergesort").drop(columns=["_sort_time"])
    timeline["平均热度"] = pd.to_numeric(timeline["平均热度"], errors="coerce").fillna(0.0).round(2)
    timeline["平均即时热度"] = pd.to_numeric(timeline["平均即时热度"], errors="coerce").fillna(0.0).round(2)
    return timeline[columns]


def hotspot_timeline_state(timeline: pd.DataFrame) -> dict[str, str]:
    if timeline.empty or len(timeline) < 2:
        return {"状态": "样本不足", "说明": "时间切片不足，暂不能判断热点扩散或降温。"}
    latest = timeline.iloc[-1]
    previous = timeline.iloc[-2]
    latest_heat = float(latest.get("平均热度", 0.0) or 0.0)
    previous_heat = float(previous.get("平均热度", 0.0) or 0.0)
    latest_strong = int(latest.get("偏强对象", 0) or 0)
    previous_strong = int(previous.get("偏强对象", 0) or 0)
    latest_weak = int(latest.get("偏弱对象", 0) or 0)
    previous_weak = int(previous.get("偏弱对象", 0) or 0)
    heat_delta = latest_heat - previous_heat
    strong_delta = latest_strong - previous_strong
    weak_delta = latest_weak - previous_weak
    if heat_delta >= 3.0 and strong_delta >= 1:
        return {"状态": "热点扩散", "说明": f"平均热度上升 {heat_delta:.2f}，偏强对象增加 {strong_delta} 个。"}
    if heat_delta <= -3.0 and weak_delta >= 1:
        return {"状态": "热点降温", "说明": f"平均热度下降 {abs(heat_delta):.2f}，偏弱对象增加 {weak_delta} 个。"}
    if latest_strong > 0 and latest_weak > 0:
        return {"状态": "强弱分化", "说明": f"同一时间切片内偏强 {latest_strong} 个、偏弱 {latest_weak} 个，先复核板块差异。"}
    return {"状态": "横盘轮动", "说明": f"平均热度变化 {heat_delta:.2f}，暂未看到明显扩散或降温。"}


def resolve_hotspot_snapshot(snapshot_options: list[str], requested: str | None, fallback: str | None = None) -> str:
    if not snapshot_options:
        return ""
    default = fallback if fallback in snapshot_options else snapshot_options[-1]
    query = str(requested or "").strip()
    if not query:
        return default
    if query in snapshot_options:
        return query
    lowered = query.lower()
    partial_matches = [item for item in snapshot_options if lowered in item.lower()]
    if partial_matches:
        return partial_matches[-1]
    parsed_query = pd.to_datetime(query, errors="coerce")
    if pd.isna(parsed_query):
        return default
    parsed_options = pd.to_datetime(pd.Series(snapshot_options), errors="coerce")
    valid = parsed_options.dropna()
    if valid.empty:
        return default
    nearest_position = (valid - parsed_query).abs().idxmin()
    return snapshot_options[int(nearest_position)]


def show_hotspot_timeline(history: pd.DataFrame) -> None:
    timeline = hotspot_timeline_frame(history)
    if timeline.empty:
        return
    st.markdown("#### 热点时间轴")
    st.caption("拖动下方图表时间轴或使用页面的时间切片，检查热点是持续扩散、快速消退，还是只是一小时噪声。默认线条为平滑热度，浅色线为即时热度。")
    timeline_state = hotspot_timeline_state(timeline)
    st.info(f"{timeline_state['状态']}：{timeline_state['说明']}")
    if go is None or make_subplots is None:
        st.dataframe(timeline, width="stretch", hide_index=True)
        return
    x_values = pd.to_datetime(timeline["snapshot_time"], errors="coerce")
    if x_values.isna().all():
        x_values = timeline["snapshot_time"].astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=timeline["平均热度"],
            name="平均平滑热度",
            mode="lines+markers",
            line=dict(color="#8a1538", width=2.2),
            hovertemplate="时间 %{x}<br>平均平滑热度 %{y:.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=timeline["平均即时热度"],
            name="平均即时热度",
            mode="lines",
            line=dict(color="rgba(138, 21, 56, 0.35)", width=1.4, dash="dot"),
            hovertemplate="时间 %{x}<br>平均即时热度 %{y:.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=x_values,
            y=timeline["偏强对象"],
            name="偏强对象",
            marker_color="rgba(185, 28, 28, 0.28)",
            hovertemplate="时间 %{x}<br>偏强对象 %{y}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Bar(
            x=x_values,
            y=-timeline["偏弱对象"],
            name="偏弱对象",
            marker_color="rgba(31, 95, 122, 0.26)",
            customdata=timeline["偏弱对象"],
            hovertemplate="时间 %{x}<br>偏弱对象 %{customdata}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=40),
        barmode="relative",
    )
    fig.update_yaxes(title_text="平均热度", range=[0, 100], secondary_y=False)
    fig.update_yaxes(title_text="对象数量", secondary_y=True)
    fig.update_xaxes(
        title="",
    )
    apply_research_chart_ux(fig, height=380, hovermode="x unified", dragmode="pan", x_range_slider=True, x_range_selector=True)
    st.plotly_chart(fig, width="stretch", config=research_chart_config("pfi_os_hotspot_timeline"))


def show_hotspot_heatmap(history: pd.DataFrame, snapshot_time: str) -> None:
    current = history[history["snapshot_time"].astype(str).eq(str(snapshot_time))].copy()
    if current.empty:
        return
    st.markdown("#### 热力图")
    if go is None:
        st.dataframe(_display_hotspot_frame(current), width="stretch", hide_index=True)
        return
    current["label"] = current["name"] + " (" + current["symbol"] + ")"
    pivot = current.pivot_table(index="sector", columns="label", values="heat_score", aggfunc="mean")
    text = current.pivot_table(index="sector", columns="label", values="five_step_return", aggfunc="mean").reindex_like(pivot)
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            text=[[f"{value:.2%}" if pd.notna(value) else "" for value in row] for row in text.values],
            texttemplate="%{text}",
            hovertemplate="板块 %{y}<br>对象 %{x}<br>平滑热度 %{z:.2f}<br>近5期 %{text}<extra></extra>",
            colorscale=[[0, "#166534"], [0.5, "#f8fafc"], [1, "#b91c1c"]],
            zmin=0,
            zmax=100,
            colorbar=dict(title="平滑热度"),
        )
    )
    heatmap_height = max(340, 58 * len(pivot.index))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=90),
    )
    apply_research_chart_ux(fig, height=heatmap_height, hovermode="closest", dragmode="zoom")
    st.caption("红色表示短期偏强，绿色表示短期偏弱；颜色代表平滑后的横向热度，不代表操作建议。")
    st.plotly_chart(fig, width="stretch", config=research_chart_config("pfi_os_hotspot_heatmap"))


def show_hotspot_bubble_chart(history: pd.DataFrame, snapshot_time: str) -> None:
    current = history[history["snapshot_time"].astype(str).eq(str(snapshot_time))].copy()
    if current.empty or go is None:
        return
    st.markdown("#### 气泡图")
    fig = go.Figure(
        go.Scatter(
            x=current["one_step_return"],
            y=current["five_step_return"],
            mode="markers+text",
            text=current["name"],
            textposition="top center",
            marker=dict(
                size=current["bubble_size"],
                color=current["heat_score"],
                colorscale=[[0, "#166534"], [0.5, "#f8fafc"], [1, "#b91c1c"]],
                cmin=0,
                cmax=100,
                line=dict(color="#334155", width=0.8),
                opacity=0.82,
                colorbar=dict(title="平滑热度"),
            ),
            customdata=current[["symbol", "sector", "hotspot_state", "rsi14", "volatility20", "drawdown20", "instant_heat_score", "heat_score_delta"]],
            hovertemplate=(
                "%{text} (%{customdata[0]})<br>"
                "板块 %{customdata[1]}<br>"
                "状态 %{customdata[2]}<br>"
                "即时热度 %{customdata[6]:.2f}<br>"
                "平滑热度 %{marker.color:.2f}<br>"
                "热度变化 %{customdata[7]:+.2f}<br>"
                "近1期 %{x:.2%}<br>"
                "近5期 %{y:.2%}<br>"
                "RSI %{customdata[3]:.2f}<br>"
                "20期波动 %{customdata[4]:.2%}<br>"
                "20期回撤 %{customdata[5]:.2%}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="#94a3b8")
    fig.add_vline(x=0, line_dash="dot", line_color="#94a3b8")
    fig.add_annotation(x=0.98, y=0.96, xref="paper", yref="paper", text="短期延续偏强", showarrow=False, font=dict(size=12, color="#7f1d1d"), bgcolor="rgba(255,255,255,0.72)")
    fig.add_annotation(x=0.02, y=0.04, xref="paper", yref="paper", text="同步偏弱", showarrow=False, font=dict(size=12, color="#14532d"), bgcolor="rgba(255,255,255,0.72)")
    fig.add_annotation(x=0.02, y=0.96, xref="paper", yref="paper", text="短线反弹待确认", showarrow=False, font=dict(size=12, color="#334155"), bgcolor="rgba(255,255,255,0.72)")
    fig.add_annotation(x=0.98, y=0.04, xref="paper", yref="paper", text="回落分歧", showarrow=False, font=dict(size=12, color="#334155"), bgcolor="rgba(255,255,255,0.72)")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(title="近1期涨跌", tickformat=".2%"),
        yaxis=dict(title="近5期涨跌", tickformat=".2%"),
    )
    apply_research_chart_ux(fig, height=520, hovermode="closest", dragmode="pan")
    st.caption("右上角代表短期和近5期同时偏强；左下角代表同步偏弱；颜色使用平滑热度，悬停可看即时热度和热度变化。")
    st.plotly_chart(fig, width="stretch", config=research_chart_config("pfi_os_hotspot_bubble"))


def _display_hotspot_frame(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()
    display = rows.copy()
    percentage_columns = ["one_step_return", "five_step_return", "twenty_step_return", "volatility20", "drawdown20"]
    for column in percentage_columns:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):.2%}")
    for column in ["close", "rsi14", "instant_heat_score", "heat_score", "heat_score_delta", "bubble_size"]:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):,.2f}")
    return display.rename(
        columns={
            "snapshot_time": "时间切片",
            "bar_time": "实际行情时间",
            "symbol": "代码",
            "name": "名称",
            "market": "市场",
            "sector": "板块/类别",
            "close": "价格",
            "one_step_return": "近1期涨跌",
            "five_step_return": "近5期涨跌",
            "twenty_step_return": "近20期涨跌",
            "rsi14": "RSI14",
            "volatility20": "20期波动",
            "drawdown20": "20期回撤",
            "instant_heat_score": "即时热度",
            "heat_score": "平滑热度",
            "heat_score_delta": "热度变化",
            "hotspot_state": "热点状态",
            "bubble_size": "气泡大小",
            "evidence_note": "证据摘要",
            "data_source": "数据源",
            "data_points": "样本点",
        }
    )


def hotspot_terms_panel() -> None:
    with st.expander("热点分析口径", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {"术语": "热点热度", "说明": TERM_HELP["热点热度"]},
                    {"术语": "热点工作台模式", "说明": TERM_HELP["热点工作台模式"]},
                    {"术语": "52ETF公开参考", "说明": TERM_HELP["52ETF公开参考"]},
                    {"术语": "即时热度", "说明": TERM_HELP["即时热度"]},
                    {"术语": "平滑热度", "说明": TERM_HELP["平滑热度"]},
                    {"术语": "热度变化", "说明": TERM_HELP["热度变化"]},
                    {"术语": "热力图", "说明": TERM_HELP["热力图"]},
                    {"术语": "气泡图", "说明": TERM_HELP["气泡图"]},
                    {"术语": "时间切片", "说明": "选择某一个小时或日期，只查看该时点的横向热点结构。"},
                    {"术语": "每小时刷新", "说明": "页面缓存 TTL 为 3600 秒；开启自动刷新后，页面每小时触发一次刷新。真实行情是否更新取决于数据源。"},
                    {"术语": "近1期/近5期", "说明": "当前时间粒度下最近 1 个 bar 或 5 个 bar 的涨跌幅。60min 表示小时，1d 表示交易日。"},
                    {"术语": "RSI14", "说明": TERM_HELP["RSI14"]},
                    {"术语": "20期波动", "说明": "最近 20 个 bar 收益率标准差的年化近似，用于观察异动强度。"},
                    {"术语": "20期回撤", "说明": "最近 20 个 bar 内从高点到低点的最大跌幅。"},
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def _display_holdings_frame(holdings: pd.DataFrame) -> pd.DataFrame:
    display = holdings.copy()
    display["holding_return_rate"] = _holding_return_rate_series(display)
    columns = [
        "source_system",
        "symbol",
        "name",
        "market",
        "quantity",
        "cost_basis",
        "position_value",
        "unrealized_pnl",
        "holding_return_rate",
        "weight",
        "updated_at",
    ]
    for column in columns:
        if column not in display.columns:
            display[column] = ""
    display = display[columns].copy()
    for column in ["quantity", "cost_basis", "position_value", "unrealized_pnl"]:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):,.2f}")
    display["holding_return_rate"] = pd.to_numeric(display["holding_return_rate"], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):.2%}")
    if "weight" in display.columns:
        display["weight"] = pd.to_numeric(display["weight"], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):.2%}")
    return display.rename(
        columns={
            "source_system": "来源系统",
            "source_file": "来源文件",
            "symbol": "代码",
            "name": "名称",
            "market": "市场",
            "quantity": "数量/份额",
            "cost_basis": "成本/成本价",
            "position_value": "持仓金额",
            "unrealized_pnl": "持有收益",
            "holding_return_rate": "持有收益率",
            "weight": "权重",
            "updated_at": "更新时间",
        }
    )


def _holding_return_rate_series(holdings: pd.DataFrame) -> pd.Series:
    if holdings.empty:
        return pd.Series(dtype=float)
    position_value = _numeric_app_column(holdings, "position_value")
    pnl = _numeric_app_column(holdings, "unrealized_pnl")
    invested = position_value - pnl
    return (pnl / invested.where(invested.abs() > 1e-9)).replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)


def _numeric_app_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _sentiment_option_label(instrument: SentimentInstrument, include_weight: bool = False) -> str:
    holding_name = str(getattr(instrument, "holding_name", "") or "").strip()
    prefix = f"{holding_name} -> " if holding_name and holding_name != instrument.name else ""
    label = f"{prefix}{instrument.name} ({instrument.symbol}) · {instrument.market} · {instrument.role}"
    weight = getattr(instrument, "weight", None)
    if include_weight and weight is not None:
        try:
            label = f"{label} · {float(weight):.2%}"
        except (TypeError, ValueError):
            pass
    return label


def _holding_sentiment_options(holdings: pd.DataFrame, market: str, limit: int = 50) -> list[SentimentInstrument]:
    if holdings.empty:
        return []
    data = holdings.copy()
    for column in ["symbol", "name", "market"]:
        if column not in data.columns:
            data[column] = ""
        data[column] = data[column].fillna("").astype(str).str.strip()
    data["weight"] = _numeric_app_column(data, "weight")
    data["position_value"] = _numeric_app_column(data, "position_value")
    normalized_market = market.upper()
    market_match = data[data["market"].str.upper().eq(normalized_market)] if normalized_market else data
    selected = market_match if not market_match.empty else data
    selected = selected.sort_values(["weight", "position_value"], ascending=[False, False])
    instruments: list[SentimentInstrument] = []
    for row in selected.head(limit).to_dict("records"):
        symbol = str(row.get("symbol", "")).strip()
        name = str(row.get("name", symbol)).strip() or symbol
        resolved = resolve_holding_symbol_proxy(name=name, symbol=symbol, market=str(row.get("market", market)).strip() or market)
        if not resolved:
            continue
        instrument = SentimentInstrument(
            symbol=resolved.symbol,
            name=resolved.name,
            market=resolved.market,
            role=resolved.role,
        )
        object.__setattr__(instrument, "weight", float(row.get("weight", 0.0) or 0.0))
        object.__setattr__(instrument, "holding_name", name)
        object.__setattr__(instrument, "mapping_confidence", resolved.confidence)
        object.__setattr__(instrument, "mapping_reason", resolved.reason)
        instruments.append(instrument)
    return instruments


def _display_holding_symbol_proxy_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["名称", "市场", "原代码", "代理代码", "代理名称", "代理市场", "状态", "置信度", "说明"])
    return frame.rename(
        columns={
            "name": "名称",
            "market": "市场",
            "symbol": "原代码",
            "proxy_symbol": "代理代码",
            "proxy_name": "代理名称",
            "proxy_market": "代理市场",
            "status": "状态",
            "confidence": "置信度",
            "reason": "说明",
        }
    )


def _sentiment_instruments_from_selection(
    market: str,
    market_options: dict[str, SentimentInstrument],
    selected_market_labels: list[str],
    holding_options: dict[str, SentimentInstrument],
    selected_holding_labels: list[str],
    custom_symbols: str,
) -> list[SentimentInstrument]:
    instruments: list[SentimentInstrument] = []
    instruments.extend(market_options[label] for label in selected_market_labels if label in market_options)
    instruments.extend(holding_options[label] for label in selected_holding_labels if label in holding_options)
    symbols = [item.strip() for item in re.split(r"[,\s，、]+", custom_symbols) if item.strip()]
    instruments.extend(SentimentInstrument(symbol=symbol, name=symbol, market=market, role="自选") for symbol in symbols[:20])
    return _dedupe_sentiment_instruments(instruments)


def _dedupe_sentiment_instruments(instruments: list[SentimentInstrument]) -> list[SentimentInstrument]:
    deduped: list[SentimentInstrument] = []
    seen: set[str] = set()
    for instrument in instruments:
        key = f"{instrument.market.upper()}|{instrument.symbol.upper()}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(instrument)
    return deduped


def fetch_sentiment_rows(data_source: str, market: str, instruments: list[SentimentInstrument], start, end) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    request_start = indicator_warmup_start(end, "1d").date().isoformat()
    try:
        provider = make_provider(data_source)
    except Exception as exc:
        return pd.DataFrame(), [{"代码": "", "名称": "", "错误": f"数据源不可用：{exc}"}]
    for instrument in instruments:
        symbol = _sentiment_symbol_for_provider(instrument.symbol, instrument.market or market, data_source)
        try:
            request = BarDataRequest(symbol=symbol, market=instrument.market or market, interval="1d", start=request_start, end=end, adjustment="auto")
            bars, _fallback = get_bars_with_interval_fallback(provider, request)
            result = sentiment_from_bars(
                bars,
                symbol=instrument.symbol,
                name=instrument.name,
                market=instrument.market or market,
                role=instrument.role,
            )
            rows.append(result.to_row())
        except Exception as exc:
            errors.append({"代码": instrument.symbol, "名称": instrument.name, "错误": str(exc)})
    return pd.DataFrame(rows), errors


def sentiment_distribution_frame(rows: pd.DataFrame) -> pd.DataFrame:
    columns = ["情绪状态", "对象数量", "平均情绪分", "占比"]
    if rows.empty or "sentiment_state" not in rows.columns:
        return pd.DataFrame(columns=columns)
    state_order = ["极度低迷", "偏冷", "中性", "偏热", "过热"]
    frame = rows.copy()
    frame["sentiment_score"] = pd.to_numeric(frame.get("sentiment_score", 0.0), errors="coerce").fillna(0.0)
    total = max(1, len(frame))
    grouped = frame.groupby("sentiment_state", dropna=False).agg(
        对象数量=("sentiment_state", "size"),
        平均情绪分=("sentiment_score", "mean"),
    )
    records: list[dict[str, object]] = []
    for state in state_order:
        count = int(grouped.loc[state, "对象数量"]) if state in grouped.index else 0
        average = float(grouped.loc[state, "平均情绪分"]) if state in grouped.index else 0.0
        records.append({"情绪状态": state, "对象数量": count, "平均情绪分": average, "占比": count / total})
    return pd.DataFrame(records, columns=columns)


def show_sentiment_distribution_chart(rows: pd.DataFrame) -> None:
    distribution = sentiment_distribution_frame(rows)
    if distribution.empty:
        return
    st.markdown("#### 情绪结构")
    st.caption("先看横向状态分布，再看具体对象。偏热集中时复核拥挤和估值；偏冷集中时复核趋势走弱、基本面和数据质量。")
    if go is None:
        display = distribution.copy()
        display["占比"] = display["占比"].map(lambda value: f"{float(value):.2%}")
        display["平均情绪分"] = display["平均情绪分"].map(lambda value: f"{float(value):.2f}")
        st.dataframe(display, width="stretch", hide_index=True)
        return
    colors = [_sentiment_distribution_color(str(state)) for state in distribution["情绪状态"]]
    fig = go.Figure(
        go.Bar(
            x=distribution["情绪状态"],
            y=distribution["对象数量"],
            marker_color=colors,
            text=[f"{value:.2%}" for value in distribution["占比"]],
            textposition="auto",
            customdata=distribution[["平均情绪分", "占比"]],
            hovertemplate="%{x}<br>对象 %{y}<br>占比 %{customdata[1]:.2%}<br>平均情绪分 %{customdata[0]:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=20, b=40),
        yaxis=dict(title="对象数量", rangemode="tozero"),
        xaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")


def _sentiment_distribution_color(state: str) -> str:
    if state == "过热":
        return "#b91c1c"
    if state == "偏热":
        return "#dc6b45"
    if state == "偏冷":
        return "#3b82a0"
    if state == "极度低迷":
        return "#1f5f7a"
    return "#94a3b8"


def _sentiment_symbol_for_provider(symbol: str, market: str, data_source: str) -> str:
    value = symbol.strip()
    source = data_source.strip().lower()
    normalized_market = market.upper()
    if source == "yahoo finance" and normalized_market == "CN" and re.fullmatch(r"\d{6}", value):
        yahoo_cn_overrides = {
            "000001": "000001.SS",
            "399001": "399001.SZ",
            "399006": "399006.SZ",
            "510300": "510300.SS",
            "518880": "518880.SS",
        }
        if value in yahoo_cn_overrides:
            return yahoo_cn_overrides[value]
        return f"{value}.SS" if value.startswith(("5", "6")) else f"{value}.SZ"
    if source == "yahoo finance" and normalized_market == "CN" and re.fullmatch(r"\d{6}\.(SH|SS|SZ)", value, flags=re.IGNORECASE):
        root, suffix = value.split(".", 1)
        return f"{root}.SS" if suffix.upper() in {"SH", "SS"} else f"{root}.SZ"
    if source == "yahoo finance" and normalized_market == "HK" and re.fullmatch(r"\d{1,5}", value):
        return f"{value.zfill(4)}.HK"
    if source == "akshare" and normalized_market == "CN":
        return value.split(".", 1)[0]
    return value


def render_sentiment_overview(rows: pd.DataFrame, errors: list[dict[str, str]], data_source: str) -> None:
    summary = sentiment_summary(rows)
    object_count = max(1, int(summary["object_count"]))
    hot_ratio = float(summary["hot_count"]) / object_count
    cold_ratio = float(summary["cold_count"]) / object_count
    if hot_ratio >= 0.50:
        temperature = "偏热扩散"
    elif cold_ratio >= 0.50:
        temperature = "偏冷扩散"
    else:
        temperature = "分化/中性"
    st.markdown("#### 情绪总览")
    metric_cols = st.columns(6)
    metric_cols[0].metric("对象数量", str(summary["object_count"]), help="本次成功生成情绪结果的对象数量。")
    metric_cols[1].metric("平均情绪分", f"{summary['average_score']:.2f}", help=TERM_HELP["情绪分"])
    metric_cols[2].metric("偏热比例", f"{hot_ratio:.2%}", help=TERM_HELP["偏热比例"])
    metric_cols[3].metric("偏冷比例", f"{cold_ratio:.2%}", help=TERM_HELP["偏冷比例"])
    metric_cols[4].metric("研究状态", temperature, help="用于描述横向市场温度；不输出买卖建议。")
    metric_cols[5].metric("失败对象", str(len(errors)), help="数据源、代码格式或样本长度导致未成功计算的对象数量。")
    st.caption(f"数据源：{data_source}；最新数据日期：{summary['latest_date']}。情绪观察只用于研究复核，不生成实盘指令。")
    gate_rows = sentiment_evidence_gate_rows(rows, errors, data_source)
    st.markdown(f'<h4 title="{_escape_html(TERM_HELP["证据闸门"])}">情绪证据闸门</h4>', unsafe_allow_html=True)
    st.caption("先确认这些检查项，再阅读情绪分。任何 Review 或 Block 都表示只能作为观察线索，不能直接进入交易前参考。")
    st.dataframe(pd.DataFrame(gate_rows), width="stretch", hide_index=True)


def sentiment_evidence_gate_rows(rows: pd.DataFrame, errors: list[dict[str, str]], data_source: str) -> list[dict[str, str]]:
    requested_count = len(rows) + len(errors)
    success_count = len(rows)
    failure_rate = 0.0 if requested_count == 0 else len(errors) / requested_count
    sample_min = 0
    if not rows.empty and "data_points" in rows.columns:
        sample_min = int(pd.to_numeric(rows["data_points"], errors="coerce").fillna(0).min())
    latest_date = ""
    if not rows.empty and "latest_date" in rows.columns:
        latest_date = str(rows["latest_date"].max())
    summary = sentiment_summary(rows)
    object_count = max(1, int(summary["object_count"]))
    hot_ratio = float(summary["hot_count"]) / object_count
    cold_ratio = float(summary["cold_count"]) / object_count
    concentration = max(hot_ratio, cold_ratio)
    source_status = "Review" if data_source.strip().lower() == "sample" else "Pass"
    source_note = "Sample 只用于功能演示；真实研究请切换到可验证数据源。" if source_status == "Review" else "当前选择真实数据源；仍需检查失败对象和最新日期。"
    return [
        {
            "检查项": "数据源",
            "状态": source_status,
            "说明": source_note,
        },
        {
            "检查项": "对象覆盖",
            "状态": "Pass" if success_count >= 3 else "Review" if success_count > 0 else "Block",
            "说明": f"成功 {success_count} 个，失败 {len(errors)} 个；横向情绪观察建议至少 3 个对象。",
        },
        {
            "检查项": "失败率",
            "状态": "Pass" if failure_rate <= 0.20 else "Review" if failure_rate <= 0.50 else "Block",
            "说明": f"失败率 {failure_rate:.2%}。失败对象过多时，先修正代码、权限、时间粒度或网络。",
        },
        {
            "检查项": "样本长度",
            "状态": "Pass" if sample_min >= 60 else "Review" if sample_min >= 30 else "Block",
            "说明": f"最小样本点 {sample_min}。低于 60 时，波动、回撤和 RSI 稳定性下降。",
        },
        {
            "检查项": "数据新鲜度",
            "状态": "Pass" if latest_date else "Block",
            "说明": f"最新行情日期：{latest_date or '缺失'}。日期明显滞后时，应降级为观察线索。",
        },
        {
            "检查项": "情绪集中度",
            "状态": "Review" if concentration >= 0.70 else "Pass",
            "说明": f"偏热集中 {hot_ratio:.2%}，偏冷集中 {cold_ratio:.2%}。集中度高时需补充基本面、新闻和资金流证据。",
        },
    ]


def render_sentiment_priority_table(rows: pd.DataFrame) -> None:
    if rows.empty:
        return
    focus = rows.copy()
    focus["score_distance"] = (pd.to_numeric(focus["sentiment_score"], errors="coerce").fillna(50.0) - 50.0).abs()
    focus = focus.sort_values(["score_distance", "twenty_day_return"], ascending=[False, False]).head(8)
    display = _display_sentiment_frame(focus).drop(columns=["样本点"], errors="ignore")
    st.markdown("#### 优先复核对象")
    st.caption("先看最偏离中性的对象：偏热要复核拥挤和估值证据，偏冷要区分错杀、趋势走弱和数据异常。")
    st.dataframe(display, width="stretch", hide_index=True)


def render_sentiment_cards(rows: pd.DataFrame) -> None:
    st.markdown("#### 情绪观察卡片")
    columns = st.columns(3)
    for index, row in enumerate(rows.to_dict("records")):
        color_class = _sentiment_color_class(str(row.get("sentiment_state", "")))
        score = float(row.get("sentiment_score", 0.0) or 0.0)
        name = _escape_html(row.get("name", ""))
        symbol = _escape_html(row.get("symbol", ""))
        role = _escape_html(row.get("role", ""))
        latest_date = _escape_html(row.get("latest_date", ""))
        state = _escape_html(row.get("sentiment_state", ""))
        reading = _escape_html(row.get("research_reading", ""))
        rsi_help = _escape_html(TERM_HELP["RSI14"])
        drawdown_help = _escape_html(TERM_HELP["最大回撤"])
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="ql-sentiment-card {color_class}">
                  <div class="ql-sentiment-top">
                    <span>{name}</span>
                    <strong>{score:.2f}</strong>
                  </div>
                  <div class="ql-sentiment-symbol">{symbol} · {role} · {latest_date}</div>
                  <div class="ql-sentiment-state">{state}</div>
                  <div class="ql-sentiment-grid">
                    <span title="最近一个交易期的涨跌幅。">1日 {float(row.get("one_day_return", 0.0)):.2%}</span>
                    <span title="近20个交易期涨跌幅，用于观察短期趋势。">20日 {float(row.get("twenty_day_return", 0.0)):.2%}</span>
                    <span title="{rsi_help}">RSI {float(row.get("rsi14", 0.0)):.2f}</span>
                    <span title="{drawdown_help}">回撤 {float(row.get("max_drawdown60", 0.0)):.2%}</span>
                  </div>
                  <div class="ql-sentiment-reading">{reading}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)


def show_sentiment_score_chart(rows: pd.DataFrame) -> None:
    if go is None or rows.empty:
        return
    data = rows.sort_values("sentiment_score", ascending=True)
    colors = [_sentiment_plot_color(str(state)) for state in data["sentiment_state"]]
    fig = go.Figure(
        go.Bar(
            x=data["sentiment_score"],
            y=data["name"],
            orientation="h",
            marker_color=colors,
            text=data["sentiment_state"],
            textposition="auto",
            hovertemplate="%{y}<br>情绪分 %{x:.2f}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        title="情绪分对比",
        height=max(320, 48 * len(data)),
        margin=dict(l=20, r=20, t=50, b=30),
        xaxis=dict(range=[0, 100], title="情绪分"),
        yaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.add_vrect(x0=45, x1=55, fillcolor="#e5e7eb", opacity=0.35, line_width=0)
    st.plotly_chart(fig, width="stretch")


def _display_sentiment_frame(rows: pd.DataFrame) -> pd.DataFrame:
    display = rows.copy()
    percentage_columns = ["one_day_return", "twenty_day_return", "price_vs_ma20", "volatility20", "max_drawdown60"]
    for column in percentage_columns:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):.2%}")
    for column in ["close", "rsi14", "sentiment_score"]:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):,.2f}")
    return display.rename(
        columns={
            "symbol": "代码",
            "name": "名称",
            "market": "市场",
            "role": "角色",
            "latest_date": "最新日期",
            "close": "收盘价",
            "one_day_return": "1日涨跌",
            "twenty_day_return": "20日涨跌",
            "rsi14": "RSI14",
            "price_vs_ma20": "相对20日均线",
            "volatility20": "20日年化波动",
            "max_drawdown60": "60日最大回撤",
            "sentiment_score": "情绪分",
            "sentiment_state": "情绪状态",
            "research_reading": "研究解读",
            "data_points": "样本点",
        }
    )


def sentiment_terms_panel() -> None:
    with st.expander("情绪分析口径", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {"术语": "情绪分", "说明": "0-100 分，综合短期涨跌、20 日趋势、RSI、波动率和回撤；越高代表短期越偏热。"},
                    {"术语": "RSI14", "说明": "14 日相对强弱指标。高于 70 通常表示短期偏拥挤，低于 30 通常表示短期偏低迷。"},
                    {"术语": "相对20日均线", "说明": "当前收盘价相对 20 日均线的偏离。正值表示价格在短期均线上方。"},
                    {"术语": "20日年化波动", "说明": "近 20 个交易日收益率标准差年化。波动越高，情绪判断的不确定性越高。"},
                    {"术语": "60日最大回撤", "说明": "近 60 个交易日从高点到低点的最大跌幅，用于识别压力和风险温度。"},
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def _sentiment_color_class(state: str) -> str:
    if state in {"过热", "偏热"}:
        return "ql-sentiment-hot"
    if state in {"偏冷", "极度低迷"}:
        return "ql-sentiment-cold"
    return "ql-sentiment-neutral"


def _sentiment_plot_color(state: str) -> str:
    if state == "过热":
        return "#b91c1c"
    if state == "偏热":
        return "#dc6b45"
    if state == "偏冷":
        return "#3b82a0"
    if state == "极度低迷":
        return "#1f5f7a"
    return "#6b7280"


def market_feel_training_view() -> None:
    st.subheader("盘感训练")
    st.caption("用趋势、动能、波动、回撤和量价结构练习读图。页面只输出研究观察、训练讲解和风险提示，不输出实盘买卖指令。")
    st.markdown(
        f"训练顺序：先选 {term_badge('训练难度')} 和 {term_badge('判断周期')}，再点击开始，让 {term_badge('限时秒数', '自动倒计时')} 记录是否超时。",
        unsafe_allow_html=True,
    )
    control_col, body_col = st.columns([0.28, 0.72], gap="large")
    with control_col:
        data_source = st.selectbox("数据源", ["Sample", "Moomoo", "Yahoo Finance", "AKShare"], index=0, key="market_feel_data", help=TERM_HELP["数据源"])
        market = st.selectbox("市场", ["US", "CN", "HK"], index=0, key="market_feel_market", help=TERM_HELP["市场"])
        object_sources = st.multiselect(
            "对象来源",
            ["大盘对象", "我的持仓", "自选代码"],
            default=["大盘对象"],
            key="market_feel_object_sources",
            help=f"{TERM_HELP['对象来源']} 建议先用大盘对象训练，再加入自己的持仓和自选代码。",
        )
        market_options = {_sentiment_option_label(item): item for item in default_sentiment_universe(market)}
        selected_market_labels: list[str] = []
        if "大盘对象" in object_sources:
            selected_market_labels = st.multiselect(
                "大盘对象",
                list(market_options),
                default=list(market_options)[:3],
                key="market_feel_market_objects",
            )
        holding_options: dict[str, SentimentInstrument] = {}
        selected_holding_labels: list[str] = []
        if "我的持仓" in object_sources:
            current_holdings = load_current_holdings()
            holding_options = {_sentiment_option_label(item, include_weight=True): item for item in _holding_sentiment_options(current_holdings, market)}
            if holding_options:
                selected_holding_labels = st.multiselect(
                    "我的持仓",
                    list(holding_options),
                    default=list(holding_options)[:8],
                    key="market_feel_holding_objects",
                )
            elif current_holdings.empty:
                st.info("当前没有可用于训练的正式持仓。")
            else:
                st.warning("当前持仓缺少可用行情代码，可在自选代码中输入代理代码。")
        start = st.date_input("开始日期", value=(pd.Timestamp.today() - pd.Timedelta(days=520)).date(), key="market_feel_start", help="训练样本起点。至少需要 60 个可见交易日加答案周期。")
        end = date_input_with_today("结束日期", key="market_feel_end", default=pd.Timestamp.today())
        custom_symbols = ""
        if "自选代码" in object_sources:
            custom_symbols = st.text_area("自选代码", value="SPY, QQQ, GLD" if market == "US" else "000001, 510300, 518880", height=90, key="market_feel_custom")
            st.caption("多个代码用逗号、空格或换行分隔。")
        training_mode = st.selectbox("训练场景", ["收盘复盘", "盘中观察", "策略前检查"], index=0, key="market_feel_mode", help="训练题的使用语境。它不改变计算公式，只改变你复盘时的关注重点。")
        training_level = st.selectbox(
            "训练难度",
            ["入门", "中等", "专家"],
            index=0,
            key="market_feel_training_level",
            help=TERM_HELP["训练难度"],
        )
        answer_horizon = st.selectbox("判断周期", [1, 5, 20], index=1, format_func=lambda value: f"未来 {value} 个交易日", key="market_feel_answer_horizon", help=TERM_HELP["判断周期"])
        default_seconds = {"入门": 20, "中等": 35, "专家": 60}[training_level]
        time_limit_seconds = st.number_input("限时秒数", min_value=10, max_value=180, value=default_seconds, step=5, key="market_feel_time_limit", help=TERM_HELP["限时秒数"])
        instruments = _sentiment_instruments_from_selection(
            market=market,
            market_options=market_options,
            selected_market_labels=selected_market_labels,
            holding_options=holding_options,
            selected_holding_labels=selected_holding_labels,
            custom_symbols=custom_symbols,
        )
        run = st.button("生成盘感训练", type="primary", help="生成后选择一个图表对象，先开始限时判断，再提交查看答案和复盘。")
        st.caption("真实数据依赖数据源权限；单个对象失败不会阻断其他对象。")

    with body_col:
        st.markdown("#### 训练对象")
        if instruments:
            st.dataframe(pd.DataFrame([instrument.__dict__ for instrument in instruments]), width="stretch", hide_index=True)
        else:
            st.info("请选择至少一个大盘对象、持仓对象或自选代码。")

        if run:
            rows, errors, chart_frames, reveal_chart_frames, indicator_rows = fetch_market_feel_results(
                data_source,
                market,
                instruments,
                start,
                end,
                int(answer_horizon),
            )
            st.session_state["market_feel_rows"] = rows.to_dict("records") if not rows.empty else []
            st.session_state["market_feel_errors"] = errors
            st.session_state["market_feel_chart_frames"] = chart_frames
            st.session_state["market_feel_reveal_chart_frames"] = reveal_chart_frames
            st.session_state["market_feel_indicator_rows"] = indicator_rows
            st.session_state["market_feel_mode_value"] = training_mode
            st.session_state["market_feel_level_value"] = training_level
            st.session_state["market_feel_time_limit_value"] = int(time_limit_seconds)
            st.session_state["market_feel_answer_horizon_value"] = int(answer_horizon)

        rows = pd.DataFrame(st.session_state.get("market_feel_rows", []))
        errors = st.session_state.get("market_feel_errors", [])
        chart_frames = st.session_state.get("market_feel_chart_frames", {})
        reveal_chart_frames = st.session_state.get("market_feel_reveal_chart_frames", {})
        indicator_rows = st.session_state.get("market_feel_indicator_rows", {})
        saved_mode = st.session_state.get("market_feel_mode_value", training_mode)
        saved_level = st.session_state.get("market_feel_level_value", training_level)
        saved_time_limit = int(st.session_state.get("market_feel_time_limit_value", time_limit_seconds))
        saved_answer_horizon = int(st.session_state.get("market_feel_answer_horizon_value", answer_horizon))

        if rows.empty:
            st.info("确认对象列表后点击“生成盘感训练”。")
            market_feel_terms_panel()
            if errors:
                with st.expander("未成功对象", expanded=True):
                    st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
            return

        summary_cols = st.columns(5)
        summary_cols[0].metric("训练对象", str(len(rows)))
        summary_cols[1].metric("平均盘感分", f"{float(pd.to_numeric(rows['market_feel_score'], errors='coerce').mean()):.2f}", help=TERM_HELP["盘感分"])
        summary_cols[2].metric("偏强对象", str(int(rows["trend_state"].isin(["多头结构", "短期改善"]).sum())), help="趋势状态为多头结构或短期改善的对象数量。")
        summary_cols[3].metric("风险升温", str(int(rows["risk_state"].eq("风险升温").sum())), help="波动、ATR 或回撤提示风险升温的对象数量。")
        summary_cols[4].metric("训练模式", f"{saved_level} · {saved_answer_horizon}日", help="当前题目采用的难度和答案周期。")

        render_market_feel_cards(rows)
        if chart_frames:
            chart_label = st.selectbox("图表对象", list(chart_frames), key="market_feel_chart_label")
            st.caption("下方图表默认隐藏答案区间，只显示判断前已知数据。提交后才揭示完整走势。")
            show_market_feel_chart(chart_frames[chart_label], chart_label)
            render_market_feel_training_challenge(
                rows=rows,
                chart_label=chart_label,
                training_level=str(saved_level),
                time_limit_seconds=saved_time_limit,
                reveal_frame=reveal_chart_frames.get(chart_label),
            )
            st.markdown("#### 指标讲解")
            st.dataframe(pd.DataFrame(indicator_rows.get(chart_label, [])), width="stretch", hide_index=True)

        st.markdown("#### 训练明细")
        st.dataframe(_display_market_feel_frame(rows), width="stretch", hide_index=True)
        if errors:
            with st.expander("未成功对象", expanded=True):
                st.dataframe(pd.DataFrame(errors), width="stretch", hide_index=True)
        market_feel_terms_panel()


def fetch_market_feel_results(
    data_source: str,
    market: str,
    instruments: list[SentimentInstrument],
    start,
    end,
    answer_horizon: int = 5,
) -> tuple[pd.DataFrame, list[dict[str, str]], dict[str, pd.DataFrame], dict[str, pd.DataFrame], dict[str, list[dict[str, str]]]]:
    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    chart_frames: dict[str, pd.DataFrame] = {}
    reveal_chart_frames: dict[str, pd.DataFrame] = {}
    indicator_rows: dict[str, list[dict[str, str]]] = {}
    if not instruments:
        return pd.DataFrame(), [{"代码": "", "名称": "", "错误": "没有可分析对象。"}], {}, {}, {}
    try:
        provider = make_provider(data_source)
    except Exception as exc:
        return pd.DataFrame(), [{"代码": "", "名称": "", "错误": f"数据源不可用：{exc}"}], {}, {}, {}
    for instrument in instruments:
        symbol = _sentiment_symbol_for_provider(instrument.symbol, instrument.market or market, data_source)
        try:
            request = BarDataRequest(symbol=symbol, market=instrument.market or market, interval="1d", start=start, end=end, adjustment="auto")
            bars, _fallback = get_bars_with_interval_fallback(provider, request)
            case = market_feel_training_case(
                bars,
                symbol=instrument.symbol,
                name=instrument.name,
                market=instrument.market or market,
                role=instrument.role,
                answer_horizon=answer_horizon,
            )
            result = case.result
            row = case.to_row()
            label = f"{result.name} ({result.symbol})"
            row["chart_label"] = label
            rows.append(row)
            chart_frames[label] = market_feel_chart_frame(bars.iloc[: -int(answer_horizon)])
            reveal_chart_frames[label] = market_feel_chart_frame(bars)
            indicator_rows[label] = market_feel_indicator_rows(result)
        except Exception as exc:
            errors.append({"代码": instrument.symbol, "名称": instrument.name, "错误": str(exc)})
    return pd.DataFrame(rows), errors, chart_frames, reveal_chart_frames, indicator_rows


def render_market_feel_cards(rows: pd.DataFrame) -> None:
    st.markdown("#### 盘感训练卡片")
    columns = st.columns(3)
    for index, row in enumerate(rows.to_dict("records")):
        color_class = _market_feel_color_class(str(row.get("risk_state", "")), str(row.get("trend_state", "")))
        name = _escape_html(row.get("name", ""))
        symbol = _escape_html(row.get("symbol", ""))
        score = float(row.get("market_feel_score", 0.0) or 0.0)
        conclusion = _escape_html(row.get("training_conclusion", ""))
        explanation = _escape_html(row.get("explanation", ""))
        ma_help = _escape_html(f"{TERM_HELP['MA20']} {TERM_HELP['MA60']}")
        macd_help = _escape_html(TERM_HELP["MACD"])
        drawdown_help = _escape_html(TERM_HELP["最大回撤"])
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="ql-market-feel-card {color_class}">
                  <div class="ql-sentiment-top">
                    <span>{name}</span>
                    <strong>{score:.2f}</strong>
                  </div>
                  <div class="ql-sentiment-symbol">{symbol} · {row.get("role", "")} · {row.get("latest_date", "")}</div>
                  <div class="ql-market-feel-grid">
                    <span title="{ma_help}">趋势：{row.get("trend_state", "")}</span>
                    <span title="{macd_help}">动能：{row.get("momentum_state", "")}</span>
                    <span title="{drawdown_help}">风险：{row.get("risk_state", "")}</span>
                    <span>量价：{row.get("volume_state", "")}</span>
                  </div>
                  <div class="ql-sentiment-reading">{explanation}</div>
                  <div class="ql-market-feel-conclusion">{conclusion}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_market_feel_training_challenge(
    rows: pd.DataFrame,
    chart_label: str,
    training_level: str,
    time_limit_seconds: int,
    reveal_frame: pd.DataFrame | None,
) -> None:
    matching = rows[rows.get("chart_label", "") == chart_label] if "chart_label" in rows.columns else pd.DataFrame()
    if matching.empty:
        return
    row = matching.iloc[0].to_dict()
    key = hashlib.sha1(chart_label.encode("utf-8")).hexdigest()[:12]
    start_key = f"market_feel_started_{key}"
    feedback_key = f"market_feel_feedback_{key}"
    st.markdown("#### 限时判断")
    st.caption("先在限定时间内独立判断，再提交查看答案。技术分析在答案揭示前已锁定，不按结果倒推。")
    info_cols = st.columns(4)
    info_cols[0].metric("难度", training_level, help=TERM_HELP["训练难度"])
    info_cols[1].metric("判断周期", f"{int(row.get('answer_horizon', 0) or 0)}日", help=TERM_HELP["判断周期"])
    info_cols[2].metric("限时", f"{int(time_limit_seconds)}秒", help=TERM_HELP["限时秒数"])
    info_cols[3].metric("可见截止", str(row.get("latest_date", "")), help="你作答前可看到的最后一个交易日；后面的答案区间会被隐藏。")

    if st.button("开始限时判断", key=f"market_feel_start_button_{key}"):
        st.session_state[start_key] = time.time()
        st.session_state.pop(feedback_key, None)
    start_time = st.session_state.get(start_key)
    if start_time:
        elapsed = max(0.0, time.time() - float(start_time))
        remaining = max(0.0, float(time_limit_seconds) - elapsed)
        st.progress(min(1.0, elapsed / max(1.0, float(time_limit_seconds))))
        render_countdown_component(key, float(start_time), int(time_limit_seconds))
        if remaining <= 0:
            st.warning(f"已超时 {elapsed - float(time_limit_seconds):.1f} 秒。仍可提交，但成绩会记录为超时。")
        else:
            st.caption(f"已用 {elapsed:.1f} 秒，后端记录剩余 {remaining:.1f} 秒；上方计时器会自动刷新显示。")
    else:
        st.info("点击“开始限时判断”后再作答；也可以直接作答，但本次不计入限时。")

    direction = st.radio("方向判断", ["上涨", "下跌", "震荡"], horizontal=True, key=f"market_feel_direction_{key}", help="只判断答案周期结束时相对当前可见截止价的方向。")
    selected_interval = ""
    precise_return = None
    if training_level in {"中等", "专家"}:
        selected_interval = st.radio("收益区间判断", _market_feel_return_interval_options(), horizontal=True, key=f"market_feel_interval_{key}", help=TERM_HELP["收益区间判断"])
    if training_level == "专家":
        precise_return = st.number_input("预计区间涨跌幅", min_value=-50.0, max_value=50.0, value=0.0, step=0.10, format="%.2f", key=f"market_feel_precise_{key}", help=TERM_HELP["预计区间涨跌幅"])
        st.caption("单位是百分比。例如预计上涨 2.35%，填写 2.35；预计下跌 1.20%，填写 -1.20。")

    if st.button("提交并查看答案", key=f"market_feel_submit_{key}"):
        elapsed = max(0.0, time.time() - float(start_time)) if start_time else None
        st.session_state[feedback_key] = _market_feel_answer_feedback(
            row=row,
            training_level=training_level,
            direction=direction,
            selected_interval=selected_interval,
            precise_return=precise_return,
            elapsed_seconds=elapsed,
            time_limit_seconds=time_limit_seconds,
        )

    feedback = st.session_state.get(feedback_key)
    if not feedback:
        return
    status = "正确" if feedback["passed"] else "需要复盘"
    st.markdown(
        f"""
        <div class="ql-market-feel-answer">
          <div class="ql-market-feel-answer-title">{status} · 得分 {feedback["score"]:.2f}</div>
          <div>{_escape_html(feedback["summary"])}</div>
          <div class="ql-market-feel-answer-note">{_escape_html(str(row.get("fairness_note", "")))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("##### 事前技术分析")
    st.write(str(row.get("pre_result_analysis", row.get("analysis", ""))))
    st.markdown("##### 揭示后多维复盘")
    st.write(str(row.get("post_result_review", "")))
    if reveal_frame is not None and not reveal_frame.empty:
        with st.expander("揭示完整走势", expanded=True):
            show_market_feel_chart(reveal_frame, f"{chart_label} · 完整结果")


def _market_feel_answer_feedback(
    row: dict[str, object],
    training_level: str,
    direction: str,
    selected_interval: str,
    precise_return: float | None,
    elapsed_seconds: float | None,
    time_limit_seconds: int,
) -> dict[str, object]:
    actual_direction = str(row.get("actual_direction", ""))
    actual_interval = str(row.get("actual_return_interval", ""))
    actual_return = float(row.get("actual_return", 0.0) or 0.0)
    direction_ok = direction == actual_direction
    interval_ok = selected_interval == actual_interval if training_level in {"中等", "专家"} else True
    precise_ok = True
    precise_error = None
    if training_level == "专家":
        predicted = float(precise_return or 0.0) / 100.0
        precise_error = abs(predicted - actual_return)
        precise_ok = precise_error <= max(0.01, abs(actual_return) * 0.35)
    timed_ok = True if elapsed_seconds is None else elapsed_seconds <= float(time_limit_seconds)
    passed = direction_ok and interval_ok and precise_ok and timed_ok
    score = 0.0
    score += 45.0 if direction_ok else 0.0
    score += 30.0 if interval_ok else 0.0
    score += 20.0 if precise_ok else 0.0
    score += 5.0 if timed_ok else 0.0
    if training_level == "入门":
        score = 100.0 if direction_ok and timed_ok else 60.0 if direction_ok else 0.0
    elif training_level == "中等":
        score = (55.0 if direction_ok else 0.0) + (40.0 if interval_ok else 0.0) + (5.0 if timed_ok else 0.0)
    elapsed_text = "未计时" if elapsed_seconds is None else f"{elapsed_seconds:.1f}秒"
    precise_text = "" if precise_error is None else f"，精确误差 {precise_error:.2%}"
    summary = (
        f"你的方向：{direction}，实际方向：{actual_direction}；"
        f"你的区间：{selected_interval or '未要求'}，实际区间：{actual_interval}；"
        f"实际收益率：{actual_return:.2%}；用时：{elapsed_text}{precise_text}。"
    )
    return {"passed": bool(passed), "score": round(float(score), 2), "summary": summary}


def _market_feel_return_interval_options() -> list[str]:
    return ["-5.00%以下", "-5.00%至-2.00%", "-2.00%至0.00%", "0.00%至2.00%", "2.00%至5.00%", "5.00%以上"]


def show_market_feel_chart(frame: pd.DataFrame, title: str) -> None:
    if go is None or make_subplots is None or frame.empty:
        return
    data = frame.copy()
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.56, 0.20, 0.24],
        vertical_spacing=0.04,
        subplot_titles=(title, "RSI14", "MACD"),
    )
    fig.add_trace(
        go.Candlestick(
            x=data["datetime"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            increasing_line_color="#b91c1c",
            increasing_fillcolor="#b91c1c",
            decreasing_line_color="#15803d",
            decreasing_fillcolor="#15803d",
            name="价格",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["ma20"], mode="lines", name="MA20", line=dict(color="#2563eb", width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["ma60"], mode="lines", name="MA60", line=dict(color="#7c3aed", width=1.4)), row=1, col=1)
    if {"support20", "resistance20"}.issubset(data.columns):
        fig.add_trace(go.Scatter(x=data["datetime"], y=data["support20"], mode="lines", name="20日支撑", line=dict(color="#0f766e", width=1, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=data["datetime"], y=data["resistance20"], mode="lines", name="20日压力", line=dict(color="#b7791f", width=1, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["bb_upper"], mode="lines", name="Bollinger 上轨", line=dict(color="#94a3b8", width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["bb_lower"], mode="lines", name="Bollinger 下轨", line=dict(color="#94a3b8", width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["rsi14"], mode="lines", name="RSI14", line=dict(color="#0f766e", width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#b91c1c", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#2563eb", row=2, col=1)
    macd_colors = ["#b91c1c" if value >= 0 else "#15803d" for value in data["macd_hist"].fillna(0.0)]
    fig.add_trace(go.Bar(x=data["datetime"], y=data["macd_hist"], name="MACD 柱", marker_color=macd_colors, opacity=0.62), row=3, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["macd"], mode="lines", name="MACD", line=dict(color="#111827", width=1.1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["macd_signal"], mode="lines", name="信号线", line=dict(color="#64748b", width=1.1)), row=3, col=1)
    fig.update_layout(
        height=780,
        margin=dict(l=20, r=20, t=70, b=30),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    st.plotly_chart(fig, width="stretch")


def _display_market_feel_frame(rows: pd.DataFrame) -> pd.DataFrame:
    display = rows.copy()
    percentage_columns = [
        "one_day_return",
        "five_day_return",
        "twenty_day_return",
        "sixty_day_return",
        "price_vs_ma20",
        "price_vs_ma60",
        "atr14_ratio",
        "volatility20",
        "max_drawdown60",
        "price_vs_support20",
        "price_vs_resistance20",
        "actual_return",
    ]
    for column in percentage_columns:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):.2%}")
    for column in ["close", "rsi14", "macd_hist", "bollinger_position", "volume_ratio20", "market_feel_score", "support20", "resistance20"]:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce").fillna(0.0).map(lambda value: f"{float(value):,.2f}")
    return display.rename(
        columns={
            "symbol": "代码",
            "name": "名称",
            "market": "市场",
            "role": "角色",
            "latest_date": "最新日期",
            "close": "收盘价",
            "one_day_return": "1日涨跌",
            "five_day_return": "5日涨跌",
            "twenty_day_return": "20日涨跌",
            "sixty_day_return": "60日涨跌",
            "rsi14": "RSI14",
            "macd_hist": "MACD 柱",
            "price_vs_ma20": "相对 MA20",
            "price_vs_ma60": "相对 MA60",
            "bollinger_position": "Bollinger 位置",
            "atr14_ratio": "ATR14/价格",
            "volatility20": "20日年化波动",
            "volume_ratio20": "成交量比",
            "max_drawdown60": "60日最大回撤",
            "support20": "20日支撑",
            "resistance20": "20日压力",
            "price_vs_support20": "距支撑",
            "price_vs_resistance20": "距压力",
            "trend_state": "趋势判断",
            "momentum_state": "动能判断",
            "risk_state": "风险判断",
            "volume_state": "量价判断",
            "market_feel_score": "盘感分",
            "training_conclusion": "训练结论",
            "explanation": "讲解",
            "analysis": "分析",
            "practice_prompt": "训练题",
            "data_points": "样本点",
            "answer_horizon": "答案周期",
            "hidden_start_date": "答案开始",
            "hidden_end_date": "答案结束",
            "actual_return": "实际收益率",
            "actual_direction": "实际方向",
            "actual_return_interval": "实际区间",
            "technical_expected_direction": "技术面倾向",
            "technical_alignment": "一致性",
            "pre_result_analysis": "事前技术分析",
            "post_result_review": "多维复盘",
            "fairness_note": "训练说明",
            "chart_label": "图表标签",
        }
    )


def market_feel_terms_panel() -> None:
    with st.expander("盘感训练口径", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {"术语": "盘感分", "说明": "0-100 分，综合趋势、动能、风险和量价确认；用于训练读图，不代表涨跌预测。"},
                    {"术语": "MA20/MA60", "说明": "20 日和 60 日均线。价格在均线上方通常说明结构偏强，在下方说明承压。"},
                    {"术语": "RSI14", "说明": "14 日相对强弱。高于 70 可能拥挤，低于 30 可能低迷。"},
                    {"术语": "MACD", "说明": "观察短中期动能差。柱体转正通常表示动能改善，转负表示动能走弱。"},
                    {"术语": "Bollinger 位置", "说明": "价格在布林带中的相对位置。接近上轨关注拥挤或突破，接近下轨关注风险释放或反弹失败。"},
                    {"术语": "ATR14/价格", "说明": "近 14 日平均真实波幅占价格比例，越高表示短线扰动越大。"},
                    {"术语": "成交量比", "说明": "最新成交量相对 20 日均量。放量上涨和放量下跌的含义不同，需要结合趋势。"},
                    {"术语": "20日支撑/压力", "说明": "用近 20 日低点和高点近似观察需求区和供给区，只是结构参考，不是固定价格墙。"},
                    {"术语": "入门模式", "说明": "只判断未来指定周期的方向：上涨、下跌或震荡。"},
                    {"术语": "中等模式", "说明": "判断方向，并选择未来指定周期的大致收益区间。"},
                    {"术语": "专家模式", "说明": "判断方向、区间和更精确的涨跌幅，系统会记录误差。"},
                    {"术语": "事前技术分析", "说明": "只使用答案揭示前的行情和指标，不能根据真实结果倒推分析过程。"},
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def _market_feel_color_class(risk_state: str, trend_state: str) -> str:
    if risk_state == "风险升温":
        return "ql-market-feel-risk"
    if trend_state in {"多头结构", "短期改善"}:
        return "ql-market-feel-strong"
    if trend_state in {"空头结构", "短期承压"}:
        return "ql-market-feel-weak"
    return "ql-market-feel-neutral"


def personal_profile_view() -> None:
    st.subheader("个人画像")
    st.caption("综合持仓数据、回测元数据、复盘记录和验证任务，分析行为习惯、风险和优化方向；不生成实盘操作指令。")
    holdings = load_current_holdings()
    if holdings.empty:
        holdings = load_holdings_frame()
    runs = run_metadata_summaries_frame(REPORT_ROOT_DIR)
    reviews = trade_review_frame()
    tasks = validation_task_frame()
    profile = build_personal_profile(holdings, runs=runs, reviews=reviews, validation_tasks=tasks)
    summary = profile["summary"]

    cols = st.columns(5)
    cols[0].metric("持仓总市值", _format_metric_value(summary["total_position_value"], "currency"))
    cols[1].metric("持仓数量", str(summary["holding_count"]))
    cols[2].metric("最大单一权重", _format_metric_value(summary["top1_weight"], "percent"))
    cols[3].metric("前三权重", _format_metric_value(summary["top3_weight"], "percent"))
    cols[4].metric("集中度 HHI", _format_metric_value(summary["concentration_hhi"], "number"))

    status = external_system_status()
    with st.expander("数据连接状态", expanded=False):
        st.dataframe(
            status.rename(columns={"system": "系统", "status": "状态", "path": "路径", "expected": "期望数据"}),
            width="stretch",
            hide_index=True,
        )
        st.caption("持仓文件支持 CSV、XLSX、JSON。字段建议包含 symbol/代码、name/名称、market/市场、quantity/持仓数量、position_value/市值、weight/权重。")

    if holdings.empty:
        st.warning("未读取到消费行为分析系统或 PFI 持仓数据。页面会先基于回测、复盘和验证任务生成画像；持仓集中度需要配置后才准确。")
    else:
        st.markdown("#### 持仓数据")
        display_holdings = holdings.copy()
        for column in ["quantity", "cost_basis", "position_value", "unrealized_pnl"]:
            display_holdings[column] = display_holdings[column].map(lambda value: f"{float(value):,.2f}")
        display_holdings["weight"] = display_holdings["weight"].map(lambda value: f"{float(value):.2%}")
        st.dataframe(
            display_holdings.rename(
                columns={
                    "source_system": "来源系统",
                    "source_file": "来源文件",
                    "symbol": "代码",
                    "name": "名称",
                    "market": "市场",
                    "quantity": "数量",
                    "cost_basis": "成本",
                    "position_value": "市值",
                    "unrealized_pnl": "浮动盈亏",
                    "weight": "权重",
                    "updated_at": "更新时间",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        exposure = holdings.groupby(["source_system", "market"], dropna=False).agg(position_value=("position_value", "sum"), weight=("weight", "sum")).reset_index()
        exposure["position_value"] = exposure["position_value"].map(lambda value: f"{float(value):,.2f}")
        exposure["weight"] = exposure["weight"].map(lambda value: f"{float(value):.2%}")
        st.write("持仓来源与市场暴露")
        st.dataframe(exposure.rename(columns={"source_system": "来源系统", "market": "市场", "position_value": "市值", "weight": "权重"}), width="stretch", hide_index=True)

    st.markdown("#### 行为习惯")
    st.dataframe(pd.DataFrame(profile["habits"]), width="stretch", hide_index=True)

    st.markdown("#### 风险画像")
    st.dataframe(pd.DataFrame(profile["risks"]), width="stretch", hide_index=True)

    st.markdown("#### 行为优化")
    st.dataframe(pd.DataFrame(profile["suggestions"]), width="stretch", hide_index=True)

    tab_runs, tab_reviews, tab_tasks = st.tabs(["研究证据", "复盘行为", "验证任务"])
    with tab_runs:
        if runs.empty:
            st.info("暂无回测运行元数据。")
        else:
            visible = [column for column in ["date_folder", "strategy_id", "total_return", "max_drawdown", "research_status", "decision_quality_score", "missing_evidence_count", "metadata_path"] if column in runs.columns]
            display = runs[visible].copy()
            for column in ["total_return", "max_drawdown"]:
                if column in display.columns:
                    display[column] = display[column].map(lambda value: f"{float(value):.2%}")
            st.dataframe(display, width="stretch", hide_index=True)
    with tab_reviews:
        if reviews.empty:
            st.info("暂无复盘记录。")
        else:
            st.dataframe(reviews, width="stretch", hide_index=True)
    with tab_tasks:
        if tasks.empty:
            st.info("暂无验证任务。")
        else:
            st.dataframe(tasks, width="stretch", hide_index=True)


def report_center_view() -> None:
    st.subheader("报告中心")
    REPORT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    st.caption(f"报告目录：{REPORT_ROOT_DIR}")
    counts = artifact_counts(REPORT_ROOT_DIR)
    artifacts = report_artifacts_frame(REPORT_ROOT_DIR)
    experiments = experiment_summaries_frame(REPORT_ROOT_DIR)
    runs = run_metadata_summaries_frame(REPORT_ROOT_DIR)
    date_folder_count = len([p for p in REPORT_ROOT_DIR.iterdir() if p.is_dir()]) if REPORT_ROOT_DIR.exists() else 0
    card_columns = st.columns(5)
    for column, card in zip(card_columns, report_dashboard_cards(counts, artifacts, runs, experiments, date_folder_count)):
        column.metric(str(card["label"]), card["value"], help=str(card["help"]))
    action_col1, action_col2 = st.columns([0.25, 0.75])
    if action_col1.button("打开报告目录"):
        _open_local_path(REPORT_ROOT_DIR)
    latest_overall = latest_report_artifact(artifacts, WORD_REPORT_TYPES)
    if latest_overall:
        action_col2.caption(
            "最新 Word 报告："
            f"{latest_overall.get('name', '')} | {latest_overall.get('artifact_type', '')} | {latest_overall.get('date_folder', '')}"
        )
    else:
        action_col2.caption("最新 Word 报告：暂无")

    tab_dashboard, tab_decision, tab_support, tab_validation, tab_reports, tab_runs, tab_experiments, tab_reviews, tab_cleanup = st.tabs(
        ["总览", "决策质量", "证据索引", "验证任务", "报告列表", "运行判读", "实验记录", "复盘错误", "安全清理"]
    )
    with tab_dashboard:
        show_report_center_dashboard(counts, artifacts, runs, experiments)

    with tab_decision:
        show_decision_quality_dashboard(runs)

    with tab_support:
        show_report_decision_support_panel()

    with tab_validation:
        show_validation_queue_panel(artifacts)

    with tab_reports:
        if artifacts.empty:
            st.info("暂无研究产物。运行一次回测或参数扫描后会自动生成。")
        else:
            artifact_types = sorted(str(value) for value in artifacts["artifact_type"].dropna().unique())
            date_folders = sorted((str(value) for value in artifacts["date_folder"].dropna().unique()), reverse=True)
            filter_col1, filter_col2 = st.columns(2)
            selected_types = filter_col1.multiselect("报告类型", artifact_types, default=artifact_types)
            selected_dates = filter_col2.multiselect("日期目录", date_folders, default=date_folders)
            search_query = st.text_input("搜索报告", placeholder="输入报告名、类型、日期或路径")
            filtered_artifacts = filter_report_artifacts_frame(artifacts, selected_types, selected_dates)
            filtered_artifacts = search_report_artifacts_frame(filtered_artifacts, search_query)
            st.caption(f"当前显示：{len(filtered_artifacts)} / {len(artifacts)}")
            if filtered_artifacts.empty:
                st.info("当前筛选条件下没有报告产物。")
            else:
                st.dataframe(_display_artifacts_frame(filtered_artifacts), width="stretch", hide_index=True)
                latest_report = latest_report_artifact(filtered_artifacts, WORD_REPORT_TYPES)
                if latest_report:
                    latest = Path(str(latest_report["path"]))
                    st.caption(f"最新报告：{latest}")
                    download_col, folder_col = st.columns(2)
                    with latest.open("rb") as handle:
                        download_col.download_button(
                            "下载最新 Word 报告",
                            data=handle,
                            file_name=latest.name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    if folder_col.button("打开最新报告所在目录"):
                        _open_local_path(latest.parent)

    with tab_runs:
        if runs.empty:
            st.info("暂无运行元数据。运行回测后会自动生成。")
        else:
            status_options = sorted(str(value) for value in runs["status"].dropna().unique())
            research_status_options = (
                sorted(str(value) for value in runs["research_status"].dropna().unique())
                if "research_status" in runs.columns
                else []
            )
            filter_col1, filter_col2 = st.columns(2)
            selected_status = filter_col1.multiselect("表现状态", status_options, default=status_options)
            selected_research_status = filter_col2.multiselect(
                "研究门禁状态",
                research_status_options,
                default=research_status_options,
            )
            filtered_runs = runs[runs["status"].isin(selected_status)] if selected_status else runs.iloc[0:0]
            if selected_research_status and "research_status" in filtered_runs.columns:
                filtered_runs = filtered_runs[filtered_runs["research_status"].isin(selected_research_status)]
            display = filtered_runs.copy()
            for column in ["total_return", "annualized_return", "max_drawdown", "cost_ratio"]:
                display[column] = display[column].map(lambda value: f"{float(value):.2%}")
            for column in ["sharpe", "initial_cash"]:
                display[column] = display[column].map(lambda value: f"{float(value):,.2f}")
            st.dataframe(
                display.rename(
                    columns={
                        "run": "运行",
                        "date_folder": "日期",
                        "strategy_id": "策略",
                        "total_return": "总收益率",
                        "annualized_return": "年化收益率",
                        "sharpe": "Sharpe",
                        "max_drawdown": "最大回撤",
                        "cost_ratio": "成本占比",
                        "trade_count": "交易次数",
                        "status": "状态",
                        "research_status": "研究门禁状态",
                        "decision_quality_score": "决策质量分",
                        "missing_evidence_count": "缺失证据数",
                        "initial_cash": "初始资金",
                        "metadata_path": "元数据",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    with tab_experiments:
        if experiments.empty:
            st.info("暂无实验记录。运行参数扫描后会自动生成。")
        else:
            display = experiments.copy()
            for column in ["best_total_return", "best_sharpe"]:
                if column in display.columns:
                    display[column] = display[column].map(_format_report_center_value)
            st.dataframe(display, width="stretch", hide_index=True)
            selected_summary = st.selectbox(
                "选择实验查看详情",
                options=list(experiments["summary_path"]),
                format_func=lambda path: _experiment_label(experiments, path),
            )
            if selected_summary:
                show_experiment_detail(selected_summary)

    with tab_reviews:
        show_trade_review_panel(runs, artifacts)

    with tab_cleanup:
        junk_targets = cleanup_report_junk(REPORT_ROOT_DIR, dry_run=True)
        st.write(f"可清理杂项文件数量：{len(junk_targets)}")
        if junk_targets:
            st.dataframe(pd.DataFrame({"路径": junk_targets}), width="stretch", hide_index=True)
        st.caption("只会清理 `.DS_Store`、旧 HTML 报告和 0 字节 Word 占位文件，不会删除正常 Word、JSON、CSV 研究产物。")
        if st.button("清理杂项文件"):
            removed = cleanup_report_junk(REPORT_ROOT_DIR, dry_run=False)
            st.success(f"已清理 {len(removed)} 个杂项文件。")


def show_decision_quality_dashboard(runs: pd.DataFrame) -> None:
    st.markdown("#### 决策质量 Dashboard")
    if runs.empty:
        st.info("暂无运行元数据。运行回测后会显示 Decision Quality Score。")
        return

    frame = runs.copy()
    if "research_status" not in frame.columns:
        frame["research_status"] = ""
    if "decision_quality_score" not in frame.columns:
        frame["decision_quality_score"] = 0
    if "missing_evidence_count" not in frame.columns:
        frame["missing_evidence_count"] = 0
    frame["decision_quality_score"] = pd.to_numeric(frame["decision_quality_score"], errors="coerce").fillna(0)
    frame["missing_evidence_count"] = pd.to_numeric(frame["missing_evidence_count"], errors="coerce").fillna(0)
    scored = frame[frame["decision_quality_score"] > 0]
    status_series = frame["research_status"].astype(str).replace("", "未记录")
    status_counts = status_series.value_counts().reset_index()
    status_counts.columns = ["研究状态", "数量"]

    cols = st.columns(4)
    cols[0].metric("研究运行", str(len(frame)))
    cols[1].metric("平均质量分", "N/A" if scored.empty else f"{scored['decision_quality_score'].mean():.0f}/100")
    cols[2].metric("需补证据", str(int((status_series == "NeedsMoreEvidence").sum())))
    cols[3].metric("缺失证据均值", f"{frame['missing_evidence_count'].mean():.2f}")

    if go is not None:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig = go.Figure(go.Bar(x=status_counts["研究状态"], y=status_counts["数量"], marker_color="#8A1538"))
            fig.update_layout(height=340, title="研究门禁状态分布", xaxis_title="研究状态", yaxis_title="数量")
            st.plotly_chart(fig, width="stretch")
        with chart_col2:
            plot = frame.copy()
            plot["total_return"] = pd.to_numeric(plot.get("total_return", 0.0), errors="coerce").fillna(0.0)
            fig = go.Figure(
                go.Scatter(
                    x=plot["decision_quality_score"],
                    y=plot["total_return"],
                    mode="markers",
                    text=plot["strategy_id"],
                    marker={"color": plot["missing_evidence_count"], "colorscale": "Blues", "showscale": True},
                    hovertemplate="策略=%{text}<br>质量分=%{x}<br>收益=%{y:.2%}<extra></extra>",
                )
            )
            fig.update_layout(height=340, title="质量分与回测收益", xaxis_title="Decision Quality Score", yaxis_title="总收益率")
            fig.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig, width="stretch")
    else:
        st.dataframe(status_counts, width="stretch", hide_index=True)

    low_quality = frame.sort_values(["decision_quality_score", "missing_evidence_count"], ascending=[True, False]).head(20)
    display = low_quality[
        [
            column
            for column in [
                "date_folder",
                "strategy_id",
                "research_status",
                "decision_quality_score",
                "missing_evidence_count",
                "total_return",
                "max_drawdown",
                "metadata_path",
            ]
            if column in low_quality.columns
        ]
    ].copy()
    for column in ["total_return", "max_drawdown"]:
        if column in display.columns:
            display[column] = display[column].map(lambda value: f"{float(value):.2%}")
    st.write("优先复核列表")
    st.dataframe(
        display.rename(
            columns={
                "date_folder": "日期",
                "strategy_id": "策略",
                "research_status": "研究状态",
                "decision_quality_score": "质量分",
                "missing_evidence_count": "缺失证据",
                "total_return": "总收益率",
                "max_drawdown": "最大回撤",
                "metadata_path": "元数据",
            }
        ),
        width="stretch",
        hide_index=True,
    )


def show_validation_queue_panel(artifacts: pd.DataFrame) -> None:
    st.markdown("#### 验证任务队列")
    st.caption("这里承接行研、政策、新闻或手工研究问题。任务只用于安排 PFI 验证，不代表实盘操作。默认先看“证据索引”页的报告验证工作台，再决定是否执行高级动作。")
    frame = validation_task_frame()
    card_cols = st.columns(4)
    for col, card in zip(card_cols, validation_queue_cards(frame)):
        col.metric(str(card["label"]), str(card["value"]), help=str(card["help"]))
    with st.expander("高级动作：入队、排序和执行", expanded=False):
        gap_col, priority_col, execute_col, refresh_col = st.columns([0.24, 0.24, 0.24, 0.28])
        if gap_col.button("从报告缺失证据生成任务"):
            result = append_report_gap_validation_tasks(project_root=ROOT, report_root=REPORT_ROOT_DIR, output_dir=ROOT / "data" / "reportDecision")
            st.success(
                "已生成补证据任务："
                f"候选 {result.get('task_count', 0)}，新增 {result.get('appended_task_count', 0)}，已存在 {result.get('skipped_existing_count', 0)}。"
            )
            frame = validation_task_frame()
        if priority_col.button("生成验证优先级计划"):
            plan = write_validation_priority_plan(project_root=ROOT, output_dir=ROOT / "data" / "validationQueue")
            st.success(
                "已生成优先级计划："
                f"队列 {plan.get('queue_record_count', 0)}，候选 {plan.get('candidate_record_count', 0)}，优先任务 {plan.get('prioritized_task_count', 0)}。"
            )
            priority_frame = validation_priority_frame(plan)
            if not priority_frame.empty:
                st.dataframe(
                    priority_frame.head(20).rename(
                        columns={
                            "priority_rank": "优先级",
                            "priority_score": "分数",
                            "action_bucket": "处理桶",
                            "evidence_gap": "证据缺口",
                            "symbol": "标的",
                            "market": "市场",
                            "research_topic": "研究主题",
                            "blockers": "阻塞项",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )
        if execute_col.button("执行最高优先级验证任务"):
            execution = write_validation_task_execution(project_root=ROOT, output_dir=ROOT / "data" / "validationQueue")
            st.success(
                "已生成验证执行记录："
                f"状态 {execution.get('execution_status', '')}，"
                f"证据 {execution.get('evidence_status', '')}，"
                f"任务 {execution.get('task_id', '')}。"
            )
            if execution.get("blockers"):
                st.warning("阻塞项：" + "；".join(str(item) for item in execution.get("blockers", [])))
            if execution.get("outputs"):
                st.caption(f"执行记录：{execution['outputs'].get('json', '')}")
        refresh_col.caption("补证据入队和执行验证属于显式高级动作；不会自动刷新行情、不改旧报告、不连接实盘。")

    report_options = _word_report_options(artifacts)
    with st.form("validation_task_form"):
        st.write("新增验证任务")
        col_a, col_b = st.columns(2)
        source_report = col_a.text_input("来源报告", value="")
        source_paragraph = col_b.text_input("来源段落", value="")
        research_topic = st.text_input("研究主题", value="")
        col_c, col_d, col_e = st.columns(3)
        symbol = col_c.text_input("待验证标的", value="")
        market = col_d.selectbox("市场", ["CN", "US", "HK", "Other"], index=0)
        status = col_e.selectbox("当前状态", list(VALIDATION_TASK_STATUSES), index=0)
        signal_to_validate = st.text_area("待验证信号", value="")
        col_f, col_g = st.columns(2)
        sample_period = col_f.text_input("样本区间", value="")
        benchmark = col_g.text_input("基准", value="")
        cost_assumption = st.text_input("成本假设", value="佣金、滑点、市场冲击按回测参数设置")
        validation_report_path = st.selectbox("验证报告路径", [""] + report_options)
        notes = st.text_area("备注", value="")
        submitted = st.form_submit_button("保存验证任务")
        if submitted:
            task = create_validation_task(
                {
                    "source_report": source_report,
                    "source_paragraph": source_paragraph,
                    "research_topic": research_topic,
                    "symbol": symbol,
                    "market": market,
                    "signal_to_validate": signal_to_validate,
                    "sample_period": sample_period,
                    "cost_assumption": cost_assumption,
                    "benchmark": benchmark,
                    "status": status,
                    "validation_report_path": validation_report_path,
                    "notes": notes,
                }
            )
            path = save_validation_task(task)
            st.success(f"验证任务已保存：{path}")

    if frame.empty:
        st.info("暂无验证任务。新增任务后会显示任务队列。")
        return
    display = frame.copy().sort_values("created_at", ascending=False)
    visible = [
        "created_at",
        "research_topic",
        "symbol",
        "market",
        "signal_to_validate",
        "sample_period",
        "cost_assumption",
        "benchmark",
        "status",
        "validation_report_path",
        "source_report",
    ]
    st.write("任务列表")
    st.dataframe(
        display[visible].rename(
            columns={
                "created_at": "创建时间",
                "research_topic": "研究主题",
                "symbol": "标的",
                "market": "市场",
                "signal_to_validate": "待验证信号",
                "sample_period": "样本区间",
                "cost_assumption": "成本假设",
                "benchmark": "基准",
                "status": "状态",
                "validation_report_path": "验证报告",
                "source_report": "来源报告",
            }
        ),
        width="stretch",
        hide_index=True,
    )


def show_trade_review_panel(runs: pd.DataFrame, artifacts: pd.DataFrame) -> None:
    st.markdown("#### 复盘与错误画像")
    st.caption("这里保存手工复盘记录，用于长期统计错误类型、纪律执行率和盈亏归因；不连接券商，也不生成实盘操作指令。")
    frame = trade_review_frame()
    card_cols = st.columns(4)
    for col, card in zip(card_cols, review_dashboard_cards(frame)):
        col.metric(str(card["label"]), str(card["value"]), help=str(card["help"]))

    if not frame.empty:
        profile = error_profile_frame(frame)
        display_profile = profile.copy()
        for column in ["avg_pnl_ratio", "discipline_violation_rate"]:
            display_profile[column] = display_profile[column].map(lambda value: f"{float(value):.2%}")
        display_profile["avg_pnl"] = display_profile["avg_pnl"].map(lambda value: f"{float(value):,.2f}")
        st.write("错误画像")
        st.dataframe(
            display_profile.rename(
                columns={
                    "error_type": "错误类型",
                    "count": "次数",
                    "avg_pnl": "平均盈亏",
                    "avg_pnl_ratio": "平均盈亏率",
                    "discipline_violation_rate": "纪律违反率",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    with st.form("trade_review_form"):
        st.write("新增复盘记录")
        latest_run = _latest_run_payload(runs)
        run_options = ["手动录入"] + list(runs["metadata_path"]) if not runs.empty and "metadata_path" in runs.columns else ["手动录入"]
        selected_run = st.selectbox("关联运行元数据", run_options)
        selected_payload = _run_payload_from_selection(runs, selected_run) if selected_run != "手动录入" else latest_run
        report_options = _word_report_options(artifacts)
        default_report = report_options[0] if report_options else ""

        col_a, col_b, col_c = st.columns(3)
        symbol = col_a.text_input("标的", value=str(selected_payload.get("symbol", "")))
        market = col_b.selectbox("市场", ["CN", "US", "HK", "Other"], index=0)
        strategy_id = col_c.text_input("策略", value=str(selected_payload.get("strategy_id", "")))

        col_d, col_e, col_f = st.columns(3)
        research_status = col_d.selectbox(
            "研究状态",
            ["ContinueResearch", "WatchOnly", "NeedsMoreEvidence", "DoNotUse", "未记录"],
            index=_select_index(["ContinueResearch", "WatchOnly", "NeedsMoreEvidence", "DoNotUse", "未记录"], selected_payload.get("research_status", "未记录")),
        )
        decision_quality_score = col_e.number_input("Decision Quality Score", min_value=0, max_value=100, value=int(selected_payload.get("decision_quality_score", 0) or 0))
        action_type = col_f.selectbox("记录类型", list(ACTION_TYPES), index=2)

        col_g, col_h = st.columns(2)
        planned_amount = col_g.number_input("计划暴露金额", min_value=0.0, value=0.0, step=1000.0)
        planned_ratio = col_h.number_input("计划暴露比例", min_value=0.0, max_value=1.0, value=0.0, step=0.01, format="%.2f")

        original_plan = st.text_area("原始研究计划", value="")
        observation_reason = st.text_area("观察或执行理由", value="")
        backtest_reference = st.selectbox("关联 Word 报告", [default_report] + [item for item in report_options if item != default_report] if default_report else [""])

        col_i, col_j, col_k = st.columns(3)
        actual_time = col_i.text_input("实际执行时间", value="")
        actual_price = col_j.number_input("实际价格", min_value=0.0, value=0.0, step=0.01)
        final_pnl = col_k.number_input("最终盈亏金额", value=0.0, step=100.0)
        final_pnl_ratio = st.number_input("最终盈亏率", value=0.0, step=0.01, format="%.4f")

        check_cols = st.columns(6)
        executed_as_planned = check_cols[0].checkbox("按计划执行", value=True)
        discipline_violation = check_cols[1].checkbox("违反纪律")
        early_exit = check_cols[2].checkbox("提前退出")
        news_impulse = check_cols[3].checkbox("新闻冲动")
        emotional_add = check_cols[4].checkbox("情绪补仓")
        chase_up = check_cols[5].checkbox("追高")

        col_l, col_m = st.columns(2)
        return_attribution = col_l.selectbox("盈亏来源归因", list(RETURN_ATTRIBUTION_TYPES), index=len(RETURN_ATTRIBUTION_TYPES) - 1)
        error_type = col_m.selectbox("错误类型", ["未确认"] + list(ERROR_TYPES), index=0)
        market_environment = st.text_input("市场环境", value="")
        notes = st.text_area("复盘备注", value="")
        submitted = st.form_submit_button("保存复盘记录")
        if submitted:
            record = create_trade_review_record(
                {
                    "symbol": symbol,
                    "market": market,
                    "strategy_id": strategy_id,
                    "research_status": research_status,
                    "decision_quality_score": decision_quality_score,
                    "action_type": action_type,
                    "planned_exposure_amount": planned_amount,
                    "planned_exposure_ratio": planned_ratio,
                    "original_plan": original_plan,
                    "observation_reason": observation_reason,
                    "backtest_reference": backtest_reference,
                    "actual_execution_time": actual_time,
                    "actual_price": actual_price,
                    "executed_as_planned": executed_as_planned,
                    "discipline_violation": discipline_violation,
                    "early_exit": early_exit,
                    "news_impulse": news_impulse,
                    "emotional_add": emotional_add,
                    "chase_up": chase_up,
                    "final_pnl_amount": final_pnl,
                    "final_pnl_ratio": final_pnl_ratio,
                    "return_attribution": return_attribution,
                    "error_type": error_type,
                    "market_environment": market_environment,
                    "notes": notes,
                }
            )
            path = save_trade_review_record(record)
            st.success(f"复盘记录已保存：{path}")

    if frame.empty:
        st.info("暂无复盘记录。保存第一条记录后会显示明细和错误画像。")
    else:
        display = frame.copy().sort_values("created_at", ascending=False)
        for column in ["planned_exposure_ratio", "final_pnl_ratio"]:
            display[column] = display[column].map(lambda value: f"{float(value):.2%}")
        for column in ["planned_exposure_amount", "actual_price", "final_pnl_amount"]:
            display[column] = display[column].map(lambda value: f"{float(value):,.2f}")
        visible = [
            "created_at",
            "symbol",
            "market",
            "strategy_id",
            "research_status",
            "decision_quality_score",
            "action_type",
            "executed_as_planned",
            "discipline_violation",
            "final_pnl_amount",
            "final_pnl_ratio",
            "return_attribution",
            "error_type",
            "market_environment",
            "notes",
        ]
        st.write("复盘明细")
        st.dataframe(display[visible], width="stretch", hide_index=True)


def _latest_run_payload(runs: pd.DataFrame) -> dict[str, object]:
    if runs.empty:
        return {}
    row = runs.iloc[0]
    return {
        "strategy_id": row.get("strategy_id", ""),
        "research_status": row.get("research_status", "未记录"),
        "decision_quality_score": int(row.get("decision_quality_score", 0) or 0),
    }


def _run_payload_from_selection(runs: pd.DataFrame, selected: str) -> dict[str, object]:
    if runs.empty or "metadata_path" not in runs.columns:
        return {}
    row = runs[runs["metadata_path"].astype(str) == str(selected)]
    if row.empty:
        return {}
    item = row.iloc[0]
    return {
        "strategy_id": item.get("strategy_id", ""),
        "research_status": item.get("research_status", "未记录"),
        "decision_quality_score": int(item.get("decision_quality_score", 0) or 0),
    }


def _word_report_options(artifacts: pd.DataFrame) -> list[str]:
    if artifacts.empty or "artifact_type" not in artifacts.columns:
        return []
    word_reports = artifacts[artifacts["artifact_type"].isin(WORD_REPORT_TYPES)].copy()
    if word_reports.empty:
        return []
    return [str(path) for path in word_reports["path"].dropna().head(50)]


def _select_index(options: list[str], value: object) -> int:
    text = str(value)
    return options.index(text) if text in options else len(options) - 1


def _display_artifacts_frame(artifacts: pd.DataFrame) -> pd.DataFrame:
    display = artifacts.rename(
        columns={
            "name": "名称",
            "artifact_type": "类型",
            "date_folder": "日期",
            "size_kb": "大小 KB",
            "path": "路径",
        }
    )
    return display[["名称", "类型", "日期", "大小 KB", "路径"]]


def show_report_center_dashboard(counts: dict[str, int], artifacts: pd.DataFrame, runs: pd.DataFrame, experiments: pd.DataFrame) -> None:
    st.markdown("#### 研究资产总览")
    if artifacts.empty and runs.empty and experiments.empty:
        st.info("暂无可视化数据。运行回测、参数扫描或导出报告后，这里会显示研究资产趋势。")
        return

    artifact_rows = [
        {"类型": key, "数量": value}
        for key, value in counts.items()
        if key != "Word Report" and int(value) > 0
    ]
    activity = report_activity_frame(artifacts)
    status_counts = run_status_counts_frame(runs)
    strategy_summary = strategy_run_summary_frame(runs)

    if go is None:
        if artifact_rows:
            st.dataframe(pd.DataFrame(artifact_rows), width="stretch", hide_index=True)
        if not strategy_summary.empty:
            st.dataframe(_display_strategy_summary(strategy_summary), width="stretch", hide_index=True)
        return

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if artifact_rows:
            artifact_df = pd.DataFrame(artifact_rows).sort_values("数量", ascending=True)
            fig = go.Figure(go.Bar(x=artifact_df["数量"], y=artifact_df["类型"], orientation="h", marker_color="#8A1538"))
            fig.update_layout(height=360, title="研究资产类型", xaxis_title="数量", yaxis_title="")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("暂无资产类型统计。")
    with chart_col2:
        if not activity.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=activity["date_folder"], y=activity["word_reports"], name="Word 报告", marker_color="#8A1538"))
            fig.add_trace(go.Bar(x=activity["date_folder"], y=activity["data_checks"], name="数据检查", marker_color="#0F766E"))
            fig.add_trace(go.Bar(x=activity["date_folder"], y=activity["experiments"], name="实验记录", marker_color="#2563EB"))
            fig.update_layout(height=360, title="日期活动", barmode="stack", xaxis_title="日期", yaxis_title="数量")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("暂无日期活动。")

    run_col1, run_col2 = st.columns(2)
    with run_col1:
        if not runs.empty:
            plot_runs = runs.copy()
            plot_runs["total_return"] = pd.to_numeric(plot_runs["total_return"], errors="coerce").fillna(0.0)
            plot_runs["max_drawdown"] = pd.to_numeric(plot_runs["max_drawdown"], errors="coerce").fillna(0.0)
            plot_runs["trade_count"] = pd.to_numeric(plot_runs["trade_count"], errors="coerce").fillna(0.0)
            fig = go.Figure(
                go.Scatter(
                    x=plot_runs["max_drawdown"],
                    y=plot_runs["total_return"],
                    mode="markers",
                    text=plot_runs["strategy_id"],
                    marker={
                        "size": (plot_runs["trade_count"].clip(lower=1, upper=80) ** 0.5) * 4,
                        "color": plot_runs["sharpe"],
                        "colorscale": "RdYlGn",
                        "showscale": True,
                        "colorbar": {"title": "Sharpe"},
                        "line": {"color": "#344054", "width": 0.5},
                    },
                    hovertemplate="策略=%{text}<br>总收益=%{y:.2%}<br>回撤=%{x:.2%}<extra></extra>",
                )
            )
            fig.update_layout(height=390, title="运行收益/回撤分布", xaxis_title="最大回撤", yaxis_title="总收益率")
            fig.update_xaxes(tickformat=".2%")
            fig.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("暂无运行元数据。")
    with run_col2:
        if not runs.empty and "date_folder" in runs.columns:
            trend = runs.copy().sort_values("date_folder")
            trend["total_return"] = pd.to_numeric(trend["total_return"], errors="coerce").fillna(0.0)
            trend["max_drawdown"] = pd.to_numeric(trend["max_drawdown"], errors="coerce").fillna(0.0)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["date_folder"], y=trend["total_return"], mode="lines+markers", name="总收益率", line={"color": "#8A1538"}))
            fig.add_trace(go.Scatter(x=trend["date_folder"], y=trend["max_drawdown"], mode="lines+markers", name="最大回撤", line={"color": "#0F766E"}))
            fig.update_layout(height=390, title="最近运行趋势", xaxis_title="日期", yaxis_title="收益 / 回撤")
            fig.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig, width="stretch")
        elif not status_counts.empty:
            fig = go.Figure(go.Bar(x=status_counts["status"], y=status_counts["count"], marker_color="#2563EB"))
            fig.update_layout(height=390, title="运行状态", xaxis_title="状态", yaxis_title="数量")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("暂无运行趋势。")

    if not strategy_summary.empty:
        st.markdown("#### 策略表现汇总")
        st.dataframe(_display_strategy_summary(strategy_summary), width="stretch", hide_index=True)

    if not experiments.empty and "best_total_return" in experiments.columns:
        experiment_plot = experiments.copy()
        experiment_plot["best_total_return"] = pd.to_numeric(experiment_plot["best_total_return"], errors="coerce").fillna(0.0)
        experiment_plot = experiment_plot.sort_values("best_total_return", ascending=False).head(12)
        fig = go.Figure(go.Bar(x=experiment_plot["experiment"], y=experiment_plot["best_total_return"], marker_color="#8A1538"))
        fig.update_layout(height=360, title="实验最佳收益", xaxis_title="实验", yaxis_title="最佳总收益率")
        fig.update_yaxes(tickformat=".2%")
        st.plotly_chart(fig, width="stretch")


def show_report_decision_support_panel() -> None:
    from pfi_os.reports import build_report_decision_support_index, write_report_decision_support_index

    payload = build_report_decision_support_index(project_root=ROOT, report_root=REPORT_ROOT_DIR)
    hub = build_report_validation_hub(project_root=ROOT, report_root=REPORT_ROOT_DIR, report_decision_payload=payload)
    hub_payload = report_validation_hub_summary(hub)
    summary = payload.get("summary", {})
    st.markdown("#### 报告验证工作台")
    st.caption("默认只读合并报告证据、补证据候选和验证优先级；不写文件、不入队、不执行验证，减少重复按钮和上下文噪音。")
    hub_cols = st.columns(5)
    hub_cols[0].metric("工作台状态", str(hub.get("status", "")))
    hub_cols[1].metric("报告记录", int(hub["summary"].get("report_record_count", 0) or 0))
    hub_cols[2].metric("需补证据", int(hub["summary"].get("needs_more_evidence_count", 0) or 0))
    hub_cols[3].metric("候选任务", int(hub["summary"].get("gap_candidate_task_count", 0) or 0))
    hub_cols[4].metric("优先任务", int(hub["summary"].get("prioritized_task_count", 0) or 0))
    if st.button("刷新报告验证摘要", type="primary"):
        st.json(hub_payload, expanded=False)
    st.caption(str(hub.get("next_action", "")))

    st.markdown("#### 报告证据索引")
    st.caption("按 RunMetadata 和 Word 报告判断每份报告是否足够支撑研究决策。下方明细只读；写入正式产物放在高级动作里。")
    cols = st.columns(5)
    cols[0].metric("报告记录", int(payload.get("record_count", 0) or 0))
    cols[1].metric("继续研究", int(summary.get("continue_research_count", 0) or 0))
    cols[2].metric("需要证据", int(summary.get("needs_more_evidence_count", 0) or 0))
    cols[3].metric("仅观察", int(summary.get("watch_only_count", 0) or 0))
    cols[4].metric("不要使用", int(summary.get("do_not_use_count", 0) or 0))
    with st.expander("高级动作：写入报告证据索引产物", expanded=False):
        if st.button("生成报告证据索引"):
            saved = write_report_decision_support_index(project_root=ROOT, report_root=REPORT_ROOT_DIR, output_dir=ROOT / "data" / "reportDecision")
            st.success("已生成报告证据索引。")
            st.json(saved.get("outputs", {}), expanded=False)
    records = pd.DataFrame(payload.get("records", []))
    if records.empty:
        st.info("暂无 RunMetadata。生成回测报告后这里会显示报告证据状态。")
    else:
        display_columns = [
            "date_folder",
            "run",
            "strategy_id",
            "report_readiness",
            "evidence_score",
            "decision_quality_score",
            "critical_missing_evidence",
            "next_action",
        ]
        existing = [column for column in display_columns if column in records.columns]
        st.dataframe(records[existing], width="stretch", hide_index=True)
    missing_counts = pd.DataFrame(summary.get("missing_evidence_counts", []))
    if not missing_counts.empty:
        st.markdown("#### 高频缺失证据")
        st.dataframe(missing_counts, width="stretch", hide_index=True)


def _display_strategy_summary(summary: pd.DataFrame) -> pd.DataFrame:
    display = summary.copy()
    for column in ["avg_total_return", "best_total_return", "worst_max_drawdown", "avg_cost_ratio"]:
        display[column] = display[column].map(lambda value: f"{float(value):.2%}")
    display["avg_sharpe"] = display["avg_sharpe"].map(lambda value: f"{float(value):.2f}")
    return display.rename(
        columns={
            "strategy_id": "策略",
            "run_count": "运行次数",
            "avg_total_return": "平均收益",
            "best_total_return": "最佳收益",
            "avg_sharpe": "平均 Sharpe",
            "worst_max_drawdown": "最差回撤",
            "avg_cost_ratio": "平均成本占比",
            "review_count": "需复核次数",
        }
    )


def _open_local_path(path: Path) -> None:
    if not path.exists():
        st.warning(f"路径不存在：{path}")
        return
    try:
        subprocess.Popen(["open", str(path)])
    except OSError as exc:
        st.warning(f"无法打开路径：{exc}")


def show_experiment_detail(summary_path: str) -> None:
    detail = load_experiment_detail(summary_path)
    best = detail["best_run"]
    best_params = detail["best_params"]
    risk_gate = evaluate_research_risk_gates(
        metrics=best,
        stability=detail.get("stability"),
        train_test=detail.get("train_test_validation"),
        walk_forward=detail.get("walk_forward_validation"),
    )
    decision_quality = evaluate_decision_quality(
        metrics=best,
        risk_gate=risk_gate,
        stability=detail.get("stability"),
        train_test=detail.get("train_test_validation"),
        walk_forward=detail.get("walk_forward_validation"),
    )
    st.subheader("实验详情")
    st.caption(f"Summary: {detail['summary_path']}")
    if detail.get("runs_path"):
        st.caption(f"Runs: {detail['runs_path']}")
    if detail.get("stability_path"):
        st.caption(f"Stability: {detail['stability_path']}")
    if detail.get("validation_path"):
        st.caption(f"TrainTestValidation: {detail['validation_path']}")
    if detail.get("walk_forward_path"):
        st.caption(f"WalkForwardValidation: {detail['walk_forward_path']}")
    if st.button("导出实验 Word 报告", key=f"export_experiment_{detail['experiment']}"):
        try:
            from pfi_os.reports import export_experiment_docx

            report_path = export_experiment_docx(summary_path)
            st.success(f"实验报告已生成：{report_path}")
        except Exception as exc:
            st.error(f"实验报告生成失败：{exc}")
    show_decision_quality(decision_quality)
    show_risk_gate(risk_gate)
    show_parameter_stability(detail["stability"])
    if detail.get("train_test_validation"):
        show_train_test_validation(detail["train_test_validation"])
    if detail.get("walk_forward_validation"):
        show_walk_forward_validation(detail["walk_forward_validation"])
    cols = st.columns(5)
    metric_items = [
        ("total_return", "最佳总收益率", "percent"),
        ("sharpe", "最佳 Sharpe", "number"),
        ("max_drawdown", "最大回撤", "percent"),
        ("cost_total", "交易摩擦", "currency"),
        ("trade_count", "交易次数", "integer"),
    ]
    for col, (key, label, formatter) in zip(cols, metric_items):
        col.metric(label, _format_metric_value(best.get(key, ""), formatter))
    st.write("最佳参数")
    st.dataframe(pd.DataFrame([best_params]), width="stretch", hide_index=True)
    summary = detail["summary"]
    metric_columns = ["run_id"] + [column for column in detail["metric_columns"] if column in summary.columns]
    parameter_columns = [column for column in summary.columns if column.startswith("param_")]
    visible_columns = metric_columns + parameter_columns
    st.write("实验明细")
    st.dataframe(summary[visible_columns], width="stretch", hide_index=True)


def show_parameter_stability(stability) -> None:
    payload = stability if isinstance(stability, dict) else stability.__dict__
    st.write("参数稳定性")
    cols = st.columns(5)
    cols[0].metric("状态", str(payload.get("stability_status", "")))
    cols[1].metric("最佳分数", _format_metric_value(payload.get("best_score", ""), "number"))
    cols[2].metric("前 20% 均值", _format_metric_value(payload.get("top_quantile_mean", ""), "number"))
    cols[3].metric("邻域均值", _format_metric_value(payload.get("neighbor_mean", ""), "number"))
    cols[4].metric("覆盖度", _format_metric_value(payload.get("parameter_coverage", ""), "percent"))
    st.caption(f"稳定性说明：{payload.get('notes', '')}")


def show_train_test_validation(validation) -> None:
    payload = validation if isinstance(validation, dict) else validation.__dict__
    if not payload:
        return
    st.write("Train-Test 验证")
    cols = st.columns(5)
    cols[0].metric("状态", str(payload.get("validation_status", "")))
    cols[1].metric("训练分数", _format_metric_value(payload.get("train_score", ""), "number"))
    cols[2].metric("测试分数", _format_metric_value(payload.get("test_score", ""), "number"))
    cols[3].metric("泛化比率", _format_metric_value(payload.get("generalization_ratio", ""), "percent"))
    cols[4].metric("切分时间", str(payload.get("split_datetime", ""))[:10])
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("训练收益", _format_metric_value(payload.get("train_total_return", ""), "percent"))
    col_b.metric("测试收益", _format_metric_value(payload.get("test_total_return", ""), "percent"))
    col_c.metric("训练回撤", _format_metric_value(payload.get("train_max_drawdown", ""), "percent"))
    col_d.metric("测试回撤", _format_metric_value(payload.get("test_max_drawdown", ""), "percent"))
    if payload.get("best_params"):
        st.write("训练期最佳参数")
        st.dataframe(pd.DataFrame([payload["best_params"]]), width="stretch", hide_index=True)
    st.caption(f"样本外说明：{payload.get('notes', '')}")


def show_walk_forward_validation(validation) -> None:
    payload = validation if isinstance(validation, dict) else validation.__dict__
    if not payload:
        return
    st.write("Walk-Forward 验证")
    cols = st.columns(5)
    cols[0].metric("状态", str(payload.get("validation_status", "")))
    cols[1].metric("窗口数量", _format_metric_value(payload.get("window_count", ""), "integer"))
    cols[2].metric("通过数量", _format_metric_value(payload.get("pass_count", ""), "integer"))
    cols[3].metric("平均测试分数", _format_metric_value(payload.get("average_test_score", ""), "number"))
    cols[4].metric("平均泛化", _format_metric_value(payload.get("average_generalization_ratio", ""), "percent"))
    st.caption(f"滚动验证说明：{payload.get('notes', '')}")
    windows = payload.get("windows", [])
    if windows:
        display = pd.DataFrame(windows).copy()
        if "best_params" in display.columns:
            display["best_params"] = display["best_params"].map(str)
        st.dataframe(display, width="stretch", hide_index=True)


def show_risk_gate(risk_gate) -> None:
    st.write("研究风险闸门")
    cols = st.columns(4)
    cols[0].metric("研究状态", risk_gate.status)
    cols[1].metric("风险分数", str(risk_gate.score))
    cols[2].metric("触发原因数量", str(len(risk_gate.reasons)))
    cols[3].metric("缺失证据", str(len(getattr(risk_gate, "missing_evidence", []) or [])))
    st.write("触发原因")
    st.dataframe(pd.DataFrame({"原因": risk_gate.reasons, "行动": risk_gate.actions}), width="stretch", hide_index=True)
    missing = getattr(risk_gate, "missing_evidence", []) or []
    if missing:
        st.write("缺失证据")
        st.dataframe(pd.DataFrame({"项目": missing}), width="stretch", hide_index=True)


def _experiment_label(experiments: pd.DataFrame, path: str) -> str:
    row = experiments[experiments["summary_path"] == path]
    if row.empty:
        return path
    item = row.iloc[0]
    return f"{item['date_folder']} / {item['experiment']} / {item['run_count']} runs"


def _format_report_center_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _format_metric_value(value, formatter: str) -> str:
    if value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if formatter == "percent":
        return f"{number:.2%}"
    if formatter == "currency":
        return f"{number:,.2f}"
    if formatter == "integer":
        return str(int(number))
    return f"{number:.2f}"


def data_tools_view() -> None:
    render_pfi_local_data_upload_panel()
    st.divider()
    st.subheader("数据源状态")
    status = pd.DataFrame(provider_status_rows())
    status_display = status.rename(
        columns={
            "provider": "数据源",
            "market_cn": "市场",
            "credential_cn": "凭证",
            "status": "状态",
            "note_cn": "中文说明",
        }
    )
    status_display = status_display[[column for column in ["数据源", "市场", "凭证", "状态", "中文说明"] if column in status_display.columns]]
    st.dataframe(status_display, width="stretch", hide_index=True)
    st.caption("Ready 表示本地配置已满足基础条件；NeedsConfig 表示需要先配置对应环境变量。")

    st.subheader("代码格式示例")
    st.dataframe(pd.DataFrame(market_symbol_examples()), width="stretch", hide_index=True)

    st.divider()
    st.subheader("A 股代码助手")
    st.caption("作用：把你输入的 A 股代码转换成不同数据源需要的格式，例如 AKShare 用 000001，TuShare 用 000001.SZ。")
    symbol = st.text_input("A 股代码", value="000001")
    try:
        normalized = normalize_a_share_symbol(symbol)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "原始输入": normalized.raw,
                        "交易所": normalized.exchange,
                        "AKShare": normalized.akshare,
                        "TuShare": normalized.tushare,
                        "展示": normalized.display,
                    }
                ]
            ),
            width="stretch",
            hide_index=True,
        )
    except ValueError as exc:
        st.warning(f"代码格式需要检查：{exc}")

    st.divider()
    st.subheader("多源交叉校验")
    check_market = st.selectbox("校验市场", ["US", "CN", "HK"], index=0)
    check_symbol = symbol_search_input(check_market, default="AAPL" if check_market == "US" else "600000", key_prefix="validation")
    provider_choices = st.multiselect(
        "数据源",
        ["Yahoo Finance", "AKShare", "TuShare", "Alpha Vantage", "Polygon"],
        default=["Yahoo Finance"],
    )
    check_start = st.date_input("校验开始日期", value=pd.Timestamp("2024-01-01"))
    check_end = date_input_with_today("校验结束日期", key="validation_end", default=pd.Timestamp("2024-01-15"))
    tolerance = st.number_input("容忍差异", min_value=0.0001, value=0.01, step=0.001, format="%.4f")
    if st.button("运行交叉校验", type="primary"):
        if len(provider_choices) < 2:
            st.warning("至少选择两个数据源。")
        else:
            try:
                request = BarDataRequest(
                    symbol=check_symbol,
                    market=check_market,
                    interval="1d",
                    start=str(check_start),
                    end=str(check_end),
                )
                result = validate_close_across_sources(provider_choices, request, tolerance_pct=float(tolerance))
                validation_path = save_cross_source_validation_result(result)
                st.session_state["latest_cross_validation_result"] = result
                st.metric("状态", result.status)
                st.metric("最大差异", f"{result.max_close_diff_pct:.2%}")
                st.metric("平均差异", f"{result.mean_close_diff_pct:.2%}")
                st.caption(f"交叉校验报告：{validation_path}")
                st.dataframe(result.details, width="stretch")
            except Exception as exc:
                st.error(f"交叉校验失败：{exc}")


def english_name_from_chinese(display_name: str) -> str:
    raw = str(display_name or "").strip()
    if not raw:
        return "Custom Strategy"
    if raw.isascii():
        return _title_case_name(raw)
    phrase_map = [
        ("自定义", "Custom"),
        ("个人", "Personal"),
        ("我的", "Personal"),
        ("均值回归", "Mean Reversion"),
        ("趋势跟随", "Trend Following"),
        ("突破", "Breakout"),
        ("动量轮动", "Momentum Rotation"),
        ("动量", "Momentum"),
        ("轮动", "Rotation"),
        ("布林带", "Bollinger Bands"),
        ("布林", "Bollinger"),
        ("均线", "Moving Average"),
        ("成交量", "Volume"),
        ("过滤", "Filter"),
        ("波动率", "Volatility"),
        ("风险", "Risk"),
        ("择时", "Timing"),
        ("策略", "Strategy"),
        ("组合", "Portfolio"),
        ("多因子", "Multi Factor"),
        ("低吸", "Dip Buying"),
        ("高抛", "Profit Taking"),
    ]
    matches = []
    for phrase, english in phrase_map:
        index = raw.find(phrase)
        if index >= 0:
            matches.append((index, english))
    ascii_words = re.findall(r"[A-Za-z0-9]+", raw)
    if ascii_words:
        matches.extend((raw.find(word), word.upper() if word.upper() in {"RSI", "ATR", "MA"} else word.title()) for word in ascii_words)
    if not matches:
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:6].upper()
        return f"Custom Strategy {digest}"
    words = []
    for _, english in sorted(matches, key=lambda item: item[0]):
        if english not in words:
            words.append(english)
    return _title_case_name(" ".join(words))


def _title_case_name(value: str) -> str:
    acronyms = {"rsi": "RSI", "atr": "ATR", "ma": "MA", "etf": "ETF"}
    words = re.split(r"[\s_\-]+", str(value or "").strip())
    titled = [acronyms.get(word.lower(), word[:1].upper() + word[1:].lower()) for word in words if word]
    return " ".join(titled) or "Custom Strategy"


def strategy_id_from_names(display_name: str, display_name_en: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", display_name_en.strip().lower()).strip("_")
    if not base or base == "custom_strategy":
        digest = hashlib.sha1(str(display_name or display_name_en).encode("utf-8")).hexdigest()[:8]
        base = f"custom_strategy_{digest}"
    if not base.startswith("custom_"):
        base = f"custom_{base}"
    try:
        return normalize_strategy_id(base)
    except ValueError:
        digest = hashlib.sha1(str(display_name or display_name_en).encode("utf-8")).hexdigest()[:8]
        return f"custom_strategy_{digest}"


def _logic_label(key: str) -> str:
    cn, en = CUSTOM_LOGIC_OPTIONS[key]
    return f"{cn} {en}"


def _indicator_label(key: str) -> str:
    cn, en = CUSTOM_INDICATOR_OPTIONS[key]
    return f"{cn} {en}"


def _key_from_label(label: str, options: dict[str, tuple[str, str]]) -> str:
    for key, (cn, en) in options.items():
        if label == f"{cn} {en}":
            return key
    return next(iter(options))


def custom_strategy_parameter_controls(
    indicator_keys: list[str],
    default_settings: dict[str, dict[str, float]] | None = None,
    key_prefix: str = "custom",
) -> dict[str, dict[str, float]]:
    settings: dict[str, dict[str, float]] = {}
    default_settings = default_settings or {}
    if not indicator_keys:
        st.warning("至少选择一个指标。\n\nSelect at least one indicator.")
        return settings
    for indicator_key in indicator_keys:
        cn, en = CUSTOM_INDICATOR_OPTIONS[indicator_key]
        st.markdown(f"##### {cn} {en}")
        defaults = default_settings.get(indicator_key, {})
        if indicator_key == "moving_average":
            col1, col2 = st.columns(2)
            settings[indicator_key] = {
                "short_window": int(col1.number_input("短均线 Short Window", min_value=2, value=int(defaults.get("short_window", 20)), step=1, key=f"{key_prefix}_ma_short")),
                "long_window": int(col2.number_input("长均线 Long Window", min_value=3, value=int(defaults.get("long_window", 60)), step=1, key=f"{key_prefix}_ma_long")),
            }
        elif indicator_key == "rsi":
            col1, col2, col3 = st.columns(3)
            settings[indicator_key] = {
                "window": int(col1.number_input("RSI 窗口 RSI Window", min_value=2, value=int(defaults.get("window", 14)), step=1, key=f"{key_prefix}_rsi_window")),
                "entry": float(col2.number_input("入场阈值 Entry Threshold", min_value=1.0, max_value=99.0, value=float(defaults.get("entry", 30.0)), step=1.0, key=f"{key_prefix}_rsi_entry")),
                "exit": float(col3.number_input("退出阈值 Exit Threshold", min_value=1.0, max_value=99.0, value=float(defaults.get("exit", 55.0)), step=1.0, key=f"{key_prefix}_rsi_exit")),
            }
        elif indicator_key == "bollinger":
            col1, col2, col3 = st.columns(3)
            settings[indicator_key] = {
                "window": int(col1.number_input("布林窗口 Bollinger Window", min_value=5, value=int(defaults.get("window", 20)), step=1, key=f"{key_prefix}_bb_window")),
                "std_multiplier": float(col2.number_input("标准差倍数 Std Multiplier", min_value=0.5, max_value=5.0, value=float(defaults.get("std_multiplier", 2.0)), step=0.1, key=f"{key_prefix}_bb_std")),
                "exit_z": float(col3.number_input("退出 Z 值 Exit Z", min_value=-2.0, max_value=2.0, value=float(defaults.get("exit_z", 0.0)), step=0.1, key=f"{key_prefix}_bb_exit_z")),
            }
        elif indicator_key == "breakout_channel":
            col1, col2 = st.columns(2)
            settings[indicator_key] = {
                "lookback": int(col1.number_input("突破回看 Breakout Lookback", min_value=5, value=int(defaults.get("lookback", 55)), step=1, key=f"{key_prefix}_breakout_lookback")),
                "exit_lookback": int(col2.number_input("退出回看 Exit Lookback", min_value=2, value=int(defaults.get("exit_lookback", 20)), step=1, key=f"{key_prefix}_breakout_exit")),
            }
        elif indicator_key == "momentum":
            col1, col2 = st.columns(2)
            settings[indicator_key] = {
                "lookback": int(col1.number_input("动量回看 Momentum Lookback", min_value=5, value=int(defaults.get("lookback", 60)), step=1, key=f"{key_prefix}_momentum_lookback")),
                "minimum_return": float(col2.number_input("最小动量 Minimum Return", min_value=-1.0, max_value=1.0, value=float(defaults.get("minimum_return", 0.02)), step=0.01, key=f"{key_prefix}_momentum_min_return")),
            }
        elif indicator_key == "volume_filter":
            col1, col2 = st.columns(2)
            settings[indicator_key] = {
                "window": int(col1.number_input("成交量窗口 Volume Window", min_value=2, value=int(defaults.get("window", 20)), step=1, key=f"{key_prefix}_volume_window")),
                "minimum_ratio": float(col2.number_input("最低量比 Minimum Volume Ratio", min_value=0.1, max_value=10.0, value=float(defaults.get("minimum_ratio", 1.2)), step=0.1, key=f"{key_prefix}_volume_ratio")),
            }
        elif indicator_key == "atr_risk":
            col1, col2 = st.columns(2)
            settings[indicator_key] = {
                "window": int(col1.number_input("ATR 窗口 ATR Window", min_value=2, value=int(defaults.get("window", 14)), step=1, key=f"{key_prefix}_atr_window")),
                "stop_multiplier": float(col2.number_input("止损倍数 Stop Multiplier", min_value=0.5, max_value=10.0, value=float(defaults.get("stop_multiplier", 2.5)), step=0.1, key=f"{key_prefix}_atr_stop")),
            }
    return settings


def infer_custom_strategy_profile(logic_key: str, indicator_keys: list[str], settings: dict[str, dict[str, float]]) -> dict[str, object]:
    category_map = {
        "mean_reversion": ("均值回归", "Mean Reversion", ("行为偏差",)),
        "trend_following": ("趋势跟随", "Trend Following", ("行为偏差", "风险溢价")),
        "breakout": ("趋势跟随", "Trend Following", ("行为偏差", "风险溢价", "结构性约束")),
        "momentum_rotation": ("组合轮动", "Portfolio Rotation", ("行为偏差", "风险溢价", "组合优势")),
    }
    category_cn, category_en, base_sources = category_map.get(logic_key, category_map["mean_reversion"])
    sources = list(base_sources)
    if "volume_filter" in indicator_keys and "信息优势" not in sources:
        sources.append("信息优势")
    if "atr_risk" in indicator_keys and "执行优势" not in sources:
        sources.append("执行优势")
    if len(indicator_keys) >= 3 and "组合优势" not in sources:
        sources.append("组合优势")
    indicators_cn = "、".join(CUSTOM_INDICATOR_OPTIONS[key][0] for key in indicator_keys) or "所选指标"
    indicators_en = ", ".join(CUSTOM_INDICATOR_OPTIONS[key][1] for key in indicator_keys) or "selected indicators"
    return_source = "；".join(f"{source} {RETURN_SOURCE_EN[source]}" for source in sources)
    return_source_en = "; ".join(RETURN_SOURCE_EN[source] for source in sources)
    if logic_key == "mean_reversion":
        thesis = f"该策略以均值回归为核心，通过{indicators_cn}识别短期过度偏离，尝试捕捉情绪修复和流动性恢复带来的反弹。"
        thesis_en = f"The strategy is centered on mean reversion. It uses {indicators_en} to identify short-term dislocation and attempts to capture rebound from sentiment normalization and liquidity recovery."
        failure = "单边趋势、基本面突变、流动性断裂、波动率急剧扩张或交易成本升高时，均值回归假设可能失效。"
        failure_en = "The mean-reversion thesis can fail during one-way trends, fundamental regime changes, liquidity breaks, volatility expansion, or higher trading costs."
    elif logic_key in {"trend_following", "breakout"}:
        thesis = f"该策略以趋势确认为核心，通过{indicators_cn}确认价格强势或突破，尝试捕捉反应不足和资金延续流带来的趋势收益。"
        thesis_en = f"The strategy is centered on trend confirmation. It uses {indicators_en} to confirm strength or breakout and attempts to capture trend returns from underreaction and continuing capital flows."
        failure = "区间震荡、假突破、快速反转、低流动性、高滑点或趋势强度不足时，趋势跟随假设可能失效。"
        failure_en = "The trend-following thesis can fail in range-bound markets, false breakouts, fast reversals, low liquidity, high slippage, or weak trend regimes."
    else:
        thesis = f"该策略以相对强弱轮动为核心，通过{indicators_cn}筛选更强资产，尝试捕捉资金流、反应不足和组合分散带来的收益。"
        thesis_en = f"The strategy is centered on relative-strength rotation. It uses {indicators_en} to select stronger assets and attempts to capture returns from flows, underreaction, and diversification."
        failure = "风格急剧反转、相关性同时上升、资产池关系变化或再平衡成本升高时，动量轮动假设可能失效。"
        failure_en = "The momentum-rotation thesis can fail during sharp factor reversals, rising correlations, changing universe relationships, or higher rebalancing costs."
    parameter_notes, parameter_notes_en = custom_parameter_settings_text(logic_key, indicator_keys, settings)
    return {
        "category": f"{category_cn} {category_en}",
        "return_source": return_source,
        "return_source_en": return_source_en,
        "thesis": thesis,
        "thesis_en": thesis_en,
        "failure": failure,
        "failure_en": failure_en,
        "parameter_notes": parameter_notes,
        "parameter_notes_en": parameter_notes_en,
    }


def custom_parameter_settings_text(logic_key: str, indicator_keys: list[str], settings: dict[str, dict[str, float]]) -> tuple[str, str]:
    logic_cn, logic_en = CUSTOM_LOGIC_OPTIONS.get(logic_key, CUSTOM_LOGIC_OPTIONS["mean_reversion"])
    lines_cn = [f"策略逻辑：{logic_cn}。", "指标组合：" + ("、".join(CUSTOM_INDICATOR_OPTIONS[key][0] for key in indicator_keys) or "未选择") + "。"]
    lines_en = [f"Strategy logic: {logic_en}.", "Indicator combination: " + (", ".join(CUSTOM_INDICATOR_OPTIONS[key][1] for key in indicator_keys) or "None") + "."]
    for indicator_key in indicator_keys:
        cn, en = CUSTOM_INDICATOR_OPTIONS[indicator_key]
        values = settings.get(indicator_key, {})
        setting_text = ", ".join(f"{key}={value}" for key, value in values.items()) or "未设置"
        lines_cn.append(f"{cn} 参数：{setting_text}。")
        lines_en.append(f"{en} settings: {setting_text}.")
    lines_cn.append("支持多指标、多参数组合；正式用于研究前必须完成代码逻辑、数据验证、成本复核和策略库确认。")
    lines_en.append("Multi-indicator and multi-parameter combinations are supported; formal research use requires code logic, data validation, cost review, and strategy-library confirmation.")
    return "\n".join(lines_cn), "\n".join(lines_en)


def custom_strategy_builder_panel() -> None:
    with st.expander("新增自定义策略", expanded=False):
        st.caption("输入中文名称，选择策略逻辑、指标和参数设置；类别、收益来源、研究假设和失效环境由系统自动分析生成。")
        col1, col2, col3 = st.columns(3)
        with col1:
            display_name = st.text_input("中文名称", value="自定义均值回归", key="custom_builder_display_name")
        display_name_en = english_name_from_chinese(display_name)
        strategy_id = strategy_id_from_names(display_name, display_name_en)
        with col2:
            st.caption("英文名称")
            st.code(display_name_en, language="text")
        with col3:
            st.caption("策略编号")
            st.code(strategy_id, language="text")

        logic_label = st.selectbox(
            "策略逻辑",
            [_logic_label(key) for key in CUSTOM_LOGIC_OPTIONS],
            index=0,
            key="custom_builder_logic",
        )
        logic_key = _key_from_label(logic_label, CUSTOM_LOGIC_OPTIONS)
        indicator_labels = st.multiselect(
            "指标组合",
            [_indicator_label(key) for key in CUSTOM_INDICATOR_OPTIONS],
            default=[_indicator_label("moving_average"), _indicator_label("rsi")],
            key="custom_builder_indicators",
        )
        indicator_keys = [_key_from_label(label, CUSTOM_INDICATOR_OPTIONS) for label in indicator_labels]
        st.markdown("#### 参数设置")
        settings = custom_strategy_parameter_controls(indicator_keys, key_prefix="custom_builder")
        inferred = infer_custom_strategy_profile(logic_key, indicator_keys, settings)
        st.markdown("#### 系统分析")
        st.info(
            f"类别：{inferred['category']}\n\n"
            f"收益来源：{inferred['return_source']}\n\n"
            f"{inferred['thesis']}\n\n"
            f"{inferred['failure']}"
        )
        with st.expander("查看参数设置文本", expanded=False):
            st.write(inferred["parameter_notes"])
        overwrite = st.checkbox("覆盖同名草稿", value=False, key="custom_builder_overwrite")
        if st.button("生成策略模板", type="primary", key="custom_builder_submit"):
            if not display_name.strip():
                st.error("中文名称不能为空。")
                return
            if not indicator_keys:
                st.error("至少选择一个指标后再生成策略。")
                return
            try:
                artifact = create_strategy_template(
                    strategy_id=strategy_id,
                    display_name=display_name,
                    display_name_en=display_name_en,
                    category=str(inferred["category"]),
                    return_source=str(inferred["return_source"]),
                    thesis=str(inferred["thesis"]),
                    failure=str(inferred["failure"]),
                    parameter_notes=str(inferred["parameter_notes"]),
                    return_source_en=str(inferred["return_source_en"]),
                    thesis_en=str(inferred["thesis_en"]),
                    failure_en=str(inferred["failure_en"]),
                    parameter_notes_en=str(inferred["parameter_notes_en"]),
                    custom_spec={
                        "logic_key": logic_key,
                        "indicator_keys": indicator_keys,
                        "settings": settings,
                    },
                    overwrite=overwrite,
                )
                st.success(f"已生成自定义策略草稿：{artifact.strategy_id}")
                st.write({"StrategyFile": artifact.strategy_file, "ProfileFile": artifact.profile_file, "ApprovalId": artifact.approval_id})
            except Exception as exc:
                st.error(f"新增策略失败：{exc}")


def candidate_profile_editor(candidate) -> None:
    with st.expander("编辑候选策略档案", expanded=False):
        with st.form(f"edit_candidate_profile_{candidate.strategy_id}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                display_name = st.text_input("中文名称", value=candidate.display_name, key=f"edit_cn_{candidate.strategy_id}")
                display_name_en = english_name_from_chinese(display_name)
                st.caption("英文名称")
                st.code(display_name_en, language="text")
            with col2:
                version = st.text_input("版本", value=candidate.version or "0.1.0", key=f"edit_version_{candidate.strategy_id}")
                category = st.text_input("类别", value=candidate.category, key=f"edit_category_{candidate.strategy_id}")
            with col3:
                return_source = st.text_input("收益来源", value=candidate.return_source, key=f"edit_source_{candidate.strategy_id}")
                approval_status = st.selectbox("确认状态", ["Pending", "Approved", "Review", "Rejected"], index=["Pending", "Approved", "Review", "Rejected"].index(candidate.approval_status if candidate.approval_status in {"Pending", "Approved", "Review", "Rejected"} else "Pending"))
            thesis = st.text_area("研究假设", value=candidate.thesis, key=f"edit_thesis_{candidate.strategy_id}")
            failure = st.text_area("失效环境", value=candidate.failure, key=f"edit_failure_{candidate.strategy_id}")
            parameter_notes = st.text_area("参数设置", value=candidate.parameter_notes, key=f"edit_params_{candidate.strategy_id}")
            saved = st.form_submit_button("保存档案")
        if saved:
            Path(candidate.path).write_text(
                _candidate_profile_markdown(
                    strategy_id=candidate.strategy_id,
                    display_name=display_name,
                    display_name_en=display_name_en,
                    version=version,
                    category=category,
                    thesis=thesis,
                    return_source=return_source,
                    failure=failure,
                    parameter_notes=parameter_notes,
                    approval_status=approval_status,
                ),
                encoding="utf-8",
            )
            st.success("候选策略档案已保存。")
            st.rerun()


def _candidate_profile_markdown(
    strategy_id: str,
    display_name: str,
    display_name_en: str,
    version: str,
    category: str,
    thesis: str,
    return_source: str,
    failure: str,
    parameter_notes: str,
    approval_status: str,
) -> str:
    return f"""# {display_name} {display_name_en}

策略编号：`{strategy_id}`

Strategy Id: `{strategy_id}`

版本：`{version}`

Version: `{version}`

类别：{category}

Category: {category}

## 研究假设

{thesis}

## Research Thesis

{thesis}

## 收益来源

{return_source}

## Return Source

{return_source}

## 失效环境

{failure}

## Failure Regime

{failure}

## 参数设置

{parameter_notes}

## Parameter Settings

{parameter_notes}

## 变更确认状态

当前状态为 `{approval_status}`。

## Change Confirmation Status

Current status is `{approval_status}`.
"""


def built_in_strategy_profile_editor(profile) -> None:
    with st.expander("编辑内置策略档案", expanded=False):
        st.caption("保存后写入持久化覆盖文件；不会修改内置策略源代码。")
        payload = editable_strategy_profile_payload(profile)
        source_options = [item.source for item in RETURN_SOURCE_TAXONOMY]
        default_sources = [source for source in profile.primary_sources if source in source_options]
        with st.form(f"edit_builtin_profile_{profile.strategy_id}"):
            col1, col2 = st.columns(2)
            with col1:
                display_name = st.text_input("中文名称", value=str(payload["display_name"]), key=f"builtin_cn_{profile.strategy_id}")
                category = st.text_input("中文类别", value=str(payload["category"]), key=f"builtin_category_{profile.strategy_id}")
            with col2:
                display_name_en = st.text_input("英文名称", value=str(payload["display_name_en"]), key=f"builtin_en_{profile.strategy_id}")
                category_en = st.text_input("英文类别", value=str(payload["category_en"]), key=f"builtin_category_en_{profile.strategy_id}")
            primary_sources = st.multiselect(
                "主要收益来源",
                source_options,
                default=default_sources,
                key=f"builtin_sources_{profile.strategy_id}",
            )
            col_cn, col_en = st.columns(2)
            with col_cn:
                thesis = st.text_area("研究假设", value=str(payload["thesis"]), key=f"builtin_thesis_{profile.strategy_id}")
                earnings = st.text_area("收益解释", value=str(payload["earnings"]), key=f"builtin_earnings_{profile.strategy_id}")
                persistence = st.text_area("长期存在理由", value=str(payload["persistence"]), key=f"builtin_persistence_{profile.strategy_id}")
                failure = st.text_area("失效环境", value=str(payload["failure"]), key=f"builtin_failure_{profile.strategy_id}")
                default_parameter_note = st.text_area("默认参数设置", value=str(payload["default_parameter_note"]), key=f"builtin_params_{profile.strategy_id}")
                approval_note = st.text_area("确认说明", value=str(payload["approval_note"]), key=f"builtin_approval_{profile.strategy_id}")
            with col_en:
                thesis_en = st.text_area("Research Thesis EN", value=str(payload["thesis_en"]), key=f"builtin_thesis_en_{profile.strategy_id}")
                earnings_en = st.text_area("Return Thesis EN", value=str(payload["earnings_en"]), key=f"builtin_earnings_en_{profile.strategy_id}")
                persistence_en = st.text_area("Persistence EN", value=str(payload["persistence_en"]), key=f"builtin_persistence_en_{profile.strategy_id}")
                failure_en = st.text_area("Failure Regime EN", value=str(payload["failure_en"]), key=f"builtin_failure_en_{profile.strategy_id}")
                default_parameter_note_en = st.text_area("Default Parameter Settings EN", value=str(payload["default_parameter_note_en"]), key=f"builtin_params_en_{profile.strategy_id}")
                approval_note_en = st.text_area("Approval Notes EN", value=str(payload["approval_note_en"]), key=f"builtin_approval_en_{profile.strategy_id}")
            saved = st.form_submit_button("保存内置策略修改")
        if saved:
            try:
                path = save_strategy_profile_override(
                    profile.strategy_id,
                    {
                        "display_name": display_name,
                        "display_name_en": display_name_en,
                        "category": category,
                        "category_en": category_en,
                        "thesis": thesis,
                        "thesis_en": thesis_en,
                        "earnings": earnings,
                        "earnings_en": earnings_en,
                        "persistence": persistence,
                        "persistence_en": persistence_en,
                        "failure": failure,
                        "failure_en": failure_en,
                        "default_parameter_note": default_parameter_note,
                        "default_parameter_note_en": default_parameter_note_en,
                        "approval_note": approval_note,
                        "approval_note_en": approval_note_en,
                        "primary_sources": primary_sources,
                    },
                )
                st.success(f"内置策略修改已保存：{path}")
                st.rerun()
            except Exception as exc:
                st.error(f"保存失败：{exc}")


def custom_strategy_specs_panel() -> None:
    specs = load_custom_strategy_specs()
    st.write("可运行自定义策略规格")
    if not specs:
        st.info("暂无可运行自定义策略规格。使用上方新增自定义策略后会自动保存。")
        return
    registry = StrategyApprovalRegistry()
    rows = []
    for spec in specs:
        row = spec.to_row()
        row["确认状态"] = "已确认" if registry.is_approved(CustomNoCodeStrategy(spec)) else "待确认"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    selected_id = st.selectbox(
        "选择自定义策略规格",
        options=[spec.strategy_id for spec in specs],
        format_func=lambda strategy_id: next(f"{spec.display_name} {spec.display_name_en} / {spec.version}" for spec in specs if spec.strategy_id == strategy_id),
        key="custom_spec_selector",
    )
    selected_spec = next(spec for spec in specs if spec.strategy_id == selected_id)
    custom_strategy_spec_editor(selected_spec, registry)
    custom_strategy_approval_panel(selected_spec, registry)
    history_rows = custom_strategy_spec_history_rows()
    if history_rows:
        with st.expander("修改历史", expanded=False):
            st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)
    with st.expander("规格存储位置", expanded=False):
        st.code(str(ROOT / "data" / "strategyLibrary" / "CustomStrategySpecs.json"), language="text")


def custom_strategy_spec_editor(spec, registry: StrategyApprovalRegistry) -> None:
    with st.expander("编辑自定义策略规格", expanded=False):
        next_version = next_strategy_version(spec.version)
        st.caption(f"当前版本：{spec.version} / 保存后版本：{next_version}")
        logic_labels = [_logic_label(key) for key in CUSTOM_LOGIC_OPTIONS]
        default_logic_label = _logic_label(spec.logic_key) if spec.logic_key in CUSTOM_LOGIC_OPTIONS else logic_labels[0]
        logic_label = st.selectbox(
            "策略逻辑",
            logic_labels,
            index=logic_labels.index(default_logic_label),
            key=f"edit_spec_logic_{spec.strategy_id}",
        )
        logic_key = _key_from_label(logic_label, CUSTOM_LOGIC_OPTIONS)
        indicator_labels = [_indicator_label(key) for key in CUSTOM_INDICATOR_OPTIONS]
        default_indicator_labels = [_indicator_label(key) for key in spec.indicator_keys if key in CUSTOM_INDICATOR_OPTIONS]
        selected_indicator_labels = st.multiselect(
            "指标组合",
            indicator_labels,
            default=default_indicator_labels or [indicator_labels[0]],
            key=f"edit_spec_indicators_{spec.strategy_id}",
        )
        indicator_keys = [_key_from_label(label, CUSTOM_INDICATOR_OPTIONS) for label in selected_indicator_labels]
        settings = custom_strategy_parameter_controls(
            indicator_keys,
            default_settings=spec.settings,
            key_prefix=f"edit_spec_{spec.strategy_id}",
        )
        inferred = infer_custom_strategy_profile(logic_key, indicator_keys, settings)
        st.info(
            f"保存后类别：{inferred['category']}\n\n"
            f"保存后收益来源：{inferred['return_source']}\n\n"
            f"{inferred['thesis']}"
        )
        change_summary = st.text_area(
            "修改说明",
            value=f"更新 {spec.display_name} 的 no-code 参数。",
            key=f"edit_spec_change_{spec.strategy_id}",
        )
        risk_notes = st.text_area(
            "风险说明",
            value="参数变化可能改变交易频率、回撤和交易成本敏感性，使用前需要重新做数据验证和回测。",
            key=f"edit_spec_risk_{spec.strategy_id}",
        )
        if st.button("保存为新版本并提交确认", type="primary", key=f"edit_spec_save_{spec.strategy_id}"):
            if not indicator_keys:
                st.error("至少选择一个指标。")
                return
            updated_payload = spec.to_dict()
            updated_payload.update(
                {
                    "version": next_version,
                    "logic_key": logic_key,
                    "indicator_keys": indicator_keys,
                    "settings": settings,
                    "category": str(inferred["category"]),
                    "return_source": str(inferred["return_source"]),
                    "return_source_en": str(inferred["return_source_en"]),
                    "thesis": str(inferred["thesis"]),
                    "thesis_en": str(inferred["thesis_en"]),
                    "failure": str(inferred["failure"]),
                    "failure_en": str(inferred["failure_en"]),
                    "parameter_notes": str(inferred["parameter_notes"]),
                    "parameter_notes_en": str(inferred["parameter_notes_en"]),
                }
            )
            try:
                spec_path, history_path = save_custom_strategy_spec_revision(spec, updated_payload, change_summary, risk_notes)
                strategy_path = write_custom_strategy_code_for_spec(updated_payload)
                registry.request_approval(spec.strategy_id, next_version, change_summary, risk_notes)
                st.success(f"已保存新版本并提交确认：{next_version}")
                st.write({"SpecFile": str(spec_path), "HistoryFile": str(history_path), "StrategyFile": str(strategy_path)})
                st.rerun()
            except Exception as exc:
                st.error(f"保存失败：{exc}")


def custom_strategy_approval_panel(spec, registry: StrategyApprovalRegistry) -> None:
    status = "Approved" if registry.is_approved(CustomNoCodeStrategy(spec)) else registry.latest_status(spec.strategy_id, spec.version) or "Pending Approval"
    with st.expander("当前版本确认", expanded=False):
        cols = st.columns(3)
        cols[0].metric("策略编号", spec.strategy_id)
        cols[1].metric("版本", spec.version)
        cols[2].metric("确认状态", _clean_ui_label(status))
        if status != "Approved":
            if st.button("确认当前版本", type="primary", key=f"approve_spec_{spec.strategy_id}_{spec.version}"):
                record = registry.approve_or_request(
                    spec.strategy_id,
                    spec.version,
                    f"Approve custom no-code strategy {spec.display_name_en} {spec.version}.",
                    "User confirmed approval after reviewing strategy spec, data assumptions, and risk notes.",
                )
                st.success(f"已确认当前版本：{record.strategy_id} {record.version}")
                st.rerun()


def built_in_strategy_order_editor() -> None:
    with st.expander("策略顺序设置", expanded=False):
        st.caption("这里调整的是策略库内置策略展示顺序，并同步影响单标的回测里的默认策略下拉顺序。组合轮动策略只在策略库展示，不会出现在单标的回测策略下拉中。")
        order_ids = ordered_strategy_ids()
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "顺序": index,
                        "策略编号": strategy_id,
                        "策略名称": get_strategy_profile(strategy_id).display_name,
                        "单标的回测可选": "是" if strategy_id in BUILT_IN_STRATEGY_FACTORIES else "否",
                    }
                    for index, strategy_id in enumerate(order_ids, start=1)
                ]
            ),
            width="stretch",
            hide_index=True,
        )
        selected_strategy_id = st.selectbox(
            "选择要移动的策略",
            options=order_ids,
            format_func=lambda strategy_id: f"{order_ids.index(strategy_id) + 1}. {get_strategy_profile(strategy_id).display_name} ({strategy_id})",
            key="strategy_order_selected",
        )
        col_up, col_down, col_reset = st.columns(3)
        if col_up.button("上移", key="strategy_order_move_up"):
            move_strategy_order_item(selected_strategy_id, "up")
            st.success("策略顺序已上移，并同步到默认策略顺序。")
            st.rerun()
        if col_down.button("下移", key="strategy_order_move_down"):
            move_strategy_order_item(selected_strategy_id, "down")
            st.success("策略顺序已下移，并同步到默认策略顺序。")
            st.rerun()
        if col_reset.button("恢复默认顺序", key="strategy_order_reset"):
            save_strategy_order(list(DEFAULT_STRATEGY_ORDER))
            st.success("策略顺序已恢复默认。")
            st.rerun()


def strategy_library_view() -> None:
    st.subheader("策略库")
    st.info(
        "策略库用于沉淀可复用的研究假设、收益来源、失效条件、参数设置和确认状态。自定义策略必须先生成模板、补全研究档案并完成变更确认后，才能进入回测流程。"
    )
    custom_strategy_builder_panel()
    custom_strategy_specs_panel()
    built_in_strategy_order_editor()
    st.write("内置策略")
    profiles = pd.DataFrame(strategy_profile_rows())
    st.dataframe(profiles, width="stretch", hide_index=True)
    selected = st.selectbox(
        "选择策略查看档案",
        options=ordered_strategy_ids(),
        format_func=lambda strategy_id: f"{get_strategy_profile(strategy_id).display_name} {get_strategy_profile(strategy_id).display_name_en}",
    )
    profile = get_strategy_profile(selected)
    cols = st.columns(4)
    cols[0].metric("策略编号", profile.strategy_id)
    cols[1].metric("类别", profile.category)
    cols[2].metric("英文类别", profile.category_en)
    cols[3].metric("主要来源", str(len(profile.primary_sources)))
    st.write("研究假设")
    st.info(profile.thesis)
    rows = [
        ("收益来源", profile.earnings),
        ("长期存在理由", profile.persistence),
        ("失效环境", profile.failure),
        ("默认参数设置", profile.default_parameter_note),
        ("确认说明", profile.approval_note),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["项目", "内容"]), width="stretch", hide_index=True)
    built_in_strategy_profile_editor(profile)
    built_in_strategy_parameter_editor(profile)
    st.write("收益来源分类")
    source_rows = []
    for item in RETURN_SOURCE_TAXONOMY:
        source_rows.append(
            {
                "收益来源": item.source,
                "解释": item.explanation,
                "当前策略": "主要" if item.source in profile.primary_sources else "次要 / 待验证",
            }
        )
    st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)

    st.divider()
    st.write("自定义策略候选")
    candidates = collect_strategy_profile_candidates()
    if not candidates:
        st.info("暂无自定义策略档案候选。可在上方新增自定义策略。")
        return
    code_reports = {report.strategy_id: report for report in collect_strategy_code_quality_reports()}
    smoke_reports = {report.strategy_id: report for report in collect_strategy_smoke_tests()}
    approval_records = StrategyApprovalRegistry().records()
    candidate_rows = []
    for candidate_item in candidates:
        row = candidate_item.to_row()
        report = code_reports.get(candidate_item.strategy_id)
        smoke = smoke_reports.get(candidate_item.strategy_id)
        readiness = evaluate_strategy_readiness_gate(candidate_item, report, approval_records, smoke_report=smoke)
        row["综合状态"] = readiness.status
        row["代码状态"] = report.status if report else "MissingCode"
        row["代码分数"] = report.score if report else 0
        row["Smoke Test"] = smoke.status if smoke else "MissingCode"
        row["信号行数"] = smoke.rows if smoke else 0
        candidate_rows.append(row)
    st.dataframe(pd.DataFrame(candidate_rows), width="stretch", hide_index=True)
    selected_candidate_path = st.selectbox(
        "选择候选档案",
        options=[candidate.path for candidate in candidates],
        format_func=lambda path: next(candidate.strategy_id for candidate in candidates if candidate.path == path),
    )
    candidate = next(item for item in candidates if item.path == selected_candidate_path)
    code_report = code_reports.get(candidate.strategy_id)
    smoke_report = smoke_reports.get(candidate.strategy_id)
    readiness = evaluate_strategy_readiness_gate(candidate, code_report, approval_records, smoke_report=smoke_report)
    cols = st.columns(8)
    cols[0].metric("策略编号", candidate.strategy_id)
    cols[1].metric("版本", candidate.version)
    cols[2].metric("综合状态", _clean_ui_label(readiness.status))
    cols[3].metric("质量状态", _clean_ui_label(candidate.quality_status))
    cols[4].metric("质量分数", str(candidate.quality_score))
    cols[5].metric("代码状态", _clean_ui_label(code_report.status if code_report else "MissingCode"))
    cols[6].metric("Smoke Test", _clean_ui_label(smoke_report.status if smoke_report else "MissingCode"))
    cols[7].metric("确认状态", _clean_ui_label(candidate.approval_status))
    candidate_profile_editor(candidate)
    st.write("确认前综合门禁")
    st.dataframe(
        pd.DataFrame({"原因": list(readiness.reasons), "行动": list(readiness.actions)}),
        width="stretch",
        hide_index=True,
    )
    if st.button("导出候选策略审查报告", key=f"export_strategy_review_{candidate.strategy_id}"):
        try:
            from pfi_os.reports import export_strategy_review_docx

            report_path = export_strategy_review_docx(candidate.path)
            st.success(f"候选策略审查报告已生成：{report_path}")
        except Exception as exc:
            st.error(f"候选策略审查报告生成失败：{exc}")
    if candidate.missing_items:
        st.warning("候选档案仍有缺失项。")
        st.dataframe(pd.DataFrame({"缺失项": list(candidate.missing_items)}), width="stretch", hide_index=True)
    if code_report and code_report.findings:
        st.warning("候选策略代码仍有检查项。")
        st.dataframe(pd.DataFrame({"代码检查项": list(code_report.findings)}), width="stretch", hide_index=True)
    if code_report is None:
        st.warning("未找到对应策略代码文件。")
    if smoke_report and smoke_report.findings:
        st.warning("候选策略 Smoke Test 未通过。")
        st.dataframe(pd.DataFrame({"Smoke Test 检查项": list(smoke_report.findings)}), width="stretch", hide_index=True)
    st.write("候选研究假设")
    st.info(candidate.thesis or "未提供研究假设。")
    st.write("候选审查")
    st.dataframe(
        pd.DataFrame(
            [
                ("质量状态", _clean_ui_label(candidate.quality_status)),
                ("质量分数", str(candidate.quality_score)),
                ("综合状态", _clean_ui_label(readiness.status)),
                ("代码状态", _clean_ui_label(code_report.status if code_report else "MissingCode")),
                ("代码分数", str(code_report.score) if code_report else "0"),
                ("Smoke Test", _clean_ui_label(smoke_report.status if smoke_report else "MissingCode")),
                ("信号行数", str(smoke_report.rows) if smoke_report else "0"),
                ("收益来源", candidate.return_source),
                ("失效环境", candidate.failure),
                ("参数设置", candidate.parameter_notes),
                ("档案路径", candidate.path),
            ],
            columns=["项目", "内容"],
        ),
        width="stretch",
        hide_index=True,
    )


def _int_default(defaults: dict[str, object], key: str, fallback: int) -> int:
    return int(float(defaults.get(key, fallback)))


def _float_default(defaults: dict[str, object], key: str, fallback: float) -> float:
    return float(defaults.get(key, fallback))


def _str_default(defaults: dict[str, object], key: str, fallback: str) -> str:
    value = str(defaults.get(key, fallback)).strip()
    return value or fallback


def built_in_strategy_parameter_controls(strategy_id: str, defaults: dict[str, object], key_prefix: str) -> dict:
    if strategy_id == "ma_crossover":
        col1, col2 = st.columns(2)
        with col1:
            short_window = st.number_input("短均线 MA", min_value=2, value=_int_default(defaults, "short_window", 20), step=1, key=f"{key_prefix}_short_ma")
        with col2:
            long_window = st.number_input("长均线 MA", min_value=3, value=_int_default(defaults, "long_window", 60), step=1, key=f"{key_prefix}_long_ma")
        return {"short_window": int(short_window), "long_window": int(long_window)}
    if strategy_id == "rsi_reversion":
        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.number_input("RSI 窗口", min_value=2, value=_int_default(defaults, "window", 14), step=1, key=f"{key_prefix}_rsi_window")
        with col2:
            entry = st.number_input("入场 RSI", min_value=1.0, max_value=99.0, value=_float_default(defaults, "entry", 30.0), key=f"{key_prefix}_rsi_entry")
        with col3:
            exit_ = st.number_input("离场 RSI", min_value=1.0, max_value=99.0, value=_float_default(defaults, "exit", 55.0), key=f"{key_prefix}_rsi_exit")
        return {"window": int(window), "entry": float(entry), "exit": float(exit_)}
    if strategy_id == "bollinger_reversion":
        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.number_input("布林带窗口", min_value=5, value=_int_default(defaults, "window", 20), step=1, key=f"{key_prefix}_bb_window")
        with col2:
            num_std = st.number_input("标准差倍数", min_value=0.5, max_value=5.0, value=_float_default(defaults, "num_std", 2.0), step=0.1, key=f"{key_prefix}_bb_std")
        with col3:
            exit_z = st.number_input("退出 Z 值", min_value=-2.0, max_value=2.0, value=_float_default(defaults, "exit_z", 0.0), step=0.1, key=f"{key_prefix}_bb_exit_z")
        return {"window": int(window), "num_std": float(num_std), "exit_z": float(exit_z)}
    if strategy_id == "breakout":
        col1, col2 = st.columns(2)
        with col1:
            lookback = st.number_input("突破回看", min_value=5, value=_int_default(defaults, "lookback", 55), step=1, key=f"{key_prefix}_breakout_lookback")
        with col2:
            exit_lookback = st.number_input("离场回看", min_value=2, value=_int_default(defaults, "exit_lookback", 20), step=1, key=f"{key_prefix}_breakout_exit")
        return {"lookback": int(lookback), "exit_lookback": int(exit_lookback)}
    if strategy_id == "alipay":
        col1, col2 = st.columns(2)
        with col1:
            buy_base_amount = st.number_input("补仓基准金额", min_value=1000.0, value=_float_default(defaults, "buy_base_amount", 100000.0), step=10000.0, key=f"{key_prefix}_alipay_buy_base")
        with col2:
            signal_time = st.text_input("A 股决策时间", value=_str_default(defaults, "signal_time", "14:30"), key=f"{key_prefix}_alipay_signal_time")
        col3, col4, col5 = st.columns(3)
        with col3:
            sell_25_return = st.number_input("卖出 1/4 持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_25_return", 0.10), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_sell_25")
        with col4:
            sell_50_return = st.number_input("卖出 1/2 持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_50_return", 0.15), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_sell_50")
        with col5:
            sell_100_return = st.number_input("全卖持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_100_return", 0.20), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_sell_100")
        return {
            "buy_base_amount": float(buy_base_amount),
            "sell_25_return": float(sell_25_return),
            "sell_50_return": float(sell_50_return),
            "sell_100_return": float(sell_100_return),
            "signal_time": str(signal_time).strip() or "14:30",
        }
    if strategy_id == "alipay_enhanced":
        col1, col2, col3 = st.columns(3)
        with col1:
            buy_base_amount = st.number_input("补仓基准金额", min_value=1000.0, value=_float_default(defaults, "buy_base_amount", 100000.0), step=10000.0, key=f"{key_prefix}_alipay_enhanced_buy_base")
        with col2:
            signal_time = st.text_input("A 股决策时间", value=_str_default(defaults, "signal_time", "14:30"), key=f"{key_prefix}_alipay_enhanced_signal_time")
        with col3:
            max_position_weight = st.slider("最大仓位", min_value=0.10, max_value=1.00, value=_float_default(defaults, "max_position_weight", 0.95), step=0.05, key=f"{key_prefix}_alipay_enhanced_max_weight")
        col4, col5, col6 = st.columns(3)
        with col4:
            sell_25_return = st.number_input("卖出 1/4 持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_25_return", 0.10), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_enhanced_sell_25")
        with col5:
            sell_50_return = st.number_input("卖出 1/2 持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_50_return", 0.15), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_enhanced_sell_50")
        with col6:
            sell_100_return = st.number_input("全卖持仓收益", min_value=0.01, max_value=1.00, value=_float_default(defaults, "sell_100_return", 0.20), step=0.01, format="%.2f", key=f"{key_prefix}_alipay_enhanced_sell_100")
        col7, col8, col9 = st.columns(3)
        with col7:
            rsi_oversold = st.slider("RSI 超卖", min_value=10.0, max_value=50.0, value=_float_default(defaults, "rsi_oversold", 35.0), step=1.0, key=f"{key_prefix}_alipay_enhanced_rsi_os")
        with col8:
            rsi_overbought = st.slider("RSI 超买", min_value=55.0, max_value=90.0, value=_float_default(defaults, "rsi_overbought", 72.0), step=1.0, key=f"{key_prefix}_alipay_enhanced_rsi_ob")
        with col9:
            trend_hold_buffer = st.slider("强趋势延迟卖出缓冲", min_value=0.00, max_value=0.20, value=_float_default(defaults, "trend_hold_buffer", 0.05), step=0.01, key=f"{key_prefix}_alipay_enhanced_hold_buffer")
        col10, col11, col12 = st.columns(3)
        with col10:
            oversold_buy_multiplier = st.slider("超卖买入倍数", min_value=1.0, max_value=3.0, value=_float_default(defaults, "oversold_buy_multiplier", 1.5), step=0.1, key=f"{key_prefix}_alipay_enhanced_os_mult")
        with col11:
            weak_trend_buy_multiplier = st.slider("弱趋势买入折扣", min_value=0.1, max_value=1.0, value=_float_default(defaults, "weak_trend_buy_multiplier", 0.6), step=0.1, key=f"{key_prefix}_alipay_enhanced_weak_mult")
        with col12:
            trend_buy_multiplier = st.slider("趋势参与买入倍数", min_value=0.0, max_value=1.0, value=_float_default(defaults, "trend_buy_multiplier", 0.35), step=0.05, key=f"{key_prefix}_alipay_enhanced_trend_mult")
        col13, col14, col15 = st.columns(3)
        with col13:
            fast_ma_window = st.number_input("快均线 MA", min_value=2, value=_int_default(defaults, "fast_ma_window", 20), step=1, key=f"{key_prefix}_alipay_enhanced_fast_ma")
        with col14:
            slow_ma_window = st.number_input("慢均线 MA", min_value=3, value=_int_default(defaults, "slow_ma_window", 60), step=1, key=f"{key_prefix}_alipay_enhanced_slow_ma")
        with col15:
            bollinger_window = st.number_input("布林带窗口", min_value=5, value=_int_default(defaults, "bollinger_window", 20), step=1, key=f"{key_prefix}_alipay_enhanced_bb_window")
        return {
            "buy_base_amount": float(buy_base_amount),
            "sell_25_return": float(sell_25_return),
            "sell_50_return": float(sell_50_return),
            "sell_100_return": float(sell_100_return),
            "signal_time": str(signal_time).strip() or "14:30",
            "rsi_oversold": float(rsi_oversold),
            "rsi_overbought": float(rsi_overbought),
            "fast_ma_window": int(fast_ma_window),
            "slow_ma_window": int(slow_ma_window),
            "bollinger_window": int(bollinger_window),
            "oversold_buy_multiplier": float(oversold_buy_multiplier),
            "weak_trend_buy_multiplier": float(weak_trend_buy_multiplier),
            "trend_buy_multiplier": float(trend_buy_multiplier),
            "max_position_weight": float(max_position_weight),
            "trend_hold_buffer": float(trend_hold_buffer),
        }
    return {}


def built_in_strategy_parameter_editor(profile) -> None:
    with st.expander("编辑内置策略默认参数", expanded=False):
        st.caption("这里修改的是回测页面自动带出的默认参数。保存后永久写入配置文件，并记录一次已确认的策略变更。")
        st.dataframe(pd.DataFrame(built_in_strategy_parameter_rows(profile.strategy_id)), width="stretch", hide_index=True)
        current_defaults = get_built_in_strategy_parameters(profile.strategy_id)
        with st.form(f"edit_builtin_parameters_{profile.strategy_id}"):
            params = built_in_strategy_parameter_controls(profile.strategy_id, current_defaults, key_prefix=f"builtin_default_{profile.strategy_id}")
            change_summary = st.text_area("修改说明", value=f"更新内置策略 {profile.display_name} 的默认参数。", key=f"builtin_param_change_{profile.strategy_id}")
            risk_notes = st.text_area("风险说明", value="默认参数变化会影响后续回测结果、交易频率、成本敏感性和最大回撤，需要重新复核报告。", key=f"builtin_param_risk_{profile.strategy_id}")
            confirmed = st.checkbox("我确认本次内置策略默认参数修改仅用于研究回测，不接入实盘下单，并已经理解需要重新验证。", key=f"builtin_param_confirm_{profile.strategy_id}")
            col_save, col_reset = st.columns(2)
            with col_save:
                saved = st.form_submit_button("保存默认参数并记录确认")
            with col_reset:
                reset = st.form_submit_button("恢复系统默认参数")
        if saved:
            if not confirmed:
                st.error("保存前必须确认策略修改。")
                return
            try:
                path = save_built_in_strategy_parameters(profile.strategy_id, params)
                registry = StrategyApprovalRegistry()
                record = registry.request_approval(profile.strategy_id, "0.1.0-parameters", change_summary, risk_notes)
                approved = registry.approve(record.strategy_id, record.version)
                st.success(f"默认参数已保存并记录确认：{approved.approval_id}")
                st.write({"ParameterFile": str(path)})
                st.rerun()
            except Exception as exc:
                st.error(f"保存失败：{exc}")
        if reset:
            if not confirmed:
                st.error("恢复默认前必须确认策略修改。")
                return
            try:
                path = reset_built_in_strategy_parameters(profile.strategy_id)
                registry = StrategyApprovalRegistry()
                record = registry.request_approval(
                    profile.strategy_id,
                    "0.1.0-parameters",
                    f"恢复内置策略 {profile.display_name} 的系统默认参数。",
                    "恢复系统默认参数后，后续回测会重新使用源码默认参数，仍需复核报告变化。",
                )
                approved = registry.approve(record.strategy_id, record.version)
                st.success(f"已恢复系统默认参数并记录确认：{approved.approval_id}")
                st.write({"ParameterFile": str(path)})
                st.rerun()
            except Exception as exc:
                st.error(f"恢复失败：{exc}")


def strategy_params(strategy_name: str, prefix: str, strategy_options: dict[str, dict[str, object]] | None = None) -> dict:
    option = (strategy_options or {}).get(strategy_name, {})
    if option.get("kind") == "custom":
        spec = option["spec"]
        st.info(
            "该自定义策略使用策略库中保存的参数设置运行。修改参数请回到策略库编辑并重新确认。"
        )
        st.dataframe(pd.DataFrame([spec.to_row()]), width="stretch", hide_index=True)
        setting_rows = []
        for indicator_key, values in spec.settings.items():
            for key, value in values.items():
                setting_rows.append({"指标": indicator_key, "参数": key, "值": value})
        if setting_rows:
            st.dataframe(pd.DataFrame(setting_rows), width="stretch", hide_index=True)
        return {}
    strategy_id = str(option.get("strategy_id", "breakout"))
    defaults = get_built_in_strategy_parameters(strategy_id)
    if strategy_id in {"ma_crossover", "rsi_reversion", "bollinger_reversion", "breakout"}:
        return built_in_strategy_parameter_controls(strategy_id, defaults, prefix)
    if strategy_id == "alipay":
        st.info(
            "该策略只做研究回测：A 股按 14:30 决策点近似；同一天最多一个方向；不支持做空或实盘下单。"
        )
        st.caption("买入金额公式：BuyAmount = floor(abs(当前价 / 前一交易日收盘价 - 1) * 补仓基准金额)。")
        st.caption("卖出规则使用最高档：20% 全卖，15% 卖 1/2，10% 卖 1/4。")
        return built_in_strategy_parameter_controls(strategy_id, defaults, prefix)
    if strategy_id == "alipay_enhanced":
        st.info(
            "增强版保留原追跌杀涨低吸逻辑，并加入 RSI、布林带、MA 和 MACD：超卖时提高低吸金额，趋势转强时小额参与，强趋势未超买时延迟卖出。"
        )
        st.caption("增强版目标：亏损阶段保留低仓/分批买入防守，上涨阶段通过趋势参与和延迟卖出减少输给买入持有。")
        return built_in_strategy_parameter_controls(strategy_id, defaults, prefix)
    return built_in_strategy_parameter_controls(strategy_id, defaults, prefix)


def backtest_config(prefix: str) -> BacktestConfig:
    st.subheader("回测")
    initial_cash = st.number_input("初始资金", min_value=1000.0, value=100000.0, step=10000.0, key=f"{prefix}_cash")
    commission_rate = st.number_input(
        "佣金率",
        min_value=0.0,
        max_value=0.05,
        value=0.001,
        step=0.0005,
        format="%.4f",
        key=f"{prefix}_commission",
    )
    slippage_bps = st.number_input("滑点 bps", min_value=0.0, max_value=200.0, value=5.0, step=1.0, key=f"{prefix}_slippage")
    market_impact_bps = st.number_input(
        "冲击成本 bps",
        min_value=0.0,
        max_value=500.0,
        value=0.0,
        step=1.0,
        key=f"{prefix}_market_impact",
    )
    st.caption("滑点基点：预期成交价相对开盘价的不利偏移，1 个基点 = 0.01%。")
    st.caption("冲击成本基点：你的交易本身推动价格造成的额外成本，规模越大、流动性越差通常越高。")
    return BacktestConfig(
        initial_cash=float(initial_cash),
        commission_rate=float(commission_rate),
        slippage_bps=float(slippage_bps),
        market_impact_bps=float(market_impact_bps),
    )


def load_data(data_mode: str, csv_file, symbol: str, market: str, interval: str, start, end):
    request = BarDataRequest(symbol=symbol, market=market, interval=interval, start=str(start), end=str(end))
    csv_path = None
    if data_mode == "CSV" and csv_file is not None:
        content = csv_file.read()
        temp_path = _private_runtime_upload_path(content, suffix=Path(str(getattr(csv_file, "name", "uploaded.csv"))).suffix)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(content)
        csv_path = temp_path
    provider = make_provider(data_mode, csv_path=csv_path)
    data, resampled_from = get_bars_with_interval_fallback(provider, request)
    notes = f"Resampled locally from {resampled_from} bars because provider did not support {interval} natively." if resampled_from else ""
    quality = assess_bars(data, provider=provider.name, symbol=symbol, market=market, interval=interval, notes=notes)
    quality_path = save_quality_report(quality)
    return data, str(quality_path), quality


def load_universe_data(data_mode: str, symbols: list[str], market: str, interval: str, start, end) -> tuple[pd.DataFrame, list[str]]:
    frames = []
    quality_paths = []
    provider = make_provider(data_mode)
    for symbol in symbols:
        request = BarDataRequest(symbol=symbol, market=market, interval=interval, start=str(start), end=str(end))
        data, resampled_from = get_bars_with_interval_fallback(provider, request)
        frames.append(data)
        notes = f"Resampled locally from {resampled_from} bars because provider did not support {interval} natively." if resampled_from else ""
        quality = assess_bars(data, provider=provider.name, symbol=symbol, market=market, interval=interval, notes=notes)
        quality_paths.append(str(save_quality_report(quality)))
    return pd.concat(frames, ignore_index=True), quality_paths


def show_metrics(metrics: dict) -> None:
    cols = st.columns(6)
    items = [
        ("total_return", "总收益率"),
        ("annualized_return", "年化收益率"),
        ("sharpe", "Sharpe"),
        ("max_drawdown", "策略最大回撤"),
        ("win_rate", "胜率"),
        ("trade_count", "交易次数"),
    ]
    for col, (key, label) in zip(cols, items):
        value = metrics.get(key, 0)
        if key == "trade_count":
            text = f"{int(value)}"
        else:
            text = f"{value:.2%}" if "return" in key or "drawdown" in key or key == "win_rate" else f"{value:.2f}"
        col.metric(label, text)


def show_metric_comparison_table(metrics: dict, buy_hold: dict[str, float]) -> None:
    st.markdown("#### 核心指标对比")
    st.dataframe(pd.DataFrame(metric_comparison_rows(metrics, buy_hold)), width="stretch", hide_index=True)
    st.caption("胜率：当前定义为已完成买卖回合中盈利回合占比；买入持有没有同口径的回合交易，因此显示为不适用。")
    st.caption("相对：策略数值减去买入持有数值；最大回撤为负数时，相对值越高通常表示策略回撤更小。")


def metric_comparison_rows(metrics: dict, buy_hold: dict[str, float]) -> list[dict[str, str]]:
    strategy_total = float(metrics.get("total_return", 0.0))
    strategy_annual = float(metrics.get("annualized_return", 0.0))
    strategy_sharpe = float(metrics.get("sharpe", 0.0))
    strategy_drawdown = float(metrics.get("max_drawdown", 0.0))
    buy_total = float(buy_hold.get("buy_hold_total_return", 0.0))
    buy_annual = float(buy_hold.get("buy_hold_annualized_return", 0.0))
    buy_sharpe = float(buy_hold.get("buy_hold_sharpe", 0.0))
    buy_drawdown = float(buy_hold.get("buy_hold_max_drawdown", 0.0))
    return [
        _metric_row("总收益率", strategy_total, buy_total, kind="percent"),
        _metric_row("年化收益率", strategy_annual, buy_annual, kind="percent"),
        _metric_row("Sharpe", strategy_sharpe, buy_sharpe, kind="number"),
        _metric_row("最大回撤", strategy_drawdown, buy_drawdown, kind="percent"),
        {
            "指标": "胜率",
            "策略": _format_percent(float(metrics.get("win_rate", 0.0))),
            "买入持有": "不适用",
            "相对": "不适用",
        },
        {
            "指标": "交易次数",
            "策略": f"{int(metrics.get('trade_count', 0))}",
            "买入持有": "不适用",
            "相对": "不适用",
        },
        {
            "指标": "买入次数",
            "策略": f"{int(metrics.get('buy_count', 0))}",
            "买入持有": "不适用",
            "相对": "不适用",
        },
        {
            "指标": "卖出次数",
            "策略": f"{int(metrics.get('sell_count', 0))}",
            "买入持有": "不适用",
            "相对": "不适用",
        },
        {
            "指标": "建模交易摩擦",
            "策略": f"{float(metrics.get('cost_total', 0.0)):,.2f}",
            "买入持有": "不适用",
            "相对": "不适用",
        },
    ]


def _metric_row(label: str, strategy_value: float, buy_hold_value: float, kind: str) -> dict[str, str]:
    formatter = _format_percent if kind == "percent" else _format_number
    return {
        "指标": label,
        "策略": formatter(strategy_value),
        "买入持有": formatter(buy_hold_value),
        "相对": formatter(strategy_value - buy_hold_value),
    }


def show_strategy_comparison(result_a, result_b, data: pd.DataFrame, buy_hold: dict[str, float], label_a: str, label_b: str) -> None:
    st.markdown("#### 策略对比")
    st.dataframe(pd.DataFrame(strategy_comparison_rows(result_a.metrics, result_b.metrics, buy_hold)), width="stretch", hide_index=True)
    st.caption("策略相对买入持有：策略数值减去买入持有数值；策略一减策略二为正，表示策略一在该指标上更高。最大回撤为负数时，更高通常代表回撤更小。")
    show_strategy_comparison_chart(data, result_a, result_b, label_a, label_b)


def strategy_comparison_rows(metrics_a: dict, metrics_b: dict, buy_hold: dict[str, float]) -> list[dict[str, str]]:
    specs = [
        ("总收益率", "total_return", "buy_hold_total_return", "percent"),
        ("年化收益率", "annualized_return", "buy_hold_annualized_return", "percent"),
        ("Sharpe", "sharpe", "buy_hold_sharpe", "number"),
        ("最大回撤", "max_drawdown", "buy_hold_max_drawdown", "percent"),
        ("胜率", "win_rate", None, "percent"),
        ("交易次数", "trade_count", None, "integer"),
        ("买入次数", "buy_count", None, "integer"),
        ("卖出次数", "sell_count", None, "integer"),
        ("建模交易摩擦", "cost_total", None, "currency"),
    ]
    rows = []
    for label, metric_key, buy_hold_key, kind in specs:
        value_a = float(metrics_a.get(metric_key, 0.0))
        value_b = float(metrics_b.get(metric_key, 0.0))
        row = {
            "指标": label,
            "策略一": _format_strategy_metric_value(value_a, kind),
            "策略二": _format_strategy_metric_value(value_b, kind),
            "策略一减策略二": _format_strategy_metric_value(value_a - value_b, kind),
        }
        if buy_hold_key is None:
            row["买入持有"] = "不适用"
            row["策略一相对买入持有"] = "不适用"
            row["策略二相对买入持有"] = "不适用"
        else:
            hold_value = float(buy_hold.get(buy_hold_key, 0.0))
            row["买入持有"] = _format_strategy_metric_value(hold_value, kind)
            row["策略一相对买入持有"] = _format_strategy_metric_value(value_a - hold_value, kind)
            row["策略二相对买入持有"] = _format_strategy_metric_value(value_b - hold_value, kind)
        rows.append(row)
    column_order = ["指标", "策略一", "策略二", "买入持有", "策略一相对买入持有", "策略二相对买入持有", "策略一减策略二"]
    return [{column: row[column] for column in column_order} for row in rows]


def _format_strategy_metric_value(value: float, kind: str) -> str:
    if kind == "percent":
        return _format_percent(float(value))
    if kind == "integer":
        return f"{int(round(float(value)))}"
    if kind == "currency":
        return f"{float(value):,.2f}"
    return _format_number(float(value))


def _format_percent(value: float) -> str:
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    return f"{value:.2f}"


def show_strategy_diagnostics(result) -> None:
    st.markdown("#### 策略诊断")
    diagnostics = build_strategy_diagnostics(result)
    st.caption("这些诊断用于判断策略质量、成本韧性和可能失效环境；不构成实盘下单指令。")
    st.write("市场环境分层")
    if go is not None and not diagnostics.regime_breakdown.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=diagnostics.regime_breakdown["市场环境 Market Regime"],
                y=diagnostics.regime_breakdown["策略收益 Strategy Return"],
                name="策略收益",
                marker_color="#8A1538",
            )
        )
        fig.add_trace(
            go.Bar(
                x=diagnostics.regime_breakdown["市场环境 Market Regime"],
                y=diagnostics.regime_breakdown["目标收益 Target Return"],
                name="目标收益",
                marker_color="#667085",
            )
        )
        fig.update_layout(height=360, barmode="group", title="市场环境收益对比")
        fig.update_yaxes(tickformat=".2%")
        st.plotly_chart(fig, width="stretch")
    regime_display = _format_diagnostics_frame(diagnostics.regime_breakdown)
    st.dataframe(regime_display, width="stretch", hide_index=True)

    failure_display = _format_diagnostics_frame(diagnostics.failure_checks)
    st.dataframe(failure_display, width="stretch", hide_index=True)

    col_trade, col_cost = st.columns(2)
    with col_trade:
        st.write("交易质量")
        st.dataframe(_format_diagnostics_frame(diagnostics.trade_quality), width="stretch", hide_index=True)
    with col_cost:
        st.write("成本压力")
        cost_display = _format_diagnostics_frame(diagnostics.cost_sensitivity)
        st.dataframe(cost_display, width="stretch", hide_index=True)

    if not diagnostics.round_trips.empty:
        with st.expander("最近完成交易回合", expanded=False):
            st.dataframe(_format_diagnostics_frame(diagnostics.round_trips.tail(20)), width="stretch", hide_index=True)


def _format_diagnostics_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    display = frame.copy()
    for column in display.columns:
        if column == "Type":
            continue
        if "Return" in column or "收益" in column or "Rate" in column or "率" in column or "Worst Period" in column or "最差" in column:
            display[column] = display[column].map(lambda value: _format_percent_like(value))
        elif "Cost" in column or "成本" in column or "Equity" in column or "权益" in column or "PnL" in column or "损益" in column or "盈利" in column or "亏损" in column:
            display[column] = display[column].map(lambda value: _format_currency_like(value))
        elif column == "Value":
            display[column] = [
                _format_value_by_type(value, value_type)
                for value, value_type in zip(display["Value"], display.get("Type", ["number"] * len(display)))
            ]
    if "Type" in display.columns:
        display = display.drop(columns=["Type"])
    for column in display.columns:
        if display[column].dtype == object:
            display[column] = display[column].map(_clean_ui_label)
    display = display.rename(columns={column: str(_clean_ui_label(column)) for column in display.columns})
    return display


def _clean_ui_label(value):
    if not isinstance(value, str):
        return value
    text = value.split(" / ", 1)[0]
    replacements = {
        "类型 Type": "类型",
        "市场环境 Market Regime": "市场环境",
        "样本数 Observations": "样本数",
        "策略收益 Strategy Return": "策略收益",
        "目标收益 Target Return": "目标收益",
        "相对收益 Relative Return": "相对收益",
        "周期胜率 Period Win Rate": "周期胜率",
        "最差单期 Worst Period": "最差单期",
        "成本倍数 Cost Multiplier": "成本倍数",
        "调整后总收益 Adjusted Total Return": "调整后总收益",
        "额外成本 Additional Cost": "额外成本",
        "期末权益 Ending Equity": "期末权益",
        "状态 Status": "状态",
        "指标 Metric": "指标",
        "值 Value": "值",
        "模拟次数 Simulations": "模拟次数",
        "重采样周期 Horizon": "重采样周期",
        "中位总收益 Median Total Return": "中位总收益",
        "5% 分位总收益 5th Percentile Return": "5% 分位总收益",
        "95% 分位总收益 95th Percentile Return": "95% 分位总收益",
        "中位最大回撤 Median Max Drawdown": "中位最大回撤",
        "5% 分位最大回撤 5th Percentile Max DD": "5% 分位最大回撤",
        "中位夏普 Median Sharpe": "中位 Sharpe",
        "亏损概率 Loss Probability": "亏损概率",
        "达到目标收益概率 Target Probability": "达到目标收益概率",
        "严重回撤概率 Severe DD Probability": "严重回撤概率",
        "方向 Direction": "方向",
        "波动 Volatility": "波动",
        "高波动 High Volatility": "高波动",
        "低波动 Low Volatility": "低波动",
        "上涨 Up": "上涨",
        "下跌 Down": "下跌",
        "横盘 Flat": "横盘",
        "Pass": "通过",
        "Review": "复核",
        "Fail": "未通过",
        "Approved": "已确认",
        "Pending Approval": "待确认",
        "Pending": "待确认",
        "Rejected": "已拒绝",
        "MissingCode": "缺少代码",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _format_value_by_type(value, value_type: str) -> str:
    if value_type == "percent":
        return _format_percent_like(value)
    if value_type == "currency":
        return _format_currency_like(value)
    return _format_number_like(value)


def _format_percent_like(value) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return str(value)


def _format_currency_like(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _format_number_like(value) -> str:
    try:
        numeric = float(value)
        return f"{int(numeric)}" if numeric.is_integer() else f"{numeric:.2f}"
    except (TypeError, ValueError):
        return str(value)


def trade_marker_style(side: str) -> dict[str, object]:
    """Return a quiet, high-contrast marker style for trade annotations."""
    normalized = str(side).upper()
    if normalized == "BUY":
        return {
            "symbol": "circle-open",
            "size": 7,
            "color": "#d97706",
            "opacity": 0.95,
            "line": {"color": "#d97706", "width": 1.6},
        }
    if normalized == "SELL":
        return {
            "symbol": "x-thin",
            "size": 8,
            "color": "#2563eb",
            "opacity": 0.90,
            "line": {"color": "#2563eb", "width": 1.4},
        }
    return {"symbol": "circle", "size": 6, "color": "#667085", "opacity": 0.70}


def show_portfolio_attribution(result) -> None:
    st.markdown("#### 组合归因")
    concentration = portfolio_concentration_metrics(result)
    cols = st.columns(5)
    cols[0].metric("最大单标的权重", f"{concentration['max_symbol_weight']:.2%}")
    cols[1].metric("前三权重", f"{concentration['top3_ending_weight']:.2%}")
    cols[2].metric("标的数量", f"{int(concentration['symbol_count'])}")
    cols[3].metric("现金权重", f"{concentration.get('cash_weight', 0.0):.2%}")
    cols[4].metric("总暴露", f"{concentration.get('gross_exposure', 0.0):.2%}")
    attribution = portfolio_attribution(result)
    if attribution.empty:
        st.info("暂无持仓归因。")
        return
    display = attribution.rename(
        columns={
            "symbol": "标的",
            "avg_weight": "平均权重",
            "max_weight": "最大权重",
            "ending_weight": "期末权重",
            "ending_position_value": "期末持仓",
            "price_return": "价格收益",
            "trade_count": "交易次数",
            "execution_cost": "执行成本",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)


def show_portfolio_risk_view(result) -> None:
    st.markdown("#### 组合风险视图")
    exposure = portfolio_exposure_breakdown(result)
    stress = portfolio_stress_scenarios(result)
    single_loss = portfolio_single_symbol_loss(result)

    if exposure.empty and stress.empty:
        st.info("暂无组合风险数据。")
        return

    if not exposure.empty:
        display_exposure = exposure.copy()
        display_exposure["exposure_value"] = display_exposure["exposure_value"].map(lambda value: f"{float(value):,.2f}")
        display_exposure["exposure_weight"] = display_exposure["exposure_weight"].map(lambda value: f"{float(value):.2%}")
        st.write("市场、货币和主题暴露")
        st.dataframe(
            display_exposure.rename(
                columns={
                    "dimension": "维度",
                    "bucket": "分类",
                    "exposure_value": "暴露金额",
                    "exposure_weight": "暴露比例",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    if not stress.empty:
        display_stress = stress.copy()
        display_stress["shock"] = display_stress["shock"].map(lambda value: f"{float(value):.0%}")
        display_stress["loss_amount"] = display_stress["loss_amount"].map(lambda value: f"{float(value):,.2f}")
        display_stress["account_loss_ratio"] = display_stress["account_loss_ratio"].map(lambda value: f"{float(value):.2%}")
        display_stress["ending_equity_after_shock"] = display_stress["ending_equity_after_shock"].map(lambda value: f"{float(value):,.2f}")
        display_stress["rebound_needed_to_recover"] = display_stress["rebound_needed_to_recover"].map(lambda value: "N/A" if float(value) == float("inf") else f"{float(value):.2%}")
        st.write("下跌情景压力测试")
        st.dataframe(
            display_stress.rename(
                columns={
                    "shock": "持仓下跌情景",
                    "loss_amount": "账户损失金额",
                    "account_loss_ratio": "账户损失比例",
                    "ending_equity_after_shock": "情景后权益",
                    "rebound_needed_to_recover": "回本所需涨幅",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    if not single_loss.empty:
        display_single = single_loss.head(10).copy()
        display_single["position_value"] = display_single["position_value"].map(lambda value: f"{float(value):,.2f}")
        display_single["shock"] = display_single["shock"].map(lambda value: f"{float(value):.0%}")
        display_single["loss_amount"] = display_single["loss_amount"].map(lambda value: f"{float(value):,.2f}")
        display_single["account_loss_ratio"] = display_single["account_loss_ratio"].map(lambda value: f"{float(value):.2%}")
        st.write("单一标的冲击")
        st.dataframe(
            display_single.rename(
                columns={
                    "symbol": "标的",
                    "position_value": "持仓金额",
                    "shock": "下跌情景",
                    "loss_amount": "损失金额",
                    "account_loss_ratio": "账户损失比例",
                }
            ),
            width="stretch",
            hide_index=True,
        )


def show_strategy_performance_chart(data: pd.DataFrame, result, strategy_name: str) -> None:
    if go is None or make_subplots is None:
        st.warning("需要安装 plotly 才能显示图表。")
        return
    returns = strategy_target_return_frame(data, result)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45])
    fig.add_trace(
        go.Candlestick(
            x=data["datetime"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="Price",
            increasing={"line": {"color": "#d92d20"}, "fillcolor": "#f04438"},
            decreasing={"line": {"color": "#039855"}, "fillcolor": "#12b76a"},
        ),
        row=1,
        col=1,
    )
    trades = result.trades
    if not trades.empty:
        buys = trades[trades["side"] == "BUY"]
        sells = trades[trades["side"] == "SELL"]
        fig.add_trace(
            go.Scatter(
                x=buys["datetime"],
                y=buys["price"],
                mode="markers",
                name="买入",
                marker=trade_marker_style("BUY"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=sells["datetime"],
                y=sells["price"],
                mode="markers",
                name="卖出",
                marker=trade_marker_style("SELL"),
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(x=returns["datetime"], y=returns["strategy_return"], name="策略收益率", line={"color": "#b42318"}),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=returns["datetime"], y=returns["target_return"], name="目标走势收益率", line={"color": "#475467"}),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=returns["datetime"], y=returns["relative_return"], name="相对收益", line={"color": "#2563eb", "dash": "dot"}),
        row=2,
        col=1,
    )
    fig.update_layout(height=720, title=f"目标走势与策略收益 - {strategy_name}", xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="收益率", tickformat=".2%", row=2, col=1)
    st.plotly_chart(fig, width="stretch")


def strategy_target_return_frame(data: pd.DataFrame, result) -> pd.DataFrame:
    equity = result.equity_curve[["datetime", "equity"]].copy()
    equity["datetime"] = pd.to_datetime(equity["datetime"])
    equity["equity"] = pd.to_numeric(equity["equity"], errors="coerce")
    first_equity = float(equity["equity"].dropna().iloc[0]) if not equity["equity"].dropna().empty else 0.0
    equity["strategy_return"] = equity["equity"] / first_equity - 1.0 if first_equity else 0.0

    target = data[["datetime", "close"]].copy()
    target["datetime"] = pd.to_datetime(target["datetime"])
    target["close"] = pd.to_numeric(target["close"], errors="coerce")
    first_close = float(target["close"].dropna().iloc[0]) if not target["close"].dropna().empty else 0.0
    target["target_return"] = target["close"] / first_close - 1.0 if first_close else 0.0

    frame = equity[["datetime", "strategy_return"]].merge(target[["datetime", "target_return"]], on="datetime", how="inner")
    frame["relative_return"] = frame["strategy_return"] - frame["target_return"]
    return frame.sort_values("datetime").reset_index(drop=True)


def strategy_comparison_return_frame(data: pd.DataFrame, result_a, result_b) -> pd.DataFrame:
    frame_a = strategy_target_return_frame(data, result_a).rename(
        columns={
            "strategy_return": "strategy_a_return",
            "relative_return": "strategy_a_relative_return",
        }
    )
    frame_b = strategy_target_return_frame(data, result_b).rename(
        columns={
            "strategy_return": "strategy_b_return",
            "relative_return": "strategy_b_relative_return",
        }
    )
    frame = frame_a[["datetime", "target_return", "strategy_a_return", "strategy_a_relative_return"]].merge(
        frame_b[["datetime", "strategy_b_return", "strategy_b_relative_return"]],
        on="datetime",
        how="inner",
    )
    frame["strategy_a_minus_b_return"] = frame["strategy_a_return"] - frame["strategy_b_return"]
    return frame.sort_values("datetime").reset_index(drop=True)


def show_strategy_comparison_chart(data: pd.DataFrame, result_a, result_b, label_a: str, label_b: str) -> None:
    if go is None or make_subplots is None:
        st.warning("需要安装 plotly 才能显示图表。")
        return
    frame = strategy_comparison_return_frame(data, result_a, result_b)
    if frame.empty:
        st.info("暂无可对比的收益路径。")
        return
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.58, 0.42])
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["target_return"], name="目标走势收益率", line={"color": "#667085", "width": 2}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["strategy_a_return"], name=f"策略一：{label_a}", line={"color": "#b42318", "width": 2}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["strategy_b_return"], name=f"策略二：{label_b}", line={"color": "#2563eb", "width": 2}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["strategy_a_relative_return"], name="策略一相对目标", line={"color": "#f97316", "dash": "dot"}),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["strategy_b_relative_return"], name="策略二相对目标", line={"color": "#0ea5e9", "dash": "dot"}),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=frame["datetime"], y=frame["strategy_a_minus_b_return"], name="策略一减策略二", line={"color": "#344054", "dash": "dash"}),
        row=2,
        col=1,
    )
    fig.update_layout(height=650, title="策略收益路径对比")
    fig.update_yaxes(title_text="收益率", tickformat=".2%", row=1, col=1)
    fig.update_yaxes(title_text="相对收益", tickformat=".2%", row=2, col=1)
    st.plotly_chart(fig, width="stretch")


def show_equity_friction_chart(result, data: pd.DataFrame | None = None) -> None:
    if go is None or make_subplots is None:
        st.warning("需要安装 plotly 才能显示图表。")
        return
    curve_columns = ["datetime", "equity"]
    if "position_value" in result.equity_curve.columns:
        curve_columns.append("position_value")
    curve = result.equity_curve[curve_columns].copy()
    curve["datetime"] = pd.to_datetime(curve["datetime"])
    if "position_value" not in curve.columns:
        curve["position_value"] = 0.0
    curve["position_value"] = pd.to_numeric(curve["position_value"], errors="coerce").fillna(0.0)
    initial_cash = float(result.metadata.get("backtest", {}).get("initial_cash", curve["equity"].iloc[0] if not curve.empty else 0.0))
    curve["strategy_return"] = curve["equity"] / initial_cash - 1.0 if initial_cash else 0.0
    if result.trades.empty:
        curve["cumulative_friction_pct"] = 0.0
    else:
        costs = result.trades.groupby("datetime")["execution_cost"].sum().reset_index()
        curve = curve.merge(costs, on="datetime", how="left")
        curve["execution_cost"] = curve["execution_cost"].fillna(0.0)
        curve["cumulative_execution_cost"] = curve["execution_cost"].cumsum()
        curve["cumulative_friction_pct"] = curve["cumulative_execution_cost"] / curve["equity"].replace(0, pd.NA)
        curve["cumulative_friction_pct"] = curve["cumulative_friction_pct"].fillna(0.0)
    if data is not None:
        returns = strategy_target_return_frame(data, result)
        curve = curve.merge(returns[["datetime", "relative_return"]], on="datetime", how="left")
        curve["relative_return"] = curve["relative_return"].fillna(0.0)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=curve["datetime"], y=curve["equity"], name="权益", line={"color": "#b42318"}), secondary_y=False)
    fig.add_trace(
        go.Scatter(x=curve["datetime"], y=curve["position_value"], name="持仓金额", line={"color": "#667085", "dash": "dash"}),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=curve["datetime"], y=curve["strategy_return"], name="策略收益率", line={"color": "#dc2626", "dash": "dot"}),
        secondary_y=True,
    )
    if "relative_return" in curve.columns:
        fig.add_trace(
            go.Scatter(x=curve["datetime"], y=curve["relative_return"], name="相对收益", line={"color": "#2563eb", "dash": "dash"}),
            secondary_y=True,
        )
    fig.add_trace(
        go.Scatter(
            x=curve["datetime"],
            y=curve["cumulative_friction_pct"],
            name="累计交易摩擦占当前权益比例",
            line={"color": "#7dd3fc"},
        ),
        secondary_y=True,
    )
    fig.update_layout(height=420, title="权益与累计交易摩擦占比")
    fig.update_yaxes(title_text="权益 / 持仓金额", secondary_y=False)
    fig.update_yaxes(title_text="收益率 / 摩擦占比", tickformat=".2%", secondary_y=True)
    st.plotly_chart(fig, width="stretch")


def show_bootstrap_robustness(result, target_return: float = 0.0) -> None:
    st.markdown("#### Bootstrap 鲁棒性")
    robustness = bootstrap_equity_robustness(result.equity_curve, simulations=10_000, seed=42, target_return=float(target_return))
    st.dataframe(_bootstrap_summary_display(robustness), width="stretch", hide_index=True)
    st.caption("Bootstrap 使用历史策略日收益重采样生成模拟路径，用于检查结果脆弱性；它不是未来收益预测。")
    if go is None or robustness.simulations.empty:
        return
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Histogram(x=robustness.simulations["total_return"], nbinsx=32, marker_color="#8A1538"))
        fig.update_layout(height=330, title="模拟总收益分布", xaxis_title="总收益率", yaxis_title="次数")
        fig.update_xaxes(tickformat=".2%")
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig = go.Figure(go.Histogram(x=robustness.simulations["max_drawdown"], nbinsx=32, marker_color="#0F766E"))
        fig.update_layout(height=330, title="模拟最大回撤分布", xaxis_title="最大回撤", yaxis_title="次数")
        fig.update_xaxes(tickformat=".2%")
        st.plotly_chart(fig, width="stretch")
    if not robustness.sample_paths.empty:
        fig = go.Figure()
        if not robustness.path_interval.empty:
            interval = robustness.path_interval
            fig.add_trace(
                go.Scatter(
                    x=interval["step"],
                    y=interval["p95"] - 1.0,
                    mode="lines",
                    line={"color": "rgba(14, 165, 233, 0.0)", "width": 0},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=interval["step"],
                    y=interval["p05"] - 1.0,
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(125, 211, 252, 0.24)",
                    line={"color": "rgba(14, 165, 233, 0.0)", "width": 0},
                    name="5%-95% 分散区间",
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=interval["step"],
                    y=interval["median"] - 1.0,
                    mode="lines",
                    line={"color": "#0ea5e9", "width": 2},
                    name="中位路径",
                )
            )
        for column in [column for column in robustness.sample_paths.columns if column != "step"]:
            fig.add_trace(
                go.Scatter(
                    x=robustness.sample_paths["step"],
                    y=robustness.sample_paths[column] - 1.0,
                    mode="lines",
                    line={"color": "rgba(138, 21, 56, 0.18)", "width": 1},
                    showlegend=False,
                )
            )
        fig.update_layout(height=360, title="Bootstrap 样本收益路径", xaxis_title="步数", yaxis_title="收益率")
        fig.update_yaxes(tickformat=".2%")
        st.plotly_chart(fig, width="stretch")


def _bootstrap_summary_display(robustness) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"指标": _clean_ui_label(row["指标 Metric"]), "值": row["值 Value"]}
            for row in robustness_summary_rows(robustness)
        ]
    )


def show_scan_chart(summary: pd.DataFrame) -> None:
    st.markdown("#### 参数扫描可视化")
    param_cols = [column for column in summary.columns if column.startswith("param_")]
    if len(param_cols) >= 2:
        heatmap_cols = st.columns(3)
        heatmap_specs = [
            ("total_return", "总收益热力图", "RdYlGn_r", ".2%"),
            ("sharpe", "Sharpe 热力图", "Viridis", ".2f"),
            ("max_drawdown", "最大回撤热力图", "RdYlGn_r", ".2%"),
        ]
        for col, (metric, title, colorscale, text_format) in zip(heatmap_cols, heatmap_specs):
            with col:
                heatmap = parameter_heatmap_frame(summary, metric)
                if heatmap.empty:
                    st.info(f"{title}: 暂无数据 No data.")
                    continue
                fig = go.Figure(
                    go.Heatmap(
                        z=heatmap.to_numpy(),
                        x=[str(value) for value in heatmap.columns],
                        y=[str(value) for value in heatmap.index],
                        colorscale=colorscale,
                        colorbar={"title": metric},
                        text=heatmap.applymap(lambda value: _format_heatmap_text(value, text_format)).to_numpy(),
                        texttemplate="%{text}",
                        hovertemplate=f"{param_cols[0]}=%{{x}}<br>{param_cols[1]}=%{{y}}<br>{metric}=%{{z}}<extra></extra>",
                    )
                )
                fig.update_layout(height=330, title=title, xaxis_title=param_cols[0].replace("param_", ""), yaxis_title=param_cols[1].replace("param_", ""))
                st.plotly_chart(fig, width="stretch")
    else:
        st.info("参数少于两个时，热力图不可用。")

    top = top_experiment_runs_frame(summary, n=10)
    if top.empty:
        return
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=top["run_label"], y=top["total_return"], name="总收益率", marker_color="#8A1538"), secondary_y=False)
    fig.add_trace(go.Scatter(x=top["run_label"], y=top["sharpe"], name="Sharpe", mode="lines+markers", line={"color": "#0F766E"}), secondary_y=True)
    fig.update_layout(height=390, title="Top N 参数组合对比", xaxis_title="参数组合")
    fig.update_yaxes(title_text="总收益率", tickformat=".2%", secondary_y=False)
    fig.update_yaxes(title_text="Sharpe", secondary_y=True)
    st.plotly_chart(fig, width="stretch")


def parameter_heatmap_frame(summary: pd.DataFrame, metric: str) -> pd.DataFrame:
    param_cols = [column for column in summary.columns if column.startswith("param_")]
    if len(param_cols) < 2 or metric not in summary.columns:
        return pd.DataFrame()
    x_param, y_param = param_cols[:2]
    frame = summary[[x_param, y_param, metric]].copy()
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    frame = frame.dropna(subset=[metric])
    if frame.empty:
        return pd.DataFrame()
    heatmap = frame.pivot_table(index=y_param, columns=x_param, values=metric, aggfunc="mean")
    return heatmap.sort_index().sort_index(axis=1)


def top_experiment_runs_frame(summary: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    frame = summary.head(n).copy()
    for column in ["total_return", "sharpe", "max_drawdown"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
        else:
            frame[column] = 0.0
    param_cols = [column for column in frame.columns if column.startswith("param_")]
    if param_cols:
        frame["run_label"] = frame[param_cols].astype(str).agg(" / ".join, axis=1)
    elif "run_id" in frame.columns:
        frame["run_label"] = frame["run_id"].astype(str)
    else:
        frame["run_label"] = [str(index + 1) for index in range(len(frame))]
    return frame[["run_label", "total_return", "sharpe", "max_drawdown"] + param_cols]


def _format_heatmap_text(value: object, text_format: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(number):
        return ""
    if text_format == ".2%":
        return f"{number:.1%}"
    return f"{number:.2f}"


def show_tables(result) -> None:
    tab1, tab2, tab3 = st.tabs(["交易", "持仓", "信号"])
    with tab1:
        trades = result.trades
        if not trades.empty:
            st.dataframe(trades.style.map(_side_cell_style, subset=["side"]), width="stretch")
        else:
            st.dataframe(trades, width="stretch")
    with tab2:
        st.dataframe(result.positions.tail(200), width="stretch")
    with tab3:
        st.dataframe(result.signals.tail(200), width="stretch")


def _side_cell_style(value: str) -> str:
    if value == "BUY":
        return "background-color: #fde2e2; color: #991b1b; font-weight: 700"
    if value == "SELL":
        return "background-color: #dcfce7; color: #166534; font-weight: 700"
    return ""


def parse_int_list(text: str) -> list[int]:
    values = []
    for item in text.split(","):
        item = item.strip()
        if item:
            values.append(int(item))
    return values


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ql-ink: #1f2937;
          --ql-muted: #667085;
          --ql-panel: #f7f8fa;
          --ql-accent: #8a1538;
          --ql-border: #d9dee7;
          --ql-soft: #f3f5f8;
          --ql-navy: #172033;
        }
        .stApp {
          background: #fbfcfd;
          color: var(--ql-ink);
        }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        header[data-testid="stHeader"],
        #MainMenu,
        footer {
          display: none !important;
          visibility: hidden !important;
        }
        .block-container {
          padding-top: 1rem;
          padding-bottom: 4rem;
        }
        [data-testid="stSidebar"] {
          background: #ffffff;
          border-right: 1px solid var(--ql-border);
        }
        [data-testid="stSidebar"] h3 {
          margin-top: 0.8rem !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
          border: 1px solid transparent;
          border-radius: 8px;
          padding: 5px 8px;
          margin-bottom: 2px;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
          background: #f6f8fb;
          border-color: var(--ql-border);
        }
        h1 {
          font-size: 2.9rem !important;
          letter-spacing: 0 !important;
          color: var(--ql-navy);
          margin: 0 !important;
        }
        h2, h3 {
          letter-spacing: 0 !important;
          color: var(--ql-navy);
          margin-top: 1.4rem !important;
        }
        .ql-hero {
          border: 1px solid var(--ql-border);
          background: #ffffff;
          border-radius: 8px;
          padding: 24px 26px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
          margin-bottom: 18px;
        }
        .ql-eyebrow {
          color: var(--ql-accent);
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        .ql-hero-cn, .ql-hero-en {
          color: var(--ql-muted);
          max-width: 760px;
          margin: 8px 0 0 0;
          line-height: 1.55;
          font-size: 1.02rem;
        }
        [data-testid="stMetric"] {
          background: #ffffff;
          border: 1px solid var(--ql-border);
          padding: 14px 16px;
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        [data-testid="stMetricLabel"] {
          color: var(--ql-muted);
        }
        [data-testid="stMetricValue"] {
          color: #111827;
          font-weight: 650;
        }
        div.stButton > button[kind="primary"],
        button[data-testid="stBaseButton-primary"] {
          background: #e0f2fe !important;
          color: #075985 !important;
          border: 1px solid #7dd3fc !important;
          border-radius: 6px;
          font-weight: 650;
          box-shadow: 0 1px 2px rgba(14, 165, 233, 0.16);
        }
        div.stButton > button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover {
          background: #bae6fd !important;
          border-color: #38bdf8 !important;
          color: #075985 !important;
        }
        div[data-baseweb="tab-list"] {
          border-bottom: 1px solid var(--ql-border);
        }
        .ql-action {
          min-height: 238px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .ql-action-title {
          color: var(--ql-navy);
          font-weight: 700;
          line-height: 1.35;
        }
        .ql-action-title span {
          color: var(--ql-muted);
          font-weight: 650;
        }
        .ql-action-body, .ql-action-body-en {
          color: var(--ql-muted);
          line-height: 1.45;
          font-size: 0.92rem;
        }
        .ql-action-target {
          margin-top: auto;
          border-top: 1px solid var(--ql-border);
          padding-top: 10px;
          color: var(--ql-accent);
          font-weight: 700;
          font-size: 0.9rem;
          text-decoration: none;
        }
        .ql-action-target span {
          color: var(--ql-accent);
          font-weight: 650;
        }
        .ql-action-target:hover {
          text-decoration: underline;
        }
        .ql-term {
          display: inline-block;
          margin: 0 6px 8px 0;
          padding: 4px 8px;
          border: 1px solid var(--ql-border);
          border-radius: 999px;
          background: #ffffff;
          color: var(--ql-navy);
          font-size: 0.82rem;
          cursor: help;
        }
        .ql-term:hover {
          border-color: #7dd3fc;
          background: #f0f9ff;
        }
        .ql-term-inline {
          display: inline-block;
          padding: 1px 6px;
          border: 1px solid #b9d7e8;
          border-radius: 999px;
          background: #f8fbfd;
          color: #075985;
          font-size: 0.92em;
          font-weight: 650;
          cursor: help;
          white-space: nowrap;
        }
        .ql-term-inline:hover {
          background: #e0f2fe;
          border-color: #38bdf8;
        }
        .ql-sidebar-guide-card {
          margin: 10px 0 12px 0;
          padding: 12px;
          border: 1px solid var(--ql-border);
          border-radius: 8px;
          background: #f9fafb;
          color: var(--ql-ink);
          line-height: 1.5;
          font-size: 0.9rem;
        }
        .ql-sidebar-guide-label {
          margin-top: 8px;
          color: var(--ql-accent);
          font-size: 0.76rem;
          font-weight: 750;
          letter-spacing: 0.02em;
        }
        .ql-sidebar-guide-label:first-child {
          margin-top: 0;
        }
        .ql-sidebar-mini-list {
          margin: 6px 0 0 18px;
          padding: 0;
          color: var(--ql-ink);
          line-height: 1.45;
          font-size: 0.86rem;
        }
        .ql-sidebar-mini-list li {
          margin-bottom: 5px;
        }
        .ql-runbook {
          min-height: 278px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-radius: 8px;
          padding: 15px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        .ql-runbook-phase {
          color: var(--ql-navy);
          font-weight: 750;
          line-height: 1.35;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--ql-border);
        }
        .ql-runbook-phase span {
          color: var(--ql-muted);
          font-weight: 650;
        }
        .ql-runbook-label {
          margin-top: 4px;
          color: var(--ql-accent);
          font-size: 0.78rem;
          font-weight: 750;
          text-transform: uppercase;
        }
        .ql-runbook-body, .ql-runbook-body-en {
          color: var(--ql-muted);
          line-height: 1.42;
          font-size: 0.88rem;
        }
        .ql-step {
          min-height: 188px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-radius: 8px;
          padding: 14px;
          display: flex;
          flex-direction: column;
          gap: 9px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        .ql-step-index {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: var(--ql-navy);
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.85rem;
          font-weight: 700;
        }
        .ql-step-title {
          color: var(--ql-navy);
          font-weight: 700;
          line-height: 1.35;
        }
        .ql-step-title span {
          color: var(--ql-muted);
          font-weight: 650;
        }
        .ql-step-body, .ql-step-body-en {
          color: var(--ql-muted);
          line-height: 1.42;
          font-size: 0.9rem;
        }
        .ql-empty-panel {
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-radius: 8px;
          padding: 18px 20px;
          color: var(--ql-ink);
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        .ql-empty-panel ul {
          margin: 12px 0 0 18px;
          padding: 0;
          color: var(--ql-muted);
          line-height: 1.65;
        }
        .ql-judgement {
          min-height: 182px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-left: 5px solid var(--ql-border);
          border-radius: 8px;
          padding: 14px 16px;
          display: flex;
          flex-direction: column;
          gap: 9px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        .ql-judgement-pass {
          border-left-color: #0f766e;
        }
        .ql-judgement-watch {
          border-left-color: #b7791f;
        }
        .ql-judgement-review {
          border-left-color: #b42318;
        }
        .ql-judgement-status {
          color: var(--ql-muted);
          font-size: 0.82rem;
          font-weight: 700;
          text-transform: uppercase;
        }
        .ql-judgement-title {
          color: var(--ql-navy);
          font-weight: 700;
          line-height: 1.35;
        }
        .ql-judgement-title span {
          color: var(--ql-muted);
        }
        .ql-judgement-body, .ql-judgement-body-en {
          color: var(--ql-muted);
          line-height: 1.45;
          font-size: 0.92rem;
        }
        .ql-sentiment-card {
          min-height: 226px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-top: 5px solid #6b7280;
          border-radius: 8px;
          padding: 15px 16px;
          margin-bottom: 14px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .ql-sentiment-hot {
          border-top-color: #b91c1c;
        }
        .ql-sentiment-cold {
          border-top-color: #1f5f7a;
        }
        .ql-sentiment-neutral {
          border-top-color: #6b7280;
        }
        .ql-sentiment-top {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          color: var(--ql-navy);
          font-weight: 750;
          line-height: 1.25;
        }
        .ql-sentiment-top strong {
          font-size: 1.7rem;
          color: #111827;
        }
        .ql-sentiment-symbol {
          margin-top: 5px;
          color: var(--ql-muted);
          font-size: 0.86rem;
        }
        .ql-sentiment-state {
          margin-top: 10px;
          color: var(--ql-accent);
          font-weight: 750;
        }
        .ql-sentiment-grid {
          margin-top: 10px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 7px;
          color: var(--ql-ink);
          font-size: 0.88rem;
        }
        .ql-sentiment-grid span,
        .ql-market-feel-grid span {
          cursor: help;
        }
        .ql-sentiment-reading {
          margin-top: 12px;
          color: var(--ql-muted);
          line-height: 1.45;
          font-size: 0.9rem;
        }
        .ql-market-feel-card {
          min-height: 286px;
          background: #ffffff;
          border: 1px solid var(--ql-border);
          border-top: 5px solid #6b7280;
          border-radius: 8px;
          padding: 15px 16px;
          margin-bottom: 14px;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .ql-market-feel-strong {
          border-top-color: #b91c1c;
        }
        .ql-market-feel-weak {
          border-top-color: #15803d;
        }
        .ql-market-feel-risk {
          border-top-color: #b7791f;
        }
        .ql-market-feel-neutral {
          border-top-color: #64748b;
        }
        .ql-market-feel-grid {
          margin-top: 12px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          color: var(--ql-ink);
          font-size: 0.88rem;
        }
        .ql-market-feel-conclusion {
          margin-top: 12px;
          color: var(--ql-navy);
          font-weight: 700;
          line-height: 1.45;
          font-size: 0.92rem;
        }
        .ql-market-feel-answer {
          margin: 12px 0 16px 0;
          padding: 14px 16px;
          border: 1px solid var(--ql-border);
          border-left: 5px solid #0f766e;
          border-radius: 8px;
          background: #ffffff;
          color: var(--ql-ink);
          line-height: 1.5;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .ql-market-feel-answer-title {
          color: var(--ql-navy);
          font-weight: 750;
          margin-bottom: 8px;
        }
        .ql-market-feel-answer-note {
          margin-top: 10px;
          color: var(--ql-muted);
          font-size: 0.9rem;
        }
        @media (max-width: 900px) {
          .ql-hero {
            grid-template-columns: 1fr;
          }
          .ql-action, .ql-runbook, .ql-step, .ql-judgement, .ql-sentiment-card, .ql-market-feel-card {
            min-height: auto;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
