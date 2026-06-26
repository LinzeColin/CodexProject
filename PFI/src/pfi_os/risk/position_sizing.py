from __future__ import annotations


def fixed_fraction_weight(weight: float, max_weight: float = 1.0) -> float:
    return max(-max_weight, min(max_weight, weight))


def volatility_target_weight(realized_volatility: float, target_volatility: float = 0.15, max_weight: float = 1.0) -> float:
    if realized_volatility <= 0:
        return 0.0
    return fixed_fraction_weight(target_volatility / realized_volatility, max_weight=max_weight)
