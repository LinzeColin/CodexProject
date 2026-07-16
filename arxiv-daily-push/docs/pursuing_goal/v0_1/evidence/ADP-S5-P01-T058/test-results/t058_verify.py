#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T058 acceptance: cross-source entity resolution.

Acceptance (TASK_INDEX): 错误合并可撤销；实体来源和置信边界可追溯。
Deterministic. Verifies (1) a WRONG merge is exactly reversible via split, (2) every entity's aliases
carry per-source provenance (nothing unsourced), and (3) the confidence boundary holds: a
low-confidence merge is NOT auto-applied (held for review) while a high-confidence one is.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import entity_resolver as ER

T058 = V01 / "evidence" / "ADP-S5-P01-T058"
rep = json.loads((T058 / "entity_report.json").read_text(encoding="utf-8"))
fails = []
print(f"mentions={rep['mentions_in']} entities={rep['entities_out']} "
      f"audit={rep['merge_split_audit']['wrong_merge_applied']}/{rep['merge_split_audit']['wrong_merge_reversible']} "
      f"low_conf={rep['merge_split_audit']['low_confidence_merge_status']}")

# re-derive from the tool (load the real MENTIONS) so the report cannot be hand-edited to pass
import importlib.util
spec = importlib.util.spec_from_file_location("be", str(T058 / "build_entities.py"))
be = importlib.util.module_from_spec(spec); spec.loader.exec_module(be)
ents = ER.resolve(be.MENTIONS)

# --- schema: every entity has the required fields ---------------------------------------------
for e in ents.values():
    for k in ("entity_id", "type", "canonical_name", "aliases", "provenance", "confidence"):
        if k not in e:
            fails.append(f"{e.get('canonical_name')}: missing schema field {k}")

# --- cross-source resolution: aliases from different sources unified --------------------------
# 国家统计局 must have absorbed the standalone 'NBS' mention (from media-x)
nbs = next((e for e in ents.values() if "NBS" in e["aliases"]), None)
if not nbs or "国家统计局" not in nbs["aliases"]:
    fails.append("cross-source alias NBS did not unify into 国家统计局")
srcs = {p["source_id"] for p in nbs["provenance"]} if nbs else set()
if not {"stats-gov", "media-x"} <= srcs:
    fails.append(f"unified entity missing multi-source provenance ({srcs})")

# --- 1) WRONG merge is exactly reversible via split -------------------------------------------
ids = list(ents)
a, b = ids[0], ids[2]
merged, audit = ER.merge(ents, a, b, evidence="operator error", confidence=0.95)
if audit["status"] != "applied" or len(merged) != len(ents) - 1:
    fails.append("high-confidence merge was not applied")
restored = ER.split(merged, audit)
if not (a in restored and b in restored and len(restored) == len(ents)):
    fails.append("split did not restore both pre-merge entities")
if not (restored[a] == ents[a] and restored[b] == ents[b]):
    fails.append("split did not restore entities EXACTLY (wrong merge not fully reversible)")

# --- 2) provenance traceable: every alias -> >=1 source, nothing unsourced --------------------
for e in ents.values():
    prov = ER.provenance_of(e)
    if set(prov) != set(e["aliases"]):
        fails.append(f"{e['canonical_name']}: not every alias has provenance")
    if any(not s for s in prov.values()):
        fails.append(f"{e['canonical_name']}: an alias has no source (unsourced)")

# --- 3) confidence boundary: low-confidence merge NOT auto-applied ----------------------------
_, weak = ER.merge(ents, a, b, evidence="weak", confidence=0.5)
if weak["status"] != "pending_review":
    fails.append("a below-threshold merge was auto-applied (confidence boundary not enforced)")
_, strong = ER.merge(ents, a, b, evidence="strong", confidence=0.95)
if strong["status"] != "applied":
    fails.append("an above-threshold merge was not applied (boundary too strict / broken)")
if not (0.0 < ER.AUTO_MERGE_MIN < 1.0):
    fails.append("AUTO_MERGE_MIN is not a real (0,1) confidence boundary")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
