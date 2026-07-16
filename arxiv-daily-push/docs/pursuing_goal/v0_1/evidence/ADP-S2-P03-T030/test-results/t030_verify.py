#!/usr/bin/env python3
"""ADP-S2-P03-T030 acceptance: orchestration reliability + cost decision.

Acceptance (TASK_INDEX): Workflows 只有在可靠性收益高于新增步骤费用和维护复杂度时采用；否则保持简单路径。
Deliverables: at-least-once envelope + DLQ + idempotency test + step/operation cost benchmark + ADR.
Deterministic; no clock/random/network.
"""
import sys, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import idempotency_harness as H  # noqa: E402

fails = []
sim = H.simulate()
cost = H.cost_benchmark()

print("reliability sim:", {k: sim[k] for k in ("n_tasks", "deliveries", "applied_effects", "dlq",
      "duplicates_happened", "exactly_once_effect", "poison_all_in_dlq", "no_effect_applied_twice")})

# 1) at-least-once envelope actually exercised (duplicates delivered)
if not sim["duplicates_happened"]:
    fails.append("no duplicate deliveries -> at-least-once not exercised")
# 2) idempotency test: exactly-once effect under duplicates
if not sim["exactly_once_effect"]:
    fails.append("exactly-once effect NOT achieved on the free idempotent path")
if not sim["no_effect_applied_twice"]:
    fails.append("an effect was applied more than once (idempotency broken)")
# 3) DLQ: poison messages land in DLQ, effect never applied
if not sim["poison_all_in_dlq"]:
    fails.append("poison messages not all routed to DLQ")
if sim["dlq"] < 1:
    fails.append("DLQ never exercised")

# 4) cost benchmark distinguishes free vs paid and encodes DIR-007
A = cost["paths"]["A_cron_d1_idempotent_FREE"]
B = cost["paths"]["B_cron_queue_PAID"]
C = cost["paths"]["C_workflows_PAID"]
print("cost paths: A free =", not A["requires_paid_plan"], A["dir007_free_tier_ok"],
      "| B paid =", B["requires_paid_plan"], "| C paid =", C["requires_paid_plan"])
if A["requires_paid_plan"] or not A["dir007_free_tier_ok"]:
    fails.append("Path A (free) mis-classified")
if not (B["requires_paid_plan"] and C["requires_paid_plan"]):
    fails.append("Queues/Workflows not flagged as requiring the paid plan")
if B["dir007_free_tier_ok"] or C["dir007_free_tier_ok"]:
    fails.append("paid paths wrongly marked DIR-007 free-tier ok")
# B/C add extra steps/ops over A (added complexity/cost)
if not (B["extra_steps"] > A["extra_steps"] and C["extra_steps"] > A["extra_steps"]):
    fails.append("paid paths do not show added steps over the simple path")

# 5) decision keeps the simple path (Workflows only if reliability beats cost -- here it does not)
if not (cost["decision_inputs"]["reliability_gap_on_A"].startswith("none")):
    fails.append("decision inputs claim a reliability gap that the simulation did not show")

# 6) ADR + machine report exist
if not (V01 / "ORCHESTRATION_ADR.md").exists():
    fails.append("ORCHESTRATION_ADR.md missing")

print("\ndecision: keep Path A (free Cron+idempotent+D1 DLQ); do NOT adopt Queues/Workflows (paid, DIR-007-blocked, no reliability gain)")
print("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
