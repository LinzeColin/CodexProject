from __future__ import annotations

from typing import Any


VERSION = "v0.2.3"
STAGE = "Stage 7"
PHASE_ID = "V023-S7-P7.1"
READ_MODEL_SOURCE = "PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json"


def build_stage7_formula_registry(core_metrics_read_model: dict[str, Any] | None = None) -> dict[str, Any]:
    read_model = core_metrics_read_model or {}
    metrics = {str(item.get("metric_id")): item for item in read_model.get("core_metrics", [])}
    source = read_model.get("source", {})
    return {
        "schema": "PFIV023Stage7FormulaRegistryV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "source_read_model": READ_MODEL_SOURCE,
        "read_model_hash": read_model.get("read_model_hash"),
        "as_of": read_model.get("as_of"),
        "formulas": [
            _formula(
                metrics,
                "net_worth_cny",
                "净资产",
                "净资产 = 现金余额 + 投资市值 + 其他可确认资产 - 可确认负债。",
                ("cash_balance_cny", "investment_market_value_cny"),
                [
                    _parameter("net_worth_currency", "CNY", "Stage 6 核心指标币种", False),
                    _parameter("asset_scope", "现金余额、投资市值、其他已确认资产", "Stage 7 报告合同", False),
                    _parameter("liability_scope", "可确认负债", "Stage 7 报告合同", False),
                ],
            ),
            _formula(
                metrics,
                "cash_balance_cny",
                "现金余额",
                "现金余额 = 已挂载真实账户余额 read model 的 CNY 汇总。",
                ("cash_balance_cny",),
                [
                    _parameter("cash_currency", "CNY", "Stage 6 核心指标币种", False),
                    _parameter("cash_account_scope", "真实账户余额 read model", "Stage 7 报告合同", False),
                ],
            ),
            _formula(
                metrics,
                "investment_market_value_cny",
                "投资市值",
                "投资市值 = 持仓数量 × 最新可确认价格 × 对应 CNY 汇率。",
                ("investment_market_value_cny",),
                [
                    _parameter("investment_currency", "CNY", "Stage 6 核心指标币种", False),
                    _parameter("pricing_policy", "最新可确认价格", "Stage 7 报告合同", False),
                    _parameter("fx_policy", "对应 CNY 汇率", "Stage 7 报告合同", False),
                ],
            ),
            _formula(
                metrics,
                "life_consumption_cny",
                "生活消费",
                "生活消费 = 真实 Alipay 交易中的生活消费流出减退款。",
                ("life_consumption_cny",),
                [
                    _parameter("life_event_type", "CASH", "Stage 6 read model event_type", False),
                    _parameter("refund_offset", "REFUND 抵消", "Stage 6 read model event_type", False),
                ],
            ),
            _formula(
                metrics,
                "total_consumption_outflow_cny",
                "消费总流出",
                "消费总流出 = 生活消费 + 基金申购 + 资产买入流出 - 退款。",
                ("total_consumption_outflow_cny",),
                [
                    _parameter("life_event_type", "CASH", "Stage 6 read model event_type", False),
                    _parameter("fund_event_type", "FUND", "Stage 6 read model event_type", False),
                    _parameter("asset_buy_event_type", "BUY_ASSET", "Stage 6 read model event_type", False),
                    _parameter("refund_offset", "REFUND 抵消", "Stage 6 read model event_type", False),
                ],
            ),
            _formula(
                metrics,
                "data_health",
                "数据健康",
                "数据健康 = 已通过导入清单校验的真实标准化交易记录数。",
                ("data_health",),
                [
                    _parameter("transaction_count_source", source.get("manifest_path"), "Stage 6 read model source", False),
                    _parameter("raw_file_count", source.get("raw_file_count"), "Stage 6 read model source", False),
                ],
            ),
        ],
    }


def _formula(
    metrics: dict[str, dict[str, Any]],
    metric_id: str,
    label: str,
    formula_zh: str,
    required_inputs: tuple[str, ...],
    parameters: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_inputs = [
        input_id
        for input_id in required_inputs
        if metrics.get(input_id, {}).get("status") not in {"ready", "confirmed_zero"}
    ]
    metric = metrics.get(metric_id, {})
    return {
        "formula_id": f"formula_{metric_id}",
        "metric_id": metric_id,
        "label": label,
        "formula_zh": formula_zh,
        "input_status": "ready" if not missing_inputs and metric.get("status") in {"ready", "confirmed_zero"} else "blocked",
        "required_inputs": list(required_inputs),
        "missing_inputs": missing_inputs,
        "parameters": parameters,
        "data_sources": _data_sources(metrics, required_inputs),
        "evidence_hash": metric.get("evidence_hash"),
        "status_policy_zh": "输入指标为 ready 或 confirmed_zero 且带 source/as_of/evidence_hash 时才允许报告显示完整结论。",
    }


def _parameter(parameter_id: str, value: Any, source: str, adjustable: bool) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "label_zh": _label(parameter_id),
        "value": value,
        "source": source,
        "adjustable": adjustable,
        "display_policy_zh": "报告必须展示当前参数值、来源和是否可调整。",
    }


def _data_sources(metrics: dict[str, dict[str, Any]], metric_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for metric_id in metric_ids:
        metric = metrics.get(metric_id, {})
        sources.append(
            {
                "metric_id": metric_id,
                "source": metric.get("source"),
                "as_of": metric.get("as_of"),
                "evidence_hash": metric.get("evidence_hash"),
                "status": metric.get("status", "not_loaded"),
                "message_zh": metric.get("message_zh", "未加载真实数据"),
            }
        )
    return sources


def _label(parameter_id: str) -> str:
    labels = {
        "net_worth_currency": "净资产币种",
        "asset_scope": "资产范围",
        "liability_scope": "负债范围",
        "cash_currency": "现金币种",
        "cash_account_scope": "现金账户范围",
        "investment_currency": "投资市值币种",
        "pricing_policy": "价格口径",
        "fx_policy": "汇率口径",
        "life_event_type": "生活消费事件类型",
        "refund_offset": "退款抵消",
        "fund_event_type": "基金申购事件类型",
        "asset_buy_event_type": "资产买入事件类型",
        "transaction_count_source": "交易记录来源",
        "raw_file_count": "原始文件数",
    }
    return labels.get(parameter_id, parameter_id)
