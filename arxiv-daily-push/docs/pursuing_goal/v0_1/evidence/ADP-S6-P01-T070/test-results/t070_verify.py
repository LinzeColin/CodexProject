#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T070 acceptance: Dataset Snapshot + observed_at leakage guard.

Acceptance (TASK_INDEX row 70): 注入未来文档会使测试失败；任何预测可重建其当时数据集。
  (injecting a future document makes the test fail; any prediction can rebuild its as-of dataset.)

Deterministic. Re-derives from the TOOL (dataset_snapshot) + fixtures -- never trusts the report.
Negative controls prove discrimination: a clean snapshot passes the leakage guard while any injected
future doc trips it; and the guard is keyed on observed_at (a backfilled 2016 doc with doc_date < as_of
but observed in 2026 is excluded), not doc_date.
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import dataset_snapshot as DS

T070 = V01 / "evidence" / "ADP-S6-P01-T070"
spec = importlib.util.spec_from_file_location("bds", str(T070 / "build_dataset_snapshot.py"))
bds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bds)

fails = []
AS_OF = "2018-01-01"
snap = DS.snapshot(bds.CORPUS, AS_OF)
ids = [d["canonical_id"] for d in snap["docs"]]
print("as-of 2018 snapshot:", ids)

# =============================================================== 1) 注入未来文档会使测试失败
# a clean as-of snapshot must PASS the leakage guard
if not DS.assert_no_leakage(snap, AS_OF):
    fails.append("a clean as-of snapshot failed the leakage guard")
# INJECT a future-observed doc (c, observed 2019-02-03 > 2018) -> guard must RAISE
leaked = {"as_of": AS_OF, "docs": snap["docs"] + [next(d for d in bds.CORPUS if d["canonical_id"] == "c")]}
try:
    DS.assert_no_leakage(leaked, AS_OF)
    fails.append("injecting a future document did NOT trip the leakage guard")
except DS.LeakageError:
    pass
# INJECT the backfilled-2016 doc (observed 2026) -> also a leak despite its 2016 doc_date
leaked2 = {"as_of": AS_OF, "docs": snap["docs"] + [next(d for d in bds.CORPUS if d["canonical_id"] == "backfill16")]}
try:
    DS.assert_no_leakage(leaked2, AS_OF)
    fails.append("injecting a 2026-backfilled doc did NOT trip the leakage guard")
except DS.LeakageError:
    pass
# a doc with a MISSING observed_at is also a leak (unverifiable knowledge time)
try:
    DS.assert_no_leakage({"docs": [{"canonical_id": "x", "doc_date": "2017-01-01"}]}, AS_OF)
    fails.append("a doc with no observed_at was not treated as a leak")
except DS.LeakageError:
    pass
print("leakage guard: clean passes; injecting future / backfilled / no-observed_at all RAISE")

# =============================================================== observed_at-based, NOT doc_date
# the backfilled 2016 doc has doc_date 2016-05-01 (< as_of) but observed_at 2026 -> excluded.
bf = next(d for d in bds.CORPUS if d["canonical_id"] == "backfill16")
if not (bf["doc_date"] < AS_OF):
    fails.append("control setup broken: backfill doc_date should be before as_of")
if "backfill16" in ids:
    fails.append("a 2026-backfilled 2016 doc leaked into the 2018 snapshot (keyed on doc_date not observed_at)")
if ids != ["a", "b"]:
    fails.append(f"snapshot should be exactly the docs observed by 2018 (a,b), got {ids}")
print(f"observed_at-based: backfilled 2016 doc (doc_date {bf['doc_date']} but observed {bf['observed_at']}) excluded")

# =============================================================== 2) 任何预测可重建其当时数据集
rebuilt = DS.rebuild_for_prediction(bds.CORPUS, bds.PREDICTION)
if rebuilt["snapshot_id"] != snap["snapshot_id"]:
    fails.append("rebuild_for_prediction does not reproduce the as-of snapshot")
# reproducible: two rebuilds are byte-identical
if DS.rebuild_for_prediction(bds.CORPUS, bds.PREDICTION)["snapshot_id"] != rebuilt["snapshot_id"]:
    fails.append("snapshot rebuild is not reproducible")
# the rebuilt dataset itself passes the leakage guard for its own origin
if not DS.assert_no_leakage(rebuilt, bds.PREDICTION["origin_date"]):
    fails.append("rebuilt dataset does not pass its own leakage guard")
# determinism: same as_of -> same snapshot_id regardless of input order
shuffled = list(reversed(bds.CORPUS))
if DS.snapshot(shuffled, AS_OF)["snapshot_id"] != snap["snapshot_id"]:
    fails.append("snapshot_id is not order-independent (non-deterministic)")
# a different as_of yields a different dataset (adds doc c observed 2019)
later = DS.snapshot(bds.CORPUS, "2019-06-01")
if [d["canonical_id"] for d in later["docs"]] != ["a", "b", "c"] or later["snapshot_id"] == snap["snapshot_id"]:
    fails.append("a later as_of did not expand the dataset as expected")
print(f"rebuildable: rebuild==snapshot ({snap['snapshot_id']}), reproducible, order-independent; later as_of adds 'c'")

# snapshot_id is a CONTENT fingerprint: two docs with the same canonical_id + observed_at but different
# content (and no content_hash/version) must NOT collide to the same id.
d_a = [{"canonical_id": "z", "observed_at": "2017-01-01", "body": "text A"}]
d_b = [{"canonical_id": "z", "observed_at": "2017-01-01", "body": "text B"}]
if DS.snapshot_id(d_a) == DS.snapshot_id(d_b):
    fails.append("two docs with different content collided to the same snapshot_id (id not content-sensitive)")
# a changed content_hash also changes the id
ch1 = [{"canonical_id": "z", "observed_at": "2017-01-01", "content_hash": "h1"}]
ch2 = [{"canonical_id": "z", "observed_at": "2017-01-01", "content_hash": "h2"}]
if DS.snapshot_id(ch1) == DS.snapshot_id(ch2):
    fails.append("a changed content_hash did not change the snapshot_id")
print("snapshot_id: content-sensitive (different body / content_hash -> different id; no collision)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
