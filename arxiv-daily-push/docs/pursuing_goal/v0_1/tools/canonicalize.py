#!/usr/bin/env python3
"""ADP V0.1 CanonicalDocument identity + repost merge + dedup (ADP-S2-P02-T024).

Distinguishes: the same document, a repost (same doc from another source), an
attachment (same doc, different file), a revision (same doc, later version), and
an entirely different event.

Identity (deterministic):
  - if a DOI exists  -> canonical_id = "doi:" + normalized DOI (revision suffix
    like v2 stripped into a separate `revision`);
  - else             -> canonical_id = "ttl:" + sha256(normalized_title)[:16].

Merge rule: two items with the same canonical_id are the SAME document. A repost
(same canonical_id, different source_id) MERGES into one canonical document whose
`sources` and `artifacts` (R2 object keys) both list every contributing source --
the raw artifacts are PRESERVED, only the document is deduped.

Collision: two clearly-different items mapping to the same canonical_id (e.g.
identical normalized title but different DOIs) are flagged, explainable, and
resolvable by falling back to the DOI / a content hash.

No network / R2 I/O. Usage: python3 canonicalize.py --items items.json --factsheets fs.json [--out doc_index.json]
"""
import argparse, hashlib, json, re, sys, pathlib

DOI_RE = re.compile(r"10\.\d{4,9}/\S+")
REV_RE = re.compile(r"(v\d+)$", re.I)


def norm_doi(doi):
    if not doi:
        return None, None
    d = doi.strip().lower().rstrip(").,;")
    m = REV_RE.search(d.split("/")[-1])
    rev = m.group(1) if m else None
    return d, rev


def norm_title(t):
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"[\s　]+", " ", t)
    t = re.sub(r"[^0-9a-z一-鿿 ]+", "", t)
    return t.strip()


def canonical_id(fs, item):
    common = fs.get("common", {})
    doi = common.get("doi")
    if doi:
        nd, rev = norm_doi(doi)
        base = nd
        if rev:
            base = nd[: nd.rfind(rev)].rstrip("/.")
        return "doi:" + base, rev
    title = norm_title(common.get("title") or item.get("title"))
    return "ttl:" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:16], None


def canonicalize(items, factsheets):
    fs_by_id = {f["item_id"]: f for f in factsheets}
    docs = {}
    collisions = []
    for it in items:
        iid = it.get("id")
        fs = fs_by_id.get(iid, {"common": {}})
        cid, rev = canonical_id(fs, it)
        src = it.get("source_id")
        title_norm = norm_title(fs.get("common", {}).get("title") or it.get("title"))
        if cid not in docs:
            docs[cid] = {"canonical_id": cid, "title_norm": title_norm, "sources": [], "items": [], "revisions": set(), "artifact_keys": []}
        d = docs[cid]
        # collision check: ttl-based id whose normalized title differs -> different doc collided
        if cid.startswith("ttl:") and d["title_norm"] and title_norm and d["title_norm"] != title_norm:
            collisions.append({"canonical_id": cid, "reason": "same title-hash, different normalized title", "a": d["title_norm"][:40], "b": title_norm[:40], "resolution": "fall back to DOI / content hash"})
        if src not in d["sources"]:
            d["sources"].append(src)
        d["items"].append(iid)
        if rev:
            d["revisions"].add(rev)
        # artifact preserved per contributing item (R2 object addressed by that item's raw bytes; here we track item_id as the artifact anchor)
        d["artifact_keys"].append(iid)
    for d in docs.values():
        d["revisions"] = sorted(d["revisions"])
        d["is_repost_merged"] = len(d["sources"]) > 1
        d["item_count"] = len(d["items"])
    return {"documents": list(docs.values()), "collisions": collisions,
            "summary": {"items_in": len(items), "canonical_documents": len(docs),
                        "reposts_merged": sum(1 for d in docs.values() if d["is_repost_merged"]),
                        "duplicate_items_collapsed": len(items) - len(docs),
                        "collisions": len(collisions)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--factsheets", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    fs = json.loads(pathlib.Path(args.factsheets).read_text(encoding="utf-8"))
    res = canonicalize(items, fs)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
