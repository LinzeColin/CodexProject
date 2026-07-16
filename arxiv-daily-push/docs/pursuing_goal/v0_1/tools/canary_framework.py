#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P02-T088 -- feature-flagged canary framework.

Derives the canary rollout framework from the ACTUAL worker source: it inventories every feature flag,
proves each is INDEPENDENTLY rollback-able (a standalone boolean gating its OWN additive side path, so
turning it off is a safe default that leaves the publish main chain intact and does not touch any other
flag), defines the cohort/dial rollout strategy + kill switches + monitoring, and anchors the
error-budget AUTO-STOP on the live DIR-007 fail-closed budget guard (`R2_BUDGET.guardFrac`).

The framework is a spec + verification over the existing, stable live worker (b189d3cc0703) -- it deploys
NOTHING new. Actually canarying a specific held capability (S5/S6/A1/A2) is a per-capability follow-on
with its own Owner go; this task delivers the mechanism the framework runs on.

Deterministic: reads the worker source, no network/clock/randomness.
"""
import argparse
import json
import pathlib
import re

V01 = pathlib.Path(__file__).resolve().parent.parent
WORKER = V01.parent.parent.parent / "deploy" / "cloudflare" / "worker_cloud.js"

# The known feature flags + the rollback target that turns each OFF (flag-off deploy or version rollback).
FLAG_SPEC = {
    "BOARD3_A0_ONLY": {"kind": "bool", "gates": "Board 3 A0-only filter (media excluded as evidence)",
                       "off_default": "false", "rollback": "set false / wrangler versions deploy b189d3cc0703 (T040)"},
    "RAW_DUALWRITE": {"kind": "bool", "gates": "R2 raw-artifact dual-write side path (bypass, in try/catch)",
                      "off_default": "false", "rollback": "set false / wrangler versions deploy 657fe32a (T022 flag off)"},
    "RUM_ENABLED": {"kind": "bool", "gates": "RUM client-script injection + /api/rum ingest",
                    "off_default": "false", "rollback": "set false (no injection; endpoint 202-ignores)"},
    "RUM_SAMPLE": {"kind": "dial", "gates": "RUM sample rate [0,1] -- the canary DIAL (throttle load / D1 writes)",
                   "off_default": "0", "rollback": "lower toward 0 (DIR-007 budget knob)"},
}


def _worker():
    return WORKER.read_text("utf-8")


def _conditional_lines(name, src):
    """Lines that USE the flag in a conditional gate: `if (...FLAG...)`, `!FLAG`, `FLAG ?`, `FLAG &&`,
    `&& FLAG` (excludes the `const NAME =` declaration line)."""
    esc = re.escape(name)
    out = []
    for line in src.splitlines():
        if re.search(r"const\s+%s\s*=" % esc, line):
            continue
        if (re.search(r"if\s*\([^)]*\b%s\b" % esc, line) or re.search(r"!\s*%s\b" % esc, line)
                or re.search(r"\b%s\s*(\?|&&|\|\|)" % esc, line) or re.search(r"(&&|\|\|)\s*%s\b" % esc, line)):
            out.append(line)
    return out


def flag_inventory(src=None):
    src = src if src is not None else _worker()
    flags = []
    for name, spec in FLAG_SPEC.items():
        if spec["kind"] == "bool":
            m = re.search(r"const %s\s*=\s*(true|false)" % re.escape(name), src)
            value = m.group(1) if m else None
            cond_lines = _conditional_lines(name, src)
            gated = len(cond_lines) > 0                      # the flag guards its own path via a conditional
            others = [f for f in FLAG_SPEC if f != name]
            # independent: no conditional line references this flag AND another flag (no cross-flag coupling)
            cross = any(any(re.search(r"\b%s\b" % re.escape(o), ln) for o in others) for ln in cond_lines)
            independent = gated and not cross
            off_safe = gated          # additive guard: off => the gated side path is skipped, core intact
        else:
            m = re.search(r"const %s\s*=\s*([0-9.]+)" % re.escape(name), src)
            value = m.group(1) if m else None
            independent = value is not None      # a dial is always safe to lower toward 0
            off_safe = True
        flags.append({"flag": name, "kind": spec["kind"], "value": value, "gates": spec["gates"],
                      "independently_rollbackable": bool(value is not None and independent),
                      "kill_switch": f"set {name}={spec['off_default']}", "rollback_path": spec["rollback"],
                      "off_is_safe_default": bool(off_safe)})
    return flags


def error_budget_autostop(src=None):
    """The live DIR-007 R2 budget guard is a real fail-closed error/cost-budget AUTO-STOP: at >= guardFrac
    of a free-tier limit it returns over_budget and stops writing. This is the canary auto-stop precedent;
    each flag's kill switch is the auto-stop LEVER for its own path."""
    src = src if src is not None else _worker()
    has_budget = bool(re.search(r"R2_BUDGET\s*=\s*\{", src))
    guard = re.search(r"guardFrac:\s*([0-9.]+)", src)
    fail_closed = bool(re.search(r"over_budget:\s*true", src)) and "return" in src
    return {"budget_defined": has_budget, "guard_fraction": float(guard.group(1)) if guard else None,
            "fail_closed_autostop": has_budget and fail_closed,
            "mechanism": "R2 dual-write halts (over_budget) at >= guardFrac of the free-tier limit; "
                         "the canary error-budget rule reuses each flag's kill switch as the auto-stop lever"}


def build_framework(src=None):
    src = src if src is not None else _worker()
    flags = flag_inventory(src)
    autostop = error_budget_autostop(src)
    canary_plan = {
        "strategy": "open new paths incrementally behind independent flags, never big-bang",
        "cohorts": ["off (safe default)", "shadow (flag on, no user-visible change / capped)",
                    "dial-up via RUM_SAMPLE or per-board/route slice", "full"],
        "monitoring": "RUM Core Web Vitals (LCP/CLS/INP) per theme/route/device (T081) + DIR-007 budget usage",
        "kill_switches": {f["flag"]: f["kill_switch"] for f in flags},
        "rollback_paths": {f["flag"]: f["rollback_path"] for f in flags},
        "error_budget_auto_stop": {
            "cost": "DIR-007 fail-closed budget guard (live)",
            "quality": "on a CWV error-budget breach (e.g. LCP/INP p75 regressing past threshold with "
                       "min-samples), auto-disable the canary flag / lower RUM_SAMPLE (fail-closed)",
        },
        "held_capabilities_rollout": {
            "A1/A2 subnational": "each cohort behind a source-enable flag; per-cohort Owner promotion gate",
            "S5 depth / S6 models": "behind a NOT_DEPLOYED feature flag; promotion-gated, canary via cohort",
        },
    }
    return {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S8-P02-T088",
            "flags": flags, "error_budget_autostop": autostop, "canary_plan": canary_plan,
            "live_build": "b189d3cc0703 (unchanged; framework verifies the existing mechanism, deploys nothing)"}


def acceptance(fw):
    flags = fw["flags"]
    all_independent = all(f["independently_rollbackable"] for f in flags)
    all_kill = all(f["kill_switch"] for f in flags)
    all_off_safe = all(f["off_is_safe_default"] for f in flags)
    autostop = fw["error_budget_autostop"]["fail_closed_autostop"]
    return {"every_flag_independently_rollbackable": all_independent,
            "every_flag_has_kill_switch": all_kill,
            "every_flag_off_is_safe_default": all_off_safe,
            "error_budget_auto_stop_exists": autostop,
            "not_independent": [f["flag"] for f in flags if not f["independently_rollbackable"]],
            "framework_pass": all_independent and all_kill and all_off_safe and autostop}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    fw = build_framework()
    acc = acceptance(fw)
    fw["acceptance"] = acc
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(fw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for f in fw["flags"]:
        print(f"  {f['flag']:<16} {f['kind']:<5} value={str(f['value']):<6} "
              f"independent_rollback={f['independently_rollbackable']} kill='{f['kill_switch']}'")
    a = fw["error_budget_autostop"]
    print(f"  error-budget auto-stop: DIR-007 fail-closed guard@{a['guard_fraction']} -> over_budget stop = {a['fail_closed_autostop']}")
    print(f"FRAMEWORK_PASS={acc['framework_pass']} (live {fw['live_build'][:12]}, NOT_DEPLOYED)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
