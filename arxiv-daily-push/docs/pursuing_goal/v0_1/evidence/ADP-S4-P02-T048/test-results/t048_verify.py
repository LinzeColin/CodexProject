#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P02-T048 acceptance: A0 history attachment / revision / effectivity QA Gate.

Acceptance (TASK_INDEX): 100 个附件可读；修订链和 as-of 样本正确；0 个未解释 P0 缺口。
Deterministic re-check (no network -- the live attachment readback is cached by
discover_attachments.py into evidence/.../attachment_readback.json). Verifies the A0 backfilled
history is real, readable, versioned, and point-in-time-resolvable; production is untouched.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import a0_qa_gate as Q

fails = []
pack = Q.build_pack()
gates = {g["name"]: g for g in pack["gates"]}

# --- 1) 100 attachments readable -------------------------------------------------------------
ag = gates["attachment_gate"]
print(f"[attachment_gate] readable={ag.get('readable_count')} distinct_sha256={ag.get('distinct_sha256')} "
      f"target={ag['target']} by_source={ag.get('by_source')} by_magic={ag.get('by_magic')}")
if not ag["passed"]:
    fails.append(f"attachment gate: {ag['reason']}")

# --- 2) revision-chain samples correct -------------------------------------------------------
rg = gates["revision_gate"]
print(f"[revision_gate] passed={rg['passed']}")
for s in rg["samples"]:
    print(f"    - {s['kind']}: correct={s['correct']}")
if not rg["passed"]:
    fails.append(f"revision gate: {rg['reason']}")

# --- 3) as-of samples correct (no future-version leakage) ------------------------------------
og = gates["as_of_gate"]
print(f"[as_of_gate] chains={og['chains']} samples={og['samples']} future_leakage={og['future_leakage']} "
      f"oracle_disagreements={og['oracle_disagreements']} ordering_ok={og['ordering_ok']} "
      f"control_catches_broken={og['control_catches_broken']} malformed_rejected={og['malformed_rejected']}")
if not og["passed"]:
    fails.append(f"as-of gate: {og['reason']}")
# non-tautology guards: the leak check must catch a deliberately-broken resolver, agree with an
# independent oracle, and reject malformed dates -- else "0 leakage" would prove nothing.
if not og["control_catches_broken"]:
    fails.append("as-of gate is tautological: broken resolver not caught by the leak check")
if og["oracle_disagreements"] != 0:
    fails.append("as-of resolver disagrees with the independent oracle")
if not og["malformed_rejected"]:
    fails.append("as-of gate does not reject malformed observed_at")

# --- 4) 0 unexplained P0 gaps (no ATTEMPTED cell silently dropped) ---------------------------
gg = gates["gap_gate"]
print(f"[gap_gate] cells={gg['cells']} months={gg['months']} attempted={gg['attempted_cells']} "
      f"silent_holes={gg['silent_holes']} fetch_failed_surfaced={gg['fetch_failed_surfaced']}/{gg['attempted_failures']} "
      f"control_detects_silent_hole={gg['control_detects_silent_hole']} unexplained_p0={gg['unexplained_p0']} reasons={gg['reasons']}")
if not gg["passed"]:
    fails.append(f"gap gate: {gg['reason']}")
# informativeness guards: real attempted-failures must be surfaced (not hidden), and the silent-hole
# detector must provably fire on a realistic mutation -- else "0 gaps" would be vacuous.
if gg["fetch_failed_surfaced"] != gg["attempted_failures"]:
    fails.append("gap gate hides a real attempted failure (ndrc/cac not surfaced as fetch_failed)")
if not gg["control_detects_silent_hole"]:
    fails.append("gap gate is vacuous: silent-hole detector does not fire on a realistic mutation")

print("\ncorpus_docs =", pack["corpus_docs"], "| all_gates_passed =", pack["all_passed"])
print("ACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
