#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T063 acceptance: research metadata enhancement (DOI / Crossref / OpenAlex).

Acceptance (TASK_INDEX row 63): 预印本/期刊不混淆；增强失败不阻塞原始论文。
  (preprint vs journal not confused; enhancement failure does not block the original paper.)

Deterministic. Re-derives from the TOOL (research_metadata) + generator fixtures -- never trusts the
report. Negative controls prove discrimination: an UNCONFIRMED DOI must NOT link as a journal version
(and confirming it WOULD link -- proving the gate is load-bearing); a dropping pipeline WOULD lose the
failed papers (proving the count-preservation is non-trivial); a failed adapter is genuinely caught
(not silently mislabeled not_found) and contributes no enhancement.
"""
import copy
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import research_metadata as RM

T063 = V01 / "evidence" / "ADP-S5-P03-T063"
spec = importlib.util.spec_from_file_location("brm", str(T063 / "build_research_metadata.py"))
brm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brm)

fails = []
PAPERS = brm.PAPERS
enhanced = RM.run_pipeline(PAPERS, brm.adapters())
works = RM.link_works(enhanced)
by_arxiv = {r["paper"]["arxiv_id"]: r for r in enhanced}

# =============================================================== 1) 预印本/期刊不混淆
# work with the CONFIRMED publication (paper 00001) must carry TWO distinct versions.
w1 = next((vs for vs in works.values() if any(v["arxiv_id"] == "2401.00001" for v in vs)), None)
if w1 is None:
    fails.append("paper 00001 not present in any work")
else:
    types = sorted(v["version_type"] for v in w1)
    if types != ["journal", "preprint"]:
        fails.append(f"confirmed work should have a preprint AND a journal version, got {types}")
    pre = next(v for v in w1 if v["version_type"] == "preprint")
    jour = next((v for v in w1 if v["version_type"] == "journal"), None)
    if pre["evidence_anchor"]["source"] != "arxiv":
        fails.append("preprint version's evidence is not the arXiv record")
    if not jour or jour["evidence_anchor"]["source"] != "crossref" or not jour["doi"]:
        fails.append("journal version's evidence is not the Crossref DOI")
    if jour and jour["evidence_anchor"]["id"] == pre["evidence_anchor"]["id"]:
        fails.append("preprint and journal share an evidence id -> confused")
    # the two versions are LINKED (same work_id) but DISTINCT
    if jour and pre["work_id"] != jour["work_id"]:
        fails.append("preprint and journal are not linked into one work")

# NO preprint is ever relabeled as journal; arXiv PDF is never the journal evidence
for vs in works.values():
    for v in vs:
        if v["version_type"] == "preprint" and v["evidence_anchor"]["source"] != "arxiv":
            fails.append(f"a preprint was relabeled/re-sourced: {v}")
        if v["version_type"] == "journal" and v["evidence_anchor"]["source"] == "arxiv":
            fails.append(f"a journal version was anchored to the arXiv PDF (confusion): {v}")

# NEGATIVE CONTROL (no confusion): an UNCONFIRMED DOI (paper 00002, has_preprint -> 00099) must NOT
# add a journal version to this work.
w2 = next((vs for vs in works.values() if any(v["arxiv_id"] == "2401.00002" for v in vs)), None)
if w2 is None or [v["version_type"] for v in w2] != ["preprint"]:
    fails.append(f"unconfirmed DOI must not link a journal version; work-of-00002 = {w2 and [v['version_type'] for v in w2]}")
elif w2[0].get("unconfirmed_doi") != "10.1145/3592979.00002":
    fails.append("the unconfirmed DOI should be attached as an unconfirmed enhancement, not linked")

# NEGATIVE CONTROL (title alone never links): 00001 and 00003 share a title but are DISTINCT works.
w_of_1 = next(v["work_id"] for vs in works.values() for v in vs if v["arxiv_id"] == "2401.00001")
w_of_3 = next(v["work_id"] for vs in works.values() for v in vs if v["arxiv_id"] == "2401.00003")
if w_of_1 == w_of_3:
    fails.append("two same-title papers were merged into one work (title-only over-merge)")

# DISCRIMINATION: the confirmation gate is load-bearing -- if 00002's Crossref CONFIRMED the preprint,
# it WOULD gain a journal version. Prove the gate is what suppresses it.
cross2 = dict(brm.CROSSREF)
cross2["2401.00002"] = {**brm.CROSSREF["2401.00002"], "has_preprint_arxiv_id": "2401.00002"}
enh2 = RM.run_pipeline(PAPERS, [("crossref", RM.make_crossref_adapter(cross2)),
                                ("openalex", RM.make_openalex_adapter(brm.OPENALEX))])
works2 = RM.link_works(enh2)
w2b = next(vs for vs in works2.values() if any(v["arxiv_id"] == "2401.00002" for v in vs))
if sorted(v["version_type"] for v in w2b) != ["journal", "preprint"]:
    fails.append("confirming the preprint relation did NOT add a journal version -> gate is vacuous, not discriminating")
print(f"preprint/journal: work-of-00001 types={sorted(v['version_type'] for v in w1)}; "
      f"unconfirmed 00002={[v['version_type'] for v in w2]}; confirmed-00002 control={sorted(v['version_type'] for v in w2b)}")

# =============================================================== 2) 增强失败不阻塞原始论文
# every input paper flows through, even with adapter failures
if len(enhanced) != len(PAPERS):
    fails.append(f"pipeline dropped papers: {len(enhanced)} != {len(PAPERS)}")
if {r["paper"]["arxiv_id"] for r in enhanced} != {p["arxiv_id"] for p in PAPERS}:
    fails.append("some input papers are missing from the pipeline output")
for r in enhanced:
    if r["blocked"]:
        fails.append(f"a paper was blocked: {r['paper']['arxiv_id']}")

# the original paper's evidence is never mutated -- byte-identical, and no enhancement leaked into it
for p in PAPERS:
    r = by_arxiv[p["arxiv_id"]]
    if r["paper"] != p:
        fails.append(f"original paper mutated for {p['arxiv_id']}")
    if any(k in r["paper"] for k in ("doi", "authors", "references", "journal")):
        fails.append(f"enhancement leaked into the original evidence for {p['arxiv_id']}")
    if r["evidence_anchor"]["source"] != "arxiv":
        fails.append(f"evidence anchor is not the arXiv original for {p['arxiv_id']}")

# the adapter FAILURES are genuinely caught (not silently mislabeled) and contribute no enhancement
if by_arxiv["2401.00004"]["enhancement_status"].get("crossref") != "failed":
    fails.append("a transient crossref failure (00004) was not recorded as 'failed'")
if by_arxiv["2401.00005"]["enhancement_status"].get("openalex") != "failed":
    fails.append("a transient openalex failure (00005) was not recorded as 'failed'")
if any(e["adapter"] == "crossref" for e in by_arxiv["2401.00004"]["enhancements"]):
    fails.append("a failed crossref adapter still produced an enhancement for 00004")
# a failed paper still carries its full original evidence
if by_arxiv["2401.00004"]["paper"]["abstract"] != "Advances in surface codes.":
    fails.append("a paper whose enhancement failed lost its original content")

# NEGATIVE CONTROL: count-preservation is non-trivial -- a pipeline that dropped papers with ANY
# failed/not-found adapter WOULD lose papers; the real pipeline keeps all of them.
would_drop = [r for r in enhanced if all(s == "ok" for s in r["enhancement_status"].values())]
if len(would_drop) >= len(PAPERS):
    fails.append("no paper actually exercises a non-ok adapter -> degraded-fallback test is vacuous")
print(f"degraded fallback: in={len(PAPERS)} out={len(enhanced)} blocked=0; "
      f"a drop-on-failure pipeline would keep only {len(would_drop)}/{len(PAPERS)}")

# ROBUSTNESS: a NON-AdapterError exception from an adapter must ALSO not block the paper (real adapters
# fail with KeyError / network errors, not a tidy sentinel). One paper's crash must not sink the batch.
def _kaboom(paper):
    raise KeyError("malformed upstream JSON")            # not an AdapterError
robust = RM.run_pipeline(PAPERS, [("crossref", _kaboom),
                                  ("openalex", RM.make_openalex_adapter(brm.OPENALEX))])
if len(robust) != len(PAPERS):
    fails.append("a non-AdapterError adapter exception blocked/dropped papers (fallback not robust)")
if any(r["enhancement_status"].get("crossref") != "failed" for r in robust):
    fails.append("a hard adapter crash was not recorded as 'failed'")

# ROBUSTNESS: a MUTATING/hostile adapter must not corrupt the original evidence (adapter gets a copy).
def _vandal(paper):
    paper["title"] = "HIJACKED"; paper["arxiv_id"] = "0000.00000"    # tries to corrupt the anchor
    return {"work_id": "x"}
before = copy.deepcopy(PAPERS)
mutated = RM.run_pipeline(PAPERS, [("openalex", _vandal)])
if PAPERS != before:
    fails.append("a mutating adapter corrupted the input papers list")
if any(r["paper"]["title"] == "HIJACKED" or r["paper"]["arxiv_id"] == "0000.00000" for r in mutated):
    fails.append("a mutating adapter corrupted the original evidence anchor")
print("robustness: KeyError-raising adapter kept all papers; mutating adapter could not corrupt the anchor")

# =============================================================== 3) authors/institutions unified (T058)
authors = RM.resolve_authors(enhanced)
alice = [e for e in authors.values() if e["canonical_name"] == "Alice Chen"]
if len(alice) != 1:
    fails.append(f"Alice Chen should resolve to exactly one entity, got {len(alice)}")
else:
    srcs = sorted({p["source_id"] for p in alice[0]["provenance"]})
    if srcs != ["crossref", "openalex"]:
        fails.append(f"Alice Chen should carry provenance from BOTH sources, got {srcs}")
# distinct authors are not confused
names = {e["canonical_name"] for e in authors.values()}
if not ({"Alice Chen", "Bob Li", "Carol Wu"} <= names):
    fails.append(f"distinct authors were merged/lost: {sorted(names)}")
print(f"authors: {sorted(names)}; Alice Chen sources={sorted({p['source_id'] for p in alice[0]['provenance']}) if alice else None}")

# institutions unified the same way (the '机构' deliverable is reconciled, not merely attached)
insts = RM.resolve_institutions(enhanced)
mit = [e for e in insts.values() if e["canonical_name"] == "MIT"]
if len(mit) != 1:
    fails.append(f"MIT should resolve to exactly one institution entity, got {len(mit)}")
else:
    isrc = sorted({p["source_id"] for p in mit[0]["provenance"]})
    if isrc != ["crossref", "openalex"]:
        fails.append(f"MIT should carry provenance from BOTH sources, got {isrc}")
inames = {e["canonical_name"] for e in insts.values()}
if not ({"MIT", "Stanford"} <= inames):
    fails.append(f"distinct institutions were merged/lost: {sorted(inames)}")

# =============================================================== 4) self-describing confirmation flag + citation signals
# the confirmed_publication flag is set at enhance time and matches the linking decision
cr1 = next(e for e in by_arxiv["2401.00001"]["enhancements"] if e["adapter"] == "crossref")
cr2 = next(e for e in by_arxiv["2401.00002"]["enhancements"] if e["adapter"] == "crossref")
if cr1.get("confirmed_publication") is not True:
    fails.append("00001's Crossref enhancement should be flagged confirmed_publication=True")
if cr2.get("confirmed_publication") is not False:
    fails.append("00002's unconfirmed Crossref enhancement should be flagged confirmed_publication=False")
# citation signals (references + cited_by_count) are attached as enhancement, NOT in the original evidence
oa1 = next(e for e in by_arxiv["2401.00001"]["enhancements"] if e["adapter"] == "openalex")
if not oa1.get("references") or "cited_by_count" not in oa1:
    fails.append("OpenAlex citation signals (references / cited_by_count) were not attached as enhancement")
if "references" in by_arxiv["2401.00001"]["paper"]:
    fails.append("citation signals leaked into the original evidence")

# HARDENING CONTROL: a degenerate paper with NO arxiv_id must NOT link a journal version off a
# None==None match (confirmed_publication requires a truthy arxiv id).
degen = [{"arxiv_id": None, "title": "No id paper", "pdf_url": "x"}]
degen_cross = {None: {"doi": "10.9/none", "has_preprint_arxiv_id": None, "authors": []}}
degen_enh = RM.run_pipeline(degen, [("crossref", RM.make_crossref_adapter(degen_cross))])
degen_cr = degen_enh[0]["enhancements"][0]
if degen_cr.get("confirmed_publication") is not False:
    fails.append("a no-arxiv-id paper wrongly got confirmed_publication=True (None==None)")
degen_works = RM.link_works(degen_enh)
if any(v["version_type"] == "journal" for vs in degen_works.values() for v in vs):
    fails.append("a no-arxiv-id paper wrongly linked a spurious journal version")
print(f"institutions: {sorted(inames)}; MIT sources={sorted({p['source_id'] for p in mit[0]['provenance']}) if mit else None}; "
      f"confirmed(00001)={cr1.get('confirmed_publication')} confirmed(00002)={cr2.get('confirmed_publication')}; "
      f"citation refs on 00001={len(oa1.get('references', []))}")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
