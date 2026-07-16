#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T061 -- full-text search benchmark + semantic-rerank experiment + adopt/reject decision.

Introduces a semantic layer ONLY when exact/structured retrieval (T060) is insufficient, and never
prematurely. Provides:

  * fts_search    -- a deterministic full-text ranker (term-overlap / IDF-weighted) over the corpus;
  * a fixed query set with ground-truth relevant docs, and metrics (MRR, recall@k);
  * a semantic-rerank EXPERIMENT harness (a candidate reranker is plugged in and benchmarked on the
    SAME fixed query set, and its structured-filter behavior is checked);
  * decide_adopt -- the ADR rule: a semantic layer is ADOPTED only if it (1) IMPROVES the fixed query
    set metric AND (2) does NOT bypass structured filters (its results stay a subset of the
    structured-filtered candidate set). Otherwise it is NOT adopted -- no premature vector infra.

Deterministic; no network, no production side effects.
"""
import math, re


def _tokens(text):
    """Tokenize: CJK bigrams + ASCII words + digit runs. Deterministic."""
    text = (text or "").lower()
    toks = re.findall(r"[a-z]+|\d+", text)
    cjk = re.findall(r"[一-鿿]", text)
    toks += ["".join(p) for p in zip(cjk, cjk[1:])]   # CJK bigrams
    toks += cjk                                        # + unigrams
    return toks


def _doc_text(d):
    return " ".join(str(d.get(k, "")) for k in ("title", "doc_number", "agency", "region", "status"))


def build_fts(corpus):
    """Precompute document token sets + IDF for a small IDF-weighted overlap ranker."""
    docs_tok = {d["doc_id"]: set(_tokens(_doc_text(d))) for d in corpus}
    df = {}
    for toks in docs_tok.values():
        for t in toks:
            df[t] = df.get(t, 0) + 1
    n = max(1, len(corpus))
    idf = {t: math.log(1 + n / c) for t, c in df.items()}
    return {"corpus": corpus, "docs_tok": docs_tok, "idf": idf}


def fts_search(fts, query, k=10):
    """Rank docs by IDF-weighted query-token overlap. Ties broken by doc_id for determinism."""
    q = set(_tokens(query))
    scored = []
    for d in fts["corpus"]:
        toks = fts["docs_tok"][d["doc_id"]]
        score = sum(fts["idf"].get(t, 0.0) for t in q & toks)
        if score > 0:
            scored.append((score, d["doc_id"]))
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [doc_id for _, doc_id in scored[:k]]


def mrr(results_by_query, relevant_by_query):
    """Mean reciprocal rank of the first relevant hit."""
    total = 0.0
    for q, res in results_by_query.items():
        rel = relevant_by_query[q]
        rr = 0.0
        for i, doc_id in enumerate(res, 1):
            if doc_id in rel:
                rr = 1.0 / i
                break
        total += rr
    return round(total / max(1, len(results_by_query)), 4)


def recall_at_k(results_by_query, relevant_by_query, k=5):
    total = 0.0
    for q, res in results_by_query.items():
        rel = relevant_by_query[q]
        hit = len(set(res[:k]) & rel) / max(1, len(rel))
        total += hit
    return round(total / max(1, len(results_by_query)), 4)


def decide_adopt(fts_metrics, semantic_metrics, semantic_respects_filters, min_improvement=0.0):
    """ADR rule: adopt the semantic layer ONLY if it improves the fixed-query-set metric AND respects
    structured filters. Otherwise reject (avoid premature vector infra)."""
    improved = (semantic_metrics["mrr"] - fts_metrics["mrr"]) > min_improvement \
        or (semantic_metrics["recall@5"] - fts_metrics["recall@5"]) > min_improvement
    adopt = bool(improved and semantic_respects_filters)
    reasons = []
    if not improved:
        reasons.append("semantic did not improve the fixed query set -> not adopted")
    if not semantic_respects_filters:
        reasons.append("semantic bypasses structured filters -> not adopted")
    if adopt:
        reasons.append("semantic improves the fixed query set AND respects structured filters -> adopt")
    return {"adopt": adopt, "improved": improved, "respects_filters": semantic_respects_filters,
            "reasons": reasons}
