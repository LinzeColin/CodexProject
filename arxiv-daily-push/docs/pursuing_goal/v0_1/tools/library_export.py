#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T067 -- Library, notes, and Provenance export.

Makes reading and evidence a LONG-TERM asset (not something that only exists in Today): a user saves
items into a Library with notes and collections, and exports them to Markdown / CSV / JSON. Every
exported entry carries its full PROVENANCE -- the original URL, the version, the fetch (capture) time,
the claim evidence, and a license notice -- so an export is self-describing and never a decontextualized
copy. An export with any missing provenance field is REFUSED (never silently emitted).

  * add_to_library(lib, item, note?, collection?) -- save an item; provenance is carried from the item.
  * export_markdown / export_csv / export_json(lib) -- each includes ALL provenance fields per entry.
  * provenance_complete(entry) -- every provenance field present and non-empty.

Deterministic; no network, no clock (capture time comes from the item), no randomness, no production
side effects.
"""
import csv
import io
import json

# The provenance every saved entry MUST carry to be exportable.
PROVENANCE_FIELDS = ("source_url", "version", "fetched_at", "claim_evidence", "license")


def _is_blank(v):
    """Missing = None, [], or an empty/whitespace-only string. A genuine value like 0 is NOT blank."""
    return v is None or v == [] or (isinstance(v, str) and not v.strip())


def new_library(name="library"):
    return {"name": name, "entries": []}


def add_to_library(lib, item, note=None, collection=None):
    """Save an item into the library. The item MUST carry provenance (source_url, version, fetched_at,
    claim_evidence, license). Raises if provenance is incomplete -- an un-provenanced save is refused."""
    entry = {
        "canonical_id": item["canonical_id"],
        "title": item.get("title"),
        "note": note,
        "collection": collection,
        "provenance": {f: item.get(f) for f in PROVENANCE_FIELDS},
    }
    if not provenance_complete(entry):
        missing = [f for f in PROVENANCE_FIELDS if _is_blank(entry["provenance"].get(f))]
        raise ValueError(f"cannot save {item['canonical_id']} without provenance: missing {missing}")
    lib["entries"].append(entry)
    return lib


def provenance_complete(entry):
    """Every provenance field must be present and non-empty. None / [] / an empty-or-whitespace-only
    string count as missing; a genuine value like 0 counts as present."""
    p = entry.get("provenance") or {}
    return not any(_is_blank(p.get(f)) for f in PROVENANCE_FIELDS)


def _assert_exportable(lib):
    for e in lib["entries"]:
        if not provenance_complete(e):
            raise ValueError(f"refusing to export {e.get('canonical_id')}: incomplete provenance")


def export_json(lib):
    """JSON export -- round-trippable; each entry keeps its full provenance."""
    _assert_exportable(lib)
    return json.dumps({"name": lib["name"], "entries": lib["entries"]},
                      ensure_ascii=False, indent=2, sort_keys=True)


def export_csv(lib):
    """CSV export -- one row per entry, a column for each provenance field."""
    _assert_exportable(lib)
    buf = io.StringIO()
    cols = ["canonical_id", "title", "note", "collection", *PROVENANCE_FIELDS]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for e in lib["entries"]:
        row = {"canonical_id": e["canonical_id"], "title": e.get("title") or "",
               "note": e.get("note") or "", "collection": e.get("collection") or ""}
        row.update({f: e["provenance"][f] for f in PROVENANCE_FIELDS})
        w.writerow(row)
    return buf.getvalue()


def export_markdown(lib):
    """Markdown export -- a heading + a labeled provenance block per entry (human-readable, all fields)."""
    _assert_exportable(lib)
    out = [f"# {lib['name']}", ""]
    for e in lib["entries"]:
        out.append(f"## {e.get('title') or e['canonical_id']}")
        if e.get("collection"):
            out.append(f"- Collection: {e['collection']}")
        if e.get("note"):
            out.append(f"- Note: {e['note']}")
        p = e["provenance"]
        out.append(f"- Source URL: {p['source_url']}")
        out.append(f"- Version: {p['version']}")
        out.append(f"- Fetched at: {p['fetched_at']}")
        out.append(f"- Claim evidence: {p['claim_evidence']}")
        out.append(f"- License: {p['license']}")
        out.append("")
    return "\n".join(out)


def export(lib, fmt):
    return {"markdown": export_markdown, "csv": export_csv, "json": export_json}[fmt](lib)
