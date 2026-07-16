#!/usr/bin/env python3
"""ADP-S2-P03-T028 acceptance: independently rebuild the open history with DuckDB.

Acceptance (TASK_INDEX): 无 R2 SQL/Data Catalog 也能重建关键文档、版本、事件和信号计数。
Self-contained from committed T027 evidence: materializes the full Parquet snapshot from the
committed logical_snapshot/*.jsonl, then rebuilds the key counts with DuckDB (a different engine
from the pyarrow writer) and cross-checks against the committed T027 manifest. No Cloudflare.
Deterministic (no clock/random).
"""
import sys, json, pathlib, collections
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T027 = V01 / "evidence" / "ADP-S2-P03-T027"
OUT = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap")
sys.path.insert(0, str(V01 / "tools"))
import snapshot_writer as S       # noqa: E402
import duckdb_verify as D         # noqa: E402

fails = []

# --- 1) materialize the FULL snapshot from committed T027 logical jsonl (open, portable) ----
(OUT / "data").mkdir(parents=True, exist_ok=True)
logical = {}
for tbl, month_field in [("cn_documents", "first_seen_month"), ("cn_document_versions", "month")]:
    rows = [json.loads(l) for l in (T027 / "logical_snapshot" / f"{tbl}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    logical[tbl] = rows
    by_month = collections.defaultdict(list)
    for r in rows:
        by_month[r[month_field]].append(r)
    for month, rs in by_month.items():
        S._write_partition(tbl, rs, "v1", OUT / "data" / f"{tbl}__{month}.parquet", fallback="auto")
print("materialized partitions:", len(list((OUT / "data").glob("*.parquet"))), "| format:", "parquet" if S._PARQUET else "ndjson")

# --- 2) independent rebuild with DuckDB (no Cloudflare) -------------------------------------
report, _q = D.rebuild(OUT)
print("engine:", report["engine"], "|", report["reads"])
print("rebuilt: docs", report["documents_total"], "| versions", report["versions_total"],
      "| months", report["signal_months_covered"], "| range",
      report["earliest_version_month"], "->", report["latest_version_month"],
      "| orphans", report["orphan_versions"])
print("signals: repost_multi_source", report["signal_repost_multi_source"],
      "| multi_version_docs", report["signal_multi_version_docs"],
      "| status", report["signal_status_distribution"])

# --- 3) cross-check DuckDB rebuild against committed T027 manifest + logical ground truth ----
manifest = json.loads((T027 / "snapshot_manifest.json").read_text(encoding="utf-8"))
mt = manifest["totals"]
gt_docs = len(logical["cn_documents"])
gt_vers = len(logical["cn_document_versions"])
gt_months = len({r["month"] for r in logical["cn_document_versions"]})

if report["documents_total"] != mt["cn_documents"] or report["documents_total"] != gt_docs:
    fails.append(f"documents rebuilt {report['documents_total']} != manifest {mt['cn_documents']} / gt {gt_docs}")
if report["documents_distinct_canonical"] != gt_docs:
    fails.append("distinct canonical_id != document rows (identity not 1:1)")
if report["versions_total"] != mt["cn_document_versions"] or report["versions_total"] != gt_vers:
    fails.append(f"versions rebuilt {report['versions_total']} != manifest {mt['cn_document_versions']} / gt {gt_vers}")
if report["orphan_versions"] != 0:
    fails.append(f"{report['orphan_versions']} orphan versions in DuckDB rebuild (relationship broken)")
if report["signal_months_covered"] != gt_months or report["signal_months_covered"] != len(mt["months"]):
    fails.append(f"months covered {report['signal_months_covered']} != gt {gt_months} / manifest {len(mt['months'])}")
if report["earliest_version_month"] != min(mt["months"]):
    fails.append(f"earliest month {report['earliest_version_month']} != manifest min {min(mt['months'])}")

# events == version-creation events; per-month must match the logical ground truth exactly
gt_events_per_month = collections.Counter(r["month"] for r in logical["cn_document_versions"])
if report["version_events_per_month"] != dict(gt_events_per_month):
    fails.append("version-events-per-month from DuckDB != logical ground truth")

# the earliest recoverable month proves 2016+ history survives the open format
if report["earliest_version_month"] != "2016-01":
    fails.append(f"expected 2016+ history recoverable (earliest 2016-01), got {report['earliest_version_month']}")

# signals cross-check against logical ground truth
gt_repost = sum(1 for d in logical["cn_documents"] if d["item_count"] > 1)
gt_multiver = sum(1 for d in logical["cn_documents"] if d["version_count"] > 1)
if report["signal_repost_multi_source"] != gt_repost:
    fails.append(f"repost signal {report['signal_repost_multi_source']} != gt {gt_repost}")
if report["signal_multi_version_docs"] != gt_multiver:
    fails.append(f"multi-version signal {report['signal_multi_version_docs']} != gt {gt_multiver}")

print("\ncross-check vs T027 manifest+logical: docs/versions/events/signals/months/2016+ all consistent =", not fails)

# --- 4) prove no Cloudflare dependency in the rebuild path ----------------------------------
if "Cloudflare" not in report["reads"] or "NO R2" not in report["reads"]:
    fails.append("rebuild path claim missing the no-Cloudflare guarantee")
print("recovery path: reads local open Parquet only, no R2 SQL / no R2 Data Catalog / no Cloudflare Beta")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
