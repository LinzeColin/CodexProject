#!/usr/bin/env python3
"""ADP V0.1 Board 3 (policy view) eligibility gate + date/status extractors (ADP-S3-P03-T037).

Before ranking, admit ONLY official primary documents to Board 3 and exclude news noise, and identify
the four policy dates -- 成文 (written), 发布 (published), 施行 (effective), 失效 (expired) -- plus the
effectiveness status. Media / search / news / interpretation never enter the ranked policy view (they
may still be discovery leads, resolved back to the official original in T038).

Builds on T033 (official identity), T034 (policy dates), T036 (doc-type classifier). Deterministic.
NOT_DEPLOYED: gate + extractors; not wired into the worker ranker.
"""
from __future__ import annotations
import dataclasses, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import official_identity as OI
from adapter_gov_policy import norm_date, _meta
from adapter_cac_nda import classify_doc_type

# doc types that are official PRIMARY policy content admissible to Board 3
ADMISSIBLE_TYPES = {"formal", "consultation"}     # news / interpretation excluded


@dataclasses.dataclass(frozen=True)
class PolicyDates:
    written: str | None       # 成文
    published: str | None     # 发布
    effective: str | None     # 施行
    expired: str | None       # 失效/废止
    status: str | None        # 现行有效 / 已废止 / 失效 / 尚未施行


def extract_dates_status(html, title=""):
    def _find(*labels):
        for lb in labels:
            v = _meta(html, lb)
            if v:
                return norm_date(v)
        return None
    written = _find("成文日期")
    published = _find("发布日期", "发布时间")
    # effective: 自YYYY年MM月DD日起施行 / 施行日期 / 自公布之日起施行
    eff = None
    m = re.search(r"自(\d{4}年\d{1,2}月\d{1,2}日)起施行", html) or None
    if m:
        eff = norm_date(m.group(1))
    elif _meta(html, "施行日期"):
        eff = norm_date(_meta(html, "施行日期"))
    elif re.search(r"自公布之日起施行", html):
        eff = published
    # expired: 自YYYY年MM月DD日起废止 / 已废止 / 失效日期
    exp = None
    m2 = re.search(r"自(\d{4}年\d{1,2}月\d{1,2}日)起废止", html)
    if m2:
        exp = norm_date(m2.group(1))
    elif _meta(html, "失效日期") or _meta(html, "废止日期"):
        exp = norm_date(_meta(html, "失效日期") or _meta(html, "废止日期"))
    # status
    status = None
    sm = re.search(r"(现行有效|已废止|失效|尚未施行)", html)
    if sm:
        status = sm.group(1)
    elif exp:
        status = "已废止"
    elif eff:
        status = "现行有效"
    return PolicyDates(written, published, eff, exp, status)


def is_eligible(source_authority, doc_type):
    """Admit only official (A0/A1) primary policy documents. Media/search/news/interpretation excluded."""
    official = source_authority in ("A0", "A1")
    admissible_type = doc_type in ADMISSIBLE_TYPES
    return official and admissible_type


def admit(candidate):
    """candidate: {source_id, category, title, html, ...}. Returns (eligible, reason, doc_type, authority)."""
    ident = OI.verify_identity({"source_id": candidate.get("source_id"), "url": candidate.get("url", ""),
                                "category": candidate.get("category", ""),
                                "host_org": candidate.get("host_org"), "id_code": candidate.get("id_code")})
    authority = ident["authority_level"]
    dt = classify_doc_type(candidate.get("title", ""), candidate.get("url", ""), candidate.get("html", ""))
    eligible = is_eligible(authority, dt.doc_type)
    if not eligible:
        if authority not in ("A0", "A1"):
            reason = f"non-official source (authority={authority})"
        else:
            reason = f"non-primary doc_type={dt.doc_type}"
    else:
        reason = f"official {authority} + {dt.doc_type}"
    return {"source_id": candidate.get("source_id"), "eligible": eligible, "reason": reason,
            "doc_type": dt.doc_type, "authority": authority}


def gate_board3(candidates):
    admitted, rejected = [], []
    for c in candidates:
        r = admit(c)
        (admitted if r["eligible"] else rejected).append({**c, **r})
    return {"admitted": admitted, "rejected": rejected,
            "counts": {"in": len(candidates), "admitted": len(admitted), "rejected": len(rejected)}}
