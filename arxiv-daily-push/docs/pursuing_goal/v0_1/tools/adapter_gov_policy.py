#!/usr/bin/env python3
"""ADP V0.1 A0 adapter: State Council policy documents + national laws/regulations (ADP-S3-P02-T034).

The first real A0 official adapter. Parses the gov.cn policy-document template (国务院政策文件 /
国家法律法规) into the A0 field set -- original title, 发文字号 (doc number), issuing organ, TYPED
dates (成文日期 written vs 发布日期 published, kept distinct), effectiveness status, and attachments --
on the T031 SDK, verified official by T033, and contract-tested by T032. Deterministic parse; the real
HTTP fetch is the T031 HttpFetcher (Owner: real fetch at the kernel stage). NOT_DEPLOYED: not wired to
the worker; a live fetch runs from the dev environment.

Real DOM (confirmed against gov.cn/zhengce/content/*.htm): a meta table with
  <b>发文字号：</b></td> <td>国办发〔2020〕50号</td> ... <b>成文日期：</b></td><td>2020年12月07日</td>
  <b>发布日期：</b></td><td>2020年12月21日</td>   (成文 != 发布 -> date types must not be confused)
"""
from __future__ import annotations
import dataclasses, hashlib, html as _html, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import official_connector as OC
import official_identity as OI

_DATE_CN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
_DATE_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def norm_date(s):
    """Chinese or ISO date -> YYYY-MM-DD; None if unparseable (never guessed)."""
    if not s:
        return None
    m = _DATE_CN.search(s) or _DATE_ISO.search(s)
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def _meta(html, label):
    m = re.search(r'<b>\s*' + label + r'\s*[：:]\s*</b>\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>', html)
    return _html.unescape(m.group(1).strip()) if m else None


def _title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return _html.unescape(m.group(1)).split("_")[0].strip() if m else ""


class FixtureFetcher:
    """Reads local fixture files, for deterministic contract tests (no network)."""
    def __init__(self, d):
        self.d = pathlib.Path(d)

    def get(self, url, fetched_at):
        body = (self.d / url).read_bytes()
        return OC.FetchResult(url, 200, "text/html", body, hashlib.sha256(body).hexdigest(), fetched_at, True)


class GovCnPolicyConnector(OC.OfficialConnector):
    """State Council policy documents / national laws & regulations on gov.cn. Parameterised by a
    listing URL so 政策文件 and 法规 register as two sources sharing one parser (same template)."""
    def __init__(self, source_id="gov-cn-policy", listing="https://www.gov.cn/zhengce/xxgk/",
                 fetcher=None, host="www.gov.cn"):
        self.source_id = source_id
        self.authority_level = "A0"
        self.listing = listing
        self.host = host
        self.fetcher = fetcher or OC.HttpFetcher(timeout=15)

    def health(self):
        return OC.HealthResult(True, "gov.cn policy adapter", self.listing)

    def fetch(self, url, fetched_at):
        return self.fetcher.get(url, fetched_at)

    def discover(self, cursor):
        """Parse the policy listing into DiscoverItems (content links + publish dates); resume after
        cursor.last_date so the historical cursor is recoverable."""
        fr = self.fetcher.get(self.listing, "listing")
        html = fr.body.decode("utf-8", "ignore")
        items = []
        for m in re.finditer(r'href="(https?://[^"]*/zhengce/(?:content|zhengceku)/[^"]+\.htm)"[^>]*>([^<]{4,80})', html):
            url, title = m.group(1), _html.unescape(m.group(2)).strip()
            dm = re.search(r"/(\d{4})-(\d{1,2})/(\d{1,2})/", url)
            d = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else None
            items.append(OC.DiscoverItem(url, title, d))
        # dedup by url, keep first
        seen, uniq = set(), []
        for it in items:
            if it.url not in seen:
                seen.add(it.url); uniq.append(it)
        if cursor and cursor.last_date:
            uniq = [it for it in uniq if (it.hint_date or "") > cursor.last_date]
        return uniq

    def verify(self, item, fetched):
        r = OI.verify_identity({"source_id": self.source_id, "url": item.url if isinstance(item, OC.DiscoverItem) else item,
                                "category": "china_official", "host_org": "国务院办公厅"})
        return OC.VerifyResult(r["verified"], r["authority_level"], r["evidence"]["official_domain"], tuple(r["reasons"]))

    def parse_policy(self, fetched):
        """Full A0 policy template with TYPED dates (成文 written vs 发布 published kept distinct)."""
        html = fetched.body.decode("utf-8", "ignore")
        status = None
        sm = re.search(r"(现行有效|已废止|失效|尚未生效)", html)
        if sm:
            status = sm.group(1)
        atts = [OC.Attachment(u, u.rsplit(".", 1)[-1].lower())
                for u in re.findall(r'href="([^"]+\.(?:pdf|docx?|wps|xlsx?))"', html, re.I)]
        return {
            "title": _title(html),
            "doc_number": _meta(html, "发文字号"),
            "issuing_org": _meta(html, "发文机关"),
            "subject": _meta(html, "主题分类"),
            "dates": {"written": norm_date(_meta(html, "成文日期")),
                      "published": norm_date(_meta(html, "发布日期"))},
            "status": status,
            "attachments": [{"url": a.url, "kind": a.kind} for a in atts],
        }

    def normalize(self, item, fetched):
        p = self.parse_policy(fetched)
        # canonical doc_date = PUBLISHED date (not 成文); the written date is preserved in parse_policy
        return OC.NormalizedDoc(
            self.source_id, item.url if isinstance(item, OC.DiscoverItem) else item, p["title"],
            p["doc_number"], p["dates"]["published"], p["status"], "A0",
            body_text=(p["issuing_org"] or ""), attachments=tuple(OC.Attachment(a["url"], a["kind"]) for a in p["attachments"]),
            canonical_hint="ttl:" + hashlib.sha256(p["title"].encode()).hexdigest()[:16])

    def attachments(self, fetched):
        return [OC.Attachment(a["url"], a["kind"]) for a in self.parse_policy(fetched)["attachments"]]

    def cursor(self, docs):
        dates = [d.doc_date for d in docs if d.doc_date]
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=max(dates) if dates else None)


def build_registry(fetcher=None):
    reg = OC.AdapterRegistry()
    reg.register(GovCnPolicyConnector("gov-cn-policy", "https://www.gov.cn/zhengce/xxgk/", fetcher))
    reg.register(GovCnPolicyConnector("gov-cn-fagui", "https://www.gov.cn/zhengce/fagui/", fetcher))
    return reg


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture-dir")
    ap.add_argument("--doc", help="fixture filename or URL to parse")
    ap.add_argument("--out")
    args = ap.parse_args()
    conn = GovCnPolicyConnector(fetcher=FixtureFetcher(args.fixture_dir) if args.fixture_dir else None)
    fr = conn.fetch(args.doc, "2026-07-17T00:00:00+10:00")
    res = conn.parse_policy(fr)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
