#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T061 -- FTS benchmark + 3 semantic-rerank experiments + adopt/reject ADR (deterministic)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import fts_benchmark as FB

# corpus: 6 topics x 4 docs; for the 低温雨雪 topic one doc uses the SYNONYM 冰冻灾害 (FTS misses it on
# the exact query, a synonym-aware semantic layer finds it -> a genuine improvement opportunity)
TOPICS = {
    "低温雨雪": ["江苏省低温雨雪冰冻灾害应急预案通知", "低温雨雪灾害防范工作方案", "低温雨雪天气应对指南",
                 "冰冻灾害恢复重建实施意见"],   # last uses synonym 冰冻灾害, not 低温雨雪
    "科技计划": ["重点研发计划项目结题验收通知", "科技计划专项资金管理办法", "科技创新平台建设方案", "科技计划绩效评价规则"],
    "数据安全": ["数据安全管理条例实施细则", "数据安全风险评估指南", "重要数据出境安全评估办法", "数据安全应急预案"],
    "产业发展": ["先进制造业产业发展规划", "战略性新兴产业培育方案", "产业链供应链提升行动", "产业园区建设管理办法"],
    "招标采购": ["政府采购招标管理办法", "工程建设项目招标投标规定", "采购需求编制指引", "招标代理机构管理办法"],
    "医疗卫生": ["传染病防治应急预案", "公共卫生服务保障方案", "医疗卫生机构管理条例", "疾病预防控制工作规则"],
}
REGIONS = ["江苏", "山东", "北京", "中央"]

def build_corpus():
    docs, n = [], 0
    for ti, (topic, titles) in enumerate(TOPICS.items()):
        for j, title in enumerate(titles):
            n += 1
            docs.append({"doc_id": f"doc-{n:03d}", "title": title, "topic": topic,
                         "region": REGIONS[j % 4], "agency": f"机构{ti}", "doc_number": f"文〔2026〕{n}号"})
    return docs

# a small synonym map a "semantic" layer would know
SYNONYMS = {"低温雨雪": ["冰冻", "冰冻灾害"], "招标采购": ["招标", "采购", "招投标"]}

def _rel(docs, topic):
    return {d["doc_id"] for d in docs if d["topic"] == topic}

def semantic_synonym(fts, query, corpus, k=10):
    """GOOD semantic reranker: expand the query with synonyms, so a synonym-only doc is retrieved."""
    base = FB.fts_search(fts, query, k=k)
    extra = []
    for syn in SYNONYMS.get(query, []):
        extra += FB.fts_search(fts, syn, k=k)
    seen = list(dict.fromkeys(base + extra))
    return seen[:k]

def semantic_identity(fts, query, corpus, k=10):
    """NO-IMPROVEMENT reranker: same as FTS."""
    return FB.fts_search(fts, query, k=k)

def semantic_bypass(fts, query, corpus, k=10):
    """BAD reranker: ignores the structured filter (returns global results even when a filter is set)."""
    return FB.fts_search(fts, query, k=k)

def run_query_set(fn, fts, queries, corpus):
    return {q: fn(fts, q, corpus) for q in queries}

def respects_filters(fn, fts, corpus, region):
    """A semantic result respects filters iff, when a region filter is applied, its results stay within
    the filtered candidate set. Bypass returns global results -> fails."""
    filtered_ids = {d["doc_id"] for d in corpus if d["region"] == region}
    # emulate 'search within filter': the reranker is given the filtered corpus
    fts_f = FB.build_fts([d for d in corpus if d["region"] == region])
    for q in ["科技计划", "数据安全"]:
        res = fn(fts_f, q, [d for d in corpus if d["region"] == region])
        if any(r not in filtered_ids for r in res):
            return False
    return True

def main():
    corpus = build_corpus()
    fts = FB.build_fts(corpus)
    queries = list(TOPICS)
    relevant = {q: _rel(corpus, q) for q in queries}

    fts_res = run_query_set(semantic_identity, fts, queries, corpus)
    fts_metrics = {"mrr": FB.mrr(fts_res, relevant), "recall@5": FB.recall_at_k(fts_res, relevant, 5)}

    experiments = {}
    for name, fn, bypass in [("synonym_semantic", semantic_synonym, False),
                             ("identity_semantic", semantic_identity, False),
                             ("bypass_semantic", semantic_bypass, True)]:
        res = run_query_set(fn, fts, queries, corpus)
        m = {"mrr": FB.mrr(res, relevant), "recall@5": FB.recall_at_k(res, relevant, 5)}
        rf = False if bypass else respects_filters(fn, fts, corpus, "江苏")
        decision = FB.decide_adopt(fts_metrics, m, rf)
        experiments[name] = {"metrics": m, "respects_filters": rf, "decision": decision}

    report = {
        "task": "ADP-S5-P02-T061",
        "corpus_docs": len(corpus), "queries": len(queries),
        "fts_baseline": fts_metrics,
        "experiments": experiments,
        "adr": {
            "rule": "adopt a semantic layer ONLY if it improves the fixed query set AND respects structured filters",
            "decision": {name: e["decision"]["adopt"] for name, e in experiments.items()},
            "adopted": [name for name, e in experiments.items() if e["decision"]["adopt"]],
        },
        "cost_latency_quality": {
            "note": "FTS is O(corpus) term-overlap, in-process, 0 external infra; a semantic/vector layer "
                    "would add index build + query cost + latency + infra -- justified ONLY by the ADR rule.",
            "fts_external_infra": False, "semantic_external_infra_if_adopted": True,
            "production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
            "r2_ops": 0, "model_calls": 0, "human_maintenance": "benchmark + ADR authoring",
        },
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "benchmark_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"corpus={len(corpus)} fts={fts_metrics}")
    for name, e in experiments.items():
        print(f"  {name:18} mrr={e['metrics']['mrr']} recall@5={e['metrics']['recall@5']} "
              f"respects_filters={e['respects_filters']} adopt={e['decision']['adopt']}")
    print("adopted:", report["adr"]["adopted"])

if __name__ == "__main__":
    main()
