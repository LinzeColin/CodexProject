#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T058 -- cross-source entity resolution.

Unifies the entities that appear across boards -- agencies, institutions, authors, companies, regions,
topics, standards -- so the same real-world entity referred to differently by different sources
(full name, abbreviation, English name, variant) resolves to ONE entity, WITHOUT losing provenance
and WITHOUT being irreversible:

  * entity schema  -- {entity_id, type, canonical_name, aliases[], provenance[], confidence, merged_from[]}
  * aliases        -- every surface form seen, each kept with the source that used it (provenance)
  * provenance     -- per (alias, attribute): which source_id asserted it, so nothing is unsourced
  * merge/split audit -- every merge is logged with its evidence and confidence; a wrong merge is
                      REVERSIBLE via split(), which restores the pre-merge entities exactly.

A merge below the confidence boundary (AUTO_MERGE_MIN) is NOT auto-applied -- it is flagged for
manual review, so the resolver never silently over-merges on a weak signal. Deterministic.
"""
import hashlib, copy

AUTO_MERGE_MIN = 0.80   # below this, a merge is flagged for manual review, not auto-applied


def _eid(canonical):
    return "ent:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def make_entity(canonical_name, etype, source_id, aliases=None):
    """A single-mention entity with its first provenance record."""
    aliases = list(dict.fromkeys([canonical_name] + list(aliases or [])))
    return {
        "entity_id": _eid(canonical_name), "type": etype, "canonical_name": canonical_name,
        "aliases": aliases,
        "provenance": [{"alias": a, "source_id": source_id} for a in aliases],
        "confidence": 1.0, "merged_from": [],
    }


def resolve(mentions):
    """mentions: [{name, type, source_id, aliases?}]. Cluster by shared alias into entities; each
    entity keeps every alias with the source that used it (provenance). No fuzzy-substring merging."""
    alias_to_ent = {}
    entities = {}
    for m in mentions:
        forms = list(dict.fromkeys([m["name"]] + list(m.get("aliases") or [])))
        hit = next((alias_to_ent[f] for f in forms if f in alias_to_ent), None)
        if hit is None:
            e = make_entity(m["name"], m["type"], m["source_id"], m.get("aliases"))
            entities[e["entity_id"]] = e
            for f in forms:
                alias_to_ent[f] = e["entity_id"]
        else:
            e = entities[hit]
            for f in forms:
                if f not in e["aliases"]:
                    e["aliases"].append(f)
                e["provenance"].append({"alias": f, "source_id": m["source_id"]})
                alias_to_ent[f] = e["entity_id"]
    return entities


def merge(entities, id_a, id_b, evidence, confidence):
    """Merge b into a with an AUDIT record. Below AUTO_MERGE_MIN the merge is NOT applied -- it is
    returned as a pending review. Returns (entities, audit)."""
    a, b = entities[id_a], entities[id_b]
    audit = {"audit_id": "mrg:" + hashlib.sha256((id_a + "|" + id_b).encode()).hexdigest()[:16],
             "kept": id_a, "absorbed": id_b, "evidence": evidence, "confidence": confidence,
             "before": {id_a: copy.deepcopy(a), id_b: copy.deepcopy(b)}}
    if confidence < AUTO_MERGE_MIN:
        audit["status"] = "pending_review"          # confidence boundary: do NOT auto-merge weak signals
        return entities, audit
    merged = copy.deepcopy(a)
    for al in b["aliases"]:
        if al not in merged["aliases"]:
            merged["aliases"].append(al)
    merged["provenance"] = a["provenance"] + b["provenance"]
    merged["merged_from"] = a.get("merged_from", []) + [id_b, *b.get("merged_from", [])]
    merged["confidence"] = round(min(a["confidence"], b["confidence"], confidence), 4)
    ents = dict(entities)
    ents[id_a] = merged
    del ents[id_b]
    audit["status"] = "applied"
    return ents, audit


def split(entities, audit):
    """Reverse a merge exactly: restore the two pre-merge entities from the audit's `before` snapshot.
    Makes any wrong merge undoable."""
    if audit.get("status") != "applied":
        return entities
    ents = dict(entities)
    ents.pop(audit["kept"], None)
    for eid, snap in audit["before"].items():
        ents[eid] = copy.deepcopy(snap)
    return ents


def provenance_of(entity):
    """Every alias -> the set of sources that asserted it (nothing unsourced)."""
    out = {}
    for pr in entity["provenance"]:
        out.setdefault(pr["alias"], set()).add(pr["source_id"])
    return {a: sorted(s) for a, s in out.items()}
