#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + Golden Set + report for ADP-S5-P03-T064 (Research Set / compare / filter).

The Golden Set hand-labels the method/sample/result each paper's SOURCE text actually states -- with
some fields intentionally ABSENT so the extractor must report them MISSING (not guess). Fixtures are
literals so the verifier can re-derive and check traceability byte-for-byte.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import research_set as RS

MISSING = "__MISSING__"

# Each paper: source text + the GOLDEN expected field values (MISSING where the source omits it).
PAPERS = [
    {"paper_id": "P001", "title": "Protein folding via deep nets",
     "text": "方法：我们采用图神经网络对蛋白质结构建模。样本：训练集包含 5000 条序列。结果：在测试集上准确率达到 92%。",
     "golden": {"method": "我们采用图神经网络对蛋白质结构建模",
                "sample": "训练集包含 5000 条序列",
                "result": "在测试集上准确率达到 92%"}},
    {"paper_id": "P002", "title": "Sparse attention study",
     "text": "Method: we introduce a sparse attention kernel. Results: 3x speedup at equal accuracy.",
     "golden": {"method": "we introduce a sparse attention kernel",
                "sample": MISSING,                         # no sample marker in the source
                "result": "3x speedup at equal accuracy"}},
    {"paper_id": "P003", "title": "GNN chemistry",
     "text": "方法：使用消息传递网络。实验涉及 n = 128 个分子。",   # no 样本 label -> bare stat path
     "golden": {"method": "使用消息传递网络",
                "sample": "n = 128",                       # captured by the bare n=.. statistic path
                "result": MISSING}},                       # no result marker
    {"paper_id": "P004", "title": "Bare abstract, no structure",
     "text": "This paper discusses several ideas without any labeled sections at all.",
     "golden": {"method": MISSING, "sample": MISSING, "result": MISSING}},   # nothing extractable
    {"paper_id": "P005", "title": "Quantum codes",
     "text": "Approach: surface-code decoding. Sample: 200 syndrome rounds. Conclusion: lower error floor.",
     "golden": {"method": "surface-code decoding",
                "sample": "200 syndrome rounds",
                "result": "lower error floor"}},
]


def main():
    rset = RS.make_set("golden", PAPERS)
    table = RS.comparison_table(rset)
    has_result = RS.filter_set(rset, has_field="result")
    kw = RS.filter_set(rset, keyword="网络", field="method")
    report = {
        "set_id": rset["set_id"], "n_papers": len(rset["papers"]),
        "comparison_table": table,
        "filter_has_result": [p["paper_id"] for p in has_result["papers"]],
        "filter_method_contains_网络": [p["paper_id"] for p in kw["papers"]],
        "missing_counts": {
            c: sum(1 for r in table["rows"] if r[c]["missing"]) for c in table["columns"]
        },
    }
    (HERE / "research_set_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("n_papers:", len(rset["papers"]))
    print("missing_counts:", report["missing_counts"])
    print("filter has_result:", report["filter_has_result"])
    print("filter method~网络:", report["filter_method_contains_网络"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
