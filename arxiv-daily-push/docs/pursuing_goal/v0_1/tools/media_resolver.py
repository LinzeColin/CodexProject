#!/usr/bin/env python3
"""ADP V0.1 media-lead -> official-original resolver + event grouping + abstain (ADP-S3-P03-T038).

Media may DISCOVER a lead (a news item about a policy), but a lead must resolve back to the issuing
authority's official original before it can carry official weight, and reposts of the same event merge
into one canonical event. If no official original is found, the lead ABSTAINS (UNKNOWN) -- it is NEVER
promoted to official (不冒充官方).

Resolution signals (deterministic, no network): a document number (发文字号) mentioned in the media
text that matches an official document; else the referenced official title normalized to an official
document's normalized title. Canonical event grouping reuses the T024 identity. NOT_DEPLOYED.
"""
from __future__ import annotations
import dataclasses, hashlib, re, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from canonicalize import norm_title

# Whitelisted central-government document-number prefixes -> precise, does not over-grab the
# surrounding sentence (e.g. "...日前印发国办发〔2020〕50号" must yield 国办发〔2020〕50号, not 印发国办发...).
_ORG = r"(?:国发|国办发|国办函|国办发明电|中办发|中办国办|发改|网信发|国统字|统计|财|工信部|人社部|教|科|银发)"
DOCNUM_RE = re.compile(_ORG + r"〔\d{4}〕\d+号|国令第\d+号|中华人民共和国主席令第\d+号|第\d+号令")


@dataclasses.dataclass(frozen=True)
class Resolution:
    lead_id: str
    resolved: bool
    official_canonical_id: str | None
    authority: str                  # A0 when bound to an official original; media_lead otherwise
    status: str                     # "bound" | "ABSTAIN"
    match_signal: str | None        # docnum | title | None
    impersonates_official: bool     # ALWAYS False -- an unresolved lead never claims official


def _docnums(text):
    return {re.sub(r"\s+", "", m.group(0)) for m in DOCNUM_RE.finditer(text or "")}


def build_official_index(official_docs):
    """official_docs: [{canonical_id, doc_number, title}] -> lookup by normalized docnum + norm title."""
    by_num, by_title = {}, {}
    for d in official_docs:
        if d.get("doc_number"):
            by_num[re.sub(r"\s+", "", d["doc_number"])] = d["canonical_id"]
        if d.get("title"):
            by_title[norm_title(d["title"])] = d["canonical_id"]
    return by_num, by_title


def resolve_lead(lead, by_num, by_title):
    """lead: {lead_id, text, referenced_title?}. Bind to an official original or ABSTAIN."""
    lid = lead.get("lead_id", "?")
    # 1) a document number cited in the media text
    for n in _docnums((lead.get("text") or "") + " " + (lead.get("title") or "")):
        if n in by_num:
            return Resolution(lid, True, by_num[n], "A0", "bound", "docnum", False)
    # 2) the referenced official title
    ref = lead.get("referenced_title") or lead.get("title") or ""
    cid = by_title.get(norm_title(ref))
    if cid:
        return Resolution(lid, True, cid, "A0", "bound", "title", False)
    # 3) no official original -> ABSTAIN; NEVER impersonate official
    return Resolution(lid, False, None, "media_lead", "ABSTAIN", None, False)


def group_events(resolutions, leads_by_id):
    """Reposts of the same event merge into one canonical event: bound leads group by the official
    canonical_id; abstained leads group by the ttl of their normalized title (so duplicate news of an
    unbacked event still collapse, but stay ABSTAIN)."""
    events = {}
    for r in resolutions:
        if r.resolved:
            key = r.official_canonical_id
        else:
            key = "ttl:" + hashlib.sha256(norm_title(leads_by_id[r.lead_id].get("title", "")).encode()).hexdigest()[:16]
        ev = events.setdefault(key, {"canonical_id": key, "official_backed": r.resolved,
                                     "authority": r.authority, "lead_ids": [], "status": r.status})
        ev["lead_ids"].append(r.lead_id)
    for ev in events.values():
        ev["repost_count"] = len(ev["lead_ids"])
    return list(events.values())


def resolve_all(leads, official_docs):
    by_num, by_title = build_official_index(official_docs)
    res = [resolve_lead(l, by_num, by_title) for l in leads]
    leads_by_id = {l["lead_id"]: l for l in leads}
    events = group_events(res, leads_by_id)
    return {"resolutions": [dataclasses.asdict(r) for r in res], "events": events,
            "summary": {"leads": len(leads), "bound": sum(1 for r in res if r.resolved),
                        "abstained": sum(1 for r in res if not r.resolved),
                        "events": len(events),
                        "impersonations": sum(1 for r in res if r.impersonates_official)}}
