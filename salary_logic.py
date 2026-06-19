# -*- coding: utf-8 -*-
"""
业务逻辑：销售部门季度绩效工资计算
由原始命令行脚本抽离而来，方便接入 Web / 小程序 / App 前端。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Mapping


BASE_MONTHLY = 6000
PERF_QUARTER_POOL = 36000

projects: Dict[str, Dict[str, float]] = {
    "新疆":  {"业绩":0.25,"毛利率":0.325,"结算率":0.025,"开票率":0.05,"回款率":0.2,"审计偏差":0.05,"客情成本":0.1},
    "山东":  {"业绩":0.4,"毛利率":0.3,"结算率":0.025,"开票率":0.025,"回款率":0.175,"审计偏差":0.025,"客情成本":0.05},
    "青海":  {"业绩":0.45,"毛利率":0.25,"结算率":0.025,"开票率":0.025,"回款率":0.15,"审计偏差":0.025,"客情成本":0.075},
    "湖北":  {"业绩":0.3,"毛利率":0.35,"结算率":0.10,"开票率":0.025,"回款率":0.075,"审计偏差":0.05,"客情成本":0.1},
    "华中区域": {"业绩":0.4,"毛利率":0.175,"结算率":0.025,"开票率":0.075,"回款率":0.175,"审计偏差":0.025,"客情成本":0.125}
}

# ---------------- 权重选择/校验 ----------------
ALIASES: Dict[str, str] = {
    # 兼容不同叫法
    "华中地区": "华中区域",
    "华中区域": "华中区域",
}

def resolve_weights(
    weights: Optional[Mapping[str, float]] = None,
    province: Optional[str] = None,
) -> Dict[str, float]:
    """返回用于计算的权重字典。

    - 优先使用显式传入的 weights
    - 否则根据 province 在 projects 中自动匹配（含 ALIASES 兼容）
    """
    if weights is not None:
        return {str(k): float(v) for k, v in dict(weights).items()}
    if province is not None:
        key = ALIASES.get(province, province)
        if key in projects:
            return {str(k): float(v) for k, v in projects[key].items()}
    raise ValueError(
        "未找到权重：请传入 weights，或传入 province（可选：{}）".format(
            "、".join(projects.keys())
        )
    )


def score_performance(rate: float) -> float:
    if rate < 0.6:
        return min(0, 0 - (0.6 - rate) * 300)
    elif 0.6 <= rate <= 0.8:
        return 20 + (rate - 0.6) * 200
    elif 0.8 < rate <= 1.5:
        return 60 + (rate - 0.8) * 200
    else:  # rate > 1.5
        return max(200, 200 + (rate - 1.5) * 400)


def score_margin(rate: float) -> float:
    if rate < 0.1:
        return min(0, 0 - (0.1 - rate) * 1000)
    elif 0.1 <= rate <= 0.25:
        return (rate - 0.1) * 200
    elif 0.25 < rate <= 0.5:
        return 30 + (rate - 0.25) * 200
    else:
        return max(80, 80 + (rate - 0.5) * 500)


def score_settlement(days: int) -> float:
    if days > 60:
        return -150
    if 20 <= days <= 60:
        return min(100, 100 - (days - 20) * 5)
    if 1 < days < 20:
        return min(200, 200 - (days) * 5)
    elif days == 1:
        return 200


def score_invoice(days: int) -> float:
    if 60 < days:
        return -200
    if 20 < days <= 60:
        return min(0, 0 - (days - 20) * 5)
    if 5 < days <= 20:
        return min(125, 125 - (days - 5) * 8)
    if 1 < days <= 5:
        return min(150, 150 - (days) * 5)
    if days == 1:
        return 150


def score_payback(days: int) -> float:
    if days > 60:
        return min(-10, -10 - (days - 60) * 2)
    if 20 < days <= 60:
        return min(150, 150 - (days - 20) * 4)
    if 1 < days <= 20:
        return min(200, 200 - (days) * 2.5)
    if days == 1:
        return 200


def score_audit_bias(rate: float) -> float:
    if rate <= 0.02:
        return min(120, 120 - (rate * 3000))
    if 0.02 <= rate <= 0.08:
        return min(60, 60 - (rate - 0.02) * 8000)
    if rate > 0.08:
        return -420

def score_customer_cost(rate: float) -> float:
    if rate > 0.03:
        return min(45, 45 - (rate - 0.03) * 4000)
    if 0 <= rate <= 0.03:
        return min(120, 120 - (rate) * 2500)

@dataclass
class CalcResult:
    weights: Dict[str, float]
    performance_rate: float
    breakdown: List[Dict[str, Any]]
    total_score: float
    perf_money: float
    total_salary: float
    after_tax_salary: float


def calculate(
    year_target: float,
    quarter_actual: float,
    margin: float,
    settlement_days: int,
    invoice_days: int,
    payback_days: int,
    audit_bias: float,
    customer_rate: float,
    weights: Optional[Mapping[str, float]] = None,
    province: Optional[str] = None,
    tax_keep_rate: float = 0.97,
) -> 'CalcResult':
    if year_target <= 0:
        raise ValueError("年度目标产值必须 > 0")
    if quarter_actual <= 0:
        raise ValueError("实际季度业绩必须 > 0")

    weights = resolve_weights(weights=weights, province=province)

    performance_rate = quarter_actual / (year_target / 4)

    scores = {
        "业绩": score_performance(performance_rate),
        "毛利率": score_margin(margin),
        "结算率": score_settlement(settlement_days),
        "开票率": score_invoice(invoice_days),
        "回款率": score_payback(payback_days),
        "审计偏差": score_audit_bias(audit_bias),
        "客情成本": score_customer_cost(customer_rate),
    }

    breakdown: List[Dict[str, Any]] = []
    weighted_total = 0.0
    for k, s in scores.items():
        w = float(weights.get(k, 0))
        ws = s * w
        weighted_total += ws
        breakdown.append({
            "项目": k,
            "原始得分": round(s, 2),
            "权重": round(w, 4),
            "加权得分": round(ws, 2),
            "累计得分": round(weighted_total, 2),
        })

    perf_money = PERF_QUARTER_POOL * (weighted_total / 100.0)
    total_salary = BASE_MONTHLY * 3 + perf_money
    after_tax_salary = total_salary * tax_keep_rate

    return CalcResult(
        weights=weights,
        performance_rate=performance_rate,
        breakdown=breakdown,
        total_score=weighted_total,
        perf_money=perf_money,
        total_salary=total_salary,
        after_tax_salary=after_tax_salary,
    )
