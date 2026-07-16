#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T066 -- Watchlist + Change-only Digest.

Continuously watches topics / agencies / regions / entities / doc-numbers and pushes ONLY substantive
changes -- so a re-run never duplicates a notification, an unchanged corpus never disturbs the user,
and every notification is locatable back to the exact item and version that changed.

  * WatchRule {watch_id, facet, value} -- facet in {topic, agency, region, entity, doc_number}.
    matches(item, rule) is exact on the item's facet field(s).
  * run_digest(state, items, watches, period) -- for each watched item, decide a SUBSTANTIVE change by
    T026 content_hash (a new canonical item, or a changed substantive hash; a noise-only re-render is
    NOT a change). Emit a notification ONLY for a (watch, canonical_id, content_hash) key not already in
    `state.seen`; then record it. Returns notifications (new only), the period digest, source silence
    signals, and the updated state. Re-running with the returned state yields ZERO new notifications.
  * A silence signal is raised for a watched source that produced no change in the period.

Deterministic; no network, no clock, no randomness, no production side effects. `period` is supplied by
the caller (no wall-clock read).
"""
import copy
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import version_engine as VE   # T026: content_hash over the substantive signature (noise-insensitive)

FACETS = ("topic", "agency", "region", "entity", "doc_number")


def new_state():
    """Persisted digest state: the set of notification keys already emitted (for dedup on re-run)."""
    return {"seen": set()}


def make_watch(watch_id, facet, value):
    assert facet in FACETS, f"unknown facet {facet}"
    return {"watch_id": watch_id, "facet": facet, "value": value}


def matches(item, rule):
    """Exact match of the item's facet field to the rule value. entity/topic may be multi-valued."""
    f, v = rule["facet"], rule["value"]
    field = item.get(f)
    if isinstance(field, (list, tuple, set)):
        return v in field
    return field == v


def _notif_key(watch_id, canonical_id, content_hash):
    return f"{watch_id}|{canonical_id}|{content_hash}"


def run_digest(state, items, watches, period):
    """Match items to watches, emit notifications only for NEW substantive-change keys, raise silence
    signals for watched sources with no change. Never mutates the caller's state (returns a new one)."""
    state = {"seen": set(state.get("seen", set()))}          # copy: no in-place mutation of caller state
    notifications = []
    watched_sources = {w["watch_id"]: set() for w in watches}   # watch_id -> set of changed canonical_ids

    for it in items:
        ch = VE.content_hash(it)                              # substantive hash (noise-insensitive, T026)
        cid = it["canonical_id"]
        for w in watches:
            if not matches(it, w):
                continue
            key = _notif_key(w["watch_id"], cid, ch)
            watched_sources.setdefault(w["watch_id"], set())
            if key in state["seen"]:
                continue                                     # already notified -> no duplicate (re-run safe)
            state["seen"].add(key)
            watched_sources[w["watch_id"]].add(cid)
            notifications.append({
                "watch_id": w["watch_id"], "facet": w["facet"], "value": w["value"],
                "canonical_id": cid, "content_hash": ch,
                "title": it.get("title"), "url": it.get("url"),
                "locator": {"canonical_id": cid, "content_hash": ch,
                            "matched_facet": w["facet"], "matched_value": w["value"]},
                "period": period,
            })
    notifications.sort(key=lambda n: (n["watch_id"], n["canonical_id"]))
    silence = [{"watch_id": wid, "period": period, "signal": "no_change"}
               for wid, changed in sorted(watched_sources.items()) if not changed]
    digest = {
        "period": period, "n_notifications": len(notifications),
        "by_watch": {wid: sorted(cids) for wid, cids in sorted(watched_sources.items()) if cids},
    }
    return {"notifications": notifications, "digest": digest,
            "silence_signals": silence, "state": state}


def notification_is_locatable(n, items):
    """True iff the notification points to a real item whose current substantive hash matches."""
    by_id = {it["canonical_id"]: it for it in items}
    it = by_id.get(n["locator"]["canonical_id"])
    if it is None:
        return False
    return VE.content_hash(it) == n["locator"]["content_hash"]
