#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T061 acceptance: FTS + semantic-rerank benchmark + adopt/reject ADR.

Acceptance (TASK_INDEX): 语义层必须提升固定查询集且不绕过结构化过滤；否则不采用。
Deterministic. Verifies the ADR rule genuinely gates: a semantic layer is ADOPTED only when it BOTH
improves the fixed query set AND respects structured filters; a non-improving one and a
filter-bypassing one are both REJECTED. Re-derives from the tool (not the report).
"""
import sys, json, importlib.util, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import fts_benchmark as FB

T061 = V01 / "evidence" / "ADP-S5-P02-T061"
# re-run the benchmark from the generator so the report cannot be hand-edited to pass
spec = importlib.util.spec_from_file_location("bb", str(T061 / "build_benchmark.py"))
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
corpus = bb.build_corpus()
fts = FB.build_fts(corpus)
queries = list(bb.TOPICS)
relevant = {q: bb._rel(corpus, q) for q in queries}
fts_res = bb.run_query_set(bb.semantic_identity, fts, queries, corpus)
fts_metrics = {"mrr": FB.mrr(fts_res, relevant), "recall@5": FB.recall_at_k(fts_res, relevant, 5)}
fails = []
print(f"corpus={len(corpus)} fts_baseline={fts_metrics}")

# --- 1) FTS benchmark produces real metrics on a fixed query set -----------------------------
if not (0.0 <= fts_metrics["mrr"] <= 1.0 and 0.0 <= fts_metrics["recall@5"] <= 1.0):
    fails.append("FTS metrics out of range")
if len(queries) < 5:
    fails.append("fixed query set too small")
# the FTS baseline must have a genuine miss (recall < 1) so improvement is measurable
if fts_metrics["recall@5"] >= 1.0:
    fails.append("FTS baseline is already perfect -> improvement is not measurable (contrived)")

# --- 2) ADR decisions: adopt iff (improves AND respects filters) -----------------------------
def eval_candidate(fn, bypass):
    res = bb.run_query_set(fn, fts, queries, corpus)
    m = {"mrr": FB.mrr(res, relevant), "recall@5": FB.recall_at_k(res, relevant, 5)}
    rf = False if bypass else bb.respects_filters(fn, fts, corpus, "江苏")
    return m, rf, FB.decide_adopt(fts_metrics, m, rf)

m_syn, rf_syn, d_syn = eval_candidate(bb.semantic_synonym, False)
m_id, rf_id, d_id = eval_candidate(bb.semantic_identity, False)
m_by, rf_by, d_by = eval_candidate(bb.semantic_bypass, True)
print(f"synonym: {m_syn} rf={rf_syn} adopt={d_syn['adopt']}")
print(f"identity: {m_id} rf={rf_id} adopt={d_id['adopt']}")
print(f"bypass: {m_by} rf={rf_by} adopt={d_by['adopt']}")

# adopted one must genuinely improve AND respect filters
if not d_syn["adopt"]:
    fails.append("an improving + filter-respecting semantic layer was NOT adopted")
if not (m_syn["recall@5"] > fts_metrics["recall@5"] or m_syn["mrr"] > fts_metrics["mrr"]):
    fails.append("the adopted semantic layer does not actually improve the fixed query set")
if not rf_syn:
    fails.append("the adopted semantic layer does not respect structured filters")

# --- 3) NEGATIVE CONTROLS: non-improving and filter-bypassing are REJECTED -------------------
if d_id["adopt"]:
    fails.append("a NON-improving semantic layer was adopted (ADR rule too weak)")
if d_by["adopt"]:
    fails.append("a filter-BYPASSING semantic layer was adopted (ADR rule too weak)")
# the ADR rule must require BOTH conditions: a would-be improver that bypasses filters is rejected
if FB.decide_adopt(fts_metrics, m_syn, semantic_respects_filters=False)["adopt"]:
    fails.append("an improving-but-filter-bypassing semantic layer was adopted (AND condition broken)")
# a filter-respecting non-improver is also rejected
if FB.decide_adopt(fts_metrics, fts_metrics, semantic_respects_filters=True)["adopt"]:
    fails.append("a non-improving (equal-metric) semantic layer was adopted (improvement not required)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
