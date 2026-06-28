from __future__ import annotations

from html import escape
from typing import Mapping


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
    sample_counts: Mapping[str, int],
) -> dict[str, object]:
    return {
        "schema": "PFIV022Stage9ParameterImpactPreviewV1",
        "parameter_key": parameter_key,
        "old_value": old_value,
        "new_value": new_value,
        "affected_records": int(sample_counts.get("review_records", 0)),
        "affected_tags": int(sample_counts.get("tags", 0)),
        "affected_advice_items": int(sample_counts.get("advice_items", 0)),
        "affected_charts": int(sample_counts.get("charts", 0)),
        "network_allowed": False,
        "explanation_zh": "修改阈值前显示可能影响的记录数、标签数、建议数、图表数；该预览只使用本地 snapshot。",
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


def _default_data_status() -> dict[str, object]:
    return {
        "数据来源覆盖率": "已覆盖支付宝、银行、券商、基金、贵金属、微信和手工快照的合同层。",
        "最近更新时间": "2026-06-28 06:00 Australia/Sydney",
        "参数版本": "v0.2.2",
        "公式版本": "Stage 7 formula/scoring",
        "汇率快照 ID": "fx_AUD_CNY_20260628",
        "ledger_hash": "ledger_events_hash",
        "interconnection_hash": "interconnection_hash",
        "是否存在未匹配记录": "有，进入待复核队列。",
        "是否存在低置信记录": "有，低于 70 分进入复核。",
        "是否存在缓存": "有，本地 snapshot 缓存。",
        "是否需要重算": "由 Stage 8 Runtime Diff 判断。",
        "UI 指标是否与报告一致": "必须一致；不一致时生成本地 Codex Review Ticket。",
    }


def build_stage9_visualization_payload(catalog: Mapping[str, object]) -> dict[str, object]:
    modules = tuple({"title": title, "data_status": _default_data_status()} for title in STAGE9_REQUIRED_MODULES)
    return {
        "schema": "PFIV022Stage9VisualizationPayloadV1",
        "module_titles": STAGE9_REQUIRED_MODULES,
        "modules": modules,
        "parameter_center": build_parameter_center_model(catalog),
        "interconnection_mermaid": build_interconnection_map_mermaid(),
        "cashflow": build_cashflow_visualization_model(),
        "metric_drilldown": build_metric_drilldown_debugger_model(),
        "external_network_allowed": False,
    }


def build_cashflow_visualization_model() -> dict[str, object]:
    return {
        "schema": "PFIV022Stage9CashflowVisualizationV1",
        "windows_days": STAGE9_CASHFLOW_WINDOWS_DAYS,
        "visualizations": STAGE9_CASHFLOW_VISUALIZATIONS,
        "ladder_points": tuple({"window_days": day, "label_zh": f"{day} 天预测余额"} for day in STAGE9_CASHFLOW_WINDOWS_DAYS),
        "waterfall_components": ("当前现金", "收入", "退款", "固定支出", "弹性支出", "信用卡", "投资入金", "投资回流"),
        "reserve_safety_band": ("绿色", "黄色", "红色"),
        "investment_squeeze_explanation_zh": "投资入金挤压图显示投资入金对生活现金和储备金的影响。",
    }


def build_metric_drilldown_debugger_model() -> dict[str, object]:
    quality = {
        "confidence": ">= 70 分或进入复核",
        "match_rate": "Interconnection 匹配率",
        "last_updated": "2026-06-28 06:00",
        "compute_time_ms": 42,
        "cache_status": "cached_snapshot",
    }
    return {
        "schema": "PFIV022Stage9MetricDrilldownDebuggerV1",
        "metrics": {
            "本月消费": {
                "included": ("普通生活消费", "投资入金", "基金申购", "黄金申购", "投资买入", "金融费用"),
                "excluded": ("内部转账", "信用卡还款", "投资卖出回流"),
                "adjusted": ("退款抵消原消费",),
                "quality": quality,
            },
            "投资资产": {
                "included": ("投资现金", "持仓市值", "基金资产", "贵金属资产"),
                "excluded": ("生活现金", "普通消费", "信用卡还款"),
                "adjusted": ("汇率快照折算", "费用和税费"),
                "quality": quality,
            },
            "现金流窗口": {
                "included": ("预计收入", "预计退款", "固定支出", "弹性支出", "信用卡", "投资入金", "投资回流"),
                "excluded": ("内部账户调拨重复项",),
                "adjusted": ("储备金安全线", "投资入金挤压生活现金"),
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
