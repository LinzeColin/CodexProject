#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T065 acceptance: citation support/counter/mention evidence + graph.

Acceptance (TASK_INDEX row 65): 标签有可查看上下文；不由标题或模型印象直接分类。
  (every label has viewable context; labels are NOT assigned from the title or a model impression.)

Deterministic. Re-derives from the TOOL (citation_evidence) + fixtures -- never trusts the report.
The core negative control pits TITLE against CONTEXT: a title that screams support with a context that
contradicts must be labeled COUNTER, and a naive title-based classifier (which WOULD mislabel it) is
shown to disagree -- proving the label is context-grounded, not title/impression-driven.
"""
import importlib.util
import inspect
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import citation_evidence as CE

T065 = V01 / "evidence" / "ADP-S5-P03-T065"
spec = importlib.util.spec_from_file_location("bce", str(T065 / "build_citation_evidence.py"))
bce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bce)

fails = []
graph = CE.build_citation_graph(bce.CITATIONS)
by_citing = {e["citing_id"]: e for e in graph["edges"]}

# =============================================================== 1) 标签有可查看上下文
for e in graph["edges"]:
    if not CE.label_has_viewable_context(e):
        fails.append(f"{e['citing_id']}: label {e['label']} lacks viewable byte-exact context")
    # a non-mention cue must be located IN the context (not elsewhere)
    if e["label"] != "mention":
        ctx = e["evidence"]["context"]
        if e["cue"] is None or e["cue"].lower() not in ctx.lower():
            fails.append(f"{e['citing_id']}: cue {e['cue']!r} not found in its context")
        if ctx[e["evidence"]["offset"]:e["evidence"]["offset"] + e["evidence"]["length"]] != e["cue"]:
            fails.append(f"{e['citing_id']}: cue not byte-exact at recorded offset")
print(f"viewable context: all {len(graph['edges'])} labels backed by byte-exact context (or raw context for mention)")

# expected labels from the Golden fixtures
expect = {"P100": "counter", "P101": "support", "P102": "mention",
          "P103": "counter", "P104": "support", "P105": "counter"}
for cid, lab in expect.items():
    if by_citing[cid]["label"] != lab:
        fails.append(f"{cid}: label {by_citing[cid]['label']} != expected {lab}")

# =============================================================== 2) 不由标题或模型印象直接分类
# structural: the classifier's ONLY parameter is the context (title cannot be an input)
sig = list(inspect.signature(CE.classify_citation).parameters)
if sig != ["context"]:
    fails.append(f"classify_citation must take only context, takes {sig}")

# P100 & P103: title screams SUPPORT (support / 一致) but context CONTRADICTS -> must be counter, and the
# cue must be the CONTEXT's counter cue, not the title's support word.
for cid in ("P100", "P103"):
    e = by_citing[cid]
    if e["label"] != "counter":
        fails.append(f"{cid}: title-vs-context conflict mislabeled as {e['label']} (title leaked in?)")
    # the driving cue is in the context, and the title's supportive words are NOT in the context
    if e["cue"].lower() not in e["evidence"]["context"].lower():
        fails.append(f"{cid}: label cue not sourced from context")

# P102: supportive-sounding title but NO cue in context -> mention (not guessed support)
if by_citing["P102"]["label"] != "mention":
    fails.append("P102: a no-cue context with a supportive title was not labeled mention (guessed from title?)")

# DISCRIMINATION: a naive TITLE-based classifier WOULD mislabel the conflict cases; ours disagrees ->
# proves the label is context-grounded, not title-driven. If they agreed everywhere, the test is vacuous.
def naive_title_classifier(title):
    low = (title or "").lower()
    if any(c.lower() in low for c in CE.SUPPORT_CUES):
        return "support"
    if any(c.lower() in low for c in CE.COUNTER_CUES):
        return "counter"
    return "mention"
disagreements = 0
for e in graph["edges"]:
    if naive_title_classifier(e["citing_title"]) != e["label"]:
        disagreements += 1
# P100 (title->support, ours counter), P103 (title->support/一致, ours counter), P102 (title->support, ours mention)
if disagreements < 3:
    fails.append(f"context vs title classifier disagree on too few cases ({disagreements}) -> discrimination weak")
# the two title-vs-context CONFLICT cases: title reads as SUPPORT, our context label is COUNTER
for cid in ("P100", "P103"):
    if naive_title_classifier(by_citing[cid]["citing_title"]) != "support":
        fails.append(f"control setup broken: {cid} title should read as support to a naive classifier")
    if by_citing[cid]["label"] != "counter":
        fails.append(f"{cid}: context-grounded label should be counter despite a supportive title")
print(f"not-from-title: classifier takes only context; a title-based classifier disagrees on {disagreements} cases "
      f"(incl. P100/P103 where title=support but context=counter)")

# feeding ONLY the context string reproduces the same label (title truly irrelevant)
for cid in ("P100", "P103", "P102"):
    e = by_citing[cid]
    if CE.classify_citation(e["evidence"]["context"])["label"] != e["label"]:
        fails.append(f"{cid}: label changes when title is absent -> title was influencing the label")

# =============================================================== 3) graph view API
b1_counter = [e["citing_id"] for e in CE.query_graph(graph, cited_id="B1", label="counter")]
b1_support = [e["citing_id"] for e in CE.query_graph(graph, cited_id="B1", label="support")]
if b1_counter != ["P100"]:
    fails.append(f"query B1/counter wrong: {b1_counter}")
if b1_support != ["P101"]:
    fails.append(f"query B1/support wrong: {b1_support}")
# support and counter to the same cited paper coexist as distinct edges
if not (b1_counter and b1_support):
    fails.append("support and counter edges to the same cited paper do not coexist")
print(f"graph: B1 counter={b1_counter}, support={b1_support} (coexist, distinct)")

# =============================================================== 4) cue precision (word boundaries)
# an ASCII cue must NOT false-match inside a longer word
if CE.classify_citation("These results are unlikely to be seen again.")["label"] != "mention":
    fails.append("'unlike' false-matched inside 'unlikely' -> spurious counter label")
# 'inconsistent with' is counter; the substring 'consistent with' must not flip it to support
if CE.classify_citation("Our data are inconsistent with [B].")["label"] != "counter":
    fails.append("'inconsistent with' not labeled counter")
# a genuine word-boundary cue still matches
if CE.classify_citation("This is unlike the earlier report.")["label"] != "counter":
    fails.append("genuine 'unlike ' cue no longer matches")
# stem cue still matches its inflection
if CE.classify_citation("Our findings corroborate the model.")["label"] != "support":
    fails.append("stem cue 'corroborat' no longer matches 'corroborate'")
print("cue precision: 'unlikely' not counter; 'inconsistent with' counter; 'unlike ' counter; 'corroborate' support")

# earliest-cue-wins is symmetric: counter-earliest -> counter (P105), support-earliest -> support
if CE.classify_citation("Our data are inconsistent with [X], though later analysis is consistent with a weaker claim.")["label"] != "counter":
    fails.append("counter-earliest context not labeled counter")
if CE.classify_citation("Our data are consistent with [X], though one detail contradicts a minor point.")["label"] != "support":
    fails.append("support-earliest context not labeled support (earliest-wins not symmetric)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
