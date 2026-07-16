#!/usr/bin/env python3
"""ADP-S2-P03-T027 acceptance: Monthly open-format snapshot + manifest.

Acceptance (TASK_INDEX): 同一 logical snapshot 可重复生成；D1 抽样和 Parquet 行/关系一致。
Uses the REAL 500-item D1 sample. Deterministic (no clock/random). Anchors reproducibility on the
format-independent logical_hash; also checks physical parquet bytes are stable within this engine.
"""
import sys, json, pathlib, hashlib
TOOLS = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1/tools")
SAMPLE = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t020")
OUT = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t027_snap")
sys.path.insert(0, str(TOOLS))
import snapshot_writer as S  # noqa: E402

items = json.loads((SAMPLE / "items_500.json").read_text(encoding="utf-8"))
fs = json.loads((SAMPLE / "fs_500.json").read_text(encoding="utf-8"))
fails = []

# --- build twice into two dirs (reproducibility) -------------------------------------------
m1, t1 = S.build_snapshot(items, fs, OUT / "a", source_ref="D1 sample cn_items (500)")
m2, t2 = S.build_snapshot(items, fs, OUT / "b", source_ref="D1 sample cn_items (500)")
print("format:", m1["format"], "| engine:", m1["engine"])
print("snapshot_id run A:", m1["snapshot_id"][:26])
print("snapshot_id run B:", m2["snapshot_id"][:26])
print("totals:", m1["totals"]["cn_documents"], "docs /", m1["totals"]["cn_document_versions"],
      "versions /", len(m1["totals"]["months"]), "months /", m1["totals"]["partitions"], "partitions")

if m1["snapshot_id"] != m2["snapshot_id"]:
    fails.append("snapshot_id differs across runs (not reproducible)")
lh1 = {(p["table"], p["month"]): p["logical_hash"] for p in m1["partitions"]}
lh2 = {(p["table"], p["month"]): p["logical_hash"] for p in m2["partitions"]}
if lh1 != lh2:
    fails.append("per-partition logical_hash differs across runs")
ph1 = {(p["table"], p["month"]): p["physical_sha256"] for p in m1["partitions"]}
ph2 = {(p["table"], p["month"]): p["physical_sha256"] for p in m2["partitions"]}
if ph1 != ph2:
    fails.append("physical parquet bytes not stable within engine (in-env)")
print("reproducible: snapshot_id equal =", m1["snapshot_id"] == m2["snapshot_id"],
      "| logical_hash equal =", lh1 == lh2, "| physical bytes equal =", ph1 == ph2)

# --- D1 sample <-> Parquet rows/relationships consistent -----------------------------------
# recompute the logical tables straight from the D1 sample (ground truth)
logical = S.build_logical_tables(items, fs)
gt_docs = {d["canonical_id"] for d in logical["cn_documents"]}
gt_ver_rows = len(logical["cn_document_versions"])
gt_doc_rows = len(logical["cn_documents"])

# read every physical partition back and reassemble
def read_partition(path, table, sv):
    cols = [c for c, _t in S.SCHEMA_REGISTRY[table][sv]]
    if m1["format"] == "parquet":
        import pyarrow.parquet as pq
        tb = pq.read_table(path)
        d = tb.to_pydict()
        return [{c: d[c][i] for c in cols} for i in range(tb.num_rows)]
    return [json.loads(l) for l in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

base = OUT / "a"
read_docs, read_vers = [], []
month_ok = True
for p in m1["partitions"]:
    rows = read_partition(base / p["path"], p["table"], p["schema_version"])
    if len(rows) != p["rows"]:
        fails.append(f"partition {p['path']} row count {len(rows)} != manifest {p['rows']}")
    mf = "first_seen_month" if p["table"] == "cn_documents" else "month"
    if any(r[mf] != p["month"] for r in rows):
        month_ok = False
    (read_docs if p["table"] == "cn_documents" else read_vers).extend(rows)

if len(read_docs) != gt_doc_rows:
    fails.append(f"parquet cn_documents rows {len(read_docs)} != D1-sample-derived {gt_doc_rows}")
if len(read_vers) != gt_ver_rows:
    fails.append(f"parquet cn_document_versions rows {len(read_vers)} != D1-sample-derived {gt_ver_rows}")
read_doc_ids = {d["canonical_id"] for d in read_docs}
if read_doc_ids != gt_docs:
    fails.append("parquet document canonical_ids != D1-sample-derived set")
orphans = [v for v in read_vers if v["canonical_id"] not in read_doc_ids]
if orphans:
    fails.append(f"{len(orphans)} version rows reference a canonical_id absent from documents (relationship broken)")
if not month_ok:
    fails.append("a row landed in the wrong month partition")
print("\nD1<->Parquet: doc rows", len(read_docs), "== gt", gt_doc_rows,
      "| version rows", len(read_vers), "== gt", gt_ver_rows,
      "| orphan versions", len(orphans), "| month partitioning ok", month_ok)

# --- schema evolution: add a nullable column, old partition still reads, v1 hash stable -----
v1_docs_part = next(p for p in m1["partitions"] if p["table"] == "cn_documents")
v1_hash_before = v1_docs_part["logical_hash"]
new_ver = S.evolve_schema("cn_documents", "authority", "string")
old_rows = read_partition(base / v1_docs_part["path"], "cn_documents", "v1")   # old partition is schema v1
# read old v1 rows under the evolved v2 schema -> new column null-filled, back-compatible
v2_cols = [c for c, _t in S.SCHEMA_REGISTRY["cn_documents"][new_ver]]
evolved_view = [{c: r.get(c) for c in v2_cols} for r in old_rows]
back_compat = all(r["authority"] is None for r in evolved_view) and all("canonical_id" in r for r in evolved_view)
v1_hash_after = S.logical_hash("cn_documents", old_rows, "v1")                 # v1 hash must be unchanged
print("\nschema evolution: v1 ->", new_ver, "| old partition reads under v2 (authority null-filled) =", back_compat,
      "| v1 logical_hash stable =", (v1_hash_before == v1_hash_after))
if not back_compat:
    fails.append("evolved schema not backward compatible (old partition unreadable / column not null-filled)")
if v1_hash_before != v1_hash_after:
    fails.append("v1 partition logical_hash changed after schema evolution")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
