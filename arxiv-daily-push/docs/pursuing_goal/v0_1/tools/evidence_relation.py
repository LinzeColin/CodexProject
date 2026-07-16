#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T059 -- cross-board Evidence Relations.

Connects the boards -- policy, papers, standards, patents, statistics, pilots, procurement -- but does
NOT build a boundless knowledge graph. Two disciplines:

  * BOUNDED relation types -- only a fixed vocabulary of relations between defined board kinds is
    allowed; an unknown relation type or an off-vocabulary (subject_kind, object_kind) pair is refused.
  * EVIDENCE-BACKED only -- every SAVED relation must carry document + fragment evidence (the source
    doc id and the quoted span that supports it). A relation asserted WITHOUT evidence is not stored
    as a fact: it is returned as an explicitly-marked inference (status "inferred_unsaved"), so no
    unfounded edge ever enters the graph.

Deterministic; no network, no production side effects.
"""
import hashlib

# bounded vocabulary: predicate -> allowed (subject_kind, object_kind) pairs
RELATION_TYPES = {
    "implements":        [("policy", "policy")],            # a local policy implements a central one
    "interprets":        [("policy", "policy")],
    "cites":             [("paper", "policy"), ("paper", "standard"), ("patent", "standard")],
    "references_standard": [("policy", "standard"), ("procurement", "standard")],
    "supported_by_stat": [("policy", "statistic"), ("pilot", "statistic")],
    "pilot_under":       [("pilot", "policy")],
    "procurement_under": [("procurement", "policy")],
    "supersedes":        [("policy", "policy"), ("standard", "standard")],
}

BOARD_KINDS = {"policy", "paper", "standard", "patent", "statistic", "pilot", "procurement"}


def _valid_type(predicate, s_kind, o_kind):
    return predicate in RELATION_TYPES and (s_kind, o_kind) in RELATION_TYPES[predicate]


def _has_evidence(ev):
    """Evidence = a non-blank source document id AND a non-blank supporting fragment (quoted span)."""
    return bool(ev and (ev.get("doc_id") or "").strip() and (ev.get("fragment") or "").strip())


def add_relation(graph, subject, s_kind, predicate, obj, o_kind, evidence=None):
    """Attempt to add subject --predicate--> obj. Refused if off-vocabulary. Saved only with evidence;
    otherwise returned as an explicitly-marked, UNSAVED inference. Returns (graph, record)."""
    rel = {"subject": subject, "subject_kind": s_kind, "predicate": predicate,
           "object": obj, "object_kind": o_kind,
           "rel_id": "rel:" + hashlib.sha256(f"{subject}|{predicate}|{obj}".encode()).hexdigest()[:16]}
    if s_kind not in BOARD_KINDS or o_kind not in BOARD_KINDS:
        return graph, {**rel, "status": "refused", "reason": "unknown board kind"}
    if not _valid_type(predicate, s_kind, o_kind):
        return graph, {**rel, "status": "refused",
                       "reason": f"off-vocabulary relation ({s_kind})-{predicate}->({o_kind})"}
    if not _has_evidence(evidence):
        # asserted without evidence -> NOT a stored fact; explicitly marked inference
        return graph, {**rel, "status": "inferred_unsaved", "evidence": None,
                       "note": "no document/fragment evidence -> not saved as a fact"}
    saved = {**rel, "status": "saved",
             "evidence": {"doc_id": evidence["doc_id"], "fragment": evidence["fragment"].strip(),
                          "source_id": evidence.get("source_id")}}
    graph = dict(graph)
    graph[rel["rel_id"]] = saved
    return graph, saved


def build_graph(assertions):
    """assertions: list of (subject, s_kind, predicate, object, o_kind, evidence|None). Returns the
    bounded, evidence-backed graph plus the audit of refused/inferred assertions."""
    graph, audit = {}, []
    for a in assertions:
        graph, rec = add_relation(graph, *a)
        audit.append(rec)
    saved = [r for r in audit if r["status"] == "saved"]
    return {
        "relation_types": sorted(RELATION_TYPES),
        "assertions_in": len(assertions),
        "saved": len(saved),
        "refused": sum(1 for r in audit if r["status"] == "refused"),
        "inferred_unsaved": sum(1 for r in audit if r["status"] == "inferred_unsaved"),
        "graph": graph,
        "audit": audit,
        "every_saved_has_evidence": all(_has_evidence(r.get("evidence")) for r in saved),
    }


def query(graph, subject=None, predicate=None, object_=None):
    """Query examples: filter the evidence-backed graph. Every returned edge carries its evidence."""
    out = []
    for r in graph.values():
        if subject and r["subject"] != subject:
            continue
        if predicate and r["predicate"] != predicate:
            continue
        if object_ and r["object"] != object_:
            continue
        out.append(r)
    return out
