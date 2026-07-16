#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + the 131-item benefit-parity registry for ADP-S5-P04-T068.

The registry enumerates real competitor user benefits (Elicit / Consensus / Scite / ResearchRabbit /
Litmaps / Semantic Scholar / Connected Papers / reference managers / general scholarly tools). Every
item is given a HONEST status from the closed vocabulary {delivered, partial, planned, not_applicable}
and a named owner -- never 'unknown', never 'no-owner'. `delivered`/`partial` items cite the ADP task
(S5 library-layer tools are NOT_DEPLOYED, hence many are `partial`: the tool exists but is not yet in
the production UI). Fixtures are literals so the verifier can re-derive.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import knowledge_validity as KV

# ---- Knowledge Validity fixtures ---------------------------------------------------------------
SRC_V1 = {"canonical_id": "doc-K", "body": "第一条 数据平台上线。", "status": "published"}
SRC_V2 = {"canonical_id": "doc-K", "body": "第一条 数据平台上线。第二条 新增考核。", "status": "published"}  # substantive change
SRC_NOISE = {"canonical_id": "doc-K", "body": "第一条 数据平台上线。\n责任编辑：张三", "status": "published"}  # noise-only
SRC_OTHER = {"canonical_id": "doc-O", "body": "无关文件。", "status": "published"}


# ---- 131-item benefit-parity registry ----------------------------------------------------------
# (benefit, status, evidence_ref)   status in {delivered, partial, planned, not_applicable}
_COMP = {
    "Elicit": ("ADP-research", [
        ("Search papers by a research question", "partial", "T060/T061"),
        ("Extract method into a column", "delivered", "T064"),
        ("Extract sample/participants into a column", "delivered", "T064"),
        ("Extract results/outcomes into a column", "delivered", "T064"),
        ("Structured comparison table across papers", "delivered", "T064"),
        ("Every extracted cell traces to the source", "delivered", "T064"),
        ("Missing field reported, not guessed", "delivered", "T064"),
        ("Reproducible paper filtering", "delivered", "T064"),
        ("Summarize an abstract", "planned", "S7"),
        ("De-duplicate a paper set", "delivered", "T063"),
        ("Author / institution enrichment", "delivered", "T063"),
        ("DOI / journal metadata enrichment", "delivered", "T063"),
        ("Preprint vs journal not confused", "delivered", "T063"),
        ("Enrichment failure never blocks the paper", "delivered", "T063"),
        ("Export a research set", "delivered", "T067"),
        ("Chat over a set of papers", "not_applicable", "no LLM chat in scope"),
    ]),
    "Consensus": ("ADP-research", [
        ("Yes/No consensus meter for a claim", "planned", "S7"),
        ("Study snapshot card", "partial", "T064"),
        ("Aggregate what studies say on a topic", "partial", "T057/T064"),
        ("Quality / rigor indicators", "planned", "S7"),
        ("Citation-backed answers", "delivered", "T065"),
        ("Evidence traces to the original text", "delivered", "T064/T065"),
        ("Topic synthesis", "planned", "S7"),
        ("No claim without a source", "delivered", "T059/T065"),
        ("Surface disagreement between studies", "delivered", "T065"),
        ("Confidence/uncertainty shown honestly", "delivered", "T065"),
        ("Never fabricate a consensus", "delivered", "T065"),
    ]),
    "Scite": ("ADP-content", [
        ("Supporting citations", "delivered", "T065"),
        ("Contrasting / disputing citations", "delivered", "T065"),
        ("Mentioning citations", "delivered", "T065"),
        ("Citation statement context is viewable", "delivered", "T065"),
        ("Labels not from title or model impression", "delivered", "T065"),
        ("Citation graph with typed edges", "delivered", "T065"),
        ("Support and contrast to the same paper coexist", "delivered", "T065"),
        ("Reference check / smart references", "partial", "T065"),
        ("Citation dashboards", "planned", "S7"),
        ("Journal / institution citation profiles", "planned", "S8"),
        ("Retraction / editorial-notice awareness", "planned", "S6"),
        ("Alert on new citations of a paper", "delivered", "T066"),
        ("Every label has checkable evidence", "delivered", "T065"),
        ("No classification from headline alone", "delivered", "T065"),
    ]),
    "ResearchRabbit": ("ADP-research", [
        ("Collections of papers", "delivered", "T064/T067"),
        ("Follow an author", "partial", "T063"),
        ("Similar work discovery", "partial", "T063"),
        ("Citation / reference network graph", "delivered", "T065"),
        ("Timeline of a topic", "partial", "T062"),
        ("Recommend next papers", "planned", "S7"),
        ("Monitor a collection for new work", "delivered", "T066"),
        ("Change-only updates (no re-notify)", "delivered", "T066"),
        ("Visual network exploration", "planned", "S7"),
        ("Share a collection", "planned", "S8"),
        ("Author disambiguation", "delivered", "T063"),
        ("Institution linking", "delivered", "T063"),
        ("Export the collection", "delivered", "T067"),
        ("Provenance kept on every saved item", "delivered", "T067"),
        ("Notes on saved papers", "delivered", "T067"),
    ]),
    "Litmaps": ("ADP-research", [
        ("Citation map from a seed", "partial", "T065"),
        ("Monitor for new relevant papers", "delivered", "T066"),
        ("Email/weekly digest of changes", "partial", "T066"),
        ("Only substantive changes pushed", "delivered", "T066"),
        ("Re-run does not duplicate alerts", "delivered", "T066"),
        ("Silence signal when a source is quiet", "delivered", "T066"),
        ("Shared maps", "planned", "S8"),
        ("Discover via co-citation", "partial", "T065"),
        ("Prioritise by relevance", "planned", "S7"),
        ("Import a bibliography", "partial", "T067"),
        ("Export a map", "delivered", "T067"),
        ("Every alert is locatable to a change", "delivered", "T066"),
        ("Watch topics / agencies / regions / doc-numbers", "delivered", "T066"),
        ("Historical as-of view of a map", "partial", "T062"),
    ]),
    "Semantic Scholar": ("ADP-content", [
        ("TLDR one-line summary", "planned", "S7"),
        ("Influential citation flag", "partial", "T065"),
        ("Author pages", "partial", "T063"),
        ("Citation graph", "delivered", "T065"),
        ("Paper metadata (venue/year/authors)", "delivered", "T063"),
        ("Figures / tables extraction", "not_applicable", "no PDF figure OCR in scope"),
        ("Citation counts", "delivered", "T063"),
        ("Search", "partial", "T060/T061"),
        ("Alerts on an author", "delivered", "T066"),
        ("Open access / PDF link", "delivered", "T067"),
        ("De-duplicated records", "delivered", "T063"),
        ("Version / preprint linkage", "delivered", "T063"),
        ("Evidence-backed metadata", "delivered", "T063"),
    ]),
    "Connected Papers": ("ADP-research", [
        ("Graph of similar papers", "partial", "T065"),
        ("Prior works", "partial", "T065"),
        ("Derivative works", "partial", "T065"),
        ("Build a graph from one seed", "partial", "T065"),
        ("Visual similarity layout", "planned", "S7"),
        ("Export the graph", "delivered", "T067"),
        ("Identify foundational papers", "partial", "T065"),
        ("Graph edges carry evidence", "delivered", "T065"),
        ("No edge without a citation", "delivered", "T065"),
    ]),
    "Reference managers (Zotero/Mendeley)": ("ADP-library", [
        ("Save an item to a library", "delivered", "T067"),
        ("Add notes", "delivered", "T067"),
        ("Organise into collections", "delivered", "T067"),
        ("Export to Markdown", "delivered", "T067"),
        ("Export to CSV", "delivered", "T067"),
        ("Export to JSON", "delivered", "T067"),
        ("Keep the original URL", "delivered", "T067"),
        ("Keep the version", "delivered", "T067"),
        ("Keep the fetch/capture time", "delivered", "T067"),
        ("Keep the claim evidence", "delivered", "T067"),
        ("Keep a license notice", "delivered", "T067"),
        ("Refuse to save without provenance", "delivered", "T067"),
        ("Cite in a chosen style", "planned", "S8"),
        ("Sync across devices", "not_applicable", "handled by the cloud account, not this layer"),
        ("Deduplicate the library", "delivered", "T063"),
        ("Long-term durable storage", "delivered", "T027/T067"),
    ]),
    "General scholarly (Scholar/PubMed/etc.)": ("ADP-core", [
        ("Alert on a saved query", "delivered", "T066"),
        ("Cited-by lookup", "delivered", "T065"),
        ("All versions of a work", "delivered", "T062"),
        ("As-of historical state", "delivered", "T062"),
        ("Old-vs-new diff, changes locatable", "delivered", "T062"),
        ("Template noise not shown as a change", "delivered", "T062/T026"),
        ("Replay any old version", "delivered", "T062"),
        ("Exact identifier lookup (docnum/DOI)", "delivered", "T060"),
        ("Structured filter (agency/region/date/status)", "delivered", "T060"),
        ("Full-text ranking benchmarked", "delivered", "T061"),
        ("Semantic layer only if it earns its cost", "delivered", "T061"),
        ("Official original text (A0)", "delivered", "T034-T040"),
        ("Provincial / city official sources (A1)", "delivered", "T049-T052"),
        ("Local / zone official sources (A2)", "delivered", "T053-T055"),
        ("2016+ recoverable history", "delivered", "T046/T047/T056"),
        ("Coverage debt is explainable (no silent holes)", "delivered", "T043/T056"),
        ("Canonical event de-duplication", "delivered", "T057"),
        ("Cross-source entity resolution", "delivered", "T058"),
        ("Cross-board evidence relations", "delivered", "T059"),
        ("Knowledge auto-invalidates when the source changes", "delivered", "T068"),
        ("Old knowledge re-opened for review", "delivered", "T068"),
        ("Cost / benefit quantified per feature", "partial", "T039/T068"),
        ("Realtime MVP never regressed", "delivered", "T040"),
    ]),
}


def build_registry():
    items, n = [], 0
    for competitor, (owner, benefits) in _COMP.items():
        for benefit, status, ev in benefits:
            n += 1
            items.append({
                "benefit_id": f"P{n:03d}",
                "competitor": competitor,
                "benefit": benefit,
                "status": status,
                "owner": owner,
                "evidence_ref": ev if status in ("delivered", "partial") else "",
                "note": ev if status in ("planned", "not_applicable") else "",
            })
    return {"items": items}


def main():
    reg = build_registry()
    rep = KV.parity_report(reg)
    # knowledge validity demo
    k = KV.make_knowledge("K1", "平台已上线", SRC_V1)
    v_same = KV.check_validity(k, [SRC_V1])
    v_noise = KV.check_validity(k, [SRC_NOISE])
    v_changed = KV.check_validity(k, [SRC_V2])
    report = {
        "parity": rep,
        "validity_demo": {
            "unchanged": v_same["validity"], "noise_only": v_noise["validity"],
            "source_changed": v_changed["validity"],
        },
    }
    (HERE / "knowledge_validity_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "parity_registry_131.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("parity n_items:", rep["n_items"], "clean:", rep["clean"])
    print("by_status:", rep["by_status"])
    print("validity: unchanged=%s noise=%s changed=%s" % (
        v_same["validity"], v_noise["validity"], v_changed["validity"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
