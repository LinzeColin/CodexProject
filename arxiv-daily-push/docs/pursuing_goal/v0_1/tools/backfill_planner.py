#!/usr/bin/env python3
"""ADP V0.1 2016+ backfill planner + resumable cursor (ADP-S4-P01-T041).

Splits the 2016+ history backfill into small monthly shards that are retryable and resumable: each
shard carries a cursor (the last CONFIRMED item id) so an interrupted shard resumes from its last
checkpoint without redoing or skipping, and processing is idempotent so the same shard run any number
of times produces no duplicates. Deterministic; no clock/network. NOT_DEPLOYED.

Idempotency key = the content-addressed id (T024 canonical id / T021 raw key). A checkpoint advances
only after an item is confirmed applied, so a crash between apply and checkpoint is safe (the item is
already in the applied set; a replay skips it -- see T026 replay idempotency).
"""
from __future__ import annotations
import dataclasses, json, pathlib

SCHEMA_VERSION = "adp.backfill.v0_1"


@dataclasses.dataclass
class ShardCursor:
    shard_id: str                 # "backfill/YYYY-MM"
    year: int
    month: int
    status: str = "pending"       # pending | in_progress | done
    last_confirmed_id: str | None = None   # resume point (the last id confirmed applied)
    processed: int = 0
    total: int = 0


def plan_shards(start="2016-01", end="2026-07"):
    """Monthly shards from start..end inclusive. Small, independent, retryable units."""
    sy, sm = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    shards, y, m = [], sy, sm
    while (y, m) <= (ey, em):
        shards.append(ShardCursor(shard_id=f"backfill/{y:04d}-{m:02d}", year=y, month=m))
        m += 1
        if m > 12:
            m = 1; y += 1
    return shards


def process_shard(cursor: ShardCursor, items, applied: set, stop_after=None):
    """Process a shard's items (each a dict with a content-addressed 'id'), sorted deterministically.
    - resume: skip items with id <= cursor.last_confirmed_id (already confirmed in a prior run);
    - idempotent: skip items whose id is already in `applied` (no duplicates across runs);
    - checkpoint: advance cursor.last_confirmed_id AFTER each confirmed apply;
    - stop_after: simulate an interruption after N new applies this call (returns partial cursor).
    Returns (cursor, newly_applied_ids)."""
    cursor.total = len(items)
    cursor.status = "in_progress"
    ordered = sorted(items, key=lambda it: it["id"])
    newly = []
    for it in ordered:
        iid = it["id"]
        if cursor.last_confirmed_id is not None and iid <= cursor.last_confirmed_id:
            continue                                 # resume: before the checkpoint
        if iid in applied:
            cursor.last_confirmed_id = iid           # idempotent: already applied -> just advance
            continue
        applied.add(iid)                             # apply (content-addressed -> exactly-once effect)
        cursor.processed += 1
        cursor.last_confirmed_id = iid               # checkpoint AFTER confirm
        newly.append(iid)
        if stop_after is not None and len(newly) >= stop_after:
            return cursor, newly                     # interrupted mid-shard; cursor holds the checkpoint
    cursor.status = "done"
    return cursor, newly


def resume(cursor: ShardCursor, items, applied: set):
    """Continue an interrupted shard from its last checkpoint until done."""
    return process_shard(cursor, items, applied)


CHECKPOINT_SCHEMA = """-- ADP-S4-P01-T041 backfill cursor/checkpoint (append-only status; resumable)
CREATE TABLE IF NOT EXISTS cn_backfill_shards (
  shard_id     TEXT PRIMARY KEY,          -- backfill/YYYY-MM
  year         INTEGER NOT NULL,
  month        INTEGER NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending',   -- pending/in_progress/done
  last_confirmed_id TEXT,                  -- resume point
  processed    INTEGER NOT NULL DEFAULT 0,
  total        INTEGER NOT NULL DEFAULT 0,
  updated_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_backfill_status ON cn_backfill_shards(status);
INSERT OR IGNORE INTO cn_meta(key,value) VALUES('backfill_schema','adp.backfill.v0_1');
"""


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2016-01")
    ap.add_argument("--end", default="2026-07")
    ap.add_argument("--out")
    args = ap.parse_args()
    shards = plan_shards(args.start, args.end)
    plan = {"schema_version": SCHEMA_VERSION, "start": args.start, "end": args.end,
            "shard_count": len(shards), "shards": [dataclasses.asdict(s) for s in shards]}
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema_version": SCHEMA_VERSION, "start": args.start, "end": args.end,
                      "shard_count": len(shards), "first": shards[0].shard_id, "last": shards[-1].shard_id},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
