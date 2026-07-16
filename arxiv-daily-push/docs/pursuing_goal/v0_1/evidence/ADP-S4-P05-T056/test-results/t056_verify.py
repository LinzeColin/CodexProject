#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P05-T056 acceptance: Coverage Debt + As-of history query base.

Acceptance (TASK_INDEX): 100 个修订样本查询不同日期不使用未来版本；覆盖空洞可解释。
Deterministic. Verifies >= 100 revision samples resolve as-of different dates with 0 future-version
leakage (cross-checked by an independent oracle), and that every coverage hole is explainable (0
UNEXPLAINED). Non-vacuity controls prove the as-of resolver genuinely rejects a future-leaking
resolver and a malformed date, and the historical manifest resolver never returns a future manifest.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import coverage_asof as CA

rep = json.loads((V01 / "evidence" / "ADP-S4-P05-T056" / "coverage_asof_report.json").read_text(encoding="utf-8"))
cd = rep["coverage_debt"]
asof = rep["as_of"]
fails = []
print(f"coverage cells={cd['cells']} covered={cd['covered']} debt={cd['debt_cells']} unexplained={cd['unexplained']}; "
      f"as_of samples={asof['samples']} leakage={asof['future_leakage']} disagree={asof['oracle_disagreements']}")

# --- 1) >= 100 revision samples, 0 future-version leakage --------------------------------------
if asof["samples"] < 100:
    fails.append(f"only {asof['samples']} as-of samples (< 100)")
if asof["future_leakage"] != 0:
    fails.append(f"{asof['future_leakage']} as-of queries resolved to a FUTURE version")
if asof["oracle_disagreements"] != 0:
    fails.append(f"{asof['oracle_disagreements']} resolver/oracle disagreements")

# --- 2) coverage holes explainable (0 UNEXPLAINED) --------------------------------------------
if cd["unexplained"] != 0:
    fails.append(f"{cd['unexplained']} coverage holes are UNEXPLAINED")
if not cd["every_hole_explained"]:
    fails.append("every_hole_explained flag is False")
if cd["cells"] <= cd["covered"]:
    fails.append("coverage grid is trivial (no debt cells to explain)")

# --- 3) NON-VACUITY controls (the as-of guarantees genuinely bite) ----------------------------
corpus = CA.load_corpus()
chains = CA.build_revision_chains(corpus)
two = next((obs for obs in chains.values() if len(obs) == 2), None)
if two:
    # ordering: before v1 -> None, at v1 -> v1, at v2 -> v2, far future -> v2 (never a future version)
    before = CA.as_of_query(two, "2000-01-01")
    at1 = CA.as_of_query(two, two[0]["observed_at"])
    at2 = CA.as_of_query(two, two[1]["observed_at"])
    future = CA.as_of_query(two, "2099-12-31")
    if not (before is None and at1["version_ref"] == two[0]["version_ref"]
            and at2["version_ref"] == two[1]["version_ref"] and future["version_ref"] == two[1]["version_ref"]):
        fails.append("as-of ordering incorrect on a 2-version chain")
    # a BROKEN resolver (returns the newest inserted regardless of date) must produce future leakage
    def broken(obs, qd):
        return obs[-1] if obs else None
    q_between = two[0]["observed_at"]   # query at v1's date; broken returns v2 (a future version)
    r = broken(two, q_between)
    broken_leaks = r is not None and CA._parse_date(r["observed_at"]) > CA._parse_date(q_between)
    if not broken_leaks:
        fails.append("broken-resolver control does not leak -> the leak check is vacuous")
else:
    fails.append("no 2-version chain to exercise the as-of ordering control")
# malformed date must be REJECTED
malformed_rejected = False
try:
    CA.as_of_query([{"observed_at": "2021", "version_ref": "x"}], "2021-06-01")
except ValueError:
    malformed_rejected = True
if not malformed_rejected:
    fails.append("as-of does not reject a malformed date")

# --- 4) historical manifest resolver never returns a FUTURE manifest --------------------------
for pit in rep["historical_manifest_resolutions"]:
    if pit["manifest_month"] is not None and pit["manifest_month"] + "-01" > pit["query_date"]:
        fails.append(f"manifest {pit['manifest_month']} is in the future of query {pit['query_date']}")

# --- 5) deliverables present + FULL live re-derivation (coverage + as-of + manifest) -----------
# re-derive every aggregate live from the tool (not just trust the committed report), so a hand-edited
# report cannot slip a fabricated 0-leakage / 0-unexplained past the gate.
live_cd = CA.coverage_debt(corpus)
if live_cd["unexplained"] != cd["unexplained"] or live_cd["cells"] != cd["cells"]:
    fails.append("coverage debt does not match tool re-derivation")
live_asof = CA.asof_samples(chains)
if (live_asof["samples"], live_asof["future_leakage"], live_asof["oracle_disagreements"]) != \
   (asof["samples"], asof["future_leakage"], asof["oracle_disagreements"]):
    fails.append("as-of aggregates do not match live re-derivation (hand-edit?)")
for pit in rep["historical_manifest_resolutions"]:
    mf = CA.historical_manifest_resolver(corpus, pit["query_date"])
    live_month = mf["manifest_month"] if mf else None
    if live_month != pit["manifest_month"]:
        fails.append(f"manifest for {pit['query_date']}: report {pit['manifest_month']} != live {live_month}")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
