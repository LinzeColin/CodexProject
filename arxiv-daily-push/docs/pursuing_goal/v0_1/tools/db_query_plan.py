#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T083 -- D1 (SQLite) query-plan + rows-scanned + p95 latency proof for the T083 perf indexes.

Acceptance (TASK_INDEX row 83, the measurable part): D1 rows scanned 和 p95 查询下降 (D1 rows scanned and p95
query time drop); 无布局跳动回归 (no layout-shift regression).

D1 is SQLite under the hood, so the local SQLite query planner is representative. This builds two identical
databases -- one on the PRE-T083 schema (3 indexes) and one on the T083 schema (5 added indexes) -- fills them
with the SAME synthetic rows, and for each hot query compares:
  * EXPLAIN QUERY PLAN: pre = SCAN <table> (+ USE TEMP B-TREE FOR ORDER BY) = scans the whole table;
    post = SEARCH <table> USING INDEX ... = reads only the LIMIT rows in index order.
  * rows-scanned SCALING: the recency query is timed at growing table sizes; without the index the time grows
    with N (full scan), with the index it stays ~flat (O(LIMIT)) -- a numeric demonstration that rows scanned
    dropped from O(N) to O(LIMIT).
  * p95 wall-clock over many runs at a large N.

Deterministic structure (the plans + the scaling shape are stable); wall-clock numbers vary but the ratio is
reported. No network. Row values are derived from indices (no randomness) so the two DBs are identical.
"""
import pathlib
import re
import sqlite3
import time

V01 = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_NEW = V01.parents[3] / "arxiv-daily-push/deploy/cloudflare/schema_cloud.sql"
SCHEMA_PRE = V01 / "evidence/ADP-S7-P03-T083/pre_fix_schema.sql"

# the hot queries (verbatim shape from worker_cloud.js -- now with the T083 total-order tie-breaker `, id DESC`)
QUERIES = {
    "today_recency": ("SELECT id,title,url,board_id FROM cn_items ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 8", lambda i: ()),
    "board_recency": ("SELECT * FROM cn_items WHERE board_id=? ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 24", lambda i: (f"board{i % 5}",)),
    "lesson_latest": ("SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1", lambda i: (f"item{i}",)),
    "review_due": ("SELECT * FROM cn_reviews WHERE due_at<=? AND reps>0 ORDER BY due_at ASC LIMIT 1", lambda i: ("2026-07-18",)),
    "grade_history": ("SELECT at FROM cn_events WHERE kind='grade' ORDER BY at DESC LIMIT 400", lambda i: ()),
}


def _build(schema_path, n_items):
    db = sqlite3.connect(":memory:")
    db.executescript(schema_path.read_text(encoding="utf-8"))
    cur = db.cursor()
    # deterministic synthetic rows (values derived from index i, so PRE and POST DBs are identical).
    # IMPORTANT: published_at and fetched_at share the SAME date namespace, so CROSS-FAMILY ties are possible
    # -- a row whose recency comes from published_at can tie exactly with one whose recency comes from
    # fetched_at (the case the tie-breaker must make deterministic). Half the rows are recency-via-published,
    # half recency-via-fetched, all mapping to the same set of day strings.
    def day(i):
        return f"2026-{((i // 2) % 12) + 1:02d}-{((i // 2) % 15) + 1:02d}"   # pairs 2k,2k+1 share a day
    rows = []
    for i in range(n_items):
        d = day(i)
        if i % 2:      # odd: recency via published_at (fetched_at is old) -> ties with its even pair via fetched
            pub, fet = d, "2020-01-01"
        else:          # even: recency via fetched_at (published NULL)
            pub, fet = None, d
        rows.append((f"item{i:06d}", f"board{i%5}", f"src{i%20}", "paper", f"title {i}", f"http://x/{i}", "", "", "",
                     pub, fet, "2026-01-01"))
    cur.executemany("INSERT INTO cn_items (id,board_id,source_id,kind,title,url,summary,categories,authors,published_at,fetched_at,first_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    cur.executemany("INSERT INTO cn_lessons (id,as_of_date,item_id,doc_title,url,sections_json,generator,template_ver,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    [(f"les{i}", "2026-07-01", f"item{i}", "t", "u", "[]", "g", "v1", f"2026-07-{(i%28)+1:02d}") for i in range(n_items)])
    cur.executemany("INSERT INTO cn_reviews (item_id,due_at,stability,difficulty,reps,lapses,state,last_review,last_grade,evidence_state) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [(f"item{i}", f"2026-{(i%12)+1:02d}-{(i%28)+1:02d}", 1.0, 5.0, (i % 4), 0, 1, "2026-07-01", 3, "复习中") for i in range(n_items)])
    cur.executemany("INSERT INTO cn_events (item_id,kind,grade,at,dedup_key) VALUES (?,?,?,?,?)",
                    [(f"item{i}", ("grade" if i % 2 else "reveal"), 3, f"2026-07-{(i%28)+1:02d}T00:00:00", f"item{i}:d{i}") for i in range(n_items)])
    db.commit()
    return db


def _plan(db, sql, binds):
    rows = db.execute("EXPLAIN QUERY PLAN " + sql, binds).fetchall()
    txt = " | ".join(r[-1] for r in rows)
    return {"uses_index": "USING INDEX" in txt or "USING COVERING INDEX" in txt,
            "temp_btree": "TEMP B-TREE" in txt, "full_scan": bool(re.search(r"\bSCAN\b", txt)) and "USING INDEX" not in txt,
            "plan": txt}


def _p95_ms(db, sql, bindf, runs=300):
    ts = []
    for i in range(runs):
        t = time.perf_counter()
        db.execute(sql, bindf(i)).fetchall()
        ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    return {"median_ms": round(ts[len(ts) // 2], 4), "p95_ms": round(ts[int(len(ts) * 0.95)], 4)}


def compare(n_items=20000):
    pre = _build(SCHEMA_PRE, n_items)
    post = _build(SCHEMA_NEW, n_items)
    out = {}
    for name, (sql, bindf) in QUERIES.items():
        b = bindf(0)
        pre_plan, post_plan = _plan(pre, sql, b), _plan(post, sql, b)
        out[name] = {
            "pre": {"plan": pre_plan, **_p95_ms(pre, sql, bindf)},
            "post": {"plan": post_plan, **_p95_ms(post, sql, bindf)},
            "improved_plan": (pre_plan["full_scan"] or pre_plan["temp_btree"]) and post_plan["uses_index"] and not post_plan["temp_btree"],
        }
    pre.close(); post.close()
    return out


def determinism(n_items=4000):
    """Prove the T083 tie-breaker (`, id DESC`) makes the recency queries a DETERMINISTIC TOTAL ORDER even on
    CROSS-FAMILY ties (rows tying on COALESCE(published_at,fetched_at) but disagreeing on which column is the
    source): the index-served result equals the same query forced to a full table scan, at every LIMIT/OFFSET
    -- so page membership + order are stable and OFFSET pagination never skips/repeats. Also checks the OLD
    (no-tiebreaker) query is NON-deterministic on the same data (the hole the tie-breaker closes)."""
    post = _build(SCHEMA_NEW, n_items)
    out = {"cross_family_ties_present": None, "new_query_deterministic": True, "offset_pages_disjoint": True,
           "old_query_nondeterministic_example": None}
    # confirm cross-family ties exist (a published-recency row shares a COALESCE day with a fetched-recency row)
    tie = post.execute("SELECT COUNT(*) FROM cn_items a JOIN cn_items b ON COALESCE(a.published_at,a.fetched_at)="
                       "COALESCE(b.published_at,b.fetched_at) AND a.published_at IS NOT NULL AND b.published_at IS NULL").fetchone()[0]
    out["cross_family_ties_present"] = tie > 0
    new_q = "SELECT id FROM cn_items ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ? OFFSET ?"
    # `NOT INDEXED` forces a GENUINE full table scan + temp-b-tree sort (an independent order oracle) rather
    # than a subquery SQLite would just flatten back onto the same index (which would be tautological).
    forced = "SELECT id FROM cn_items NOT INDEXED ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ? OFFSET ?"
    seen = set()
    for page in range(6):
        idx = [r[0] for r in post.execute(new_q, (25, page * 25)).fetchall()]
        scan = [r[0] for r in post.execute(forced, (25, page * 25)).fetchall()]
        if idx != scan:
            out["new_query_deterministic"] = False
        if seen & set(idx):
            out["offset_pages_disjoint"] = False       # a row repeated across pages -> broken pagination
        seen |= set(idx)
    # the OLD query (no tie-breaker) can diverge: compare its index plan vs forced-scan order on the ties
    old_q = "SELECT id FROM cn_items ORDER BY COALESCE(published_at,fetched_at) DESC LIMIT 25"
    old_forced = "SELECT id FROM cn_items NOT INDEXED ORDER BY COALESCE(published_at,fetched_at) DESC LIMIT 25"
    a = [r[0] for r in post.execute(old_q).fetchall()]
    b = [r[0] for r in post.execute(old_forced).fetchall()]
    out["old_query_nondeterministic_example"] = (a != b)
    post.close()
    return out


def tie_breaker_load_bearing(n_items=4000):
    """Prove the tie-breaker is LOAD-BEARING (not vacuous): the board query WITHOUT it changes result
    (membership+order) between the pre-T083 schema and the T083 schema -- the exact plan-dependent divergence
    the review found -- while WITH it the result is identical across schemas (plan-independent/deterministic)."""
    pre, post = _build(SCHEMA_PRE, n_items), _build(SCHEMA_NEW, n_items)
    no_tb = "SELECT id FROM cn_items WHERE board_id='board1' ORDER BY COALESCE(published_at,fetched_at) DESC LIMIT 25"
    tb = "SELECT id FROM cn_items WHERE board_id='board1' ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 25"
    npre, npost = [r[0] for r in pre.execute(no_tb).fetchall()], [r[0] for r in post.execute(no_tb).fetchall()]
    tpre, tpost = [r[0] for r in pre.execute(tb).fetchall()], [r[0] for r in post.execute(tb).fetchall()]
    pre.close(); post.close()
    return {"no_tiebreaker_schema_dependent": (npre != npost),   # the hole: result changes with the index/plan
            "tiebreaker_schema_independent": (tpre == tpost)}    # the fix: deterministic regardless of plan


def recency_scaling(sizes=(5000, 20000, 50000)):
    """rows-scanned demonstration: without the index the recency query time grows with N (full scan);
    with it, ~flat (reads only LIMIT rows in index order)."""
    sql = QUERIES["today_recency"][0]
    out = {}
    for n in sizes:
        pre = _build(SCHEMA_PRE, n); post = _build(SCHEMA_NEW, n)
        out[n] = {"pre_p95_ms": _p95_ms(pre, sql, lambda i: (), runs=120)["p95_ms"],
                  "post_p95_ms": _p95_ms(post, sql, lambda i: (), runs=120)["p95_ms"]}
        pre.close(); post.close()
    return out
