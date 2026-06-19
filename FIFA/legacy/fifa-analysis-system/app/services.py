import json
import math
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Tuple

from .config import settings
from .constants import DISCLAIMER
from .database import row, rows

WEIGHTS = {
    "recent_form": 1.4,
    "attack": 0.9,
    "defense": 0.8,
    "ranking": 0.7,
    "home_advantage": 0.35,
    "injury": 0.8,
    "fatigue": 0.5,
    "news": 0.25,
    "trend": 0.2,
}


def _latest_stats(conn: sqlite3.Connection, team_id: int) -> Dict[str, Any]:
    return row(
        conn,
        "SELECT * FROM team_stats WHERE team_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
        (team_id,),
    ) or {}


def _form(stats: Dict[str, Any]) -> float:
    played = max(int(stats.get("matches_played") or 0), 1)
    return min(float(stats.get("recent_points") or 0) / (played * 3), 1.0)


def _attack(stats: Dict[str, Any]) -> float:
    played = max(int(stats.get("matches_played") or 0), 1)
    return min(float(stats.get("recent_goals_for") or 0) / played / 3.0, 1.0)


def _defense(stats: Dict[str, Any]) -> float:
    played = max(int(stats.get("matches_played") or 0), 1)
    goals_against = float(stats.get("recent_goals_against") or 0) / played
    return 1 / (1 + goals_against)


def _ranking_score(team: Dict[str, Any], opponent: Dict[str, Any]) -> Tuple[float, bool]:
    if team.get("fifa_rank") is None or opponent.get("fifa_rank") is None:
        return 0.0, False
    advantage = int(opponent["fifa_rank"]) - int(team["fifa_rank"])
    return max(min(advantage / 100.0, 1.0), -1.0), True


def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
    max_score = max(scores.values())
    exps = {key: math.exp(value - max_score) for key, value in scores.items()}
    total = sum(exps.values())
    return {key: value / total for key, value in exps.items()}


def _confidence(probabilities: Dict[str, float]) -> str:
    ordered = sorted(probabilities.values(), reverse=True)
    gap = ordered[0] - ordered[1]
    if gap >= 0.20:
        return "high"
    if gap >= 0.10:
        return "medium"
    return "low"


def _actual_result(match: Dict[str, Any]) -> str:
    if match.get("home_score") is None or match.get("away_score") is None:
        return "unknown"
    if int(match["home_score"]) > int(match["away_score"]):
        return "home_win"
    if int(match["home_score"]) < int(match["away_score"]):
        return "away_win"
    return "draw"


def build_prediction(conn: sqlite3.Connection, match_id: int) -> Dict[str, Any]:
    match = row(
        conn,
        """
        SELECT m.*, ht.name AS home_team, at.name AS away_team, c.name AS competition,
               ht.fifa_rank AS home_rank, at.fifa_rank AS away_rank
        FROM matches m
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        LEFT JOIN competitions c ON c.id = m.competition_id
        WHERE m.id = ?
        """,
        (match_id,),
    )
    if not match:
        raise ValueError("match not found")

    home_team = {"fifa_rank": match.get("home_rank")}
    away_team = {"fifa_rank": match.get("away_rank")}
    home_stats = _latest_stats(conn, int(match["home_team_id"]))
    away_stats = _latest_stats(conn, int(match["away_team_id"]))
    warnings: List[str] = []
    if not home_stats:
        warnings.append("home_team_stats_missing")
    if not away_stats:
        warnings.append("away_team_stats_missing")

    scores = {"home_win": 0.0, "draw": 0.15, "away_win": 0.0}
    factors: List[Dict[str, Any]] = []

    def add_factor(name: str, source: str, formula: str, weight: float, value: float, target: str, effect: str) -> None:
        scores[target] += weight * value
        factors.append(
            {
                "name": name,
                "source": source,
                "formula": formula,
                "weight": weight,
                "value": round(value, 4),
                "effect": effect,
            }
        )

    home_form = _form(home_stats)
    away_form = _form(away_stats)
    add_factor("recent_form_home", "team_stats", "recent_points / (matches_played * 3)", WEIGHTS["recent_form"], home_form, "home_win", "Home recent form lifts home score.")
    add_factor("recent_form_away", "team_stats", "recent_points / (matches_played * 3)", WEIGHTS["recent_form"], away_form, "away_win", "Away recent form lifts away score.")
    add_factor("attack_home", "team_stats", "recent_goals_for / matches_played / 3", WEIGHTS["attack"], _attack(home_stats), "home_win", "Home attacking output lifts home score.")
    add_factor("attack_away", "team_stats", "recent_goals_for / matches_played / 3", WEIGHTS["attack"], _attack(away_stats), "away_win", "Away attacking output lifts away score.")
    add_factor("defense_home", "team_stats", "1 / (1 + recent_goals_against / matches_played)", WEIGHTS["defense"], _defense(home_stats), "home_win", "Home defensive strength lifts home score.")
    add_factor("defense_away", "team_stats", "1 / (1 + recent_goals_against / matches_played)", WEIGHTS["defense"], _defense(away_stats), "away_win", "Away defensive strength lifts away score.")

    home_rank_score, has_home_rank = _ranking_score(home_team, away_team)
    away_rank_score, has_away_rank = _ranking_score(away_team, home_team)
    if not has_home_rank or not has_away_rank:
        warnings.append("fifa_ranking_missing")
    add_factor("ranking_home", "teams.fifa_rank", "clamp((away_rank - home_rank) / 100, -1, 1)", WEIGHTS["ranking"], home_rank_score, "home_win", "Better home ranking lifts home score; worse ranking lowers it.")
    add_factor("ranking_away", "teams.fifa_rank", "clamp((home_rank - away_rank) / 100, -1, 1)", WEIGHTS["ranking"], away_rank_score, "away_win", "Better away ranking lifts away score; worse ranking lowers it.")
    add_factor("home_advantage", "match venue default rule", "fixed MVP weight for home team", WEIGHTS["home_advantage"], 1.0, "home_win", "Home venue increases home result tendency.")

    add_factor("injury_home", "team_stats.injury_impact", "-injury_impact", WEIGHTS["injury"], -float(home_stats.get("injury_impact") or 0), "home_win", "Injury impact reduces home score.")
    add_factor("injury_away", "team_stats.injury_impact", "-injury_impact", WEIGHTS["injury"], -float(away_stats.get("injury_impact") or 0), "away_win", "Injury impact reduces away score.")
    add_factor("fatigue_home", "team_stats.fatigue_index", "-fatigue_index", WEIGHTS["fatigue"], -float(home_stats.get("fatigue_index") or 0), "home_win", "Schedule fatigue reduces home score.")
    add_factor("fatigue_away", "team_stats.fatigue_index", "-fatigue_index", WEIGHTS["fatigue"], -float(away_stats.get("fatigue_index") or 0), "away_win", "Schedule fatigue reduces away score.")
    add_factor("news_home", "team_stats.news_sentiment", "sentiment in [-1, 1]", WEIGHTS["news"], float(home_stats.get("news_sentiment") or 0), "home_win", "Positive news sentiment lifts home score.")
    add_factor("news_away", "team_stats.news_sentiment", "sentiment in [-1, 1]", WEIGHTS["news"], float(away_stats.get("news_sentiment") or 0), "away_win", "Positive news sentiment lifts away score.")
    add_factor("trend_home", "team_stats.trend_score", "trend in [-1, 1]", WEIGHTS["trend"], float(home_stats.get("trend_score") or 0), "home_win", "Positive trend signal lifts home score.")
    add_factor("trend_away", "team_stats.trend_score", "trend in [-1, 1]", WEIGHTS["trend"], float(away_stats.get("trend_score") or 0), "away_win", "Positive trend signal lifts away score.")

    diff = abs(scores["home_win"] - scores["away_win"])
    scores["draw"] += max(0.0, 0.45 - diff) * 0.6
    probabilities = _softmax(scores)
    recommended = max(probabilities, key=probabilities.get)
    confidence = _confidence(probabilities)

    cur = conn.execute(
        """
        INSERT INTO predictions(match_id, model_version, home_win_probability, draw_probability,
                                away_win_probability, recommended_result, confidence_level,
                                missing_data_warnings, disclaimer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            match_id,
            settings.model_version,
            probabilities["home_win"],
            probabilities["draw"],
            probabilities["away_win"],
            recommended,
            confidence,
            json.dumps(warnings, ensure_ascii=False),
            DISCLAIMER,
        ),
    )
    prediction_id = int(cur.lastrowid)
    conn.executemany(
        """
        INSERT INTO prediction_factors(prediction_id, name, source, formula, weight, value, effect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (prediction_id, factor["name"], factor["source"], factor["formula"], factor["weight"], factor["value"], factor["effect"])
            for factor in factors
        ],
    )
    generated = row(conn, "SELECT generated_at FROM predictions WHERE id = ?", (prediction_id,))
    return prediction_payload(conn, prediction_id, generated_at=generated["generated_at"] if generated else datetime.utcnow().isoformat())


def prediction_payload(conn: sqlite3.Connection, prediction_id: int, generated_at: str = "") -> Dict[str, Any]:
    prediction = row(
        conn,
        """
        SELECT p.*, m.match_time, ht.name AS home_team, at.name AS away_team, c.name AS competition
        FROM predictions p
        JOIN matches m ON m.id = p.match_id
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        LEFT JOIN competitions c ON c.id = m.competition_id
        WHERE p.id = ?
        """,
        (prediction_id,),
    )
    if not prediction:
        raise ValueError("prediction not found")
    factors = rows(
        conn,
        "SELECT name, source, formula, weight, value, effect FROM prediction_factors WHERE prediction_id = ?",
        (prediction_id,),
    )
    return {
        "prediction_id": prediction_id,
        "match_id": prediction["match_id"],
        "home_team": prediction["home_team"],
        "away_team": prediction["away_team"],
        "competition": prediction["competition"],
        "match_time": prediction["match_time"],
        "home_win_probability": round(prediction["home_win_probability"], 4),
        "draw_probability": round(prediction["draw_probability"], 4),
        "away_win_probability": round(prediction["away_win_probability"], 4),
        "recommended_result": prediction["recommended_result"],
        "confidence_level": prediction["confidence_level"],
        "key_factors": factors,
        "missing_data_warnings": json.loads(prediction["missing_data_warnings"]),
        "model_version": prediction["model_version"],
        "generated_at": generated_at or prediction["generated_at"],
        "disclaimer": prediction["disclaimer"],
    }


def run_backtest(conn: sqlite3.Connection, model_version: str = "") -> Dict[str, Any]:
    params: List[Any] = []
    version_filter = ""
    if model_version:
        version_filter = " AND p.model_version = ?"
        params.append(model_version)
    predictions = rows(
        conn,
        f"""
        SELECT p.*, m.home_score, m.away_score, m.match_time
        FROM predictions p
        JOIN matches m ON m.id = p.match_id
        WHERE m.status = 'finished' AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL {version_filter}
        """,
        params,
    )
    total = len(predictions)
    if total == 0:
        return {"prediction_count": 0, "message": "No finished matches with saved predictions."}

    correct = 0
    per_result = {
        "home_win": {"total": 0, "correct": 0},
        "draw": {"total": 0, "correct": 0},
        "away_win": {"total": 0, "correct": 0},
    }
    brier = 0.0
    log_loss = 0.0
    dates = []
    for item in predictions:
        actual = _actual_result(item)
        recommended = item["recommended_result"]
        is_correct = int(actual == recommended)
        correct += is_correct
        per_result[recommended]["total"] += 1
        per_result[recommended]["correct"] += is_correct
        probs = {
            "home_win": float(item["home_win_probability"]),
            "draw": float(item["draw_probability"]),
            "away_win": float(item["away_win_probability"]),
        }
        for result, prob in probs.items():
            observed = 1.0 if result == actual else 0.0
            brier += (prob - observed) ** 2
        log_loss += -math.log(max(probs[actual], 1e-15))
        dates.append(item["match_time"])
        conn.execute(
            """
            INSERT INTO prediction_results(prediction_id, actual_result, is_correct)
            VALUES (?, ?, ?)
            """,
            (item["id"], actual, is_correct),
        )

    def acc(result: str) -> float:
        bucket = per_result[result]
        return round(bucket["correct"] / bucket["total"], 4) if bucket["total"] else 0.0

    return {
        "prediction_count": total,
        "top_prediction_accuracy": round(correct / total, 4),
        "win_draw_loss_accuracy": round(correct / total, 4),
        "home_win_prediction_accuracy": acc("home_win"),
        "draw_prediction_accuracy": acc("draw"),
        "away_win_prediction_accuracy": acc("away_win"),
        "brier_score": round(brier / total, 4),
        "log_loss": round(log_loss / total, 4),
        "sample_time_range": {"from": min(dates), "to": max(dates)},
        "model_version": model_version or "all",
    }


def create_match_report(conn: sqlite3.Connection, match_id: int, include_prediction: bool = True) -> Dict[str, Any]:
    match = row(
        conn,
        """
        SELECT m.*, ht.name AS home_team, at.name AS away_team, c.name AS competition
        FROM matches m
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        LEFT JOIN competitions c ON c.id = m.competition_id
        WHERE m.id = ?
        """,
        (match_id,),
    )
    if not match:
        raise ValueError("match not found")
    prediction = None
    if include_prediction:
        existing = row(conn, "SELECT id FROM predictions WHERE match_id = ? ORDER BY id DESC LIMIT 1", (match_id,))
        prediction = prediction_payload(conn, int(existing["id"])) if existing else build_prediction(conn, match_id)

    title = f"{match['home_team']} vs {match['away_team']} 赛前分析报告"
    lines = [
        f"# {title}",
        "",
        f"- 赛事：{match.get('competition') or '待确认'}",
        f"- 时间：{match['match_time']}",
        f"- 场地：{match.get('venue') or '待确认'}",
        f"- 重要性：{match['importance']}/5",
        "",
    ]
    if prediction:
        lines.extend(
            [
                "## 概率预测",
                "",
                f"- 主胜：{prediction['home_win_probability']:.2%}",
                f"- 平局：{prediction['draw_probability']:.2%}",
                f"- 客胜：{prediction['away_win_probability']:.2%}",
                f"- 推荐倾向：{prediction['recommended_result']}",
                f"- 置信度：{prediction['confidence_level']}",
                f"- 缺失数据：{', '.join(prediction['missing_data_warnings']) or '无'}",
                "",
                "## 免责声明",
                "",
                prediction["disclaimer"],
            ]
        )
    cur = conn.execute(
        "INSERT INTO reports(match_id, title, content_markdown) VALUES (?, ?, ?)",
        (match_id, title, "\n".join(lines)),
    )
    return row(conn, "SELECT * FROM reports WHERE id = ?", (cur.lastrowid,))
