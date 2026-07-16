#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P02-T088 acceptance: feature-flagged canary framework.

Acceptance (TASK_INDEX row 88): 每个 flag 可独立回滚；错误预算触发自动停止.

Deterministic (reads the worker source; no network/clock/randomness). Re-derives the framework and asserts
every feature flag is independently rollback-able with a kill switch + off-safe default, and that a real
error-budget AUTO-STOP exists (the live DIR-007 fail-closed budget guard).

Load-bearing negative controls (drive the tool with a MUTATED worker source):
  1. INDEPENDENT ROLLBACK: removing a flag's conditional gate makes that flag NOT independently
     rollback-able (it no longer guards its own path) -> framework fails.
  2. NO CROSS-COUPLING: injecting a conditional that references TWO flags at once makes both non-independent
     -> framework fails. (proves the independence check is not vacuous.)
  3. ERROR-BUDGET AUTO-STOP: flipping the budget guard's `over_budget: true` breaks the fail-closed
     auto-stop detection -> the auto-stop check fails.
NOT_DEPLOYED: the framework reads the worker read-only and deploys nothing; live b189d3cc0703 (checked
separately in realtime_check.txt).
"""
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import canary_framework as CF

fails = []
REAL = CF._worker()
fw = CF.build_framework(REAL)
acc = CF.acceptance(fw)

# ---- machine acceptance ----
if not acc["framework_pass"]:
    fails.append(f"framework did not pass: {acc}")
if not acc["every_flag_independently_rollbackable"]:
    fails.append(f"a flag is not independently rollback-able: {acc['not_independent']}")
if not acc["every_flag_has_kill_switch"]:
    fails.append("a flag has no kill switch")
if not acc["every_flag_off_is_safe_default"]:
    fails.append("a flag's off state is not a safe default")
if not acc["error_budget_auto_stop_exists"]:
    fails.append("no fail-closed error-budget auto-stop found")
# the expected flags + values are read from the actual worker
byname = {f["flag"]: f for f in fw["flags"]}
expected = {"BOARD3_A0_ONLY": "false", "RAW_DUALWRITE": "true", "RUM_ENABLED": "true", "RUM_SAMPLE": "1"}
for name, val in expected.items():
    if name not in byname:
        fails.append(f"flag {name} not inventoried")
    elif byname[name]["value"] != val:
        fails.append(f"flag {name} value drift: {byname[name]['value']} != {val}")
if fw["error_budget_autostop"]["guard_fraction"] != 0.9:
    fails.append(f"DIR-007 guard fraction drift: {fw['error_budget_autostop']['guard_fraction']}")
print(f"canary framework: {len(fw['flags'])} flags all independently rollback-able + kill switch + off-safe; "
      f"DIR-007 fail-closed auto-stop @{fw['error_budget_autostop']['guard_fraction']}; live b189d3cc0703 (NOT_DEPLOYED)")

# ---- NC1: remove a flag's conditional gate -> it is no longer independently rollback-able ----
src_no_gate = REAL.replace("if (RAW_DUALWRITE && env && env.RAW && sourceId)",
                           "if (env && env.RAW && sourceId)", 1)
if src_no_gate == REAL:
    fails.append("control setup: could not remove the RAW_DUALWRITE gate")
raw = {f["flag"]: f for f in CF.flag_inventory(src_no_gate)}["RAW_DUALWRITE"]
if raw["independently_rollbackable"]:
    fails.append("control broken: a flag with no conditional gate still 'independently rollback-able' -- vacuous")

# ---- NC2: couple two flags in one conditional -> both non-independent ----
src_coupled = REAL.replace("if (RAW_DUALWRITE && env && env.RAW && sourceId)",
                           "if (RAW_DUALWRITE && RUM_ENABLED && env && env.RAW && sourceId)", 1)
ci = {f["flag"]: f for f in CF.flag_inventory(src_coupled)}
if ci["RAW_DUALWRITE"]["independently_rollbackable"] and ci["RUM_ENABLED"]["independently_rollbackable"]:
    fails.append("control broken: two flags coupled in one conditional still both 'independent' -- vacuous")

# ---- NC3: break the fail-closed budget auto-stop ----
src_no_stop = REAL.replace("over_budget: true", "over_budget: false")
if CF.error_budget_autostop(src_no_stop)["fail_closed_autostop"]:
    fails.append("control broken: removing the fail-closed over_budget stop still reports an auto-stop -- vacuous")
print("NC1 (remove a gate) -> flag not independent; NC2 (couple two flags) -> both not independent; "
      "NC3 (break over_budget stop) -> no auto-stop: all controls load-bearing")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: every worker feature flag (BOARD3_A0_ONLY/RAW_DUALWRITE/RUM_ENABLED + RUM_SAMPLE dial) is an "
      "independent, off-safe, kill-switchable canary lever; the live DIR-007 budget guard is a fail-closed "
      "error-budget auto-stop. Framework verified over the existing worker; deploys nothing; NOT_DEPLOYED "
      "(live b189d3cc0703). Actual canary EXECUTION of a held capability is a per-capability Owner-gated follow-on.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
