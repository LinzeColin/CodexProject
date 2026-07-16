#!/usr/bin/env python3
"""ADP V0.1 Monthly open-format snapshot writer + manifest (ADP-S2-P03-T027).

Turns the CanonicalDocument identity (T024) and the DocumentVersion append-only chain (T026)
into a MONTHLY-PARTITIONED, open columnar snapshot for large-scale historical analysis,
recovery, and backtestable prediction -- without touching production D1/R2 (NOT_DEPLOYED).

Two logical tables, each partitioned by month (YYYY-MM):
  cn_documents          -- one row per canonical document (first_seen month)
  cn_document_versions  -- one row per version in the append-only chain (version's doc month)

Reproducibility is anchored on a format-independent LOGICAL HASH of the canonically-sorted,
typed rows -- NOT on the physical bytes, because a Parquet stream embeds the writer's version
string (created_by), so byte-equality only holds within one engine version. The manifest records
BOTH the version-independent logical_hash and the environment-specific parquet_sha256.

Physical format: real Apache Parquet via pyarrow when available (compression none, statistics off,
version 2.6 -> byte-deterministic in a fixed environment); otherwise a deterministic NDJSON
fallback (same logical_hash), so the snapshot is always reproducible and analysis-friendly.

No network, no clock, no randomness. Usage:
  python3 snapshot_writer.py --items items.json --factsheets fs.json --out-dir OUT [--fallback ndjson]
"""
import argparse, hashlib, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import canonicalize as C          # T024
import version_engine as V        # T026

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    _PARQUET = True
    _ENGINE = "pyarrow " + pa.__version__
except Exception:                 # pragma: no cover - environment dependent
    _PARQUET = False
    _ENGINE = "ndjson-fallback"

# --- schema registry (versioned; adding a NULLABLE column bumps the version, back-compatible) ---
SCHEMA_REGISTRY = {
    "cn_documents": {
        "v1": [("canonical_id", "string"), ("title_norm", "string"), ("sources_json", "string"),
               ("item_count", "int64"), ("version_count", "int64"), ("first_seen_month", "string")],
    },
    "cn_document_versions": {
        "v1": [("version_id", "string"), ("canonical_id", "string"), ("version_no", "int64"),
               ("content_hash", "string"), ("status", "string"), ("doc_date", "string"), ("month", "string")],
    },
}
CURRENT_SCHEMA = {"cn_documents": "v1", "cn_document_versions": "v1"}
SNAPSHOT_SPEC_VERSION = "adp.snapshot.v0_1"


def _month(date_str):
    return (date_str or "")[:7] or "unknown"


def build_logical_tables(items, factsheets):
    """Derive the two typed logical tables from a D1 sample, via T024 identity + T026 versioning."""
    canon = C.canonicalize(items, factsheets)
    # map canonical_id -> its member items (in the same order canonicalize assigned)
    fs_by_id = {f["item_id"]: f for f in factsheets}
    members = {}
    for it in items:
        fs = fs_by_id.get(it.get("id"), {"common": {}})
        cid, _rev = C.canonical_id(fs, it)
        members.setdefault(cid, []).append(it)

    documents, versions = [], []
    for doc in canon["documents"]:
        cid = doc["canonical_id"]
        its = sorted(members.get(cid, []), key=lambda x: ((x.get("published_at") or ""), str(x.get("id"))))
        # single pass: build the append-only version chain and record the month of each render that
        # actually created a version (a noise-only/dup render is skipped by V.ingest, T026).
        chain = []
        for it in its:
            render = {"canonical_id": cid, "body": it.get("summary") or it.get("title") or "",
                      "status": it.get("status") or "active",
                      "attachments": [{"name": "src", "sha256": V._sha(it.get("url") or str(it.get("id")))}],
                      "doc_date": (it.get("published_at") or "")[:10]}
            before = len(chain)
            chain, _act = V.ingest(chain, render)
            if len(chain) > before:                     # this render created a new version
                versions.append({
                    "version_id": f"{cid}#{chain[-1]['version_no']}", "canonical_id": cid,
                    "version_no": chain[-1]["version_no"], "content_hash": chain[-1]["content_hash"],
                    "status": chain[-1]["status"], "doc_date": chain[-1].get("doc_date") or "",
                    "month": _month(it.get("published_at")),
                })
        documents.append({
            "canonical_id": cid, "title_norm": doc["title_norm"],
            "sources_json": json.dumps(doc["sources"], ensure_ascii=False, sort_keys=True),
            "item_count": len(its), "version_count": len(chain),
            "first_seen_month": _month(its[0].get("published_at")) if its else "unknown",
        })
    return {"cn_documents": documents, "cn_document_versions": versions,
            "canonicalize_summary": canon["summary"]}


def _sort_key(table):
    return {"cn_documents": lambda r: r["canonical_id"],
            "cn_document_versions": lambda r: (r["canonical_id"], r["version_no"])}[table]


def logical_hash(table, rows, schema_version):
    """Format-independent hash over canonically-sorted, typed, column-ordered rows."""
    cols = [c for c, _t in SCHEMA_REGISTRY[table][schema_version]]
    ordered = [{c: r.get(c) for c in cols} for r in sorted(rows, key=_sort_key(table))]
    blob = json.dumps({"table": table, "schema_version": schema_version, "columns": cols, "rows": ordered},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _write_partition(table, rows, schema_version, path, fallback):
    cols = SCHEMA_REGISTRY[table][schema_version]
    ordered = sorted(rows, key=_sort_key(table))
    if _PARQUET and fallback != "ndjson":
        arrays = {c: pa.array([r.get(c) for r in ordered],
                              type=pa.string() if t == "string" else pa.int64())
                  for c, t in cols}
        tbl = pa.table(arrays, schema=pa.schema([(c, pa.string() if t == "string" else pa.int64()) for c, t in cols]))
        pq.write_table(tbl, path, compression="none", version="2.6", write_statistics=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            for r in ordered:
                f.write(json.dumps({c: r.get(c) for c, _t in cols}, ensure_ascii=False, sort_keys=True) + "\n")
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def build_snapshot(items, factsheets, out_dir, fallback="auto", source_ref="D1 sample (cn_items)"):
    out = pathlib.Path(out_dir)
    (out / "data").mkdir(parents=True, exist_ok=True)
    tables = build_logical_tables(items, factsheets)
    ext = "parquet" if (_PARQUET and fallback != "ndjson") else "ndjson"
    fmt = "parquet" if ext == "parquet" else "ndjson"
    partitions = []
    for table in ("cn_documents", "cn_document_versions"):
        sv = CURRENT_SCHEMA[table]
        month_field = "first_seen_month" if table == "cn_documents" else "month"
        by_month = {}
        for r in tables[table]:
            by_month.setdefault(r[month_field], []).append(r)
        for month in sorted(by_month):
            rows = by_month[month]
            relpath = f"data/{table}__{month}.{ext}"
            phash = _write_partition(table, rows, sv, out / relpath, fallback)
            partitions.append({
                "table": table, "month": month, "rows": len(rows), "schema_version": sv,
                "logical_hash": logical_hash(table, rows, sv), "path": relpath,
                "physical_sha256": "sha256:" + phash, "bytes": (out / relpath).stat().st_size,
            })
    snapshot_id = "sha256:" + hashlib.sha256(
        json.dumps([(p["table"], p["month"], p["logical_hash"]) for p in partitions],
                   ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    manifest = {
        "snapshot_spec_version": SNAPSHOT_SPEC_VERSION, "snapshot_id": snapshot_id,
        "format": fmt, "engine": _ENGINE, "generated_from": source_ref,
        "reproducibility": "logical_hash is format/engine independent; physical_sha256 is env-specific",
        "schemas": {t: {"schema_version": CURRENT_SCHEMA[t], "columns": SCHEMA_REGISTRY[t][CURRENT_SCHEMA[t]]}
                    for t in SCHEMA_REGISTRY},
        "totals": {"cn_documents": len(tables["cn_documents"]),
                   "cn_document_versions": len(tables["cn_document_versions"]),
                   "months": sorted({p["month"] for p in partitions}), "partitions": len(partitions)},
        "canonicalize_summary": tables["canonicalize_summary"],
        "partitions": partitions,
    }
    (out / "snapshot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest, tables


def evolve_schema(table, new_column, col_type="string"):
    """Schema evolution: append a NULLABLE column -> a new schema version, backward compatible.
    Old partitions keep their schema_version and remain readable; readers null-fill the new column."""
    versions = sorted(SCHEMA_REGISTRY[table])
    latest = versions[-1]
    new_ver = f"v{int(latest[1:]) + 1}"
    SCHEMA_REGISTRY[table][new_ver] = SCHEMA_REGISTRY[table][latest] + [(new_column, col_type)]
    return new_ver


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--factsheets", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--fallback", choices=["auto", "ndjson"], default="auto")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    fs = json.loads(pathlib.Path(args.factsheets).read_text(encoding="utf-8"))
    manifest, _ = build_snapshot(items, fs, args.out_dir, fallback=args.fallback)
    print(json.dumps({"snapshot_id": manifest["snapshot_id"], "format": manifest["format"],
                      "engine": manifest["engine"], "totals": manifest["totals"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
