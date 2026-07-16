#!/usr/bin/env python3
"""ADP V0.1 A0 adapters: CAC (网信办) + National Data Administration (国家数据局) (ADP-S3-P02-T036).

Covers front-line AI / cybersecurity / data-governance / national-data-policy content. The core
capability is a DOCUMENT-TYPE classifier that distinguishes a public consultation (征求意见), a formal
official document (正式文件), an interpretation (解读), and news (新闻) -- with the official original
text as PRIMARY. On the T031 SDK, verified by T033. Deterministic; real fetch via the T031 HttpFetcher.
NOT_DEPLOYED.

Access note (honest): www.cac.gov.cn serves normally; www.nda.gov.cn returns a JS shell and rejects
the default TLS (TLSV1_ALERT_PROTOCOL_VERSION), so nda-gov is registered but its live fetch is BLOCKED
from a plain urllib client and needs a browser / an RSS-or-API entry -- recorded, not faked.
"""
from __future__ import annotations
import dataclasses, hashlib, html as _html, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import official_connector as OC
import official_identity as OI

CONSULT_KW = ["征求意见", "公开征求", "意见征集", "征求意见稿", "草案征求意见"]
INTERP_KW = ["解读", "答记者问", "图解", "政策问答", "一图读懂"]
FORMAL_KW = ["办法", "规定", "通知", "公告", "决定", "令", "条例", "指南", "要求"]
NEWS_KW = ["考察", "会见", "座谈", "调研", "出席", "讲话", "会议", "动态"]


@dataclasses.dataclass(frozen=True)
class DocType:
    doc_type: str            # consultation / formal / interpretation / news
    is_primary: bool         # official original text is primary; 解读/新闻 point back to it
    consultation_status: str | None   # open / closed / None
    deadline: str | None


def classify_doc_type(title, url="", text=""):
    t = (title or "") + " " + (url or "")
    body = text or ""
    if any(k in t for k in CONSULT_KW):
        status, deadline = _consultation_status(body)
        return DocType("consultation", True, status, deadline)          # the consultation IS the official original
    if any(k in t for k in INTERP_KW):
        return DocType("interpretation", False, None, None)             # secondary: interprets a formal doc
    has_docnum = bool(re.search(r"第?\d+号|〔\d{4}〕", t + body))
    if any(k in t for k in FORMAL_KW) and not any(k in t for k in NEWS_KW):
        return DocType("formal", True, None, None)                      # official original text -> primary
    if any(k in t for k in NEWS_KW):
        return DocType("news", False, None, None)                       # secondary
    return DocType("formal" if has_docnum else "news", has_docnum, None, None)


def _consultation_status(text):
    m = re.search(r"(?:截止|意见反馈截止(?:日期|时间)?)[：:至\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)", text)
    deadline = None
    if m:
        d = re.findall(r"\d+", m.group(1))
        if len(d) >= 3:
            deadline = f"{int(d[0]):04d}-{int(d[1]):02d}-{int(d[2]):02d}"
    if "已结束" in text or "征集结束" in text:
        return "closed", deadline
    if any(k in text for k in ["公开征求", "欢迎社会各界", "反馈意见"]):
        return "open", deadline
    return ("open" if deadline else None), deadline


class CacNdaConnector(OC.OfficialConnector):
    def __init__(self, source_id, listing, host, fetcher=None, live_blocked=False):
        self.source_id = source_id
        self.authority_level = "A0"
        self.listing = listing
        self.host = host
        self.fetcher = fetcher or OC.HttpFetcher(timeout=15)
        self.live_blocked = live_blocked      # nda.gov.cn: TLS/JS-shell blocks a plain client

    def health(self):
        if self.live_blocked:
            return OC.HealthResult(False, f"{self.source_id} live fetch", "blocked: TLS/JS-shell; needs browser or RSS/API entry")
        return OC.HealthResult(True, f"{self.source_id} adapter", self.listing)

    def fetch(self, url, fetched_at):
        return self.fetcher.get(url, fetched_at)

    def discover(self, cursor):
        html = self.fetcher.get(self.listing, "listing").body.decode("utf-8", "ignore")
        items, seen = [], set()
        for m in re.finditer(r'href="([^"]*(?:c_\d+|content_\d+|t\d{8}_\d+)\.(?:html?|htm))"[^>]*>\s*([^<]{6,60})', html):
            url, title = m.group(1), _html.unescape(m.group(2)).strip()
            if url in seen:
                continue
            seen.add(url)
            items.append(OC.DiscoverItem(url, title, None))
        return items

    def verify(self, item, fetched):
        r = OI.verify_identity({"source_id": self.source_id, "url": self.host, "category": "china_official",
                                "host_org": "国家互联网信息办公室"})
        return OC.VerifyResult(r["verified"], r["authority_level"], r["evidence"]["official_domain"], tuple(r["reasons"]))

    def normalize(self, item, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        title = _html.unescape(title.group(1)).split("_")[0].split(" - ")[0].strip() if title else \
            (item.title if isinstance(item, OC.DiscoverItem) else "")
        dt = classify_doc_type(title, item.url if isinstance(item, OC.DiscoverItem) else "", html)
        return OC.NormalizedDoc(self.source_id, item.url if isinstance(item, OC.DiscoverItem) else item, title,
                                None, None, dt.consultation_status, "A0",
                                body_text=f"doc_type={dt.doc_type} primary={dt.is_primary}", attachments=tuple(self.attachments(fetched)),
                                canonical_hint="ttl:" + hashlib.sha256(title.encode()).hexdigest()[:16])

    def attachments(self, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        return [OC.Attachment(u, u.rsplit(".", 1)[-1].lower())
                for u in re.findall(r'href="([^"]+\.(?:pdf|docx?|wps|xlsx?))"', html, re.I)]

    def cursor(self, docs):
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=None)


def build_registry(fetcher=None):
    reg = OC.AdapterRegistry()
    reg.register(CacNdaConnector("cac-gov", "https://www.cac.gov.cn/", "https://www.cac.gov.cn/", fetcher))
    reg.register(CacNdaConnector("nda-gov", "https://www.nda.gov.cn/", "https://www.nda.gov.cn/", fetcher, live_blocked=True))
    return reg


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--url", default="")
    args = ap.parse_args()
    print(json.dumps(dataclasses.asdict(classify_doc_type(args.title, args.url)), ensure_ascii=False, indent=2))
