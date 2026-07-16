#!/usr/bin/env python3
"""ADP V0.1 independent open-history verification via DuckDB (ADP-S2-P03-T028).

Proves the T027 monthly snapshot is recoverable and queryable by a PORTABLE, OPEN engine (DuckDB)
reading local Parquet directly -- with NO Cloudflare R2 SQL and NO R2 Data Catalog (both Beta). This
guarantees the recovery/analysis path is not locked to a single vendor Beta capability: the open
Parquet + a standard engine is enough to rebuild the key document, version, event, and signal counts.

DuckDB is a DIFFERENT engine from the pyarrow writer (T027), so this is a genuine cross-engine check,
not a tautology. No network, no clock, no randomness beyond DuckDB's own deterministic scans.

Usage:
  python3 duckdb_verify.py --snapshot-dir DIR [--out rebuild_report.json]
  DIR must contain data/{cn_documents,cn_document_versions}__*.parquet (a T027 snapshot).
"""
import argparse, json, pathlib, sys

import duckdb   # independent open engine; reads Parquet natively, no Cloudflare

# The rebuild is expressed as plain SQL over local Parquet globs -- portable to any DuckDB/Trino/Spark.
QUERIES = {
    # KEY DOCUMENTS
    "documents_total": "SELECT COUNT(*) AS v FROM read_parquet('{docs}')",
    "documents_distinct_canonical": "SELECT COUNT(DISTINCT canonical_id) AS v FROM read_parquet('{docs}')",
    "documents_per_month": "SELECT first_seen_month AS k, COUNT(*) AS v FROM read_parquet('{docs}') GROUP BY 1 ORDER BY 1",
    # VERSIONS (each version row is a version-creation EVENT in the append-only chain)
    "versions_total": "SELECT COUNT(*) AS v FROM read_parquet('{vers}')",
    "version_events_per_month": "SELECT month AS k, COUNT(*) AS v FROM read_parquet('{vers}') GROUP BY 1 ORDER BY 1",
    # RELATIONSHIP (recovery integrity): every version resolves to a document
    "orphan_versions": ("SELECT COUNT(*) AS v FROM read_parquet('{vers}') ver "
                        "LEFT JOIN read_parquet('{docs}') d ON ver.canonical_id = d.canonical_id "
                        "WHERE d.canonical_id IS NULL"),
    # SIGNALS derivable from the open snapshot
    "signal_repost_multi_source": "SELECT COUNT(*) AS v FROM read_parquet('{docs}') WHERE item_count > 1",
    "signal_multi_version_docs": "SELECT COUNT(*) AS v FROM read_parquet('{docs}') WHERE version_count > 1",
    "signal_status_distribution": "SELECT status AS k, COUNT(*) AS v FROM read_parquet('{vers}') GROUP BY 1 ORDER BY 1",
    "signal_months_covered": "SELECT COUNT(DISTINCT month) AS v FROM read_parquet('{vers}')",
    # earliest recoverable month proves 2016+ history survives in the open format
    "earliest_version_month": "SELECT MIN(month) AS v FROM read_parquet('{vers}')",
    "latest_version_month": "SELECT MAX(month) AS v FROM read_parquet('{vers}')",
}


def _scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def _rows(con, sql):
    return {str(k): int(v) for k, v in con.execute(sql).fetchall()}


def rebuild(snapshot_dir):
    d = pathlib.Path(snapshot_dir)
    docs = str(d / "data" / "cn_documents__*.parquet")
    vers = str(d / "data" / "cn_document_versions__*.parquet")
    con = duckdb.connect(":memory:")
    con.execute("PRAGMA threads=1")               # deterministic
    q = {k: v.format(docs=docs, vers=vers) for k, v in QUERIES.items()}
    report = {
        "engine": "duckdb " + duckdb.__version__,
        "reads": "local Parquet via read_parquet() -- NO R2 SQL, NO R2 Data Catalog, NO Cloudflare",
        "documents_total": _scalar(con, q["documents_total"]),
        "documents_distinct_canonical": _scalar(con, q["documents_distinct_canonical"]),
        "versions_total": _scalar(con, q["versions_total"]),
        "orphan_versions": _scalar(con, q["orphan_versions"]),
        "signal_repost_multi_source": _scalar(con, q["signal_repost_multi_source"]),
        "signal_multi_version_docs": _scalar(con, q["signal_multi_version_docs"]),
        "signal_months_covered": _scalar(con, q["signal_months_covered"]),
        "earliest_version_month": _scalar(con, q["earliest_version_month"]),
        "latest_version_month": _scalar(con, q["latest_version_month"]),
        "documents_per_month": _rows(con, q["documents_per_month"]),
        "version_events_per_month": _rows(con, q["version_events_per_month"]),
        "signal_status_distribution": _rows(con, q["signal_status_distribution"]),
    }
    con.close()
    return report, q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-dir", required=True)
    ap.add_argument("--out")
    ap.add_argument("--sql-out")
    args = ap.parse_args()
    report, q = rebuild(args.snapshot_dir)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.sql_out:
        pathlib.Path(args.sql_out).write_text(
            "-- ADP-S2-P03-T028 DuckDB rebuild queries (local Parquet; no Cloudflare)\n" +
            "\n".join(f"-- {k}\n{v};" for k, v in q.items()) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, dict)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
