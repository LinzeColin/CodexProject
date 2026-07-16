#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + report for ADP-S5-P03-T065 (citation support/counter/mention evidence).

The fixtures deliberately pit the citing paper's TITLE against the citation CONTEXT so the acceptance
"不由标题或模型印象直接分类" is testable: a title that screams support but a context that contradicts
must be labeled COUNTER; a no-cue context must be a MENTION regardless of a suggestive title.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import citation_evidence as CE

CITATIONS = [
    # C1: title suggests SUPPORT, but the CONTEXT contradicts -> must be COUNTER (context wins)
    {"citing_id": "P100", "cited_id": "B1",
     "citing_title": "This work supports and confirms the folding theory",
     "context": "Our experiments contradict the results reported by [B1], which we could not reproduce."},
    # C2: genuine support, cue in context
    {"citing_id": "P101", "cited_id": "B1",
     "citing_title": "Notes on decoding",
     "context": "These findings are consistent with [B1] and corroborate the proposed mechanism."},
    # C3: neutral mention, NO cue -> mention (even though title sounds supportive)
    {"citing_id": "P102", "cited_id": "B1",
     "citing_title": "We support and validate prior work extensively",
     "context": "The dataset was preprocessed as described in [B1]."},
    # C4: Chinese counter cue in context
    {"citing_id": "P103", "cited_id": "B2",
     "citing_title": "关于该方法的一致性研究",   # title says 一致 (consistent) ...
     "context": "本文的结论与 [B2] 相矛盾，未能复现其报告的效应。"},   # ... but context says 矛盾 (contradict)
    # C5: Chinese support cue
    {"citing_id": "P104", "cited_id": "B2",
     "citing_title": "方法评述",
     "context": "我们的结果与 [B2] 一致，进一步证实了该假设。"},
    # C6: both cues present -> earliest wins (counter appears first here)
    {"citing_id": "P105", "cited_id": "B3",
     "citing_title": "Mixed evidence",
     "context": "While our data are inconsistent with [B3], later analysis is consistent with a weaker claim."},
]


def main():
    graph = CE.build_citation_graph(CITATIONS)
    report = {
        "n_citations": len(CITATIONS),
        "edges": [{"citing_id": e["citing_id"], "cited_id": e["cited_id"],
                   "label": e["label"], "cue": e["cue"],
                   "citing_title": e["citing_title"],
                   "context": e["evidence"]["context"]} for e in graph["edges"]],
        "label_counts": {lab: sum(1 for e in graph["edges"] if e["label"] == lab)
                         for lab in ("support", "counter", "mention")},
        "query_B1_counter": [e["citing_id"] for e in CE.query_graph(graph, cited_id="B1", label="counter")],
    }
    (HERE / "citation_evidence_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("n_citations:", len(CITATIONS))
    print("labels:", [(e["citing_id"], e["label"], e["cue"]) for e in graph["edges"]])
    print("label_counts:", report["label_counts"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
