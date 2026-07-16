#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T057 -- Canonical Event aggregation.

The same policy / research / event shows up as many pages: the official ORIGINAL, official
INTERPRETATIONS, media REPOSTS, and social REACTIONS. This aggregates them into ONE canonical event
so a user gets a single alert -- not 20 -- while every member page stays expandable as evidence.

  * event identity  -- the event KEY every member shares: the original's document number (文号) when
                       present, else the content-addressed id of the authoritative original. A member
                       joins an event by REFERENCING that key (a repost/interpretation cites the 文号)
                       or by being the original itself. No fuzzy title-only merging.
  * primary selection -- the highest-authority member whose own id is the event key (the ORIGINAL):
                       A0 (central official) > A1 > A2 > media/repost. The primary is what the alert
                       shows; interpretations/reposts/reactions are members.
  * member links    -- every page in the cluster, tagged with its role and kept individually
                       retrievable, so all evidence is expandable from the single event.

Deterministic; no network, no production side effects.
"""
import hashlib

# authority ordering: a lower rank is MORE authoritative -> becomes the primary
_AUTH_RANK = {"A0": 0, "A1": 1, "A2": 2, "official": 1, "media": 8, "repost": 9, "reaction": 9, "unofficial": 9}


def _page_key(p):
    """The event key a page belongs to: the doc_number it IS or REFERENCES; else the original's
    content id; else its own content id (a singleton event)."""
    if p.get("references"):
        return ("docnum", p["references"])            # a repost/interpretation -> the cited 文号
    if p.get("doc_number"):
        return ("docnum", p["doc_number"])            # an original with a 文号
    cid = p.get("canonical_id") or ("ttl:" + hashlib.sha256((p.get("url") or p.get("page_id") or "").encode()).hexdigest()[:16])
    return ("cid", cid)


def aggregate(pages):
    """Cluster pages into canonical events. Returns {events: [...], alerts, ...}."""
    clusters = {}
    for p in pages:
        clusters.setdefault(_page_key(p), []).append(p)

    events = []
    for key, members in clusters.items():
        # primary = the most authoritative member whose OWN doc_number/id equals the event key
        def is_original(m):
            k = key[1]
            return (m.get("doc_number") == k) or (m.get("canonical_id") == k) or (not m.get("references") and _page_key(m) == key)
        originals = [m for m in members if is_original(m) and not m.get("references")]
        pool = originals or members
        primary = min(pool, key=lambda m: (_AUTH_RANK.get(m.get("authority_level") or m.get("kind"), 9),
                                           m.get("page_id", "")))
        member_links = [{"page_id": m.get("page_id"), "url": m.get("url"),
                         "role": m.get("kind", "member"), "source_id": m.get("source_id"),
                         "authority_level": m.get("authority_level")} for m in members]
        events.append({
            "event_id": "evt:" + hashlib.sha256(("|".join(map(str, key))).encode()).hexdigest()[:16],
            "event_key": {"kind": key[0], "value": key[1]},
            "primary": {"page_id": primary.get("page_id"), "url": primary.get("url"),
                        "title": primary.get("title"), "authority_level": primary.get("authority_level"),
                        "doc_number": primary.get("doc_number")},
            "member_count": len(members),
            "roles": _role_counts(members),
            "members": member_links,
        })
    events.sort(key=lambda e: e["member_count"], reverse=True)
    return {
        "pages_in": len(pages),
        "events": events,
        "alert_count": len(events),         # ONE alert per canonical event, not per page
        "largest_event_members": events[0]["member_count"] if events else 0,
    }


def _role_counts(members):
    c = {}
    for m in members:
        r = m.get("kind", "member")
        c[r] = c.get(r, 0) + 1
    return c


def expand(event):
    """All evidence for an event: the full member list stays individually retrievable."""
    return event["members"]
