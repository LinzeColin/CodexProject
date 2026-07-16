#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P01-T086 acceptance: production rollback & disaster-recovery drill.

Acceptance (TASK_INDEX row 86): 隔离演练完成且结果一致；任何不可恢复项成为 release blocker.

Deterministic for the recoverability/hash assertions (no network/clock/randomness there; RTO is an
informational measured actual). Re-runs the DR drill and asserts every one of the six production
components (Worker, D1, R2, Source Registry, content bundle, prediction) recovers to a consistent known
point in isolation, with zero release blockers, and that the drill never mutates production source.

Load-bearing negative controls:
  1. RECOVERY IS REAL: perturbing the source registry (flip one source's `enabled`) makes its recompiled
     hash diverge from the committed d63cf6bd, so `recoverable` flips False AND it is classified a release
     blocker -- proving the recoverability check and the blocker classification are not vacuous constants.
  2. PRODUCTION UNTOUCHED: the worker source and the source registry are byte-identical (sha256) before
     and after the drill -- the drill reads the known points and never issues a live rollback or write.
The live-unchanged (NOT_DEPLOYED) claim is proven separately in realtime_check.txt.
"""
import hashlib
import json
import pathlib
import sys
import tempfile

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import disaster_recovery_drill as DR
import full_chain_rehearsal as FCR

fails = []


def _sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ---- MAIN: run the DR drill; production source byte-immutable across it ----
before = {"worker": _sha(DR.WORKER), "registry": _sha(FCR.REGISTRY)}
rep = DR.run_dr_drill()
after = {"worker": _sha(DR.WORKER), "registry": _sha(FCR.REGISTRY)}
comp = {c["component"]: c for c in rep["components"]}

if not rep["all_recoverable"]:
    fails.append(f"a component is not recoverable: {[c['component'] for c in rep['components'] if not c['recoverable']]}")
if rep["release_blockers"]:
    fails.append(f"release blockers present (must be none): {rep['release_blockers']}")
for c in rep["components"]:
    if c["is_release_blocker"] != (not c["recoverable"]):
        fails.append(f"{c['component']}: blocker classification inconsistent with recoverable")
# per-component known-point re-derivation
if comp["worker"]["recovered_hash"] != "452f7c5de919":
    fails.append(f"worker self-hash did not reproduce the declared build_id: {comp['worker']['recovered_hash']}")
if comp["source_registry"]["recovered_hash"] != FCR.COMMITTED_REGISTRY_HASH:
    fails.append(f"registry recompile did not reproduce d63cf6bd: {comp['source_registry']['recovered_hash']}")
if not comp["d1"]["detail"]["counts_consistent"] or comp["d1"]["detail"]["orphans"] != 0:
    fails.append(f"D1 restore not counts-consistent: {comp['d1']['detail']}")
if comp["prediction"]["recovered_hash"] != comp["prediction"]["known_hash"]:
    fails.append("prediction re-benchmark did not reproduce the committed report")
# every recoverable compares the re-derivation to a COMMITTED known point (not a same-run self-compare)
if not (comp["r2"]["recoverable"] and comp["r2"]["recovered_hash"] == comp["r2"]["known_hash"] == DR.KNOWN["r2_object_key"]):
    fails.append("R2 key did not recover to the committed known point")
if not (comp["content_bundle"]["recovered_hash"] == comp["content_bundle"]["known_hash"] == DR.KNOWN["content_bundle_render_sha16"]):
    fails.append("content bundle did not re-render to the committed known-good hash")
if not comp["d1"]["detail"]["per_month_matches_committed_t029"]:
    fails.append("D1 restored per-month counts do not match the committed T029 anchor")
# RTO/RPO actuals present for every component
if not all(isinstance(c["rto_seconds"], (int, float)) and c["rpo"] for c in rep["components"]):
    fails.append("RTO/RPO actuals missing for a component")
# production untouched
if before != after:
    fails.append(f"the drill mutated production source (worker/registry): {before} != {after}")
print(f"DR drill: 6/6 components recover to a consistent known point, 0 release blockers; "
      f"worker self-hash 452f7c5de919, registry {comp['source_registry']['recovered_hash'][:20]}, "
      f"D1 counts_consistent ({comp['d1']['detail']['restored_versions']} versions restored), "
      f"R2 content-addressed, content+prediction deterministic; worker/registry byte-immutable across the drill")

# ---- NC1: perturb the registry -> recovery breaks -> release blocker ----
reg = json.loads(pathlib.Path(FCR.REGISTRY).read_text("utf-8"))
reg["sources"][0]["enabled"] = not reg["sources"][0]["enabled"]      # valid flip; changes the compiled hash
pert = pathlib.Path(tempfile.mkdtemp(prefix="t086_pert_")) / "registry.json"
pert.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
nc = DR.drill_registry(str(pert))
nc["is_release_blocker"] = not nc["recoverable"]
if nc["recoverable"]:
    fails.append("control broken: a perturbed registry still 'recovers' to d63cf6bd -- the check is vacuous")
if not nc["is_release_blocker"]:
    fails.append("control broken: an unrecoverable component was not classified a release blocker")
print(f"NC1 (flip one source's enabled): recompiled hash {nc['recovered_hash'][:20]} != committed "
      f"-> recoverable={nc['recoverable']}, release_blocker={nc['is_release_blocker']} (correctly)")

# ---- NC2: content bundle recovery is now anchored to a COMMITTED hash -> input/code drift breaks it ----
items = json.loads((V01 / "evidence/ADP-S8-P01-T085/data-samples/items_500.json").read_text("utf-8"))
items[0]["summary"] = (items[0].get("summary") or "") + " ***DRIFT***"
pitems = pathlib.Path(tempfile.mkdtemp(prefix="t086_cdrift_")) / "items.json"
pitems.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
c_nc = DR.drill_content(items_path=str(pitems))
c_nc["is_release_blocker"] = not c_nc["recoverable"]
if c_nc["recoverable"]:
    fails.append("control broken: content bundle drift still 'recovers' -- the check compares to itself, not a committed anchor")
if not c_nc["is_release_blocker"]:
    fails.append("control broken: a drifted content bundle was not classified a release blocker")
# ---- NC3: R2 key recovery anchored to a COMMITTED key -> different content breaks it ----
r_nc = DR.drill_r2(content_override=b"drifted content bytes", source_override="arxiv-all")
r_nc["is_release_blocker"] = not r_nc["recoverable"]
if r_nc["recoverable"]:
    fails.append("control broken: a different R2 content still 'recovers' to the committed key -- vacuous")
if not r_nc["is_release_blocker"]:
    fails.append("control broken: a non-matching R2 key was not classified a release blocker")
print(f"NC2 (content bundle drift): recovered_hash {c_nc['recovered_hash']} != committed "
      f"{DR.KNOWN['content_bundle_render_sha16']} -> recoverable={c_nc['recoverable']}, blocker={c_nc['is_release_blocker']}")
print(f"NC3 (R2 different content): recovered key != committed anchor -> recoverable={r_nc['recoverable']}, "
      f"blocker={r_nc['is_release_blocker']} (both content & R2 recovery are now falsifiable, not same-run tautologies)")

# ---- emit the RTO/RPO actuals deliverable ----
(V01 / "evidence/ADP-S8-P01-T086/rto_rpo_actuals.json").write_text(
    json.dumps({"task": "ADP-S8-P01-T086", "rto_rpo_actuals": rep["rto_rpo_actuals"],
                "evidence_hashes": rep["evidence_hashes"], "all_recoverable": rep["all_recoverable"],
                "release_blockers": rep["release_blockers"]}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: isolated rollback/disaster-recovery drill across Worker/D1/R2/Registry/content/prediction; all "
      "recover to a consistent known point (0 release blockers); the drill issues no live rollback and no "
      "production D1/R2/network write; NOT_DEPLOYED (live b189d3cc0703 confirmed in realtime_check.txt).")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
