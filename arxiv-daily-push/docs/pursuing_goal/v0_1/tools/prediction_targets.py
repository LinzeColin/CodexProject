#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T069 -- prediction target catalog, Outcome Rules, and event labels.

Stage S6 opens with a discipline: DEFINE WHAT COUNTS AS "HAPPENED" BEFORE TRAINING ANY MODEL. A
prediction target is admissible only if it can be settled -- objectively, 0/1 -- by FUTURE OFFICIAL
evidence (A0/A1 original text), by an unambiguous settlement rule. A vague or subjective target (one
whose outcome cannot be read off official evidence) is REJECTED and may NOT enter the backtest.

  * make_target(...)        -- a target: {target_id, description, horizon_days, subject, settlement}.
  * is_settleable(target)   -- True iff the settlement is a recognized OBJECTIVE predicate with all its
                               required fields (not free text, not a subjective judgement).
  * admit_targets(catalog)  -- split a catalog into admitted (settleable) and rejected (ambiguous, with
                               a reason). Only admitted targets may enter a backtest.
  * settle(target, evidence, origin_date) -- apply the settlement rule to OFFICIAL evidence observed
                               within [origin_date, origin_date + horizon]; returns a definite 0/1 label,
                               or 'pending' if the horizon has not elapsed by the newest observation.

Deterministic; no network, no clock (dates are passed in), no randomness, no production side effects.
"""
import datetime
import re

# Recognized objective settlement predicates. Each names the fields it requires; anything else (free
# text, a subjective 'important'/'significant' judgement) is NOT settleable.
SETTLEMENT_TYPES = {
    "official_doc_exists": ("agency", "topic"),          # an official doc by agency on topic within H
    "status_transition": ("canonical_id", "to_status"),  # a doc reaches to_status within H
    "count_at_least": ("agency", "topic", "n"),          # >= n official docs by agency on topic within H
}
OFFICIAL_LEVELS = ("A0", "A1")                            # settlement counts only official original text
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse(d):
    if not (isinstance(d, str) and _DATE.match(d)):
        return None
    y, m, dd = d.split("-")
    return (int(y), int(m), int(dd))


def _add_days_bound(origin_date, horizon_days):
    """A coarse, deterministic upper date bound = origin year-month-day + horizon as a comparable key.
    Backtests use month/day granularity; we compare parsed (y,m,d) after adding horizon via a proleptic
    day count. No wall-clock is read."""
    y, m, d = _parse(origin_date)
    # calendar-correct end date via date arithmetic on the PASSED-IN origin (no wall-clock read)
    base = datetime.date(y, m, d) + datetime.timedelta(days=horizon_days)
    return (base.year, base.month, base.day)


def make_target(target_id, description, horizon_days, subject, settlement):
    return {"target_id": target_id, "description": description, "horizon_days": horizon_days,
            "subject": subject, "settlement": settlement}


def _pos_int(v):
    """A genuine positive integer (bool is excluded: a settlement window is not True/False)."""
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def is_settleable(target):
    """A target is settleable iff its settlement names a known objective predicate AND supplies every
    required field with a non-empty, non-subjective value."""
    s = target.get("settlement")
    if not isinstance(s, dict):                      # a non-dict settlement is not an objective rule
        return False
    stype = s.get("type")
    if stype not in SETTLEMENT_TYPES:
        return False
    for field in SETTLEMENT_TYPES[stype]:
        v = s.get(field)
        if v is None or (isinstance(v, str) and not v.strip()):
            return False
    # horizon must be a positive integer number of days (a finite settlement window)
    if not _pos_int(target.get("horizon_days")):
        return False
    # count_at_least needs a positive integer threshold
    if stype == "count_at_least" and not _pos_int(s.get("n")):
        return False
    return True


def admit_targets(catalog):
    admitted, rejected = [], []
    for t in catalog:
        if is_settleable(t):
            admitted.append(t)
        else:
            rejected.append({"target_id": t.get("target_id"),
                             "reason": "ambiguous_or_unsettleable_settlement_rule"})
    return {"admitted": admitted, "rejected": rejected}


def _official(doc):
    return doc.get("authority_level") in OFFICIAL_LEVELS


def settle(target, evidence, origin_date):
    """Settle a target against OFFICIAL evidence observed within [origin_date, origin_date+horizon].
    Returns {label: 0|1, ...} or {label: 'pending'} if the settlement window has not fully elapsed
    (the newest observed evidence date is before the window end). Ignores media / non-official and any
    evidence observed after the window (no leakage)."""
    if not is_settleable(target):
        raise ValueError(f"target {target.get('target_id')} is not settleable -> must not be backtested")
    o = _parse(origin_date)
    end = _add_days_bound(origin_date, target["horizon_days"])
    s = target["settlement"]
    # only official evidence, observed within the window [origin, end]
    in_window = [d for d in evidence
                 if _official(d) and _parse(d.get("observed_at")) is not None
                 and o <= _parse(d["observed_at"]) <= end]
    newest = max((_parse(d["observed_at"]) for d in evidence if _parse(d.get("observed_at"))), default=None)
    matched = _match(s, in_window)
    if matched >= _needed(s):
        return {"label": 1, "matched": matched, "window_end": "%04d-%02d-%02d" % end}
    # not satisfied yet: if the window has not elapsed (no observation reaches the end), it is pending
    if newest is None or newest < end:
        return {"label": "pending", "matched": matched, "window_end": "%04d-%02d-%02d" % end}
    return {"label": 0, "matched": matched, "window_end": "%04d-%02d-%02d" % end}


def _needed(s):
    return s["n"] if s["type"] == "count_at_least" else 1


def _topic_match(doc, topic):
    """Exact membership in the doc's topics LIST. A string topics field is NOT substring-matched (that
    would spuriously settle a target); a non-list topics field never matches."""
    topics = doc.get("topics")
    return isinstance(topics, list) and topic in topics


def _match(s, docs):
    if s["type"] in ("official_doc_exists", "count_at_least"):
        return sum(1 for d in docs if d.get("agency") == s["agency"] and _topic_match(d, s["topic"]))
    if s["type"] == "status_transition":
        return sum(1 for d in docs if d.get("canonical_id") == s["canonical_id"] and d.get("status") == s["to_status"])
    return 0
