import csv
import io
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .bootstrap import seed_world_cup_2026
from .config import settings
from .crawler import crawl_source
from .database import connect, init_db, row, rows
from .models import (
    BacktestRequest,
    CompetitionIn,
    CrawlSourceIn,
    MatchIn,
    PredictionOut,
    PredictionRequest,
    ReportRequest,
    TeamIn,
    TeamStatsIn,
)
from .scheduler import run_refresh_cycle, scheduler
from .services import build_prediction, create_match_report, prediction_payload, run_backtest
from .web import dashboard_html

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    with connect() as conn:
        init_db(conn)
        if settings.auto_seed_world_cup:
            seed_world_cup_2026(conn)
    scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    scheduler.stop()


def _not_found(message: str = "not found") -> HTTPException:
    return HTTPException(status_code=404, detail=message)


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "model_version": settings.model_version,
        "refresh_interval_hours": str(settings.refresh_interval_hours),
    }


@app.get("/")
def root() -> Response:
    return Response(dashboard_html(), media_type="text/html")


@app.get("/api/dashboard")
def dashboard_summary() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return {
            "competition": row(conn, "SELECT * FROM competitions WHERE name = 'FIFA World Cup 2026'"),
            "teams_count": row(conn, "SELECT COUNT(*) AS count FROM teams")["count"],
            "sources_count": row(conn, "SELECT COUNT(*) AS count FROM crawl_sources")["count"],
            "enabled_sources_count": row(conn, "SELECT COUNT(*) AS count FROM crawl_sources WHERE enabled = 1")["count"],
            "news_articles_count": row(conn, "SELECT COUNT(*) AS count FROM news_articles")["count"],
            "matches_count": row(conn, "SELECT COUNT(*) AS count FROM matches")["count"],
            "reports_count": row(conn, "SELECT COUNT(*) AS count FROM reports")["count"],
            "latest_refresh": row(conn, "SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 1"),
        }


@app.post("/bootstrap/world-cup-2026")
def bootstrap_world_cup_2026() -> Dict[str, int]:
    with connect() as conn:
        init_db(conn)
        return seed_world_cup_2026(conn)


@app.get("/teams")
def list_teams() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM teams ORDER BY name")


@app.post("/teams")
def create_team(payload: TeamIn) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        cur = conn.execute(
            "INSERT INTO teams(name, country, team_type, fifa_rank) VALUES (?, ?, ?, ?)",
            (payload.name, payload.country, payload.team_type, payload.fifa_rank),
        )
        return row(conn, "SELECT * FROM teams WHERE id = ?", (cur.lastrowid,))


@app.get("/competitions")
def list_competitions() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM competitions ORDER BY name")


@app.post("/competitions")
def create_competition(payload: CompetitionIn) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        cur = conn.execute(
            "INSERT INTO competitions(name, season, region) VALUES (?, ?, ?)",
            (payload.name, payload.season, payload.region),
        )
        return row(conn, "SELECT * FROM competitions WHERE id = ?", (cur.lastrowid,))


@app.get("/matches")
def list_matches() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(
            conn,
            """
            SELECT m.*, ht.name AS home_team, at.name AS away_team, c.name AS competition
            FROM matches m
            JOIN teams ht ON ht.id = m.home_team_id
            JOIN teams at ON at.id = m.away_team_id
            LEFT JOIN competitions c ON c.id = m.competition_id
            ORDER BY m.match_time
            """,
        )


@app.post("/matches")
def create_match(payload: MatchIn) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        cur = conn.execute(
            """
            INSERT INTO matches(competition_id, home_team_id, away_team_id, match_time, venue,
                                status, home_score, away_score, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.competition_id,
                payload.home_team_id,
                payload.away_team_id,
                payload.match_time,
                payload.venue,
                payload.status,
                payload.home_score,
                payload.away_score,
                payload.importance,
            ),
        )
        return row(conn, "SELECT * FROM matches WHERE id = ?", (cur.lastrowid,))


@app.get("/matches/{match_id}")
def get_match(match_id: int) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        result = row(conn, "SELECT * FROM matches WHERE id = ?", (match_id,))
        if not result:
            raise _not_found("match not found")
        return result


@app.post("/imports/matches")
def import_matches(items: List[MatchIn]) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        for item in items:
            conn.execute(
                """
                INSERT INTO matches(competition_id, home_team_id, away_team_id, match_time, venue,
                                    status, home_score, away_score, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.competition_id,
                    item.home_team_id,
                    item.away_team_id,
                    item.match_time,
                    item.venue,
                    item.status,
                    item.home_score,
                    item.away_score,
                    item.importance,
                ),
            )
        return {"imported": len(items)}


@app.post("/imports/team-stats")
def import_team_stats(items: List[TeamStatsIn]) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        for item in items:
            conn.execute(
                """
                INSERT INTO team_stats(team_id, matches_played, recent_points, recent_goals_for,
                                       recent_goals_against, home_win_rate, away_win_rate,
                                       injury_impact, fatigue_index, news_sentiment, trend_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.team_id,
                    item.matches_played,
                    item.recent_points,
                    item.recent_goals_for,
                    item.recent_goals_against,
                    item.home_win_rate,
                    item.away_win_rate,
                    item.injury_impact,
                    item.fatigue_index,
                    item.news_sentiment,
                    item.trend_score,
                ),
            )
        return {"imported": len(items)}


@app.post("/imports/matches.csv")
def import_matches_csv(body: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(body))
    items = [
        MatchIn(
            competition_id=int(row_data["competition_id"]) if row_data.get("competition_id") else None,
            home_team_id=int(row_data["home_team_id"]),
            away_team_id=int(row_data["away_team_id"]),
            match_time=row_data["match_time"],
            venue=row_data.get("venue") or None,
            status=row_data.get("status") or "scheduled",
            home_score=int(row_data["home_score"]) if row_data.get("home_score") else None,
            away_score=int(row_data["away_score"]) if row_data.get("away_score") else None,
            importance=int(row_data.get("importance") or 3),
        )
        for row_data in reader
    ]
    return import_matches(items)


@app.get("/crawl-sources")
def list_crawl_sources() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM crawl_sources ORDER BY name")


@app.post("/crawl-sources")
def create_crawl_source(payload: CrawlSourceIn) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        cur = conn.execute(
            "INSERT INTO crawl_sources(name, base_url, source_type, terms_note, enabled) VALUES (?, ?, ?, ?, ?)",
            (payload.name, payload.base_url, payload.source_type, payload.terms_note, int(payload.enabled)),
        )
        return row(conn, "SELECT * FROM crawl_sources WHERE id = ?", (cur.lastrowid,))


@app.post("/crawl-jobs/run")
def run_crawl_job(source_id: int) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        source = row(conn, "SELECT * FROM crawl_sources WHERE id = ? AND enabled = 1", (source_id,))
        if not source:
            raise _not_found("enabled crawl source not found")
        cur = conn.execute(
            "INSERT INTO crawl_jobs(source_id, status, started_at) VALUES (?, 'running', CURRENT_TIMESTAMP)",
            (source_id,),
        )
        job_id = int(cur.lastrowid)
        result = crawl_source(conn, source, job_id)
        conn.execute(
            "UPDATE crawl_jobs SET status = ?, finished_at = CURRENT_TIMESTAMP, summary = ? WHERE id = ?",
            (result["status"], result["summary"], job_id),
        )
        return row(conn, "SELECT * FROM crawl_jobs WHERE id = ?", (job_id,))


@app.get("/crawl-jobs")
def list_crawl_jobs() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM crawl_jobs ORDER BY id DESC")


@app.get("/crawl-logs")
def list_crawl_logs() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM crawl_logs ORDER BY id DESC")


@app.get("/news-articles")
def list_news_articles() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM news_articles ORDER BY id DESC")


@app.get("/refresh/status")
def refresh_status() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        latest = row(conn, "SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 1")
    status = scheduler.status()
    status["latest_persisted_run"] = latest
    return status


@app.post("/refresh/run")
def refresh_run_now() -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return run_refresh_cycle(conn)


@app.get("/refresh/runs")
def list_refresh_runs() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM refresh_runs ORDER BY id DESC")


@app.post("/predictions", response_model=PredictionOut)
def create_prediction(payload: PredictionRequest) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        try:
            return build_prediction(conn, payload.match_id)
        except ValueError as exc:
            raise _not_found(str(exc))


@app.get("/predictions")
def list_predictions() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM predictions ORDER BY id DESC")


@app.get("/predictions/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: int) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        try:
            return prediction_payload(conn, prediction_id)
        except ValueError as exc:
            raise _not_found(str(exc))


@app.post("/backtests")
def create_backtest(payload: BacktestRequest) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        return run_backtest(conn, payload.model_version or "")


@app.get("/backtests")
def get_backtests() -> Dict[str, str]:
    return {"message": "Backtests are calculated on demand by POST /backtests in the MVP."}


@app.post("/reports/match/{match_id}")
def post_match_report(match_id: int, payload: ReportRequest = ReportRequest()) -> Dict[str, Any]:
    with connect() as conn:
        init_db(conn)
        try:
            return create_match_report(conn, match_id, payload.include_prediction)
        except ValueError as exc:
            raise _not_found(str(exc))


@app.get("/reports")
def list_reports() -> List[Dict[str, Any]]:
    with connect() as conn:
        init_db(conn)
        return rows(conn, "SELECT * FROM reports ORDER BY id DESC")


@app.get("/reports/{report_id}.md")
def get_report_markdown(report_id: int) -> Response:
    with connect() as conn:
        init_db(conn)
        result = row(conn, "SELECT content_markdown FROM reports WHERE id = ?", (report_id,))
        if not result:
            raise _not_found("report not found")
        return Response(result["content_markdown"], media_type="text/markdown")
