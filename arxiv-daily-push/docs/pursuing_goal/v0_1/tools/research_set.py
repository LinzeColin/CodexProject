#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T064 -- Research Set, filtering, and structured comparison.

Aligns the research-set benefit of Elicit/Consensus: collect papers, extract structured
method / sample / result fields, and compare them side by side -- WITHOUT guessing. Every extracted
field value is a byte-exact span of the source text carrying an evidence locator (offset + length +
quote), so it always traces back to the original; a field with no source marker is reported MISSING,
never fabricated. Filtering is deterministic and reproducible.

  * make_set(name, papers) -- a Research Set (collection) of papers with extracted structured fields.
  * extract_fields(text)   -- source-grounded method/sample/result extraction. Each field is either
    {"value": <exact source span>, "evidence": {offset, length, quote}} or {"value": None,
    "status": "missing"}. By construction value == text[offset:offset+length] -- never a guess.
  * comparison_table(rset) -- rows = papers, columns = method/sample/result, each cell the field
    (value + evidence) or missing.
  * filter_set(rset, ...)  -- reproducible filtering (has-field / keyword), deterministic order.

Deterministic; no network, no clock, no randomness, no production side effects.
"""
import re

# Field markers. A marker is a label FOLLOWED BY A COLON (：/:); the FIRST match wins and the captured
# value runs from just after the marker to the next sentence boundary -- an exact source span, so it
# traces back verbatim. A CJK terminator (。；) or newline is always a boundary; an ASCII "." is a
# boundary only when it ends a sentence (followed by whitespace or end of text) so decimals like
# "92.5%" are NOT truncated.
_HARD_BOUNDARY = "。；;\n"
FIELD_MARKERS = {
    "method": [r"方法", r"方法学", r"methods?", r"approach"],
    "sample": [r"样本", r"被试", r"数据集", r"样本量", r"dataset", r"samples?", r"cohort"],
    "result": [r"结果", r"结论", r"发现", r"results?", r"conclusions?", r"findings?"],
}
# a label followed by a colon, e.g. "方法：..." or "Method: ..."
_LABEL_RES = {
    field: [re.compile(r"(?:" + "|".join(alts) + r")\s*[:：]\s*", re.I)]
    for field, alts in FIELD_MARKERS.items()
}
# sample also matches a bare "n = 42" statistic (still an exact source span). The negative lookbehind
# keeps a trailing "n" of another word (e.g. "functio[n] = 5") from false-matching.
_SAMPLE_STAT = re.compile(r"(?<![A-Za-z])n\s*=\s*\d+", re.I)


def _is_boundary(text, i):
    """A sentence boundary at position i. CJK terminators / newline always; an ASCII '.' only when it
    ends a sentence (next char is whitespace or end-of-text) so decimals are not split."""
    c = text[i]
    if c in _HARD_BOUNDARY:
        return True
    if c == ".":
        return i + 1 >= len(text) or text[i + 1].isspace()
    return False


def _capture_after(text, m):
    """Given a marker match, capture the value span from marker end to the next sentence boundary."""
    start = m.end()
    end = start
    while end < len(text) and not _is_boundary(text, end):
        end += 1
    value = text[start:end].strip()
    if not value:
        return None
    # tighten the recorded offset to the stripped value so evidence is byte-exact
    off = start + (len(text[start:end]) - len(text[start:end].lstrip()))
    return {"value": value, "evidence": {"offset": off, "length": len(value),
                                         "quote": text[off:off + len(value)]}}


def _extract_one(text, field):
    text = text or ""
    for rgx in _LABEL_RES[field]:
        m = rgx.search(text)
        if m:
            cap = _capture_after(text, m)
            if cap:
                return cap
    if field == "sample":
        m = _SAMPLE_STAT.search(text)
        if m:
            v = m.group(0)
            return {"value": v, "evidence": {"offset": m.start(), "length": len(v), "quote": v}}
    return {"value": None, "status": "missing"}   # 缺失不猜 -- no marker, no guess


def extract_fields(text):
    """Extract method/sample/result from source text; each value is a byte-exact source span."""
    return {field: _extract_one(text, field) for field in ("method", "sample", "result")}


def make_set(name, papers):
    """A Research Set: each paper gets its structured fields extracted from its source text.
    papers: [{paper_id, title?, text}]. `text` is the source the fields must trace back to."""
    items = []
    for p in papers:
        items.append({
            "paper_id": p["paper_id"], "title": p.get("title"),
            "text": p.get("text", ""),
            "fields": extract_fields(p.get("text", "")),
        })
    items.sort(key=lambda it: it["paper_id"])         # deterministic order
    return {"set_id": "set::" + name, "name": name, "papers": items}


def comparison_table(rset):
    """Side-by-side comparison: one row per paper, columns method/sample/result."""
    cols = ["method", "sample", "result"]
    rows = []
    for it in rset["papers"]:
        row = {"paper_id": it["paper_id"], "title": it.get("title")}
        for c in cols:
            f = it["fields"][c]
            row[c] = {"value": f.get("value"), "missing": f.get("value") is None,
                      "evidence": f.get("evidence")}
        rows.append(row)
    return {"columns": cols, "rows": rows}


def filter_set(rset, has_field=None, keyword=None, field=None):
    """Reproducible filtering. has_field: keep papers where that field is present. keyword+field: keep
    papers whose `field` value contains keyword. Deterministic order (already sorted by paper_id)."""
    out = []
    for it in rset["papers"]:
        keep = True
        if has_field is not None:
            keep = keep and it["fields"][has_field].get("value") is not None
        if keyword is not None and field is not None:
            v = it["fields"][field].get("value") or ""
            keep = keep and (keyword.lower() in v.lower())
        if keep:
            out.append(it)
    out.sort(key=lambda it: it["paper_id"])
    return {"set_id": rset["set_id"], "name": rset["name"], "papers": out}


def traces_to_source(paper):
    """True iff every extracted (non-missing) field value is byte-exact at its recorded source offset."""
    text = paper.get("text", "")
    for f in paper["fields"].values():
        if f.get("value") is None:
            continue
        ev = f["evidence"]
        if text[ev["offset"]:ev["offset"] + ev["length"]] != f["value"]:
            return False
    return True
