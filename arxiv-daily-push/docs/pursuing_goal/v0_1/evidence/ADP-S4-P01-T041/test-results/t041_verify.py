#!/usr/bin/env python3
"""ADP-S4-P01-T041 acceptance: resumable 2016+ backfill planner + cursor.

Acceptance (TASK_INDEX): 同分片执行三次无重复；中断后从最后确认点恢复。
Deterministic. Uses content-addressed (sha256) ids so the ordering + resume logic match real keys.
"""
import sys, hashlib, pathlib, dataclasses
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import backfill_planner as B  # noqa: E402

fails = []

# --- planner: 2016+ monthly shards -----------------------------------------------------------
shards = B.plan_shards("2016-01", "2026-07")
print(f"planned {len(shards)} monthly shards: {shards[0].shard_id} .. {shards[-1].shard_id}")
if len(shards) != 127:  # 2016-01..2026-07 inclusive = 10 full years*12 + 7 = 127
    fails.append(f"expected 127 monthly shards, got {len(shards)}")
if shards[0].shard_id != "backfill/2016-01" or shards[-1].shard_id != "backfill/2026-07":
    fails.append("shard range wrong")

# a shard's items (content-addressed sha256 ids)
items = [{"id": "sha256:" + hashlib.sha256(f"doc-{i}".encode()).hexdigest()[:16], "n": i} for i in range(10)]

# --- 1) same shard run 3 times = NO duplicates ----------------------------------------------
applied = set()
runs = []
for r in range(3):
    cur = B.ShardCursor(shard_id="backfill/2016-01", year=2016, month=1)  # fresh cursor each run
    cur, newly = B.process_shard(cur, items, applied)
    runs.append((cur.status, cur.processed, len(newly)))
    print(f"run {r+1}: status={cur.status} cursor_processed={cur.processed} newly_applied={len(newly)} | total_applied={len(applied)}")
if len(applied) != 10:
    fails.append(f"applied set has {len(applied)} != 10 unique (duplicates or loss)")
if runs[0][2] != 10:
    fails.append("run 1 did not apply all 10")
if runs[1][2] != 0 or runs[2][2] != 0:
    fails.append("runs 2/3 applied duplicates (should be 0 newly)")
# no id applied twice: applied is a set so uniqueness is structural; also verify count of distinct == inputs
if len(applied) != len({it["id"] for it in items}):
    fails.append("applied != distinct input ids")

# --- 2) interrupt mid-shard -> resume from last confirmed checkpoint -------------------------
applied2 = set()
cur2 = B.ShardCursor(shard_id="backfill/2020-06", year=2020, month=6)
cur2, newly_a = B.process_shard(cur2, items, applied2, stop_after=4)   # interrupt after 4
ckpt = cur2.last_confirmed_id
print(f"\ninterrupted: applied {len(newly_a)} status={cur2.status} checkpoint={ckpt[:20]}...")
if cur2.status != "in_progress" or len(applied2) != 4:
    fails.append(f"interruption did not stop mid-shard (status {cur2.status}, applied {len(applied2)})")
# resume from the SAME cursor -> continues, no redo, no skip
cur2, newly_b = B.resume(cur2, items, applied2)
print(f"resumed: applied {len(newly_b)} more status={cur2.status} total_applied={len(applied2)} processed={cur2.processed}")
if cur2.status != "done":
    fails.append("resume did not complete the shard")
if len(applied2) != 10:
    fails.append(f"after resume applied {len(applied2)} != 10 (redo/skip/dup)")
if len(newly_a) + len(newly_b) != 10:
    fails.append(f"resume redid or skipped items ({len(newly_a)}+{len(newly_b)} != 10)")
# the resume must have started strictly after the checkpoint
if any(iid <= ckpt for iid in newly_b):
    fails.append("resume reprocessed items at or before the checkpoint")

# --- checkpoint schema + resume path present ------------------------------------------------
if "cn_backfill_shards" not in B.CHECKPOINT_SCHEMA or "last_confirmed_id" not in B.CHECKPOINT_SCHEMA:
    fails.append("checkpoint schema missing shard/cursor columns")
print("\ncheckpoint schema: cn_backfill_shards with last_confirmed_id + status index; resume() path present")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
