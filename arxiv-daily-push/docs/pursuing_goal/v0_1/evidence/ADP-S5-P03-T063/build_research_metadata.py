#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + report generator for ADP-S5-P03-T063 (research metadata enhancement).

Fixtures (no network): a handful of arXiv preprints plus Crossref / OpenAlex enhancement indexes
that exercise every acceptance path -- a confirmed preprint->journal publication, an UNCONFIRMED DOI
(must NOT link as this work's journal), a same-title decoy (title alone must not link), and adapter
FAILURES (must not block the paper). Fixtures are literals so the verifier can re-derive.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import research_metadata as RM

# ---- arXiv originals (the EVIDENCE ANCHORS) ----------------------------------------------------
PAPERS = [
    {"arxiv_id": "2401.00001", "title": "Deep Learning for Protein Folding",
     "abstract": "We present a model for protein structure prediction.", "pdf_url": "https://arxiv.org/pdf/2401.00001"},
    {"arxiv_id": "2401.00002", "title": "Sparse Attention at Scale",
     "abstract": "A sparse attention mechanism for long contexts.", "pdf_url": "https://arxiv.org/pdf/2401.00002"},
    {"arxiv_id": "2401.00003", "title": "Deep Learning for Protein Folding",   # SAME title as 00001, different work
     "abstract": "An unrelated survey that happens to share a title.", "pdf_url": "https://arxiv.org/pdf/2401.00003"},
    {"arxiv_id": "2401.00004", "title": "Quantum Error Correction Advances",
     "abstract": "Advances in surface codes.", "pdf_url": "https://arxiv.org/pdf/2401.00004"},
    {"arxiv_id": "2401.00005", "title": "Graph Neural Networks for Chemistry",
     "abstract": "GNNs applied to molecular property prediction.", "pdf_url": "https://arxiv.org/pdf/2401.00005"},
]

# ---- Crossref index -----------------------------------------------------------------------------
# 00001: CONFIRMED publication (has_preprint points back at 00001) -> links a journal version.
# 00002: a DOI whose has_preprint points ELSEWHERE (00099) -> UNCONFIRMED, must NOT link as journal.
# 00004: adapter FAILURE (transient).
# 00003/00005: not found in Crossref.
CROSSREF = {
    "2401.00001": {"doi": "10.1038/s41586-024-00001", "journal": "Nature", "published_type": "journal",
                   "authors": [{"name": "Alice Chen"}, {"name": "Bob Li"}],
                   "institutions": [{"name": "MIT"}], "has_preprint_arxiv_id": "2401.00001"},
    "2401.00002": {"doi": "10.1145/3592979.00002", "journal": "NeurIPS Proc.", "published_type": "journal",
                   "authors": [{"name": "Carol Wu"}], "institutions": [{"name": "Stanford"}],
                   "has_preprint_arxiv_id": "2401.00099"},   # points elsewhere -> UNCONFIRMED
    "2401.00004": RM.AdapterError,                            # transient failure
}
# ---- OpenAlex index -----------------------------------------------------------------------------
# 00001: authors incl. "Alice Chen" (also in Crossref -> should unify) + institutions + citations.
# 00005: adapter FAILURE.
OPENALEX = {
    "2401.00001": {"work_id": "W1000001", "authors": [{"name": "Alice Chen", "orcid": "0000-0001"},
                    {"name": "Bob Li", "orcid": "0000-0002"}],
                   "institutions": [{"name": "MIT", "ror": "042nb2s44"}],
                   "references": ["10.1016/j.cell.2020.01", "10.1038/nature12373"], "cited_by_count": 42},
    "2401.00002": {"work_id": "W1000002", "authors": [{"name": "Carol Wu", "orcid": "0000-0003"}],
                   "institutions": [{"name": "Stanford", "ror": "00f54p054"}],
                   "references": ["10.5555/attn"], "cited_by_count": 7},
    "2401.00005": RM.AdapterError,                           # transient failure
}


def adapters():
    return [("crossref", RM.make_crossref_adapter(CROSSREF)),
            ("openalex", RM.make_openalex_adapter(OPENALEX))]


def main():
    enhanced = RM.run_pipeline(PAPERS, adapters())
    works = RM.link_works(enhanced)
    authors = RM.resolve_authors(enhanced)
    institutions = RM.resolve_institutions(enhanced)
    report = {
        "papers_in": len(PAPERS), "enhanced_out": len(enhanced),
        "statuses": {r["paper"]["arxiv_id"]: r["enhancement_status"] for r in enhanced},
        "works": works,
        "author_entities": {eid: {"canonical": e["canonical_name"],
                                  "sources": sorted({p["source_id"] for p in e["provenance"]})}
                            for eid, e in authors.items()},
        "institution_entities": {eid: {"canonical": e["canonical_name"],
                                       "sources": sorted({p["source_id"] for p in e["provenance"]})}
                                 for eid, e in institutions.items()},
    }
    (HERE / "research_metadata_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("papers_in:", len(PAPERS), "enhanced_out:", len(enhanced))
    print("works:", {w: [v["version_type"] for v in vs] for w, vs in works.items()})
    print("statuses:", report["statuses"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
