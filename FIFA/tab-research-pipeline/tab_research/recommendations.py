from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, Tuple

from .bankroll import allocate_time_adjusted_stakes


def match_stake_key(match: str, market: str, selection: str) -> Tuple[str, str, str]:
    return (str(match or ""), str(market or ""), str(selection or ""))


def match_stake_index(match_stakes: Iterable[Dict] | None) -> Dict[Tuple[str, str, str], Dict]:
    index = {}
    for item in match_stakes or []:
        key = match_stake_key(item.get("match", ""), item.get("market", ""), item.get("selection", ""))
        if key != ("", "", ""):
            index[key] = item
    return index


def execution_stake_for_match(item: Dict, index: Dict[Tuple[str, str, str], Dict]) -> float | None:
    stake = index.get(match_stake_key(item.get("match", ""), item.get("market", ""), item.get("selection", "")))
    if not stake:
        return None
    return optional_float(stake.get("time_adjusted_stake_aud"))


def display_stake_aud(board_id: str, item: Dict, bankroll: Dict | None = None) -> float:
    if board_id == "world_cup_matches":
        execution = execution_stake_for_match(item, match_stake_index((bankroll or {}).get("match_stakes", [])))
        if execution is not None:
            return execution
    return float(item.get("time_adjusted_stake_aud") or item.get("stake_aud") or 0)


def apply_public_time_adjusted_match_stakes(board_payload: Dict, bankroll: Dict | None, unit_aud: float = 40.0) -> Dict:
    """Recreate model-only execution stakes from public bankroll totals.

    Public bankroll artifacts intentionally omit per-match `match_stakes` to
    avoid leaking private My Bets-derived detail. The dashboard and SQLite still
    need the same public model-only execution amounts as the PDF, so this
    function reallocates the public total across match recommendations using the
    same deterministic staking algorithm.
    """

    if not isinstance(board_payload, dict):
        return {}
    result = deepcopy(board_payload)
    recommendations = result.get("recommendations", [])
    if not recommendations:
        return result
    if (bankroll or {}).get("match_stakes"):
        return result
    target = optional_float((bankroll or {}).get("time_adjusted_new_exposure_aud"))
    if target is None or target <= 0:
        return result
    allocated = allocate_time_adjusted_stakes(recommendations, target, unit_aud=unit_aud)
    for item in allocated:
        execution = float(item.get("time_adjusted_stake_aud") or 0)
        item["execution_stake_aud"] = execution
        item["stake_aud"] = execution
        if execution > 0:
            item["decision"] = "buy"
    result["recommendations"] = allocated
    return result


def enrich_match_recommendations_with_model_comparison(board_payload: Dict, model_comparison: Dict) -> Dict:
    """Attach model-consensus evidence to match recommendations.

    The model-comparison artifact is generated independently from the betting
    recommendations. Joining it here makes every executable match candidate
    explain why the market model, goalmodel proxy, and Elo/DC layer agree or
    diverge without changing staking behavior.
    """

    if not isinstance(board_payload, dict):
        return {}
    result = deepcopy(board_payload)
    rows_by_match = {row.get("match"): row for row in (model_comparison or {}).get("rows", []) if row.get("match")}
    enriched: List[Dict] = []
    for item in result.get("recommendations", []):
        row = rows_by_match.get(item.get("match"))
        if not row:
            enriched.append(item)
            continue
        next_item = deepcopy(item)
        signal = model_signal_for_recommendation(next_item, row)
        if signal:
            next_item["model_signal"] = signal
            next_item["model_divergence_summary"] = signal["summary_zh"]
            next_item["rationale"] = append_model_summary(next_item.get("rationale", ""), signal["summary_zh"])
        enriched.append(next_item)
    result["recommendations"] = enriched
    return result


def model_signal_for_recommendation(item: Dict, row: Dict) -> Dict:
    probability_key = model_probability_key(row, item.get("market", ""), item.get("selection", ""))
    probabilities = {}
    if probability_key:
        probabilities = {
            "current_market_poisson": optional_float(row.get("current_market_poisson", {}).get(probability_key)),
            "goalmodel_market_dc_proxy": optional_float(row.get("goalmodel_market_dc_proxy", {}).get(probability_key)),
            "open_source_elo_dixon_coles": optional_float(row.get("open_source_elo_dixon_coles", {}).get(probability_key)),
        }
        probabilities = {key: value for key, value in probabilities.items() if value is not None}
    consensus = row.get("consensus", {})
    disagreement = row.get("disagreement", {})
    aligned = str(consensus.get("selection") or "") == str(item.get("selection") or "")
    max_gap = optional_float(disagreement.get("max_abs_current_vs_elo_dc")) or 0.0
    return {
        "match": row.get("match", ""),
        "probability_key": probability_key or "",
        "probabilities": probabilities,
        "consensus_selection": consensus.get("selection", ""),
        "consensus_probability": optional_float(consensus.get("mean_probability")),
        "consensus_confidence": consensus.get("confidence", ""),
        "max_abs_current_vs_elo_dc": max_gap,
        "high_divergence": bool(disagreement.get("high_divergence")),
        "selection_aligned_with_consensus": aligned,
        "summary_zh": model_signal_summary_zh(item, consensus, probabilities, max_gap, aligned),
    }


def model_probability_key(row: Dict, market: str, selection: str) -> str:
    market_text = str(market or "")
    selection_text = str(selection or "")
    if market_text == "Result":
        if selection_text == row.get("home"):
            return "home_win"
        if selection_text == "Draw":
            return "draw"
        if selection_text == row.get("away"):
            return "away_win"
    if market_text == "Total Goals Over/Under":
        if "Under 2.5" in selection_text:
            return "under_2_5"
        if "Over 2.5" in selection_text:
            return "over_2_5"
    if market_text == "Both Teams to Score":
        if "Only One or Neither" in selection_text:
            return "btts_no"
        if "Both Teams to Score" in selection_text:
            return "btts_yes"
    return ""


def model_signal_summary_zh(item: Dict, consensus: Dict, probabilities: Dict[str, float], max_gap: float, aligned: bool) -> str:
    parts = []
    if probabilities:
        parts.append(
            "三模型概率：市场Poisson {current}，goalmodel {goalmodel}，Elo-DC {elo}".format(
                current=format_pct(probabilities.get("current_market_poisson")),
                goalmodel=format_pct(probabilities.get("goalmodel_market_dc_proxy")),
                elo=format_pct(probabilities.get("open_source_elo_dixon_coles")),
            )
        )
    consensus_selection = consensus.get("selection") or "无明确共识"
    confidence = consensus.get("confidence") or "unknown"
    consensus_probability = format_pct(optional_float(consensus.get("mean_probability")))
    parts.append(f"共识方向{consensus_selection}，均值{consensus_probability}，置信度{confidence}")
    parts.append(f"最大模型分歧{format_pct(max_gap)}")
    parts.append("当前选择与共识一致" if aligned else "当前选择与共识不完全一致，需小仓或观察")
    return "模型交叉验证：" + "；".join(parts) + "。"


def append_model_summary(rationale: str, summary: str) -> str:
    base = str(rationale or "").strip()
    if "模型交叉验证" in base:
        return base
    if not base:
        return summary
    return f"{base} {summary}"


def format_pct(value) -> str:
    numeric = optional_float(value)
    if numeric is None:
        return "缺失"
    return f"{numeric * 100:.2f}%"


def apply_execution_stakes_to_board_results(current_by_board: Dict[str, Dict], match_stakes: Iterable[Dict] | None) -> Dict[str, Dict]:
    result = deepcopy(current_by_board)
    index = match_stake_index(match_stakes)
    matches = result.get("world_cup_matches", {})
    for item in matches.get("recommendations", []):
        execution = execution_stake_for_match(item, index)
        if execution is None:
            continue
        base = float(item.get("stake_aud") or 0)
        item["base_stake_aud"] = base
        item["time_adjusted_stake_aud"] = execution
        item["execution_stake_aud"] = execution
        item["stake_aud"] = execution
        if execution > 0:
            item["decision"] = "buy"
    return result


def apply_execution_stakes_to_portfolio_compare(diff: Dict, match_stakes: Iterable[Dict] | None) -> Dict:
    result = deepcopy(diff or {})
    index = match_stake_index(match_stakes)
    if not result or not index:
        return result

    for section in ("added", "removed"):
        for item in result.get(section, []):
            if item.get("board_id") != "world_cup_matches":
                continue
            execution = execution_stake_for_match(
                {
                    "match": item.get("event_name", ""),
                    "market": item.get("market", ""),
                    "selection": item.get("selection", ""),
                },
                index,
            )
            if execution is None:
                continue
            previous = float(item.get("stake_aud") or 0)
            item["base_stake_aud"] = previous
            item["execution_stake_aud"] = execution
            item["stake_aud"] = execution

    for item in result.get("changed", []):
        if item.get("board_id") != "world_cup_matches":
            continue
        execution = execution_stake_for_match(
            {
                "match": item.get("event_name", ""),
                "market": item.get("market", ""),
                "selection": item.get("selection", ""),
            },
            index,
        )
        if execution is None:
            continue
        new_odds_stake = float(item.get("stake_change_aud") or 0)
        # `stake_change_aud` is a delta, so adjust summary exposure separately
        # from the visible row data when the execution amount differs from base.
        item["execution_stake_aud"] = execution
        item["stake_change_aud"] = new_odds_stake

    base_current = sum(float(item.get("base_stake_aud", item.get("stake_aud", 0)) or 0) for item in index.values())
    execution_current = sum(float(item.get("time_adjusted_stake_aud") or 0) for item in index.values())
    exposure_delta = execution_current - base_current
    summary = result.setdefault("summary", {})
    summary["current_exposure_aud"] = round(float(summary.get("current_exposure_aud") or 0) + exposure_delta, 2)
    summary["exposure_change_aud"] = round(float(summary.get("exposure_change_aud") or 0) + exposure_delta, 2)
    board = result.get("by_board", {}).get("world_cup_matches")
    if board:
        board["current_exposure_aud"] = round(float(board.get("current_exposure_aud") or 0) + exposure_delta, 2)
        board["exposure_change_aud"] = round(float(board.get("exposure_change_aud") or 0) + exposure_delta, 2)
    return result


def optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
