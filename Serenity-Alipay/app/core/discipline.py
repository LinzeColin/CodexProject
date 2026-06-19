from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class DisciplineEvent:
    trigger_reason: str
    severity: str


def deviation_events(recommendations: list[dict[str, object]], settings: Settings) -> list[DisciplineEvent]:
    events: list[DisciplineEvent] = []
    for row in recommendations:
        deviation = abs(float(row["deviation"]))
        if deviation > settings.deviation_threshold:
            events.append(
                DisciplineEvent(
                    trigger_reason=(
                        f"{row['asset_code']} deviation {deviation:.2%} exceeds "
                        f"{settings.deviation_threshold:.2%}"
                    ),
                    severity="Alert",
                )
            )
    return events


def single_position_overexpansion_events(
    conn: sqlite3.Connection,
    run_id: str,
    settings: Settings,
    consecutive_threshold: int = 2,
) -> list[DisciplineEvent]:
    current_assets = {
        row["asset_id"]
        for row in conn.execute(
            "SELECT asset_id FROM recommendation_snapshot WHERE run_id=?",
            (run_id,),
        ).fetchall()
    }
    if not current_assets:
        return []
    rows = conn.execute(
        """
        SELECT asset_id, target_weight, current_weight, run_id
        FROM recommendation_snapshot
        WHERE run_id IN (
          SELECT run_id FROM run_log
          WHERE schedule_slot LIKE 'R%'
          ORDER BY created_at DESC, rowid DESC
          LIMIT 5
        )
        ORDER BY rowid DESC
        """,
    ).fetchall()
    by_asset: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        if row["asset_id"] not in current_assets:
            continue
        by_asset.setdefault(row["asset_id"], []).append(row)

    events: list[DisciplineEvent] = []
    for asset_id, asset_rows in by_asset.items():
        consecutive = 0
        for row in asset_rows:
            current = float(row["current_weight"] or 0.0)
            target = float(row["target_weight"] or 0.0)
            if current - target > settings.deviation_threshold:
                consecutive += 1
            else:
                break
        if consecutive > consecutive_threshold:
            events.append(
                DisciplineEvent(
                    trigger_reason=(
                        f"{asset_id} current weight exceeded target by more than "
                        f"{settings.deviation_threshold:.2%} for {consecutive} consecutive runs"
                    ),
                    severity="Alert",
                )
            )
    return events


def persist_rebalance_events(
    conn: sqlite3.Connection,
    run_id: str,
    created_at: str,
    events: list[DisciplineEvent],
) -> None:
    for event in events:
        conn.execute(
            """
            INSERT INTO rebalance_event_log (run_id, trigger_reason, severity, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, event.trigger_reason, event.severity, created_at),
        )
