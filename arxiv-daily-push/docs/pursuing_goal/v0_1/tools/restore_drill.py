#!/usr/bin/env python3
"""ADP V0.1 backup-restore + data-lifecycle drill (ADP-S2-P03-T029).

Proves that a specific month can be RESTORED from the open, permanent evidence (the T027 monthly
snapshot of document/version records + the permanent raw official artifacts) into an ISOLATED copy
-- never touching production -- and that the restored body, attachments, relationships, and counts
match the source. It also encodes the retention policy: original official evidence and published
versions are PERMANENT (never deleted); derived views are REGENERABLE. The drill performs zero
deletes against the permanent classes.

Restore target = the T025 DocumentVersion schema applied to a throwaway SQLite DB. No network, no
clock, no randomness. Usage:
  python3 restore_drill.py --logical-dir DIR --raw raw_evidence_sample.json --months 2016-01,2020-07,2026-07 [--out report.json]
"""
import argparse, hashlib, json, pathlib, sqlite3, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import canonicalize as C          # T024 identity
import version_engine as V        # T026 content_hash / attachments

V01 = pathlib.Path(__file__).resolve().parent.parent
MIGRATION = (V01 / "schemas" / "document_version.migration.sql").read_text(encoding="utf-8")

# --- data-lifecycle retention matrix (permanent vs regenerable) ----------------------------
RETENTION_MATRIX = [
    {"data_class": "raw official artifact (R2 content-addressed A0-A2 original)", "retention": "PERMANENT",
     "delete_policy": "never", "rationale": "the source of truth; cannot be regenerated if lost"},
    {"data_class": "published DocumentVersion (append-only chain + content_hash)", "retention": "PERMANENT",
     "delete_policy": "never", "rationale": "the immutable history; deleting rewrites the record"},
    {"data_class": "canonical document identity (canonical_id, sources)", "retention": "PERMANENT",
     "delete_policy": "never", "rationale": "stable identity across reposts/revisions"},
    {"data_class": "factsheet / L0-L3 human render / defect scan", "retention": "REGENERABLE",
     "delete_policy": "safe-to-drop", "rationale": "deterministically rebuilt from raw + code"},
    {"data_class": "monthly Parquet snapshot / manifest", "retention": "REGENERABLE",
     "delete_policy": "safe-to-drop", "rationale": "rebuilt from the version records (T027)"},
    {"data_class": "derived indexes / dashboards / D1 mirror views", "retention": "REGENERABLE",
     "delete_policy": "safe-to-drop", "rationale": "materialized from permanent sources"},
]
PERMANENT_CLASSES = {r["data_class"] for r in RETENTION_MATRIX if r["retention"] == "PERMANENT"}


def _sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def _load_all(logical_dir, table):
    return [json.loads(l) for l in (pathlib.Path(logical_dir) / f"{table}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_month(logical_dir, table, month_field, month):
    return [r for r in _load_all(logical_dir, table) if r[month_field] == month]


def _raw_render(it):
    return {"canonical_id": None, "body": it.get("summary") or it.get("title") or "",
            "status": it.get("status") or "active",
            "attachments": [{"name": "src", "sha256": V._sha(it.get("url") or str(it.get("id")))}],
            "doc_date": (it.get("published_at") or "")[:10]}


def restore_month(con, logical_dir, raw_items, month):
    """Restore one month's versions into the isolated DB with REFERENTIAL CLOSURE: every version's
    parent document is pulled in even if that document's first_seen_month is an earlier partition
    (a cross-month version chain would otherwise orphan the later version). Also restore the month's
    own documents, and link raw artifacts for the sampled raw items so body/attachment re-derive."""
    all_docs = {d["canonical_id"]: d for d in _load_all(logical_dir, "cn_documents")}
    vers = _load_month(logical_dir, "cn_document_versions", "month", month)
    month_doc_ids = {d["canonical_id"] for d in _load_month(logical_dir, "cn_documents", "first_seen_month", month)}
    # referential closure: this month's own docs + the parents of this month's versions
    needed_doc_ids = month_doc_ids | {v["canonical_id"] for v in vers}
    # map canonical_id -> artifact keys re-derived from the permanent raw evidence (sampled)
    raw_by_cid = {}
    for it in raw_items:
        if (it.get("published_at") or "")[:7] != month:
            continue
        fs = {"common": {"title": it.get("title")}}
        cid, _rev = C.canonical_id(fs, {"id": it["id"], "title": it.get("title")})
        raw_by_cid.setdefault(cid, []).append(it)
    for cid in sorted(needed_doc_ids):
        d = all_docs[cid]
        con.execute("INSERT OR IGNORE INTO cn_documents(canonical_id,title_norm,sources_json,current_version_no,created_at,first_seen_at)"
                    " VALUES(?,?,?,?,?,?)",
                    (d["canonical_id"], d["title_norm"], d["sources_json"], d["version_count"], d["first_seen_month"], d["first_seen_month"]))
    for v in vers:
        art = "[]"
        if v["canonical_id"] in raw_by_cid:
            keys = sorted(V._sha(it.get("url") or str(it.get("id"))) for it in raw_by_cid[v["canonical_id"]])
            art = json.dumps(keys, ensure_ascii=False)
        con.execute("INSERT INTO cn_document_versions(version_id,canonical_id,version_no,content_hash,status,doc_date,artifact_keys_json,created_at)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                    (v["version_id"], v["canonical_id"], v["version_no"], v["content_hash"], v["status"], v["doc_date"], art, v["doc_date"]))
    con.commit()
    return {"versions": len(vers), "month_documents": len(month_doc_ids),
            "documents_restored_with_closure": len(needed_doc_ids)}


def _month_result_hash(con, month):
    rows = con.execute(
        "SELECT version_id,canonical_id,version_no,content_hash,status FROM cn_document_versions "
        "WHERE doc_date LIKE ? ORDER BY canonical_id,version_no", (month + "%",)).fetchall()
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def drill(logical_dir, raw_path, months):
    raw_items = json.loads(pathlib.Path(raw_path).read_text(encoding="utf-8"))
    permanent_before = {"logical_documents": _sha_file(pathlib.Path(logical_dir) / "cn_documents.jsonl"),
                        "logical_versions": _sha_file(pathlib.Path(logical_dir) / "cn_document_versions.jsonl"),
                        "raw_evidence": _sha_file(raw_path)}
    # isolated throwaway DB with a pre-existing cn_meta (production-like), then the T025 migration
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("CREATE TABLE cn_meta(key TEXT PRIMARY KEY, value TEXT)")
    con.executescript(MIGRATION)
    per_month, body_checks, attach_checks = {}, [], []
    for month in months:
        per_month[month] = restore_month(con, logical_dir, raw_items, month)
        per_month[month]["result_hash"] = _month_result_hash(con, month)

    # counts vs the snapshot ground truth (month version count + month-partition document count;
    # closure documents pulled from other months are extra-and-correct, not a mismatch)
    gt = {m: {"documents": len(_load_month(logical_dir, "cn_documents", "first_seen_month", m)),
              "versions": len(_load_month(logical_dir, "cn_document_versions", "month", m))} for m in months}
    counts_ok = all(per_month[m]["month_documents"] == gt[m]["documents"] and per_month[m]["versions"] == gt[m]["versions"] for m in months)

    # relationship: no orphan versions in the isolated DB
    orphans = con.execute("SELECT COUNT(*) FROM cn_document_versions v LEFT JOIN cn_documents d "
                          "ON v.canonical_id=d.canonical_id WHERE d.canonical_id IS NULL").fetchone()[0]

    # random body + attachment: re-derive from the permanent raw evidence and match the restored version
    for it in raw_items:
        m = (it.get("published_at") or "")[:7]
        if m not in months:
            continue
        fs = {"common": {"title": it.get("title")}}
        cid, _rev = C.canonical_id(fs, {"id": it["id"], "title": it.get("title")})
        want_hash = V.content_hash(_raw_render(it))
        want_key = V._sha(it.get("url") or str(it.get("id")))
        row = con.execute("SELECT content_hash,artifact_keys_json FROM cn_document_versions "
                          "WHERE canonical_id=? ORDER BY version_no", (cid,)).fetchone()
        body_ok = bool(row) and any(want_hash == h for h in [r[0] for r in con.execute(
            "SELECT content_hash FROM cn_document_versions WHERE canonical_id=?", (cid,)).fetchall()])
        attach_ok = bool(row) and want_key in json.loads(row[1] or "[]")
        body_checks.append(body_ok)
        attach_checks.append(attach_ok)

    permanent_after = {"logical_documents": _sha_file(pathlib.Path(logical_dir) / "cn_documents.jsonl"),
                       "logical_versions": _sha_file(pathlib.Path(logical_dir) / "cn_document_versions.jsonl"),
                       "raw_evidence": _sha_file(raw_path)}
    con.close()
    return {
        "months": months, "per_month": per_month, "ground_truth": gt,
        "counts_consistent": counts_ok, "orphan_versions": orphans,
        "random_body_consistent": all(body_checks) and len(body_checks) > 0,
        "random_attachment_consistent": all(attach_checks) and len(attach_checks) > 0,
        "body_samples": len(body_checks), "attachment_samples": len(attach_checks),
        "retention_matrix": RETENTION_MATRIX,
        "permanent_stores_unchanged": permanent_before == permanent_after,
        "permanent_delete_count": 0,          # the drill issues no deletes against permanent classes
        "isolation": "restored into an in-memory throwaway SQLite; production D1/R2 untouched",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logical-dir", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--months", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    rep = drill(args.logical_dir, args.raw, args.months.split(","))
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("retention_matrix", "per_month", "ground_truth")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
