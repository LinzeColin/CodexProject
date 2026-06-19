from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .artifacts import public_artifact_ref

def candidate_key(item: Dict) -> str:
    return "|".join([item["match"], item["market"], item["selection"]])


def load_baseline(path: Optional[Path]) -> Optional[Dict]:
    if not path or not path.exists():
        return None
    import json

    return json.loads(path.read_text())


def compare_recommendations(current: Dict, previous: Optional[Dict]) -> Dict:
    current_items = {candidate_key(item): item for item in current.get("recommendations", [])}
    previous_items = {candidate_key(item): item for item in (previous or {}).get("recommendations", [])}

    added = sorted(current_items.keys() - previous_items.keys())
    removed = sorted(previous_items.keys() - current_items.keys())
    retained = sorted(current_items.keys() & previous_items.keys())

    changed = []
    for key in retained:
        now = current_items[key]
        before = previous_items[key]
        odds_change = round(now["odds"] - before["odds"], 3)
        probability_change = round(now["model_probability"] - before["model_probability"], 4)
        ev_change = round(now["expected_value"] - before["expected_value"], 4)
        stake_change_aud = round(now["stake_aud"] - before["stake_aud"], 2)
        if odds_change or probability_change or ev_change or stake_change_aud:
            changed.append(
                {
                    "key": key,
                    "match": now["match"],
                    "market": now["market"],
                    "selection": now["selection"],
                    "old_odds": before["odds"],
                    "new_odds": now["odds"],
                    "odds_change": odds_change,
                    "probability_change": probability_change,
                    "ev_change": ev_change,
                    "stake_change_aud": stake_change_aud,
                    "status": classify_change(now, before),
                }
            )

    return {
        "previous_version": (previous or {}).get("version"),
        "current_version": current.get("version"),
        "added": [current_items[key] for key in added],
        "removed": [previous_items[key] for key in removed],
        "retained_count": len(retained),
        "changed": changed,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "retained_count": len(retained),
            "changed_count": len(changed),
            "current_exposure_aud": current.get("recommended_new_exposure_aud", 0),
            "previous_exposure_aud": (previous or {}).get("recommended_new_exposure_aud", 0),
            "exposure_change_aud": round(
                current.get("recommended_new_exposure_aud", 0)
                - (previous or {}).get("recommended_new_exposure_aud", 0),
                2,
            ),
        },
    }


def classify_change(now: Dict, before: Dict) -> str:
    if now["stake_aud"] > before["stake_aud"]:
        return "stake_up"
    if now["stake_aud"] < before["stake_aud"]:
        return "stake_down"
    if now["expected_value"] > before["expected_value"] + 0.02:
        return "value_improved"
    if now["expected_value"] < before["expected_value"] - 0.02:
        return "value_deteriorated"
    return "stable"


def compact_baseline(recommendations: Dict) -> Dict:
    return {
        "version": recommendations["version"],
        "source_raw": public_artifact_ref(recommendations["source_raw"]),
        "bankroll_aud": recommendations["bankroll_aud"],
        "unit_aud": recommendations["unit_aud"],
        "recommended_new_exposure_aud": recommendations["recommended_new_exposure_aud"],
        "recommendations": recommendations["recommendations"],
        "automation_gate": recommendations["automation_gate"],
    }


def compare_portfolio_recommendations(current_by_board: Dict[str, Dict], previous: Optional[Dict]) -> Dict:
    current_items = flatten_board_recommendations(current_by_board)
    previous_items = flatten_previous_portfolio(previous)

    added_keys = sorted(current_items.keys() - previous_items.keys())
    removed_keys = sorted(previous_items.keys() - current_items.keys())
    retained_keys = sorted(current_items.keys() & previous_items.keys())

    changed = []
    for key in retained_keys:
        now = current_items[key]
        before = previous_items[key]
        odds_change = numeric_delta(now.get("odds"), before.get("odds"), 3)
        probability_change = numeric_delta(now.get("probability"), before.get("probability"), 4)
        ev_change = numeric_delta(now.get("expected_value"), before.get("expected_value"), 4)
        stake_change_aud = numeric_delta(now.get("stake_aud"), before.get("stake_aud"), 2)
        if odds_change or probability_change or ev_change or stake_change_aud:
            changed.append(
                {
                    "key": key,
                    "board_id": now["board_id"],
                    "board_name": now["board_name"],
                    "event_name": now["event_name"],
                    "market": now["market"],
                    "selection": now["selection"],
                    "old_odds": before.get("odds"),
                    "new_odds": now.get("odds"),
                    "odds_change": odds_change,
                    "probability_change": probability_change,
                    "ev_change": ev_change,
                    "stake_change_aud": stake_change_aud,
                    "status": classify_generic_change(now, before),
                }
            )

    board_ids = sorted({item["board_id"] for item in list(current_items.values()) + list(previous_items.values())})
    by_board = {}
    for board_id in board_ids:
        current_board = [item for item in current_items.values() if item["board_id"] == board_id]
        previous_board = [item for item in previous_items.values() if item["board_id"] == board_id]
        by_board[board_id] = {
            "board_id": board_id,
            "board_name": (current_board or previous_board or [{"board_name": board_id}])[0]["board_name"],
            "added_count": len([key for key in added_keys if current_items.get(key, {}).get("board_id") == board_id]),
            "removed_count": len([key for key in removed_keys if previous_items.get(key, {}).get("board_id") == board_id]),
            "retained_count": len([key for key in retained_keys if current_items.get(key, {}).get("board_id") == board_id]),
            "changed_count": len([item for item in changed if item["board_id"] == board_id]),
            "current_exposure_aud": round(sum(float(item.get("stake_aud") or 0) for item in current_board), 2),
            "previous_exposure_aud": round(sum(float(item.get("stake_aud") or 0) for item in previous_board), 2),
        }
        by_board[board_id]["exposure_change_aud"] = round(
            by_board[board_id]["current_exposure_aud"] - by_board[board_id]["previous_exposure_aud"],
            2,
        )

    current_exposure = round(sum(float(item.get("stake_aud") or 0) for item in current_items.values()), 2)
    previous_exposure = round(sum(float(item.get("stake_aud") or 0) for item in previous_items.values()), 2)
    return {
        "version": "portfolio_compare_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "previous_version": (previous or {}).get("version"),
        "current_board_count": len(current_by_board),
        "previous_board_count": len((previous or {}).get("boards", {})),
        "added": [current_items[key] for key in added_keys],
        "removed": [previous_items[key] for key in removed_keys],
        "retained_count": len(retained_keys),
        "changed": changed,
        "by_board": by_board,
        "summary": {
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "retained_count": len(retained_keys),
            "changed_count": len(changed),
            "current_exposure_aud": current_exposure,
            "previous_exposure_aud": previous_exposure,
            "exposure_change_aud": round(current_exposure - previous_exposure, 2),
        },
    }


def compact_portfolio_baseline(current_by_board: Dict[str, Dict]) -> Dict:
    return {
        "version": "portfolio_baseline_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boards": {
            board_id: {
                "version": payload.get("version"),
                "automation_ready": bool(payload.get("automation_gate", {}).get("automation_ready")),
                "recommendation_count": len(payload.get("recommendations", [])),
                "recommendations": [
                    normalize_board_recommendation(board_id, item, payload).copy()
                    for item in payload.get("recommendations", [])
                ],
            }
            for board_id, payload in current_by_board.items()
        },
    }


def flatten_board_recommendations(current_by_board: Dict[str, Dict]) -> Dict[str, Dict]:
    items = {}
    for board_id, payload in current_by_board.items():
        for item in payload.get("recommendations", []):
            normalized = normalize_board_recommendation(board_id, item, payload)
            items[normalized["key"]] = normalized
    return items


def flatten_previous_portfolio(previous: Optional[Dict]) -> Dict[str, Dict]:
    items = {}
    for board_id, payload in (previous or {}).get("boards", {}).items():
        for item in payload.get("recommendations", []):
            normalized = normalize_board_recommendation(board_id, item, payload)
            items[normalized["key"]] = normalized
    return items


def normalize_board_recommendation(board_id: str, item: Dict, payload: Dict) -> Dict:
    if "key" in item and "board_id" in item:
        return {
            **item,
            "odds": optional_float(item.get("odds")),
            "probability": optional_float(item.get("probability")),
            "expected_value": optional_float(item.get("expected_value")),
            "stake_aud": float(item.get("stake_aud") or 0),
        }
    board_name = board_display_name(board_id, payload)
    probability = item.get("model_probability", item.get("no_vig_probability", item.get("probability")))
    event_name, selection = recommendation_event_and_selection(board_id, item)
    market = str(item.get("market", ""))
    normalized = {
        "board_id": board_id,
        "board_name": board_name,
        "event_name": event_name,
        "market": market,
        "selection": selection,
        "odds": optional_float(item.get("odds")),
        "probability": optional_float(probability),
        "expected_value": optional_float(item.get("expected_value")),
        "stake_aud": float(item.get("stake_aud") or item.get("time_adjusted_stake_aud") or 0),
        "action": str(item.get("decision") or ("buy" if float(item.get("stake_aud") or 0) > 0 else "watch_or_no_bet")),
    }
    normalized["key"] = "|".join([board_id, event_name, market, selection])
    return normalized


def board_display_name(board_id: str, payload: Dict) -> str:
    configured = payload.get("board") or payload.get("board_name")
    if configured:
        return str(configured)
    names = {
        "world_cup_matches": "2026 World Cup Matches",
        "world_cup_futures": "2026 World Cup Futures",
        "world_cup_group_betting": "2026 World Cup Group Betting",
        "world_cup_australia_markets": "2026 World Cup Australia Markets",
        "world_cup_team_futures_multi": "2026 World Cup Team Futures Multi",
    }
    return names.get(board_id, board_id)


def recommendation_event_and_selection(board_id: str, item: Dict) -> tuple[str, str]:
    if board_id == "world_cup_matches":
        return str(item.get("match", "")), str(item.get("selection", ""))
    if board_id == "world_cup_group_betting":
        return f"Group {item.get('group', '')}".strip(), str(item.get("team", item.get("selection", "")))
    if board_id in {"world_cup_futures", "world_cup_team_futures_multi"}:
        team = str(item.get("team", item.get("selection", "")))
        return team, team
    if board_id == "world_cup_australia_markets":
        return str(item.get("market", "")), str(item.get("selection", ""))
    return str(item.get("match") or item.get("team") or item.get("market") or ""), str(item.get("selection") or item.get("team") or "")


def classify_generic_change(now: Dict, before: Dict) -> str:
    if float(now.get("stake_aud") or 0) > float(before.get("stake_aud") or 0):
        return "stake_up"
    if float(now.get("stake_aud") or 0) < float(before.get("stake_aud") or 0):
        return "stake_down"
    now_ev = now.get("expected_value")
    before_ev = before.get("expected_value")
    if now_ev is not None and before_ev is not None:
        if now_ev > before_ev + 0.02:
            return "value_improved"
        if now_ev < before_ev - 0.02:
            return "value_deteriorated"
    now_probability = now.get("probability")
    before_probability = before.get("probability")
    if now_probability is not None and before_probability is not None:
        if now_probability > before_probability + 0.03:
            return "probability_up"
        if now_probability < before_probability - 0.03:
            return "probability_down"
    return "stable"


def numeric_delta(now, before, decimals: int) -> float:
    if now is None or before is None:
        return 0.0
    return round(float(now) - float(before), decimals)


def optional_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
