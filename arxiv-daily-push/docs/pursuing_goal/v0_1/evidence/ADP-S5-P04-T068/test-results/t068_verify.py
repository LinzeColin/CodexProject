#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T068 acceptance: Knowledge Validity + 131-item benefit-parity regression.

Acceptance (TASK_INDEX row 68): 旧知识因源变化自动标失效/重学；131 项无'未知/无人负责'状态。
  (old knowledge auto-marks invalid/re-learn when its source changes; all 131 parity items have no
   'unknown / no-owner' status.)

Deterministic. Re-derives from the TOOL (knowledge_validity) + fixtures -- never trusts the report.
Negative controls prove discrimination: a noise-only source re-render must NOT invalidate knowledge
(no churn); an injected 'unknown'-status or 'no-owner' parity item must be CAUGHT by the gate.
"""
import copy
import importlib.util
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import knowledge_validity as KV
import version_engine as VE

T068 = V01 / "evidence" / "ADP-S5-P04-T068"
spec = importlib.util.spec_from_file_location("bkv", str(T068 / "build_knowledge_validity.py"))
bkv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bkv)

fails = []

# =============================================================== 1) Knowledge Validity clock
k = KV.make_knowledge("K1", "平台已上线", bkv.SRC_V1)
# unchanged source -> stays valid
if KV.check_validity(k, [bkv.SRC_V1])["validity"] != "valid":
    fails.append("knowledge on an unchanged source was not valid")
# NOISE-ONLY re-render -> stays valid (no spurious invalidation / no churn)
if KV.check_validity(k, [bkv.SRC_NOISE])["validity"] != "valid":
    fails.append("a noise-only re-render wrongly invalidated knowledge (churn)")
# SUBSTANTIVE source change -> auto needs_review (re-open old knowledge)
chg = KV.check_validity(k, [bkv.SRC_V2])
if chg["validity"] != "needs_review" or chg.get("reason") != "source_changed":
    fails.append(f"a substantive source change did not auto-invalidate: {chg['validity']}")
# source removed -> invalid
if KV.check_validity(k, [])["validity"] != "invalid":
    fails.append("a removed source did not invalidate knowledge")
# re-learn: revalidate re-binds to the new version and returns to valid
relearned = KV.revalidate(chg, "平台已上线并新增考核", bkv.SRC_V2)
if relearned["validity"] != "valid" or relearned["derived_from"]["source_version"] != VE.content_hash(bkv.SRC_V2):
    fails.append("revalidate did not re-bind re-learned knowledge to the new source version")
# discrimination: the clock is driven by T026 content_hash -> noise == v1 hash != v2 hash
if VE.content_hash(bkv.SRC_V1) != VE.content_hash(bkv.SRC_NOISE):
    fails.append("control broken: noise-only re-render should share v1's content_hash")
if VE.content_hash(bkv.SRC_V1) == VE.content_hash(bkv.SRC_V2):
    fails.append("control broken: v2 should differ substantively from v1")
print("validity: unchanged=valid, noise-only=valid (no churn), changed->needs_review, removed->invalid, re-learn->valid")

# =============================================================== 2) 131 项无 '未知/无人负责'
reg = bkv.build_registry()
rep = KV.parity_report(reg)
if rep["n_items"] != 131:
    fails.append(f"parity registry must have exactly 131 items, has {rep['n_items']}")
if rep["unknown_status"]:
    fails.append(f"parity items with an unknown/undefined status: {rep['unknown_status']}")
if rep["no_owner"]:
    fails.append(f"parity items with no owner: {rep['no_owner']}")
if rep["delivered_or_partial_missing_evidence"]:
    fails.append(f"delivered/partial items missing evidence: {rep['delivered_or_partial_missing_evidence']}")
if rep["planned_or_na_missing_note"]:
    fails.append(f"planned/not_applicable items missing a note/reason: {rep['planned_or_na_missing_note']}")
if not rep["clean"]:
    fails.append("parity report is not clean")
# every status is in the closed vocabulary (never 'unknown'); every owner is real
for i in reg["items"]:
    if i["status"] not in KV.PARITY_STATUSES:
        fails.append(f"{i['benefit_id']} status {i['status']!r} not in closed vocab")
    if not KV._owner_ok(i.get("owner")):
        fails.append(f"{i['benefit_id']} has a forbidden owner {i.get('owner')!r}")
# benefit_ids are unique
ids = [i["benefit_id"] for i in reg["items"]]
if len(set(ids)) != len(ids):
    fails.append("duplicate benefit_ids in the parity registry")
print(f"parity: {rep['n_items']} items, by_status={rep['by_status']}, clean={rep['clean']}")

# NEGATIVE CONTROL: the gate genuinely catches an 'unknown' status and a 'no-owner' item.
tainted = copy.deepcopy(reg)
tainted["items"][0] = {**tainted["items"][0], "status": "unknown"}
tainted["items"][1] = {**tainted["items"][1], "owner": "no-owner"}
trep = KV.parity_report(tainted)
if not trep["unknown_status"]:
    fails.append("gate failed to catch an 'unknown'-status parity item -> vacuous")
if not trep["no_owner"]:
    fails.append("gate failed to catch a 'no-owner' parity item -> vacuous")
if trep["clean"]:
    fails.append("a tainted registry was reported clean -> gate is a stub")
# also catch an empty/whitespace owner and an undefined status token
tainted2 = copy.deepcopy(reg)
tainted2["items"][2] = {**tainted2["items"][2], "owner": "   "}
tainted2["items"][3] = {**tainted2["items"][3], "status": "maybe"}
trep2 = KV.parity_report(tainted2)
if trep2["clean"] or not trep2["no_owner"] or not trep2["unknown_status"]:
    fails.append("gate missed a whitespace owner or an undefined status token")
# the gate also catches a planned item with no note/reason
tainted3 = copy.deepcopy(reg)
planned_idx = next(n for n, i in enumerate(reg["items"]) if i["status"] == "planned")
tainted3["items"][planned_idx] = {**tainted3["items"][planned_idx], "note": ""}
if not KV.parity_report(tainted3)["planned_or_na_missing_note"] or KV.parity_report(tainted3)["clean"]:
    fails.append("gate missed a planned item with no note/reason")
print(f"gate control: injected unknown-status + no-owner + blank owner + bad token + note-less planned all caught (clean=False)")

# the emitted parity_registry_131.json must equal the re-derived registry (no stale artifact)
emitted = json.loads((T068 / "parity_registry_131.json").read_text(encoding="utf-8"))
if emitted != reg:
    fails.append("emitted parity_registry_131.json does not match the re-derived build_registry() output")
print("emitted registry == re-derived build_registry() (no stale artifact)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
