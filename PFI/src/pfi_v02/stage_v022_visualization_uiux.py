from __future__ import annotations

from collections import Counter
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Mapping

from pfi_v02.stage_v022_formula_scoring import (
    calculate_cashflow_projection,
    calculate_consumption_model_metrics,
    load_stage7_alipay_formula_inputs_from_metadatabase,
)
from pfi_v02.stage_v022_runtime_diff import build_dependency_hash_snapshot, load_stage8_runtime_diff_inputs_from_canonical_sources
from pfi_v02.stage_v022_tags_views import build_stage6_default_tag_library


STAGE9_REQUIRED_MODULES = (
    "首页总览",
    "参数中心",
    "Interconnection Map",
    "Metric Dependency Graph",
    "消费分类与标签",
    "投资模型",
    "消费模型",
    "现金流可视化",
    "Runtime Diff Dashboard",
    "Agent Review Queue",
    "验收清单",
)

STAGE9_DATA_STATUS_FIELDS = (
    "数据来源覆盖率",
    "最近更新时间",
    "参数版本",
    "公式版本",
    "汇率快照 ID",
    "ledger_hash",
    "interconnection_hash",
    "是否存在未匹配记录",
    "是否存在低置信记录",
    "是否存在缓存",
    "是否需要重算",
    "UI 指标是否与报告一致",
)

STAGE9_CASHFLOW_WINDOWS_DAYS = (7, 21, 30, 60, 90, 180, 360)
STAGE9_CASHFLOW_VISUALIZATIONS = ("现金流阶梯图", "现金流瀑布图", "储备金安全带", "投资入金挤压图")
STAGE9_PARAMETER_CENTER_DOMAINS = ("货币", "汇率", "分类", "标签", "阈值", "公式", "置信度", "现金流窗口")
STAGE9_REAL_DATA_SOURCE = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
STAGE9_UNMEASURED_COMPUTE_STATUS_ZH = "本轮未测量，不显示模拟耗时。"


def _resolve_stage9_roots(project_root: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve() if project_root is not None else Path(__file__).resolve().parents[2]
    if root.name == "PFI":
        return root, root.parent
    if (root / "PFI").is_dir() and (root / "MetaDatabase").is_dir():
        return root / "PFI", root
    return root, root.parent


def _money(value: object) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def _money_text(value: object) -> str:
    return f"CNY {_money(value):,.2f}"


def load_stage9_real_visualization_context(project_root: str | Path | None = None) -> dict[str, object]:
    pfi_root, repo_root = _resolve_stage9_roots(project_root)
    stage8 = load_stage8_runtime_diff_inputs_from_canonical_sources(pfi_root)
    stage8_summary = stage8["source_summary"]
    stage8_inputs = stage8["inputs"]
    dependency_snapshot = build_dependency_hash_snapshot(stage8_inputs, run_id="stage9-real-visualization-context")

    metadatabase_root = repo_root / "MetaDatabase" / "PFI" / "alipay_daily"
    stage7_inputs = load_stage7_alipay_formula_inputs_from_metadatabase(metadatabase_root)
    consumption_metrics = calculate_consumption_model_metrics(stage7_inputs["consumption_events"])
    normalized_transactions = tuple(stage8_inputs["normalized_transactions"])
    review_state_counts = Counter(str(row.get("review_state") or "") for row in normalized_transactions if isinstance(row, Mapping))
    review_record_count = int(review_state_counts.get("NEEDS_REVIEW", 0))
    tag_count = len(build_stage6_default_tag_library())
    cashflow_inputs = dict(stage7_inputs["cashflow_projection_inputs"])
    cashflow_projections = []
    for day in STAGE9_CASHFLOW_WINDOWS_DAYS:
        active_inputs = dict(cashflow_inputs)
        active_inputs["horizon_days"] = day
        cashflow_projections.append(calculate_cashflow_projection(**active_inputs))

    fx_content = {}
    fx_snapshot = stage8_inputs.get("fx_snapshot", {})
    if isinstance(fx_snapshot, Mapping):
        fx_content = fx_snapshot.get("content", {}) if isinstance(fx_snapshot.get("content"), Mapping) else {}
    last_updated = f"{fx_content.get('effective_date', '汇率快照日期待更新')} {fx_content.get('effective_time_local', '06:00')} Australia/Sydney"
    return {
        "schema": "PFIV022Stage9RealVisualizationContextV1",
        "real_data_source": STAGE9_REAL_DATA_SOURCE,
        "raw_file_count": int(stage8_summary["raw_file_count"]),
        "normalized_transaction_count": int(stage8_summary["normalized_transaction_count"]),
        "ledger_event_count": int(stage8_summary["ledger_event_count"]),
        "interconnection_count": int(stage8_summary["interconnection_count"]),
        "interconnection_state_zh": str(stage8_summary["interconnection_state_zh"]),
        "review_record_count": review_record_count,
        "tag_count": tag_count,
        "advice_item_count": 0,
        "chart_count": len(STAGE9_CASHFLOW_VISUALIZATIONS) + 3,
        "gross_consumption_cny": consumption_metrics["gross_consumption_cny"],
        "living_consumption_cny": consumption_metrics["living_consumption_cny"],
        "refund_offset_cny": consumption_metrics["refund_offset_cny"],
        "cashflow_projection_inputs": cashflow_inputs,
        "cashflow_projections": tuple(cashflow_projections),
        "cashflow_data_status_zh": "现金流图表使用真实支付宝历史流水派生输入；当前生活现金余额缺少真实账户快照，不展示伪造余额。",
        "investment_data_status_zh": str(stage7_inputs["investment_data_status_zh"]),
        "event_type_counts": stage7_inputs["event_type_counts"],
        "dependency_hashes": dependency_snapshot["dependency_hashes"],
        "run_hash": dependency_snapshot["run_hash"],
        "fx_snapshot_id": fx_content.get("snapshot_id", "fx_snapshot_missing"),
        "last_updated": last_updated,
        "impact_counts": {
            "review_records": review_record_count,
            "tags": tag_count,
            "advice_items": 0,
            "charts": len(STAGE9_CASHFLOW_VISUALIZATIONS) + 3,
        },
        "network_allowed": False,
        "data_boundary_zh": "Stage 9 可视化只展示真实 MetaDatabase 派生指标、本地参数和真实空态；不得使用固定假金额、固定假匹配率或模拟耗时。",
    }


def _param_value(catalog: Mapping[str, object], *path: str, default: object = "未配置") -> object:
    node: object = catalog
    for key in path:
        if not isinstance(node, Mapping) or key not in node:
            return default
        node = node[key]
    if isinstance(node, Mapping) and "value" in node:
        return node["value"]
    return node


def build_parameter_center_model(catalog: Mapping[str, object]) -> dict[str, object]:
    formulas = catalog.get("formulas", ())
    formula_count = len(formulas) if isinstance(formulas, list) else 0
    items = (
        {
            "domain_zh": "货币",
            "parameter_key": "currency.base_currency",
            "name_zh": "主货币",
            "current_value": _param_value(catalog, "parameters", "currency", "base_currency"),
            "purpose_zh": "首页、投资、消费、现金流和报告使用 CNY 作为主口径。",
            "impact_surfaces": ("首页总览", "投资管理", "消费管理", "报告与洞察"),
            "user_editable": False,
        },
        {
            "domain_zh": "汇率",
            "parameter_key": "fx.frontend_badge_format",
            "name_zh": "汇率徽标格式",
            "current_value": _param_value(catalog, "parameters", "fx", "frontend_badge_format"),
            "purpose_zh": "所有页面顶部显示本地 06:00 有效汇率快照。",
            "impact_surfaces": ("顶部汇率", "账本折算", "报告"),
            "user_editable": False,
        },
        {
            "domain_zh": "分类",
            "parameter_key": "consumption_categories.default_taxonomy",
            "name_zh": "消费分类体系",
            "current_value": "L1 <= 12 / L2 <= 50",
            "purpose_zh": "限制消费分类数量，防止分类过散且保留未来合并字段。",
            "impact_surfaces": ("消费管理", "账本流水", "报告与洞察"),
            "user_editable": True,
        },
        {
            "domain_zh": "标签",
            "parameter_key": "tags.default_tag_library",
            "name_zh": "默认标签库",
            "current_value": "通用、消费、投资、数据质量、现金流、复盘",
            "purpose_zh": "支持跨分类的多维筛选、自定义视图和复盘报告。",
            "impact_surfaces": ("账本流水", "标签视图", "报告与洞察"),
            "user_editable": True,
        },
        {
            "domain_zh": "阈值",
            "parameter_key": "consumption_model.large_spend_cny_threshold",
            "name_zh": "大额消费阈值",
            "current_value": "CNY 2000 / AUD 500",
            "purpose_zh": "识别大额消费和需要复盘的异常支出。",
            "impact_surfaces": ("消费管理", "标签系统", "建议与复盘"),
            "user_editable": True,
        },
        {
            "domain_zh": "公式",
            "parameter_key": "formulas",
            "name_zh": "公式目录",
            "current_value": f"{formula_count} 个公式",
            "purpose_zh": "展示每个公式的中文名称、用途、输入、输出、逻辑和示例。",
            "impact_surfaces": ("参数中心", "Metric Drilldown Debugger", "报告与洞察"),
            "user_editable": False,
        },
        {
            "domain_zh": "置信度",
            "parameter_key": "confidence.review_threshold",
            "name_zh": "统一复核阈值",
            "current_value": _param_value(catalog, "parameters", "confidence", "review_threshold"),
            "purpose_zh": "低于阈值的记录进入复核队列，不按 source 名称分层。",
            "impact_surfaces": ("导入", "账本复核", "数据质量报告"),
            "user_editable": True,
        },
        {
            "domain_zh": "现金流窗口",
            "parameter_key": "cashflow.windows_days",
            "name_zh": "现金流预测窗口",
            "current_value": "7/21/30/60/90/180/360",
            "purpose_zh": "同时覆盖短期、中期和长期现金压力观察。",
            "impact_surfaces": ("首页总览", "现金流可视化", "报告与洞察"),
            "user_editable": True,
        },
    )
    return {
        "schema": "PFIV022Stage9ParameterCenterV1",
        "required_domains": STAGE9_PARAMETER_CENTER_DOMAINS,
        "items": items,
    }


def calculate_parameter_impact_preview(
    *,
    parameter_key: str,
    old_value: object,
    new_value: object,
    impact_counts: Mapping[str, int],
) -> dict[str, object]:
    return {
        "schema": "PFIV022Stage9ParameterImpactPreviewV1",
        "parameter_key": parameter_key,
        "old_value": old_value,
        "new_value": new_value,
        "affected_records": int(impact_counts.get("review_records", 0)),
        "affected_tags": int(impact_counts.get("tags", 0)),
        "affected_advice_items": int(impact_counts.get("advice_items", 0)),
        "affected_charts": int(impact_counts.get("charts", 0)),
        "network_allowed": False,
        "explanation_zh": "修改阈值前显示可能影响的记录数、标签数、建议数、图表数；该预览只使用真实 MetaDatabase、本地参数和本地 snapshot。",
    }


def build_interconnection_map_mermaid() -> str:
    return "\n".join(
        (
            "graph TD",
            "  source[数据源 source] --> raw[原始记录 raw] --> normalized[标准化交易 normalized] --> group[Interconnection group] --> event[经济事件 event] --> ledger[账本事件 ledger] --> metrics[核心指标 metrics] --> UI[首页/消费/投资/现金流 UI]",
            "  source --> upload[上传中心]",
            "  raw --> parser[parser / 标准化规则]",
            "  group --> dedupe[去重与抵消]",
            "  metrics --> drilldown[Metric Drilldown Debugger]",
        )
    )


def _default_data_status(context: Mapping[str, object] | None = None) -> dict[str, object]:
    active_context = context or load_stage9_real_visualization_context()
    dependency_hashes = active_context.get("dependency_hashes", {})
    return {
        "数据来源覆盖率": f"当前真实支付宝流水 {active_context['normalized_transaction_count']} 条，raw 文件 {active_context['raw_file_count']} 个；其它来源保持合同层或真实空态。",
        "最近更新时间": active_context["last_updated"],
        "参数版本": "v0.2.2",
        "公式版本": "Stage 7 formula/scoring",
        "汇率快照 ID": active_context["fx_snapshot_id"],
        "ledger_hash": dependency_hashes.get("ledger_events_hash", "ledger_hash_missing"),
        "interconnection_hash": dependency_hashes.get("interconnection_hash", "interconnection_hash_missing"),
        "是否存在未匹配记录": active_context["interconnection_state_zh"],
        "是否存在低置信记录": f"待复核记录 {active_context['review_record_count']} 条，来自真实标准化流水 review_state。",
        "是否存在缓存": "有，本地文件 hash snapshot。",
        "是否需要重算": "由 Stage 8 Runtime Diff 判断。",
        "UI 指标是否与报告一致": "必须一致；不一致时生成本地 Codex Review Ticket。",
    }


def build_stage9_visualization_payload(
    catalog: Mapping[str, object],
    context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    active_context = context or load_stage9_real_visualization_context()
    modules = tuple({"title": title, "data_status": _default_data_status(active_context)} for title in STAGE9_REQUIRED_MODULES)
    return {
        "schema": "PFIV022Stage9VisualizationPayloadV1",
        "module_titles": STAGE9_REQUIRED_MODULES,
        "modules": modules,
        "parameter_center": build_parameter_center_model(catalog),
        "interconnection_mermaid": build_interconnection_map_mermaid(),
        "cashflow": build_cashflow_visualization_model(active_context),
        "metric_drilldown": build_metric_drilldown_debugger_model(active_context),
        "real_visualization_context": active_context,
        "external_network_allowed": False,
    }


def build_cashflow_visualization_model(context: Mapping[str, object] | None = None) -> dict[str, object]:
    active_context = context or load_stage9_real_visualization_context()
    cashflow_inputs = active_context["cashflow_projection_inputs"]
    return {
        "schema": "PFIV022Stage9CashflowVisualizationV1",
        "windows_days": STAGE9_CASHFLOW_WINDOWS_DAYS,
        "visualizations": STAGE9_CASHFLOW_VISUALIZATIONS,
        "ladder_points": tuple(
            {
                "window_days": item["horizon_days"],
                "label_zh": f"{item['horizon_days']} 天现金流窗口",
                "future_cash_balance_cny": item["future_cash_balance_cny"],
                "reserve_floor_cny": item["reserve_floor_cny"],
                "data_status_zh": active_context["cashflow_data_status_zh"],
            }
            for item in active_context["cashflow_projections"]
        ),
        "waterfall_components": ("当前现金", "收入", "退款", "固定支出", "弹性支出", "信用卡", "投资入金", "投资回流"),
        "waterfall_values_cny": {
            "当前现金": _money(cashflow_inputs.get("current_life_cash_cny")),
            "收入": _money(cashflow_inputs.get("expected_income_cny")),
            "退款": _money(cashflow_inputs.get("expected_refund_cny")),
            "固定支出": _money(cashflow_inputs.get("fixed_expense_cny")),
            "弹性支出": _money(cashflow_inputs.get("flexible_expense_cny")),
            "信用卡": _money(cashflow_inputs.get("debt_repayment_cny")),
            "投资入金": _money(cashflow_inputs.get("planned_investment_deposit_cny")),
            "投资回流": _money(cashflow_inputs.get("planned_investment_return_cny")),
        },
        "reserve_safety_band": ("绿色", "黄色", "红色"),
        "investment_squeeze_explanation_zh": "投资入金挤压图显示投资入金对生活现金和储备金的影响。",
        "data_status_zh": active_context["cashflow_data_status_zh"],
    }


def build_metric_drilldown_debugger_model(context: Mapping[str, object] | None = None) -> dict[str, object]:
    active_context = context or load_stage9_real_visualization_context()
    quality = {
        "confidence": f"待复核记录 {active_context['review_record_count']} 条来自真实标准化流水。",
        "match_rate": active_context["interconnection_state_zh"],
        "last_updated": active_context["last_updated"],
        "compute_time_ms": None,
        "compute_time_status_zh": STAGE9_UNMEASURED_COMPUTE_STATUS_ZH,
        "cache_status": "local_dependency_hash_snapshot",
    }
    return {
        "schema": "PFIV022Stage9MetricDrilldownDebuggerV1",
        "metrics": {
            "本月消费": {
                "included": ("普通生活消费", "投资入金", "基金申购", "黄金申购", "投资买入", "金融费用"),
                "excluded": ("内部转账", "信用卡还款", "投资卖出回流"),
                "adjusted": ("退款抵消原消费",),
                "gross_consumption_cny": active_context["gross_consumption_cny"],
                "living_consumption_cny": active_context["living_consumption_cny"],
                "quality": quality,
            },
            "投资资产": {
                "included": ("投资现金", "持仓市值", "基金资产", "贵金属资产"),
                "excluded": ("生活现金", "普通消费", "信用卡还款"),
                "adjusted": ("汇率快照折算", "费用和税费"),
                "data_status_zh": active_context["investment_data_status_zh"],
                "quality": quality,
            },
            "现金流窗口": {
                "included": ("预计收入", "预计退款", "固定支出", "弹性支出", "信用卡", "投资入金", "投资回流"),
                "excluded": ("内部账户调拨重复项",),
                "adjusted": ("储备金安全线", "投资入金挤压生活现金"),
                "data_status_zh": active_context["cashflow_data_status_zh"],
                "quality": quality,
            },
        },
    }


def render_stage9_html(payload: Mapping[str, object]) -> str:
    module_sections = []
    for module_item in payload["modules"]:
        status_items = "".join(
            f"<li><strong>{escape(str(key))}</strong><span>{escape(str(value))}</span></li>"
            for key, value in module_item["data_status"].items()
        )
        module_sections.append(
            f'<section class="module"><h2>{escape(str(module_item["title"]))}</h2><ul class="status-list">{status_items}</ul></section>'
        )
    return "\n".join(module_sections)


def build_stage9_contract_payload(catalog: Mapping[str, object]) -> dict[str, object]:
    payload = build_stage9_visualization_payload(catalog)
    return {
        "schema": "PFIV022VisualizationUIUXStage9PayloadV1",
        "parameter_center_domains": STAGE9_PARAMETER_CENTER_DOMAINS,
        "module_titles": STAGE9_REQUIRED_MODULES,
        "data_status_fields": STAGE9_DATA_STATUS_FIELDS,
        "cashflow_windows_days": STAGE9_CASHFLOW_WINDOWS_DAYS,
        "cashflow_visualizations": STAGE9_CASHFLOW_VISUALIZATIONS,
        "interconnection_mermaid": payload["interconnection_mermaid"],
        "external_network_allowed": False,
        "single_html_path": "PFI/web/interconnection-map.html",
    }
