#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T063 -- research metadata enhancement (DOI / Crossref / OpenAlex).

Enriches an arXiv paper's identity, authors, institutions, version, and citation signals WITHOUT ever
replacing or blocking the original paper -- the original arXiv record stays the EVIDENCE ANCHOR:

  * MetadataAdapter -- a deterministic, fixture-backed adapter (crossref / openalex). Each looks up
    a paper and returns an ADDITIVE, provenanced enhancement, or returns None (not found), or raises
    AdapterError (a transient failure). No live network (NOT_DEPLOYED; production untouched).
  * enhance(paper, adapters) -- attaches every successful enhancement as a separate, source-tagged
    record and NEVER mutates the original paper. An adapter failure is captured as a status, not a
    block: the original paper always flows through (degraded fallback).
  * link_works(enhanced) -- the dedup rule for preprint vs journal: an arXiv preprint and its
    published journal article are LINKED as two versions of ONE work ONLY on an evidence-based
    cross-reference (the journal's Crossref record names the preprint), and are kept as DISTINCT
    records with their own type and evidence -- never merged into one, never relabeled. Title
    similarity alone never links (no over-merge; no preprint/journal confusion).
  * resolve_authors(enhanced) / resolve_institutions(enhanced) -- reuse T058 entity_resolver to unify
    authors and institutions across Crossref and OpenAlex with per-source provenance, without
    confusing distinct names. These are GLOBAL cross-source identity pools (not per-work attribution).

The citation SIGNALS (OpenAlex references + cited_by_count) are attached as provenanced enhancement
fields; constructing the full citation graph with support/counter context is T065's scope.

Deterministic; no network, no clock, no randomness, no production side effects.
"""
import copy
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entity_resolver as ER   # T058: resolve() clusters mentions by shared alias with provenance


class AdapterError(Exception):
    """A transient adapter failure (e.g. a simulated network/5xx). Must NOT block the paper."""


# ----------------------------------------------------------------- fixture-backed adapters
def make_crossref_adapter(index):
    """index: {arxiv_id: {"doi","journal","published_type","authors":[..],"institutions":[..],
    "has_preprint_arxiv_id"}} | {arxiv_id: AdapterError} to simulate a failure."""
    def adapter(paper):
        key = paper.get("arxiv_id")
        rec = index.get(key)
        if rec is AdapterError or isinstance(rec, AdapterError):
            raise AdapterError(f"crossref transient failure for {key}")
        if rec is None:
            return None
        return {
            "doi": rec["doi"], "journal": rec.get("journal"),
            "published_type": rec.get("published_type", "journal"),
            "authors": list(rec.get("authors", [])),
            "institutions": list(rec.get("institutions", [])),
            "has_preprint_arxiv_id": rec.get("has_preprint_arxiv_id"),
        }
    return adapter


def make_openalex_adapter(index):
    """index: {arxiv_id: {"work_id","authors":[{"name","orcid"}],"institutions":[{"name","ror"}],
    "references":[doi..],"cited_by_count"}} | {arxiv_id: AdapterError}."""
    def adapter(paper):
        key = paper.get("arxiv_id")
        rec = index.get(key)
        if rec is AdapterError or isinstance(rec, AdapterError):
            raise AdapterError(f"openalex transient failure for {key}")
        if rec is None:
            return None
        return {
            "work_id": rec["work_id"],
            "authors": list(rec.get("authors", [])),
            "institutions": list(rec.get("institutions", [])),
            "references": list(rec.get("references", [])),
            "cited_by_count": rec.get("cited_by_count", 0),
        }
    return adapter


# ----------------------------------------------------------------- enhance (evidence-anchored)
def enhance(paper, adapters):
    """Attach additive, source-tagged enhancements. The original paper is the EVIDENCE ANCHOR and is
    never mutated; ANY adapter failure is a status, never a block.

    Two isolation guarantees make the degraded-fallback contract robust against real-world adapters:
      * each adapter is handed a fresh deepcopy of the paper, so even a buggy/hostile adapter that
        mutates its argument cannot corrupt the original evidence;
      * the adapter call is wrapped against EVERY exception (not just AdapterError) -- a network error,
        a KeyError on malformed JSON, anything -- so one paper's failing enhancement can never crash
        the pipeline and block the other papers (or this paper's original evidence)."""
    original = copy.deepcopy(paper)                       # immutable evidence anchor
    enhancements, status = [], {}
    for name, adapter in adapters:
        try:
            enh = adapter(copy.deepcopy(paper))           # adapter sees a throwaway copy, never the original
        except Exception:                                 # noqa: BLE001 -- degraded fallback: NEVER block
            status[name] = "failed"                       # 增强失败 -> recorded, NOT blocking
            continue
        if enh is None:
            status[name] = "not_found"
            continue
        rec = {"adapter": name, **enh}
        # self-describing confirmation: a Crossref record's preprint relation either points at THIS
        # arXiv id (a confirmed publication of this paper) or not. Computed once here so link_works and
        # any consumer can trust the flag rather than re-deriving it.
        if "has_preprint_arxiv_id" in enh:
            aid = original.get("arxiv_id")
            # require a truthy arxiv id so a degenerate paper (no id) can't match a None has_preprint
            rec["confirmed_publication"] = bool(aid) and enh.get("has_preprint_arxiv_id") == aid
        enhancements.append(rec)
        status[name] = "ok"
    return {
        "paper": original,                                # original arXiv record, byte-identical
        "evidence_anchor": {"type": "preprint", "source": "arxiv",
                            "id": original.get("arxiv_id"), "url": original.get("pdf_url")},
        "enhancements": enhancements,                     # additive, each carries its source
        "enhancement_status": status,
        "blocked": False,                                 # the original paper ALWAYS flows through
    }


def run_pipeline(papers, adapters):
    """Enhance every paper. Degraded fallback: the output has one record per input paper even when
    adapters fail for some -- an enhancement failure never drops or blocks a paper."""
    return [enhance(p, adapters) for p in papers]


# ----------------------------------------------------------------- dedup: preprint vs journal
def _crossref_of(rec):
    for e in rec["enhancements"]:
        if e["adapter"] == "crossref":
            return e
    return None


def link_works(enhanced):
    """Model each work as its versions. Every arXiv paper is a PREPRINT version (arXiv evidence). A
    JOURNAL version (DOI evidence) is added to the SAME work ONLY when the paper's Crossref record
    confirms the preprint relation for THIS arXiv id (has_preprint_arxiv_id == this arxiv_id). The two
    versions are kept DISTINCT with their own type and evidence -- the preprint is never relabeled as
    journal, and the arXiv PDF is never presented as the journal version-of-record. An unconfirmed DOI
    (relation missing or pointing elsewhere) does NOT add a journal version (no confusion); title
    similarity alone never links anything."""
    works = {}
    for i, r in enumerate(enhanced, 1):
        aid = r["paper"].get("arxiv_id")
        wid = f"work-{i:03d}"
        versions = [{
            "work_id": wid, "version_type": "preprint", "source": "arxiv",
            "arxiv_id": aid, "doi": None, "evidence_anchor": r["evidence_anchor"],
        }]
        cr = _crossref_of(r)
        if cr and cr.get("doi"):
            confirmed = bool(cr.get("confirmed_publication"))   # self-describing flag set in enhance()
            if confirmed:
                versions.append({
                    "work_id": wid, "version_type": "journal", "source": "crossref",
                    "arxiv_id": None, "doi": cr["doi"], "journal": cr.get("journal"),
                    "evidence_anchor": {"type": "journal", "source": "crossref", "id": cr["doi"]},
                    "linked_via": "crossref_has_preprint",
                })
            else:
                # DOI present but NOT confirmed to be THIS preprint's publication -> do not link as the
                # journal version of this work (avoid preprint/journal confusion); keep it only as an
                # attached, unconfirmed enhancement on the paper.
                versions[0]["unconfirmed_doi"] = cr["doi"]
        works[wid] = versions
    return works


# ----------------------------------------------------------------- authors/institutions (reuse T058)
def _resolve_field(enhanced, field, etype):
    """Feed a named mention field (authors|institutions) from every enhancement into the T058 resolver,
    so a name seen in both Crossref and OpenAlex is unified with multi-source provenance, without
    confusing two distinct names. A GLOBAL cross-source identity pool (not per-work attribution)."""
    mentions = []
    for r in enhanced:
        for e in r["enhancements"]:
            src = e["adapter"]
            for item in e.get(field, []):
                name = item["name"] if isinstance(item, dict) else item
                mentions.append({"name": name, "type": etype, "source_id": src, "aliases": [name]})
    return ER.resolve(mentions)


def resolve_authors(enhanced):
    """Unify authors across Crossref + OpenAlex with per-source provenance (global identity pool)."""
    return _resolve_field(enhanced, "authors", "author")


def resolve_institutions(enhanced):
    """Unify institutions across Crossref + OpenAlex with per-source provenance (global identity pool)."""
    return _resolve_field(enhanced, "institutions", "institution")
