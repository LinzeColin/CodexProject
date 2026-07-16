#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T052 acceptance: A1 Coverage/Quality/Cost gate.

Acceptance (TASK_INDEX): 官方身份 100%；质量/及时/成本均有实际证据；决定可回滚。
Deterministic. Verifies 100% official A1 identity, that each decision is backed by actual evidence
(promote only on real backfilled documents; hold on identity-without-docs; disable on a real
failure), and that decisions are reversible (NOT_DEPLOYED). Negative controls prove promotion is not
handed out on value alone or to a failed source.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import a1_scorecard as SC

sc = json.loads((V01 / "evidence" / "ADP-S4-P03-T052" / "a1_scorecard.json").read_text(encoding="utf-8"))
rows = sc["scorecard"]
fails = []
print(f"sources_scored={sc['sources_scored']} identity_rate={sc['official_identity_rate']} decisions={sc['decisions']}")

# --- 1) OFFICIAL IDENTITY 100% ---------------------------------------------------------------
if sc["official_identity_rate"] != 1.0:
    fails.append(f"official identity rate {sc['official_identity_rate']} != 100%")
for r in rows:
    if r["official_identity"] != "A1":
        fails.append(f"{r['source_id']}: scored but not A1")

# --- 2) every decision has ACTUAL EVIDENCE (quality/timeliness/cost); unknown != 0 -----------
promoted = [r for r in rows if r["decision"] == "promote"]
held = [r for r in rows if r["decision"] == "hold"]
disabled = [r for r in rows if r["decision"] == "disable"]
print(f"promote={len(promoted)} hold={len(held)} disable={len(disabled)}")
for r in promoted:
    q = r["quality"]
    if not (isinstance(q.get("docs_backfilled"), int) and q["docs_backfilled"] >= 1
            and q.get("content_addressed_A1") == q["docs_backfilled"]
            and r["timeliness"]["latest_month"]):
        fails.append(f"{r['source_id']}: PROMOTED without real document/timeliness evidence -> {q}")
for r in disabled:
    if "block" not in r["rationale"] and "fail" not in r["rationale"]:
        fails.append(f"{r['source_id']}: disabled without a real failure reason")
for r in rows:
    if "cost" not in r or r["cost"].get("production_new_requests") != 0:
        fails.append(f"{r['source_id']}: cost evidence missing/nonzero prod requests")

# --- 3) decisions REVERSIBLE (NOT_DEPLOYED; feature-flag; no prod rewrite) --------------------
if sc["deployment"] != "NOT_DEPLOYED":
    fails.append("gate is not NOT_DEPLOYED (decisions must be reversible)")
if not all(r.get("reversible") for r in rows):
    fails.append("a decision is not marked reversible")
if "rollback" not in sc["reversibility"].lower() and "revert" not in sc["reversibility"].lower():
    fails.append("no rollback/revert path stated")

# --- 4) NEGATIVE CONTROLS: promotion is earned, not given on value or to a failure ------------
# (a) a value-verified city with NO fetched original must be HELD, never promoted on value alone
city_promoted_without_docs = [r for r in rows if r["kind"] == "city"
                              and r["decision"] == "promote" and r["quality"].get("original_fetch_status") != "confirmed"]
if city_promoted_without_docs:
    fails.append(f"{len(city_promoted_without_docs)} city(ies) promoted on value alone (no confirmed original)")
if not held:
    fails.append("no source held -> the identity-without-docs -> hold path is untested")
# (b) the blocked province must be DISABLED, never promoted
if not disabled:
    fails.append("no source disabled -> the failure -> disable path is untested (blocked source should disable)")
# (c) re-derive from the tool so the scorecard was not hand-edited to pass
live = SC.build_scorecard()
if live["decisions"] != sc["decisions"] or live["sources_scored"] != sc["sources_scored"]:
    fails.append("scorecard does not match tool re-derivation (possible hand-edit)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
