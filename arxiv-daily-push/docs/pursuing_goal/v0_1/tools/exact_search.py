#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T060 -- exact + structured retrieval.

Delivers the DETERMINISTIC retrieval benefit a professional user needs first, before any semantic
layer: look up a document by its exact identifier (文号 / DOI) and get it as the first result every
time, and filter by structured facets (agency / region / date range / status) with results identical
to a SQL baseline.

  * build_index -- exact hash indexes on doc_number and doi (unique-identifier -> doc), plus facet
                   indexes on agency / region / status; O(1) exact lookup.
  * exact_lookup -- returns the document for an exact identifier as the first (and only) result; a
                    normalized form (trim + case-fold for ASCII ids like DOIs) is matched so trivial
                    formatting never misses.
  * structured_filter -- AND of facet equality + a [date_from, date_to] range; the reference
                    semantics a SQL "WHERE agency=? AND region=? AND doc_date BETWEEN ? AND ? AND
                    status=?" must reproduce exactly.

Deterministic; no network, no production side effects.
"""
import re


def _norm_id(s):
    """Normalize an exact identifier: strip, and case-fold ASCII (DOIs are case-insensitive); CJK
    docnums are left as-is apart from stripping and full/half-width space collapse."""
    s = (s or "").strip().replace("　", " ")
    s = re.sub(r"\s+", "", s)
    return s.casefold()


def build_index(docs):
    """docs: [{doc_id, doc_number?, doi?, agency?, region?, doc_date?(YYYY-MM-DD), status?}]."""
    by_docnum, by_doi = {}, {}
    by_agency, by_region, by_status = {}, {}, {}
    for d in docs:
        if d.get("doc_number"):
            by_docnum[_norm_id(d["doc_number"])] = d
        if d.get("doi"):
            by_doi[_norm_id(d["doi"])] = d
        for facet, idx in (("agency", by_agency), ("region", by_region), ("status", by_status)):
            if d.get(facet):
                idx.setdefault(d[facet], []).append(d)
    return {"docs": docs, "by_docnum": by_docnum, "by_doi": by_doi,
            "by_agency": by_agency, "by_region": by_region, "by_status": by_status}


def exact_lookup(index, identifier):
    """Return [doc] (the first/only result) for an exact 文号 or DOI, else []. Normalized match."""
    k = _norm_id(identifier)
    d = index["by_docnum"].get(k) or index["by_doi"].get(k)
    return [d] if d else []


def structured_filter(docs, agency=None, region=None, status=None, date_from=None, date_to=None):
    """AND of facet equality + inclusive date range. Deterministic; ordered by doc_id for stability."""
    out = []
    for d in docs:
        if agency is not None and d.get("agency") != agency:
            continue
        if region is not None and d.get("region") != region:
            continue
        if status is not None and d.get("status") != status:
            continue
        if date_from is not None and (d.get("doc_date") or "") < date_from:
            continue
        if date_to is not None and (d.get("doc_date") or "") > date_to:
            continue
        out.append(d)
    return sorted(out, key=lambda d: d["doc_id"])
