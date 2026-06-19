from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class BankrollPlan:
    budget_min_aud: float
    budget_mid_aud: float
    budget_max_aud: float
    open_stake_aud: float
    uncommitted_min_aud: float
    uncommitted_mid_aud: float
    uncommitted_max_aud: float
    pending_return_if_all_win_aud: float
    pending_profit_if_all_win_aud: float
    current_window_target_aud: float
    current_window_target_unit: float
    total_pending_plus_new_aud: float
    total_pending_plus_new_pct_mid: float
    lose_all_balance_mid_aud: float
    stake_return_balance_mid_aud: float
    win_all_balance_mid_aud: float
    win_all_roi_on_open_stake: float


def build_bankroll_plan(
    position_summary: Dict,
    base_candidate_exposure_aud: float,
    unit_aud: float = 40.0,
    budget_min_aud: float = 3000.0,
    budget_mid_aud: float = 4000.0,
    budget_max_aud: float = 5000.0,
) -> BankrollPlan:
    """Build a time-aware bankroll plan for pending bets plus new candidates.

    The plan treats pending bets as capital that will be released, increased, or
    lost as results settle. It therefore sets the current execution target from
    uncommitted budget instead of mechanically minimizing today's stake.
    """

    open_stake = first_number(position_summary, ("open_stake_aud", "total_stake_aud"), 0.0)
    pending_return = first_number(position_summary, ("estimated_return_if_all_win_aud",), open_stake)
    pending_profit = first_number(position_summary, ("potential_profit_if_all_win_aud",), pending_return - open_stake)
    uncommitted_min = max(0.0, budget_min_aud - open_stake)
    uncommitted_mid = max(0.0, budget_mid_aud - open_stake)
    uncommitted_max = max(0.0, budget_max_aud - open_stake)

    # Current-window target: enough to act on edge now, capped by budget that is
    # not already tied up. If the mid-budget is fully committed, fail closed.
    if uncommitted_mid <= 0 or base_candidate_exposure_aud <= 0:
        target = 0.0
    else:
        doubled_edge_budget = max(base_candidate_exposure_aud, base_candidate_exposure_aud * 2)
        uncommitted_cap = uncommitted_mid * 0.06
        portfolio_cap = budget_mid_aud * 0.035
        target = min(doubled_edge_budget, uncommitted_cap, portfolio_cap, uncommitted_mid)
        target = round_to_nearest(target, 10)

    return BankrollPlan(
        budget_min_aud=budget_min_aud,
        budget_mid_aud=budget_mid_aud,
        budget_max_aud=budget_max_aud,
        open_stake_aud=open_stake,
        uncommitted_min_aud=uncommitted_min,
        uncommitted_mid_aud=uncommitted_mid,
        uncommitted_max_aud=uncommitted_max,
        pending_return_if_all_win_aud=pending_return,
        pending_profit_if_all_win_aud=pending_profit,
        current_window_target_aud=target,
        current_window_target_unit=target / unit_aud if unit_aud else 0,
        total_pending_plus_new_aud=open_stake + target,
        total_pending_plus_new_pct_mid=(open_stake + target) / budget_mid_aud if budget_mid_aud else 0,
        lose_all_balance_mid_aud=uncommitted_mid,
        stake_return_balance_mid_aud=uncommitted_mid + open_stake,
        win_all_balance_mid_aud=uncommitted_mid + pending_return,
        win_all_roi_on_open_stake=pending_profit / open_stake if open_stake else 0,
    )


def allocate_time_adjusted_stakes(candidates: Iterable[Dict], target_aud: float, unit_aud: float = 40.0) -> List[Dict]:
    candidates = list(candidates)
    base_total = sum(float(item.get("stake_aud", 0)) for item in candidates)
    if not candidates or target_aud <= 0 or base_total <= 0:
        return [
            {
                **item,
                "base_stake_aud": float(item.get("stake_aud", 0)),
                "time_adjusted_stake_aud": 0.0,
                "time_adjusted_stake_unit": 0.0,
            }
            for item in candidates
        ]

    weighted = []
    for item in candidates:
        base = float(item.get("stake_aud", 0))
        expected_value = max(0.0, float(item.get("expected_value", 0)))
        weight = base * (1 + min(expected_value, 0.30) * 2)
        weighted.append(weight)

    total_weight = sum(weighted)
    min_executable_stake = 10.0
    active_indices = list(range(len(candidates)))
    if target_aud < min_executable_stake * len(candidates):
        active_count = int(target_aud // min_executable_stake)
        if active_count <= 0:
            active_indices = []
        else:
            active_indices = sorted(range(len(weighted)), key=lambda idx: weighted[idx], reverse=True)[:active_count]
    active_weight = sum(weighted[idx] for idx in active_indices)
    rounded = [0.0 for _ in candidates]
    if active_indices and active_weight > 0:
        raw_amounts = {idx: target_aud * weighted[idx] / active_weight for idx in active_indices}
        active_rounded = [max(min_executable_stake, round_to_nearest(raw_amounts[idx], 5)) for idx in active_indices]
        active_rounded = rebalance_rounded(active_rounded, target_aud, [weighted[idx] for idx in active_indices])
        active_rounded = cap_to_target(active_rounded, target_aud)
        for idx, amount in zip(active_indices, active_rounded):
            rounded[idx] = amount

    return [
        {
            **item,
            "base_stake_aud": float(item.get("stake_aud", 0)),
            "time_adjusted_stake_aud": amount,
            "time_adjusted_stake_unit": amount / unit_aud if unit_aud else 0,
        }
        for item, amount in zip(candidates, rounded)
    ]


def round_to_nearest(value: float, step: int) -> float:
    return float(round(value / step) * step)


def first_number(values: Dict, keys: Sequence[str], default: float) -> float:
    for key in keys:
        if key in values and values[key] is not None:
            return float(values[key])
    return float(default)


def cap_to_target(amounts: List[float], target: float) -> List[float]:
    capped = amounts[:]
    diff = round(sum(capped) - target, 2)
    idx = len(capped) - 1
    while diff > 0 and idx >= 0:
        reducible = max(0.0, capped[idx] - 10.0)
        reduction = min(reducible, diff)
        capped[idx] = round(capped[idx] - reduction, 2)
        diff = round(sum(capped) - target, 2)
        idx -= 1
    return capped


def rebalance_rounded(amounts: List[float], target: float, weights: List[float]) -> List[float]:
    adjusted = amounts[:]
    diff = round(target - sum(adjusted), 2)
    if abs(diff) < 0.01:
        return adjusted
    order = sorted(range(len(weights)), key=lambda idx: weights[idx], reverse=(diff > 0))
    step = 5.0 if diff > 0 else -5.0
    while abs(diff) >= 4.99 and order:
        changed = False
        for idx in order:
            if diff < 0 and adjusted[idx] <= 10:
                continue
            adjusted[idx] += step
            diff = round(target - sum(adjusted), 2)
            changed = True
            if abs(diff) < 4.99:
                break
        if not changed:
            break
    return adjusted
