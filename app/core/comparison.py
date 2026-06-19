from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import Settings
from app.core.discipline import DisciplineEvent
from app.scheduler import is_business_day


COMPARE_TYPES = ("same_day_previous", "previous_day", "previous_week", "previous_month")


@dataclass(frozen=True)
class ComparisonSummary:
    compare_type: str
    base_run_id: str | None
    old_top5: tuple[str, ...]
    new_top5: tuple[str, ...]
    top5_change_rate: float
    new_count: int
    replacement_count: int
    max_key_field_sigma: float


def _top5(conn: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT r.asset_id, r.rank, r.target_weight, s.total_score
        FROM recommendation_snapshot r
        JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
        WHERE r.run_id=?
        ORDER BY r.rank ASC
        LIMIT 5
        """,
        (run_id,),
    ).fetchall()


def _run_time_bj(conn: sqlite3.Connection, run_id: str) -> datetime:
    row = conn.execute("SELECT run_time_bj FROM run_log WHERE run_id=?", (run_id,)).fetchone()
    if not row:
        raise ValueError(f"run not found: {run_id}")
    return datetime.fromisoformat(row["run_time_bj"])


def _eligible_base_run(row: sqlite3.Row, primary_tz: str) -> bool:
    if row["status"] != "success" or row["data_quality_status"] != "pass":
        return False
    try:
        run_time = datetime.fromisoformat(row["run_time_bj"])
    except ValueError:
        return False
    return is_business_day(run_time, primary_tz)


def _base_run(
    conn: sqlite3.Connection,
    current_run_id: str,
    compare_type: str,
    settings: Settings,
) -> str | None:
    current_time = _run_time_bj(conn, current_run_id)
    if compare_type == "same_day_previous":
        rows = conn.execute(
            """
            SELECT run_id, run_time_bj, status, data_quality_status FROM run_log
            WHERE schedule_slot LIKE 'R%'
              AND run_id != ?
              AND substr(run_time_bj, 1, 10)=?
              AND run_time_bj < ?
            ORDER BY run_time_bj DESC
            LIMIT 50
            """,
            (current_run_id, current_time.date().isoformat(), current_time.isoformat()),
        ).fetchall()
        for row in rows:
            if _eligible_base_run(row, settings.timezone_primary):
                return row["run_id"]
        return None

    offsets = {
        "previous_day": timedelta(days=1),
        "previous_week": timedelta(days=7),
        "previous_month": timedelta(days=30),
    }
    target = current_time - offsets[compare_type]
    rows = conn.execute(
        """
        SELECT run_id, run_time_bj, status, data_quality_status FROM run_log
        WHERE schedule_slot LIKE 'R%'
          AND run_id != ?
          AND run_time_bj <= ?
        ORDER BY run_time_bj DESC
        LIMIT 200
        """,
        (current_run_id, target.isoformat()),
    ).fetchall()
    for row in rows:
        if _eligible_base_run(row, settings.timezone_primary):
            return row["run_id"]
    return None


def _score_sigma(conn: sqlite3.Connection, asset_id: str, current_score: float) -> float:
    rows = conn.execute(
        """
        SELECT total_score FROM score_snapshot
        WHERE asset_id=?
        ORDER BY rowid DESC
        LIMIT 20
        """,
        (asset_id,),
    ).fetchall()
    scores = [float(row["total_score"]) for row in rows]
    if len(scores) < 3:
        return 0.0
    mean = sum(scores) / len(scores)
    variance = sum((score - mean) ** 2 for score in scores) / len(scores)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return abs(current_score - mean) / std


def persist_comparisons(
    conn: sqlite3.Connection,
    run_id: str,
    created_at: str,
    settings: Settings,
) -> tuple[list[ComparisonSummary], list[DisciplineEvent]]:
    current_rows = _top5(conn, run_id)
    current_ids = tuple(row["asset_id"] for row in current_rows)
    summaries: list[ComparisonSummary] = []
    events: list[DisciplineEvent] = []

    for compare_type in COMPARE_TYPES:
        base_run_id = _base_run(conn, run_id, compare_type, settings)
        old_rows = _top5(conn, base_run_id) if base_run_id else []
        old_ids = tuple(row["asset_id"] for row in old_rows)
        if old_ids:
            new_assets = set(current_ids) - set(old_ids)
            removed_assets = set(old_ids) - set(current_ids)
            replacement_count = max(len(new_assets), len(removed_assets))
            change_rate = len(new_assets | removed_assets) / max(len(current_ids), 1)
        else:
            new_assets = set()
            replacement_count = 0
            change_rate = 0.0

        old_by_id = {row["asset_id"]: row for row in old_rows}
        max_sigma = 0.0
        for row in current_rows:
            old = old_by_id.get(row["asset_id"])
            delta_rank = (int(row["rank"]) - int(old["rank"])) if old else None
            delta_score = (float(row["total_score"]) - float(old["total_score"])) if old else None
            delta_weight = (
                float(row["target_weight"] or 0.0) - float(old["target_weight"] or 0.0)
                if old
                else None
            )
            sigma = _score_sigma(conn, row["asset_id"], float(row["total_score"]))
            max_sigma = max(max_sigma, sigma)
            conn.execute(
                """
                INSERT INTO comparison_snapshot (
                  run_id, asset_id, compare_type, base_run_id, delta_rank,
                  delta_score, delta_weight, top5_changed, key_field_sigma
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["asset_id"],
                    compare_type,
                    base_run_id,
                    delta_rank,
                    delta_score,
                    delta_weight,
                    int(row["asset_id"] not in old_by_id) if old_ids else 0,
                    sigma,
                ),
            )

        summary = ComparisonSummary(
            compare_type=compare_type,
            base_run_id=base_run_id,
            old_top5=old_ids,
            new_top5=current_ids,
            top5_change_rate=change_rate,
            new_count=len(new_assets),
            replacement_count=replacement_count,
            max_key_field_sigma=max_sigma,
        )
        summaries.append(summary)

        if not base_run_id:
            continue
        if change_rate > settings.top5_change_rate_threshold:
            events.append(
                DisciplineEvent(
                    trigger_reason=(
                        f"{compare_type} Top5 change rate {change_rate:.2%} exceeds "
                        f"{settings.top5_change_rate_threshold:.2%}"
                    ),
                    severity="Alert",
                )
            )
        if len(new_assets) >= 1:
            events.append(
                DisciplineEvent(
                    trigger_reason=f"{compare_type} added {len(new_assets)} new Top5 asset(s): {', '.join(sorted(new_assets))}",
                    severity="Alert",
                )
            )
        if replacement_count >= 2:
            events.append(
                DisciplineEvent(
                    trigger_reason=f"{compare_type} replaced {replacement_count} Top5 asset(s)",
                    severity="Alert",
                )
            )
        if max_sigma > 1.0:
            events.append(
                DisciplineEvent(
                    trigger_reason=f"{compare_type} key field sigma {max_sigma:.2f} exceeds 1.00",
                    severity="Alert",
                )
            )

    return summaries, events
