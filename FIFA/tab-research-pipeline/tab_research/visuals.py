from __future__ import annotations

from typing import Dict, List


COLORS = {
    "blue": "#1F4E79",
    "green": "#247A5A",
    "amber": "#A56710",
    "red": "#C62828",
    "neutral": "#91A0B3",
}


def build_visual_summary(
    board_statuses: List[Dict],
    compare_summary: Dict,
    recommendation_counts: List[Dict],
    match_recommendations: List[Dict],
    model_rows: List[Dict],
    model_references: List[Dict] | None = None,
) -> List[Dict]:
    references = model_references or []
    return [
        board_readiness_chart(board_statuses),
        compare_chart(compare_summary),
        recommendation_distribution_chart(recommendation_counts),
        stake_allocation_chart(recommendation_counts),
        match_value_chart(match_recommendations),
        odds_probability_edge_chart(match_recommendations),
        model_divergence_chart(model_rows),
        model_consensus_chart(model_rows),
        model_source_coverage_chart(references),
        model_capability_coverage_chart(references),
    ]


def chart_by_id(charts: List[Dict], chart_id: str) -> Dict:
    return next((chart for chart in charts if chart.get("id") == chart_id), empty_chart(chart_id))


def empty_chart(chart_id: str) -> Dict:
    return {
        "id": chart_id,
        "title": chart_id.replace("_", " ").title(),
        "kind": "bar",
        "items": [],
        "note": "暂无数据。",
    }


def board_readiness_chart(statuses: List[Dict]) -> Dict:
    items = []
    for board in statuses:
        score = readiness_score(board)
        items.append(
            {
                "label": short_board_name(board.get("name")),
                "value": score,
                "bar_fraction": score,
                "display": f"{int(score * 100)}%",
                "color": COLORS["green"] if board.get("ready") else COLORS["amber"],
            }
        )
    return {
        "id": "board_readiness",
        "title": "板块自动化就绪度",
        "kind": "bar",
        "unit": "%",
        "items": items,
        "note": "Raw新鲜度、Raw有效性、gate通过、报告存在四项等权计分。",
    }


def compare_chart(summary: Dict) -> Dict:
    values = [
        ("新增", int(summary.get("added_count") or 0), COLORS["green"]),
        ("移除", int(summary.get("removed_count") or 0), COLORS["red"]),
        ("变化", int(summary.get("changed_count") or 0), COLORS["amber"]),
        ("保留", int(summary.get("retained_count") or 0), COLORS["blue"]),
    ]
    max_value = max([value for _label, value, _color in values] + [1])
    return {
        "id": "report_compare",
        "title": "新旧报告对比",
        "kind": "bar",
        "unit": "count",
        "items": [
            {
                "label": label,
                "value": value,
                "bar_fraction": value / max_value if max_value else 0,
                "display": str(value),
                "color": color,
            }
            for label, value, color in values
        ],
        "note": f"暴露变化 AUD {float(summary.get('exposure_change_aud') or 0):,.0f}",
    }


def recommendation_distribution_chart(counts: List[Dict]) -> Dict:
    max_count = max([int(item.get("count") or 0) for item in counts] + [1])
    return {
        "id": "recommendation_distribution",
        "title": "盘口推荐分布",
        "kind": "bar",
        "unit": "count",
        "items": [
            {
                "label": short_board_name(item.get("name")),
                "value": int(item.get("count") or 0),
                "bar_fraction": int(item.get("count") or 0) / max_count if max_count else 0,
                "display": f"{int(item.get('count') or 0)}个",
                "color": COLORS["red"] if float(item.get("stake_aud") or 0) > 0 else COLORS["blue"],
            }
            for item in counts
        ],
        "note": "红色代表该板块存在新增执行金额，蓝色代表观察池。",
    }


def stake_allocation_chart(counts: List[Dict]) -> Dict:
    values = [float(item.get("stake_aud") or 0) for item in counts]
    max_value = max(values + [1.0])
    return {
        "id": "stake_allocation",
        "title": "跨板块新增金额分配",
        "kind": "bar",
        "unit": "AUD",
        "items": [
            {
                "label": short_board_name(item.get("name")),
                "value": float(item.get("stake_aud") or 0),
                "bar_fraction": float(item.get("stake_aud") or 0) / max_value if max_value else 0,
                "display": f"AUD {float(item.get('stake_aud') or 0):,.0f}",
                "color": COLORS["red"] if float(item.get("stake_aud") or 0) > 0 else COLORS["neutral"],
            }
            for item in counts
        ],
        "note": "金额分配只展示研究建议暴露；正式系统不自动下注。",
    }


def match_value_chart(items: List[Dict]) -> Dict:
    values = [max(0.0, float(item.get("expected_value") or 0)) for item in items]
    max_value = max(values + [0.01])
    chart_items = []
    for item in items:
        ev = max(0.0, float(item.get("expected_value") or 0))
        stake = float(item.get("stake_aud") or item.get("time_adjusted_stake_aud") or 0)
        label = f"{item.get('match', '')} / {item.get('selection', '')}"
        chart_items.append(
            {
                "label": truncate(label, 42),
                "value": ev,
                "bar_fraction": ev / max_value if max_value else 0,
                "display": pct(ev),
                "color": COLORS["red"] if stake > 0 else COLORS["amber"],
            }
        )
    return {
        "id": "match_value",
        "title": "比赛盘口价值排序",
        "kind": "bar",
        "unit": "expected_value",
        "items": chart_items,
        "note": "按正EV排序，红色代表进入执行候选。",
    }


def odds_probability_edge_chart(items: List[Dict]) -> Dict:
    chart_items = []
    for item in items:
        odds = float(item.get("odds") or 0)
        probability = float(item.get("model_probability") or item.get("probability") or 0)
        breakeven = (1 / odds) if odds > 0 else 0
        edge = probability - breakeven
        label = f"{item.get('match', '')} / {item.get('selection', '')}"
        chart_items.append((edge, item, label))
    chart_items.sort(key=lambda row: row[0], reverse=True)
    max_value = max([max(0.0, edge) for edge, _item, _label in chart_items] + [0.01])
    return {
        "id": "odds_probability_edge",
        "title": "概率-赔率边际",
        "kind": "bar",
        "unit": "probability_edge",
        "items": [
            {
                "label": truncate(label, 42),
                "value": edge,
                "bar_fraction": max(0.0, edge) / max_value if max_value else 0,
                "display": signed_pct(edge),
                "color": COLORS["green"] if edge > 0 else COLORS["neutral"],
            }
            for edge, _item, label in chart_items[:7]
        ],
        "note": "边际 = 模型概率 - 赔率盈亏平衡概率；正值才进入价值观察。",
    }


def model_divergence_chart(rows: List[Dict]) -> Dict:
    values = [float(row.get("disagreement", {}).get("max_abs_current_vs_elo_dc") or 0) for row in rows]
    max_value = max(values + [0.01])
    items = []
    for row in rows:
        disagreement = float(row.get("disagreement", {}).get("max_abs_current_vs_elo_dc") or 0)
        label = f"{row.get('match', '')} / {row.get('consensus', {}).get('selection', '')}"
        items.append(
            {
                "label": truncate(label, 42),
                "value": disagreement,
                "bar_fraction": disagreement / max_value if max_value else 0,
                "display": pct(disagreement),
                "color": COLORS["red"] if row.get("disagreement", {}).get("high_divergence") else COLORS["blue"],
            }
        )
    return {
        "id": "model_divergence",
        "title": "开源模型分歧",
        "kind": "bar",
        "unit": "probability_gap",
        "items": items,
        "note": "比较当前市场Poisson、Elo+Dixon-Coles、goalmodel proxy 的最大方向分歧。",
    }


def model_consensus_chart(rows: List[Dict]) -> Dict:
    values = [float(row.get("consensus", {}).get("mean_probability") or 0) for row in rows]
    max_value = max(values + [0.01])
    items = []
    for row in rows:
        probability = float(row.get("consensus", {}).get("mean_probability") or 0)
        confidence = str(row.get("consensus", {}).get("confidence") or "")
        label = f"{row.get('match', '')} / {row.get('consensus', {}).get('selection', '')}"
        items.append(
            {
                "label": truncate(label, 42),
                "value": probability,
                "bar_fraction": probability / max_value if max_value else 0,
                "display": f"{pct(probability)} {confidence}",
                "color": COLORS["green"] if confidence == "high" else (COLORS["amber"] if confidence == "medium" else COLORS["blue"]),
            }
        )
    return {
        "id": "model_consensus",
        "title": "模型共识强度",
        "kind": "bar",
        "unit": "probability",
        "items": items,
        "note": "展示当前市场Poisson、Elo+Dixon-Coles、goalmodel proxy 的共识方向概率。",
    }


def model_source_coverage_chart(references: List[Dict]) -> Dict:
    values = []
    for ref in references:
        coverage = ref.get("coverage", [])
        values.append((ref.get("display_name") or short_source_name(ref.get("name")), len(coverage), ref.get("adoption_status")))
    max_value = max([value for _label, value, _status in values] + [1])
    return {
        "id": "model_source_coverage",
        "title": "开源模型采用覆盖",
        "kind": "bar",
        "unit": "coverage_count",
        "items": [
            {
                "label": label,
                "value": value,
                "bar_fraction": value / max_value if max_value else 0,
                "display": f"{value}项",
                "color": COLORS["green"] if status == "implemented_proxy" else COLORS["amber"],
            }
            for label, value, status in values
        ],
        "note": "绿色代表已进入本地概率交叉验证；琥珀色代表设计参考或下一阶段接口。",
    }


def model_capability_coverage_chart(references: List[Dict]) -> Dict:
    coverage_counts: Dict[str, int] = {}
    implemented_counts: Dict[str, int] = {}
    for ref in references:
        implemented = ref.get("adoption_status") == "implemented_proxy"
        for item in ref.get("coverage", []):
            coverage_counts[item] = coverage_counts.get(item, 0) + 1
            if implemented:
                implemented_counts[item] = implemented_counts.get(item, 0) + 1
    values = sorted(coverage_counts.items(), key=lambda row: (row[1], implemented_counts.get(row[0], 0), row[0]), reverse=True)
    max_value = max([value for _label, value in values] + [1])
    return {
        "id": "model_capability_coverage",
        "title": "模型能力覆盖矩阵",
        "kind": "bar",
        "unit": "source_count",
        "items": [
            {
                "label": label,
                "value": value,
                "bar_fraction": value / max_value if max_value else 0,
                "display": f"{implemented_counts.get(label, 0)}/{value}已接入",
                "color": COLORS["green"] if implemented_counts.get(label, 0) else COLORS["amber"],
            }
            for label, value in values[:7]
        ],
        "note": "按开源参考覆盖能力聚合；已接入表示进入本地概率交叉验证或报告证据层。",
    }


def readiness_score(board: Dict) -> float:
    checks = [board.get("raw_fresh"), board.get("raw_valid"), board.get("gate_ready"), board.get("report_exists")]
    return sum(1 for item in checks if item) / len(checks) if checks else 0.0


def short_board_name(value) -> str:
    return str(value or "").replace("2026 World Cup ", "")


def short_source_name(value) -> str:
    text = str(value or "")
    return text.split("/", 1)[-1] if "/" in text else text


def truncate(value, length: int) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 1] + "…"


def pct(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def signed_pct(value: float) -> str:
    return f"{float(value) * 100:+.1f}%"
