#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T065 -- citation support / counter / mention evidence + graph.

Aligns the evidence/relationship benefit of Scite/ResearchRabbit/Litmaps: for each citation, capture
the CITATION CONTEXT (the passage where one paper cites another) and label it support / counter /
mention -- but the label is derived ONLY from explicit cue phrases found IN THAT CONTEXT, never from
the citing paper's title or a model's impression. Every non-mention label carries the exact cue,
located in the context (offset/length are CHARACTER indices, so quote == context[offset:offset+length];
they are string indices, NOT UTF-8 byte offsets), so it is always viewable and checkable.

  * classify_citation(context) -- takes ONLY the context text (no title, no metadata). Returns
    {label, cue, evidence:{quote, offset, length, context}} where label in {support, counter, mention}.
    The label comes from the EARLIEST-occurring cue phrase in the context (deterministic); with no cue
    the label is "mention" (never a guess). By construction quote == context[offset:offset+length].
  * build_citation_graph(citations) -- each citation {citing_id, cited_id, context}; classify each and
    build typed edges (support/counter/mention) carrying the context evidence.
  * query_graph(graph, cited_id?, label?) -- query edges by cited paper and/or label.

Deterministic; no network, no clock, no randomness, no model call, no production side effects.
"""
import re

# Bounded, explicit cue lexicons. A label is assigned ONLY when one of these appears in the context.
SUPPORT_CUES = [
    "consistent with", "in agreement with", "in line with", "corroborat", "supports", "support the",
    "confirms", "confirm the", "replicat", "reproduc", "extends the", "builds on", "agrees with",
    "一致", "支持", "证实", "印证", "吻合", "符合",
]
COUNTER_CUES = [
    "contradict", "in contrast to", "contrary to", "fails to", "failed to", "does not support",
    "do not support", "disagree", "refute", "challenge", "inconsistent with", "unlike", "at odds with",
    "call into question", "反驳", "矛盾", "不一致", "不支持", "质疑", "推翻", "相反",
]
_LABEL_CUES = {"support": SUPPORT_CUES, "counter": COUNTER_CUES}

# Cues that are deliberate STEMS (match e.g. corroborate/corroborating) -> no trailing word boundary.
_STEM_CUES = {"corroborat", "replicat", "reproduc"}


def _compile_cue(cue):
    """Compile a cue matcher. ASCII cues match on word boundaries so 'unlike' does NOT match inside
    'unlikely' and 'consistent with' does NOT match inside 'inconsistent with'; CJK cues (no word
    boundaries) match as substrings. Stem cues keep only a leading boundary so they still match their
    inflections. Case-insensitive."""
    if re.search(r"[一-鿿]", cue):
        return re.compile(re.escape(cue))
    lead = r"(?<![A-Za-z])"
    trail = "" if cue in _STEM_CUES else r"(?![A-Za-z])"
    return re.compile(lead + re.escape(cue) + trail, re.I)


_CUE_RES = {label: [(cue, _compile_cue(cue)) for cue in cues] for label, cues in _LABEL_CUES.items()}


_LABEL_RANK = {"counter": 0, "support": 1}


def _find_earliest_cue(context):
    """The winning cue in the context, chosen deterministically by (earliest position, counter-before-
    support at an equal position, longer surface). offset/length are character indices into `context`."""
    text = context or ""
    matches = []   # (position, label_rank, -length, label, surface, offset, length)
    for label in ("counter", "support"):
        for _cue, rgx in _CUE_RES[label]:
            m = rgx.search(text)
            if not m:
                continue
            pos, length = m.start(), m.end() - m.start()
            matches.append((pos, _LABEL_RANK[label], -length, label, text[pos:pos + length], pos, length))
    if not matches:
        return None
    _p, _r, _nl, label, surface, offset, length = min(matches)
    return (offset, label, surface, offset, length)


def classify_citation(context):
    """Label a citation from its CONTEXT ONLY. No title, no metadata, no model impression are inputs."""
    ctx = context or ""
    hit = _find_earliest_cue(ctx)
    if hit is None:
        return {"label": "mention", "cue": None,
                "evidence": {"quote": None, "offset": None, "length": None, "context": ctx}}
    _pos, label, surface, offset, length = hit
    return {"label": label, "cue": surface,
            "evidence": {"quote": ctx[offset:offset + length], "offset": offset,
                         "length": length, "context": ctx}}


def build_citation_graph(citations):
    """citations: [{citing_id, cited_id, context, citing_title?}]. citing_title is stored for display
    but is NOT passed to the classifier. Returns typed edges with context evidence."""
    edges = []
    for c in citations:
        cls = classify_citation(c["context"])          # NOTE: only c["context"] is used
        edges.append({
            "citing_id": c["citing_id"], "cited_id": c["cited_id"],
            "label": cls["label"], "cue": cls["cue"], "evidence": cls["evidence"],
            "citing_title": c.get("citing_title"),      # display-only; never fed to classify
        })
    return {"edges": edges}


def query_graph(graph, cited_id=None, label=None):
    out = []
    for e in graph["edges"]:
        if cited_id is not None and e["cited_id"] != cited_id:
            continue
        if label is not None and e["label"] != label:
            continue
        out.append(e)
    out.sort(key=lambda e: (e["cited_id"], e["citing_id"]))
    return out


def label_has_viewable_context(edge):
    """True iff the label is backed by viewable context: a non-mention label must carry a cue quote
    that is byte-exact in its context; a mention carries the raw context."""
    ev = edge["evidence"]
    if edge["label"] == "mention":
        return ev.get("context") is not None
    ctx = ev.get("context") or ""
    off, length = ev.get("offset"), ev.get("length")
    if off is None or length is None:
        return False
    return ctx[off:off + length] == edge["cue"] == ev.get("quote")
