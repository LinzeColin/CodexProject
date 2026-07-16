#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T068 -- Knowledge Validity clock + benefit-parity regression.

Two halves that close S5-P04:

  1. Knowledge Validity -- a piece of derived knowledge (a summary, a factsheet, an answer) is bound to
     the SOURCE VERSION it was derived from (T026 content_hash). A validity clock re-checks knowledge
     against the current source: if the source's substantive content changed, the knowledge is
     automatically marked INVALID / needs_review (re-open old knowledge); a noise-only re-render (same
     content_hash) leaves it VALID (no spurious churn). revalidate() re-binds re-learned knowledge.

  2. Benefit-parity regression -- a registry of competitor user benefits, each with a definite STATUS
     and a named OWNER. parity_report() proves every item has a status from a closed vocabulary (never
     'unknown') and a real owner (never blank / 'no-owner'), so no competitor benefit is left in an
     'unknown / nobody-owns-it' limbo.

Deterministic; no network, no clock (the validity check compares source hashes, not wall-time), no
randomness, no production side effects.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import version_engine as VE   # T026 content_hash = substantive source version

# ------------------------------------------------------------------ 1. Knowledge Validity clock
VALIDITY = ("valid", "needs_review", "invalid")


def make_knowledge(knowledge_id, statement, source_item):
    """Bind a piece of knowledge to the substantive version of the source it was derived from."""
    return {
        "knowledge_id": knowledge_id,
        "statement": statement,
        "derived_from": {"canonical_id": source_item["canonical_id"],
                         "source_version": VE.content_hash(source_item)},
        "validity": "valid",
    }


def check_validity(knowledge, current_items):
    """Re-check a knowledge item against the CURRENT source. If the source's substantive content changed
    (content_hash differs from the bound version), auto-mark needs_review; if the source is gone, invalid;
    a noise-only re-render (same hash) stays valid. Returns a NEW knowledge dict (no in-place mutation)."""
    by_id = {it["canonical_id"]: it for it in current_items}
    k = dict(knowledge)
    src = by_id.get(knowledge["derived_from"]["canonical_id"])
    if src is None:
        k["validity"] = "invalid"
        k["reason"] = "source_removed"
        return k
    now = VE.content_hash(src)
    if now != knowledge["derived_from"]["source_version"]:
        k["validity"] = "needs_review"                      # 源实质变化 -> 自动重开旧知识
        k["reason"] = "source_changed"
        k["current_source_version"] = now
    else:
        k["validity"] = "valid"
        k.pop("reason", None)
    return k


def revalidate(knowledge, new_statement, source_item):
    """Re-learn: re-bind the knowledge to the current source version with the refreshed statement."""
    k = dict(knowledge)
    k["statement"] = new_statement
    k["derived_from"] = {"canonical_id": source_item["canonical_id"],
                         "source_version": VE.content_hash(source_item)}
    k["validity"] = "valid"
    k.pop("reason", None)
    k.pop("current_source_version", None)
    return k


def run_validity(knowledge_items, current_items):
    checked = [check_validity(k, current_items) for k in knowledge_items]
    return {
        "checked": checked,
        "valid": [k["knowledge_id"] for k in checked if k["validity"] == "valid"],
        "needs_review": [k["knowledge_id"] for k in checked if k["validity"] == "needs_review"],
        "invalid": [k["knowledge_id"] for k in checked if k["validity"] == "invalid"],
    }


# ------------------------------------------------------------------ 2. benefit-parity regression
PARITY_STATUSES = ("delivered", "partial", "planned", "not_applicable")   # closed vocab -- NO 'unknown'
FORBIDDEN_OWNERS = ("", "no-owner", "unknown", "unassigned", None)


def _owner_ok(owner):
    return isinstance(owner, str) and owner.strip() and owner.strip().lower() not in ("no-owner", "unknown", "unassigned")


def parity_report(registry):
    """Every parity item must have a status in PARITY_STATUSES (never 'unknown') and a real owner. The
    report lists any offenders so the gate can fail; a clean registry has zero."""
    items = registry["items"]
    unknown_status = [i["benefit_id"] for i in items if i.get("status") not in PARITY_STATUSES]
    no_owner = [i["benefit_id"] for i in items if not _owner_ok(i.get("owner"))]
    # delivered/partial must cite the ADP task that delivers it; planned/not_applicable must give a
    # reason -- so no item is a bare status with no justification.
    missing_evidence = [i["benefit_id"] for i in items
                        if i.get("status") in ("delivered", "partial") and not i.get("evidence_ref")]
    missing_note = [i["benefit_id"] for i in items
                    if i.get("status") in ("planned", "not_applicable") and not i.get("note")]
    by_status = {s: sum(1 for i in items if i.get("status") == s) for s in PARITY_STATUSES}
    by_competitor = {}
    for i in items:
        by_competitor[i["competitor"]] = by_competitor.get(i["competitor"], 0) + 1
    return {
        "n_items": len(items),
        "by_status": by_status,
        "by_competitor": by_competitor,
        "unknown_status": unknown_status,
        "no_owner": no_owner,
        "delivered_or_partial_missing_evidence": missing_evidence,
        "planned_or_na_missing_note": missing_note,
        "clean": not unknown_status and not no_owner and not missing_evidence and not missing_note,
    }
