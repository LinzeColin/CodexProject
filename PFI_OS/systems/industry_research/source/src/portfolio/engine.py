from __future__ import annotations

from collections import defaultdict


def summarize_exposure(positions: list[dict[str, object]]) -> dict[str, object]:
    industry: dict[str, float] = defaultdict(float)
    total = 0.0
    for position in positions:
        weight = float(position.get("risk_adjusted_weight", position.get("weight", 0)))
        total += weight
        industry[str(position["industry"])] += weight
    return {
        "total_weight": round(total, 6),
        "industry_exposure": {key: round(value, 6) for key, value in sorted(industry.items())},
        "cash_weight": round(max(0.0, 1 - total), 6),
    }
