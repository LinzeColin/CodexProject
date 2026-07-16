#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T059 acceptance: cross-board Evidence Relations.

Acceptance (TASK_INDEX): 每条关系有文档/片段依据；无证据推断明确标记或不保存。
Deterministic. Verifies every SAVED relation carries document + fragment evidence, an evidence-free
assertion is explicitly marked (inferred_unsaved) and NOT in the saved graph, and the graph is bounded
(off-vocabulary relations and unknown board kinds are refused, so no boundless edges).
"""
import sys, json, pathlib, importlib.util
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import evidence_relation as R

T059 = V01 / "evidence" / "ADP-S5-P01-T059"
# re-derive from the tool (load the real assertions) so the report cannot be hand-edited to pass
spec = importlib.util.spec_from_file_location("br", str(T059 / "build_relations.py"))
br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)
g = R.build_graph(br.ASSERTIONS)
audit = g["audit"]
saved = [r for r in audit if r["status"] == "saved"]
fails = []
print(f"assertions={g['assertions_in']} saved={g['saved']} refused={g['refused']} "
      f"inferred_unsaved={g['inferred_unsaved']} every_saved_has_evidence={g['every_saved_has_evidence']}")

# --- 1) every SAVED relation has document/fragment evidence -----------------------------------
if not saved:
    fails.append("no relations saved")
for r in saved:
    ev = r.get("evidence") or {}
    if not (ev.get("doc_id") and (ev.get("fragment") or "").strip()):
        fails.append(f"{r['rel_id']}: saved without document/fragment evidence")
if not g["every_saved_has_evidence"]:
    fails.append("every_saved_has_evidence flag is False")
# and the saved graph contains exactly the saved relations (no unsourced edge leaked in)
if set(g["graph"]) != {r["rel_id"] for r in saved}:
    fails.append("saved graph contains edges that are not evidence-backed saved relations")

# --- 2) evidence-free assertion -> explicitly marked and NOT saved ---------------------------
inferred = [r for r in audit if r["status"] == "inferred_unsaved"]
if not inferred:
    fails.append("no evidence-free assertion exercised -> the no-evidence path is untested")
for r in inferred:
    if r.get("evidence") is not None:
        fails.append(f"{r['rel_id']}: inferred relation still carries (fake) evidence")
    if r["rel_id"] in g["graph"]:
        fails.append(f"{r['rel_id']}: an evidence-free inference was SAVED into the graph (unfounded edge)")

# --- 3) BOUNDED graph: off-vocabulary + unknown-kind assertions refused -----------------------
refused = [r for r in audit if r["status"] == "refused"]
if not any("off-vocabulary" in r["reason"] for r in refused):
    fails.append("an off-vocabulary relation was not refused (graph is unbounded)")
if not any("unknown board kind" in r["reason"] for r in refused):
    fails.append("an unknown board kind was not refused")
for r in refused:
    if r["rel_id"] in g["graph"]:
        fails.append(f"{r['rel_id']}: a refused relation leaked into the graph")

# --- 4) deliverables: relation types (bounded vocabulary) + query examples -------------------
if len(g["relation_types"]) < 4:
    fails.append("relation type vocabulary is too small to be a real bounded schema")
# query returns evidence-backed edges only
qexamples = R.query(g["graph"], predicate="procurement_under")
if not qexamples or any(not (e.get("evidence") or {}).get("doc_id") for e in qexamples):
    fails.append("query returned an edge without evidence")

# --- 5) negative control: adding a no-evidence relation never enters the saved graph ----------
g2, rec = R.add_relation(dict(g["graph"]), "P", "policy", "implements", "Q", "policy", evidence=None)
if rec["status"] != "inferred_unsaved" or len(g2) != len(g["graph"]):
    fails.append("a no-evidence relation was saved (evidence rule not enforced)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
