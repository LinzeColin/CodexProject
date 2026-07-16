#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T083 acceptance: optimize D1 queries (indexes + a deterministic total-order tie-breaker) /
bundle / long lists / no layout-shift regression.

Acceptance (TASK_INDEX row 83): CWV 达标；D1 rows scanned 和 p95 查询下降；无布局跳动回归.

Deterministic. Re-derives from the TOOL (db_query_plan on the real schema) + the worker + the pre-T083 schema.
Load-bearing checks / negative controls:
  1. D1 rows scanned + p95 DROP: every hot query goes from SCAN/TEMP-B-TREE (full table) to an index-ordered
     SEARCH with NO temp b-tree; the pre-T083 schema (negative control) full-scans -- so the indexes are
     load-bearing. Recency scaling shows post-time FLAT while pre grows -> rows scanned O(N)->O(LIMIT).
  2. DETERMINISM (the T083 tie-breaker `, id DESC`, matching the retention prune query): on CROSS-FAMILY
     ties (rows tying on COALESCE(published_at,fetched_at) but disagreeing on the source column -- the exact
     case that made the earlier index change page membership), the index-served result equals the same query
     forced to a full scan, and OFFSET pages are disjoint -- so page membership + order are STABLE and
     pagination never skips/repeats. (The verifier's synthetic data now CONTAINS cross-family ties, closing
     the earlier blind spot where published_at (2016) and fetched_at (2026) were disjoint by construction.)
  3. 无布局跳动回归: the app is server-rendered (no async content load -> no CLS), and the six-theme
     visual/motion CONTRACT is byte-identical (the query change lives in page-body functions, not the hashed
     surface). recency order is monotonic (no higher-recency row is ever dropped/reordered).
CWV 达标 is NOT claimed (NOT_DEPLOYED; no field data; per the T081 rule).
"""
import json
import pathlib
import sqlite3
import subprocess
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import db_query_plan as Q

T083 = V01 / "evidence" / "ADP-S7-P03-T083"
REPO = V01.parents[3]
WORKER = REPO / "arxiv-daily-push/deploy/cloudflare/worker_cloud.js"

fails = []

# ============ 1) D1 rows scanned + p95 drop (every hot query, no temp b-tree) ============
cmp = Q.compare(20000)
for name, d in cmp.items():
    if not d["improved_plan"]:
        fails.append(f"query {name} plan did not improve: pre={d['pre']['plan']['plan']} post={d['post']['plan']['plan']}")
    if not (d["pre"]["plan"]["full_scan"] or d["pre"]["plan"]["temp_btree"]):
        fails.append(f"control broken: pre-T083 {name} did not full-scan/temp-sort: {d['pre']['plan']}")
    if not d["post"]["plan"]["uses_index"] or d["post"]["plan"]["temp_btree"]:
        fails.append(f"post {name} not cleanly index-served (temp b-tree?): {d['post']['plan']}")
    if not (d["post"]["p95_ms"] < d["pre"]["p95_ms"]):
        fails.append(f"post {name} p95 not lower: pre={d['pre']['p95_ms']} post={d['post']['p95_ms']}")
print("D1 plans (20k): " + "; ".join(f"{n}: SCAN/sort->index (no temp-btree) p95 {d['pre']['p95_ms']}->{d['post']['p95_ms']}ms"
                                     for n, d in cmp.items()))

scale = Q.recency_scaling((5000, 20000, 50000))
if not (scale[50000]["pre_p95_ms"] > scale[5000]["pre_p95_ms"] * 3 and scale[50000]["post_p95_ms"] < scale[5000]["pre_p95_ms"]):
    fails.append(f"scaling did not show O(N)->O(LIMIT): {scale}")
print(f"rows-scanned scaling: pre {scale[5000]['pre_p95_ms']}->{scale[50000]['pre_p95_ms']}ms (grows with N); "
      f"post flat ~{scale[50000]['post_p95_ms']}ms (O(N) full-scan -> O(LIMIT) index)")

# ============ 2) DETERMINISM on cross-family ties (the tie-breaker closes the earlier hole) ============
det = Q.determinism(4000)
if not det["cross_family_ties_present"]:
    fails.append("control broken: the synthetic data has NO cross-family ties -- the failure case is not exercised (blind spot)")
if not det["new_query_deterministic"]:
    fails.append("the tie-breaker query is NOT deterministic (index result != forced-scan on ties)")
if not det["offset_pages_disjoint"]:
    fails.append("OFFSET pagination repeats/skips a row (non-deterministic order)")
# the tie-breaker is LOAD-BEARING (not vacuous): WITHOUT it the board query result depends on the schema/plan
# (the reviewed hole); WITH it the result is identical across schemas (plan-independent).
lb = Q.tie_breaker_load_bearing(4000)
if not lb["no_tiebreaker_schema_dependent"]:
    fails.append("control broken: the no-tie-breaker query is NOT schema/plan-dependent here -- the "
                 "determinism check cannot demonstrate the tie-breaker is load-bearing")
if not lb["tiebreaker_schema_independent"]:
    fails.append("the tie-breaker query is NOT schema/plan-independent (fix incomplete)")
# every recency ORDER BY in the worker carries the total-order tie-breaker (, id DESC / , i.id DESC)
w = WORKER.read_text(encoding="utf-8")
import re
recency_orderbys = re.findall(r"ORDER BY COALESCE\([^)]*fetched_at\) DESC[^`'\"]*", w)
missing_tb = [o for o in recency_orderbys if "id DESC" not in o]
if missing_tb:
    fails.append(f"a recency ORDER BY lacks the total-order tie-breaker: {missing_tb[:1]}")
print(f"determinism: cross-family ties present={det['cross_family_ties_present']}; tie-breaker query is a "
      f"deterministic total order (index==forced-scan), OFFSET pages disjoint; all {len(recency_orderbys)} "
      f"recency ORDER BYs carry `, id DESC`")

# ============ 3) 无布局跳动回归: contract byte-identical + monotonic recency order ============
pre_src = subprocess.run(["git", "-C", str(REPO), "show", "origin/main:arxiv-daily-push/deploy/cloudflare/worker_cloud.js"],
                         capture_output=True, text=True, check=True).stdout
new_src = w
specific = sorted(c["element"] for c in VB.detect_regression(VB.asset_hashes(VB.extract_contract(pre_src)), new_src)["changes"]
                  if c["element"] not in ("master_visual", "contract_root"))
if specific:
    fails.append(f"the six-theme visual/motion contract changed (expected none -- query change is page-body): {specific}")
# recency order is monotonic non-increasing (no strictly-higher recency appears after a lower one)
post_db = Q._build(Q.SCHEMA_NEW, 3000)
rows = post_db.execute("SELECT COALESCE(published_at,fetched_at) r FROM cn_items ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 100").fetchall()
post_db.close()
if any(rows[i][0] < rows[i + 1][0] for i in range(len(rows) - 1)):
    fails.append("recency order is not monotonic non-increasing (a higher-recency row appears after a lower one)")
print("no layout-shift regression: server-rendered (no async -> no CLS); the six-theme visual/motion contract "
      "is byte-identical (query change is page-body, not hashed); recency order monotonic")

# ============ 4) long lists bounded + indexes idempotent/valid ============
GROWTH = ("cn_items", "cn_events")
ordered = [s for s in re.findall(r"SELECT [^`'\"]*?ORDER BY[^`'\"]*", w) if "OVER (" not in s and "OVER(" not in s]
unbounded = [s for s in ordered if any(f"FROM {t}" in s for t in GROWTH) and "LIMIT" not in s]
if unbounded:
    fails.append(f"an unbounded ORDER BY over a growth table exists: {unbounded[:1]}")
new_schema = Q.SCHEMA_NEW.read_text(encoding="utf-8")
for idx in ("idx_cn_items_recency", "idx_cn_items_board_recency", "idx_cn_lessons_item", "idx_cn_reviews_due", "idx_cn_events_kind_at"):
    if f"CREATE INDEX IF NOT EXISTS {idx}" not in new_schema:
        fails.append(f"index {idx} not added as CREATE INDEX IF NOT EXISTS")
if "COALESCE(published_at, fetched_at) DESC, id DESC" not in new_schema:
    fails.append("the recency index does not include the id tie-breaker (would reintroduce a temp b-tree)")
try:
    sqlite3.connect(":memory:").executescript(new_schema)
except Exception as e:
    fails.append(f"schema no longer valid SQL: {e}")
print("long lists bounded (growth-table ORDER BYs all LIMIT); 5 indexes idempotent+valid; recency index "
      "carries the id tie-breaker so the total order is fully index-served")

# ============ NOT_DEPLOYED ============
if "d1dfcb3b7447" not in w:
    fails.append("could not confirm the source build_id after the change")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: schema (5 indexes, incl. the id tie-breaker) + a total-order `, id DESC` on the recency display "
      "queries (matches the prune query) so page membership/order is deterministic and OFFSET pagination never "
      "skips/repeats. BUILD recomputed d1dfcb3b7447; NOT_DEPLOYED (indexes apply at deploy). CWV 达标 NOT "
      "claimed without field data (T081 rule).")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
