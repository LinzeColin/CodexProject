-- ADP-S4-P01-T041 backfill cursor/checkpoint (append-only status; resumable)
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
