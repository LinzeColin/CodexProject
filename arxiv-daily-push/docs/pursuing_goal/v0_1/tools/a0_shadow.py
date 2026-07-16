#!/usr/bin/env python3
"""ADP V0.1 A0 14-day shadow: value-cost comparison, media stream vs A0 official stream (ADP-S3-P03-T039).

Compares the current media stream (board3 today) against the A0 official stream (T034-T036 adapters
admitted by the T037 gate and resolved by the T038 resolver) on authoritativeness, pollution,
timeliness, coverage, and cost per accepted item. Deterministic; no clock/network. release_mode
SHADOW: this does NOT switch anything (T040 is the canary switch, gated by the Owner S3 Exit).

Discipline (enforced): a decision requires >= 14 complete cycles AND the thresholds met; a single day
never decides; if the threshold is not met the recommendation is CONTINUE_SHADOW. The literal 14 days
accrue over real calendar time via the pilot; this module also produces a representative report by
bucketing the available real sample into daily cycles.
"""
from __future__ import annotations
import dataclasses, json, pathlib, sys

MIN_CYCLES = 14
THRESH = {"authoritativeness_min": 0.99, "pollution_max": 0.01}


@dataclasses.dataclass(frozen=True)
class DayReport:
    cycle: int
    media_items: int
    a0_items: int
    a0_authoritative: int          # official-backed items in the A0 stream
    a0_polluted: int               # non-official items that slipped into the A0 policy view
    media_authoritative: int       # official-backed items in the media stream (≈0)
    media_polluted: int            # non-official items in the media stream (≈all)
    a0_missed_official: int        # official docs the A0 stream failed to cover (coverage miss)
    a0_false_positive: int         # media noise wrongly admitted (false positive)
    a0_latency_hours: float        # published -> available, A0 stream
    media_latency_hours: float
    a0_cost_requests: int          # cost attributable to the A0 stream this cycle
    a0_accepted: int               # accepted (published) items from the A0 stream


def _rate(n, d):
    return (n / d) if d else 0.0


def day_metrics(r: DayReport):
    return {
        "cycle": r.cycle,
        "a0": {"items": r.a0_items, "authoritativeness": _rate(r.a0_authoritative, r.a0_items),
               "pollution": _rate(r.a0_polluted, r.a0_items), "coverage_misses": r.a0_missed_official,
               "false_positives": r.a0_false_positive, "latency_hours": r.a0_latency_hours,
               "cost_per_accepted": _rate(r.a0_cost_requests, r.a0_accepted)},
        "media": {"items": r.media_items, "authoritativeness": _rate(r.media_authoritative, r.media_items),
                  "pollution": _rate(r.media_polluted, r.media_items), "latency_hours": r.media_latency_hours},
    }


def accumulate(reports):
    """Accumulate across cycles; NEVER decide on fewer than MIN_CYCLES; require thresholds met."""
    n = len(reports)
    a0_items = sum(r.a0_items for r in reports)
    a0_auth = sum(r.a0_authoritative for r in reports)
    a0_poll = sum(r.a0_polluted for r in reports)
    media_items = sum(r.media_items for r in reports)
    media_auth = sum(r.media_authoritative for r in reports)
    media_poll = sum(r.media_polluted for r in reports)
    accepted = sum(r.a0_accepted for r in reports)
    cost = sum(r.a0_cost_requests for r in reports)
    authoritativeness = _rate(a0_auth, a0_items)
    pollution = _rate(a0_poll, a0_items)
    thresholds_met = authoritativeness >= THRESH["authoritativeness_min"] and pollution <= THRESH["pollution_max"]
    enough_cycles = n >= MIN_CYCLES
    if not enough_cycles:
        rec = "CONTINUE_SHADOW"
        reason = f"only {n}/{MIN_CYCLES} cycles -- never decide on fewer than {MIN_CYCLES} (or a single day)"
    elif not thresholds_met:
        rec = "CONTINUE_SHADOW"
        reason = f"{n} cycles but thresholds not met (authoritativeness {authoritativeness:.3f} / pollution {pollution:.3f})"
    else:
        rec = "READY_FOR_OWNER_S3_EXIT_GATE"
        reason = f"{n} cycles and thresholds met; canary switch (T040) still requires the Owner S3 Exit gate"
    return {
        "cycles": n, "min_cycles": MIN_CYCLES, "enough_cycles": enough_cycles,
        "a0_stream": {"items": a0_items, "authoritativeness": authoritativeness, "pollution": pollution,
                      "accepted": accepted, "cost_requests": cost, "cost_per_accepted": _rate(cost, accepted),
                      "coverage_misses": sum(r.a0_missed_official for r in reports),
                      "false_positives": sum(r.a0_false_positive for r in reports)},
        "media_stream": {"items": media_items, "authoritativeness": _rate(media_auth, media_items),
                         "pollution": _rate(media_poll, media_items)},
        "thresholds": THRESH, "thresholds_met": thresholds_met,
        "recommendation": rec, "reason": reason,
        "release_mode": "SHADOW", "note": "SHADOW does not switch; T040 canary switch is gated by the Owner S3 Exit.",
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", required=True, help="JSON list of day reports")
    ap.add_argument("--out")
    args = ap.parse_args()
    raw = json.loads(pathlib.Path(args.reports).read_text(encoding="utf-8"))
    reports = [DayReport(**d) for d in raw]
    result = {"daily": [day_metrics(r) for r in reports], "accumulated": accumulate(reports)}
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["accumulated"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
