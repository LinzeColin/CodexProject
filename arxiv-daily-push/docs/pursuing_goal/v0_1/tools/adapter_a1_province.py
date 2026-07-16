#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T049 -- A1 provincial-government-portal adapter FAMILY.

A1 (province-level official) coverage without copying a business-logic codebase per province.
ONE generic connector class (A1ProvinceConnector) is driven by a declarative SiteProfile; adding a
province = adding a profile, not a class. The connector body has ZERO province conditionals -- every
province-specific rule lives in the profile (regexes) or in a NAMED override hook it references.

Two template families are demonstrated over three real provincial portals:
  - "art-cms"        : /art/YYYY/M/D/art_<col>_<id>.html  -> Jiangsu, Shandong  (title hook: strip_leading_labels)
  - "beijing-zhengce": ./YYYYMM/tYYYYMMDD_<id>.html        -> Beijing            (title hook: before_underscore)

Identity: provincial .gov.cn portals are curated official entities, so the profile asserts
gov_directory_listed=True; official_identity.verify_identity then classifies official-domain +
directory-marker + NON-central -> A1 (never A0). Media/search are out of scope here.
"""
import re, sys, pathlib, hashlib, dataclasses
from urllib.parse import urljoin

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official_connector as OC   # T031
import official_identity as OI    # T033


# --- override hooks: the ONLY place province-specific title logic lives (referenced by name) -----
def _hook_strip_leading_labels(title, n_labels):
    """art-cms family: <title> is 'PROVINCE_GOV  COLUMN  REAL_TITLE'; drop the first n label tokens."""
    parts = re.split(r"\s+", (title or "").strip())
    return " ".join(parts[n_labels:]).strip() if len(parts) > n_labels else (title or "").strip()

def _hook_before_underscore(title):
    """beijing-zhengce family: <title> is 'REAL_TITLE_政策文件_首都之窗_...'; keep the head."""
    return (title or "").split("_")[0].strip()

TITLE_HOOKS = {
    "strip_leading_labels": _hook_strip_leading_labels,
    "before_underscore": _hook_before_underscore,
}


# --- declarative per-province profile ------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class SiteProfile:
    source_id: str
    province: str
    template_family: str                 # "art-cms" | "beijing-zhengce" | ...
    base_url: str                        # scheme+host, e.g. https://www.jiangsu.gov.cn
    listing_url: str
    article_url_re: str                  # group(1) = an article href in the listing HTML
    docnum_re: str                       # province document-number pattern (苏.../鲁.../京...)
    title_hook: str                      # a key in TITLE_HOOKS
    title_hook_args: tuple = ()
    date_re: str = r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})"
    attachment_re: str = r'(?:href|src)="([^"]+\.(?:pdf|docx?|wps|xlsx?))"'
    host_org: str = ""                   # curated 主办单位 (province gov)
    gov_directory_listed: bool = True    # curated: this IS the official province portal


# --- fixture fetcher (offline, deterministic contract tests; no clock/network) -------------------
class FixtureFetcher:
    def __init__(self, mapping):
        self._m = mapping               # {url: html_str}
    def get(self, url, fetched_at):
        html = self._m.get(url, "")
        b = html.encode("utf-8")
        return OC.FetchResult(url=url, status=200 if html else 404, content_type="text/html",
                              body=b, sha256=hashlib.sha256(b).hexdigest(),
                              fetched_at=fetched_at, ok=bool(html))


# --- the ONE generic connector: no province conditionals; all specifics come from the profile ----
class A1ProvinceConnector(OC.OfficialConnector):
    authority_level = "A1"

    def __init__(self, profile: SiteProfile, fetcher):
        self.profile = profile
        self.source_id = profile.source_id
        self.fetcher = fetcher
        self._art_re = re.compile(profile.article_url_re)
        self._docnum_re = re.compile(profile.docnum_re)
        self._date_re = re.compile(profile.date_re)
        self._att_re = re.compile(profile.attachment_re, re.I)

    def health(self):
        return OC.HealthResult(ok=True, checked=self.profile.listing_url, note=self.profile.template_family)

    def fetch(self, url, fetched_at):
        return self.fetcher.get(url, fetched_at)

    def _abs(self, ref, base):
        return urljoin(base, ref)

    def discover(self, cursor):
        fr = self.fetch(self.profile.listing_url, "")
        html = fr.body.decode("utf-8", "ignore")
        seen, items = set(), []
        for m in self._art_re.finditer(html):
            url = self._abs(m.group(1), self.profile.listing_url)
            if url in seen:
                continue
            seen.add(url)
            items.append(OC.DiscoverItem(url=url, title=""))
        return items

    def verify(self, item, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        r = OI.verify_identity({"source_id": self.source_id, "url": item.url, "category": "official",
                                "gov_directory_listed": self.profile.gov_directory_listed,
                                "host_org": self.profile.host_org or None}, html)
        return OC.VerifyResult(is_official=r["verified"], authority_level=r["authority_level"],
                               official_domain=r["evidence"]["official_domain"], reasons=tuple(r["reasons"]))

    def _clean_title(self, raw):
        hook = TITLE_HOOKS[self.profile.title_hook]      # special logic lives in the named hook
        return hook(raw, *self.profile.title_hook_args)

    def attachments(self, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        out, seen = [], set()
        for u in self._att_re.findall(html):
            au = self._abs(u, fetched.url)
            if au in seen:
                continue
            seen.add(au)
            out.append(OC.Attachment(url=au, kind=au.rsplit(".", 1)[-1].lower()))
        return out

    def _extract_date(self, html):
        """The DOCUMENT publish date -- not the page render/capture timestamp. Chinese gov CMS pages
        carry a `Maketime` meta (when the page was generated) BEFORE the real `PubDate/pubdate` meta;
        a naive first-date-in-page match grabs Maketime and is wrong. So: (1) drop the Maketime meta,
        (2) prefer the CMS publish-date meta, (3) fall back to a 发布/成文 label, then the profile regex."""
        html = re.sub(r"<meta\s+name=['\"]?[Mm]aketime['\"]?[^>]*>", "", html)
        m = re.search(r"<meta\s+name=['\"](?:pubdate|PubDate|publishdate|PubTime)['\"][^>]*content=['\"]\s*(\d{4})-(\d{1,2})-(\d{1,2})", html, re.I)
        if not m:
            m = re.search(r"(?:发布日期|成文日期|发文日期|印发日期)[：:\s]*[<>a-zA-Z\"'/=]*?(\d{4})[-年.](\d{1,2})[-月.](\d{1,2})", html)
        if not m:
            m = self._date_re.search(html)
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None

    def normalize(self, item, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        rt = re.search(r"<title>([^<]*)</title>", html)
        title = self._clean_title(rt.group(1) if rt else "")
        dn = self._docnum_re.search(html)
        doc_date = self._extract_date(html)
        return OC.NormalizedDoc(
            source_id=self.source_id, doc_id=item.url, title=title,
            doc_number=dn.group(1) if dn else None, doc_date=doc_date, status=None,
            authority_level="A1", body_text="",
            attachments=tuple(self.attachments(fetched)),
            canonical_hint="ttl:" + hashlib.sha256(item.url.encode()).hexdigest()[:16])

    def cursor(self, docs):
        dates = [d.doc_date for d in docs if d.doc_date]
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=max(dates) if dates else None)


# --- the profile registry (3 real provincial portals across 2 template families) -----------------
PROFILES = {
    "jiangsu-gov": SiteProfile(
        source_id="jiangsu-gov", province="江苏", template_family="art-cms",
        base_url="https://www.jiangsu.gov.cn",
        listing_url="https://www.jiangsu.gov.cn/col/col76841/index.html",
        article_url_re=r'href="(https?://www\.jiangsu\.gov\.cn/art/\d{4}/\d{1,2}/\d{1,2}/art_\d+_\d+\.html)"',
        docnum_re=r"(苏[一-龥]{0,6}〔\d{4}〕第?\s*\d+\s*号)",
        title_hook="strip_leading_labels", title_hook_args=(2,), host_org="江苏省人民政府"),
    "shandong-gov": SiteProfile(
        source_id="shandong-gov", province="山东", template_family="art-cms",
        base_url="http://www.shandong.gov.cn",
        listing_url="http://www.shandong.gov.cn/col/col94237/index.html",
        article_url_re=r'href="(https?://www\.shandong\.gov\.cn/art/\d{4}/\d{1,2}/\d{1,2}/art_\d+_\d+\.html)"',
        docnum_re=r"(鲁[一-龥]{0,6}〔\d{4}〕第?\s*\d+\s*号)",
        title_hook="strip_leading_labels", title_hook_args=(2,), host_org="山东省人民政府"),
    "beijing-gov": SiteProfile(
        source_id="beijing-gov", province="北京", template_family="beijing-zhengce",
        base_url="https://www.beijing.gov.cn",
        listing_url="https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        article_url_re=r'href="(\./\d{6}/t\d{8}_\d+\.html)"',
        docnum_re=r"(京[一-龥]{0,6}〔\d{4}〕第?\s*\d+\s*号)",
        title_hook="before_underscore", host_org="北京市人民政府"),
}


def build_family(fetcher):
    """Instantiate one connector per profile off the SAME class. Adding a province adds a profile only."""
    return {sid: A1ProvinceConnector(p, fetcher) for sid, p in PROFILES.items()}


# --- contract check: run one profile end-to-end over its captured fixtures -----------------------
def run_contract(source_id, listing_html, article_html, article_url, fetched_at="2026-07-16T00:00:00+10:00"):
    """discover -> verify -> normalize a real captured fixture pair; return a structured pass/fail record.
    A profile PASSES when: >=1 article discovered, verified A1 on an official non-central .gov.cn domain,
    a cleaned non-empty title that is genuinely shorter than the raw <title> (the hook did work), a
    province-prefixed doc_number, and a doc_date."""
    prof = PROFILES[source_id]
    conn = A1ProvinceConnector(prof, FixtureFetcher({prof.listing_url: listing_html, article_url: article_html}))
    items = conn.discover(None)
    it = OC.DiscoverItem(url=article_url, title="")
    fr = conn.fetch(article_url, fetched_at)
    ver = conn.verify(it, fr)
    nd = conn.normalize(it, fr)
    raw_title = re.search(r"<title>([^<]*)</title>", article_html)
    raw_title = raw_title.group(1).strip() if raw_title else ""
    prov_prefix = prof.docnum_re[1:2] if prof.docnum_re.startswith("(") else prof.province[:1]
    # cross-checks that the doc_date is the DOCUMENT date, not the page render timestamp:
    mk = re.search(r"[Mm]aketime['\"]?\s+content=['\"]?(\d{4}-\d{1,2}-\d{1,2})", article_html)
    maketime = mk.group(1) if mk else None
    urld = re.search(r"/art/(\d{4})/(\d{1,2})/(\d{1,2})/", article_url)
    url_date = f"{urld.group(1)}-{int(urld.group(2)):02d}-{int(urld.group(3)):02d}" if urld else None
    pm = re.search(r"<meta\s+name=['\"](?:pubdate|PubDate|publishdate)['\"][^>]*content=['\"]\s*(\d{4})-(\d{1,2})-(\d{1,2})", article_html, re.I)
    pubdate_meta = f"{pm.group(1)}-{int(pm.group(2)):02d}-{int(pm.group(3)):02d}" if pm else None
    checks = {
        "discovered": len(items) >= 1,
        "verified_A1": ver.authority_level == "A1" and ver.is_official,
        "official_noncentral_domain": ver.official_domain,
        "title_cleaned": bool(nd.title) and len(nd.title) < len(raw_title),
        "docnum_province_prefixed": bool(nd.doc_number) and nd.doc_number.startswith(prov_prefix),
        "has_date": bool(nd.doc_date),
        # the date must be the document date, not the <meta Maketime> render/capture timestamp:
        "date_not_render_timestamp": bool(nd.doc_date) and nd.doc_date != maketime,
        # for the art-cms family the URL encodes the publish date -> the doc_date must match it:
        "date_matches_url_path": (url_date is None) or (nd.doc_date == url_date),
        # wherever a CMS publish-date meta exists (all 3 families), the doc_date must equal it:
        "date_matches_pubdate_meta": (pubdate_meta is None) or (nd.doc_date == pubdate_meta),
    }
    return {
        "source_id": source_id, "province": prof.province, "template_family": prof.template_family,
        "discovered": len(items), "authority_level": ver.authority_level,
        "raw_title": raw_title[:80], "clean_title": nd.title[:80],
        "doc_number": nd.doc_number, "doc_date": nd.doc_date, "maketime_rejected": maketime,
        "url_date": url_date, "attachments": len(nd.attachments),
        "checks": checks, "passed": all(checks.values()),
    }

