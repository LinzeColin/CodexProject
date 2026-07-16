#!/usr/bin/env python3
"""ADP V0.1 A0 adapters: National Bureau of Statistics + NDRC (ADP-S3-P02-T035).

Adds two A0 official adapters on the T031 SDK -- 国家统计局 (stats.gov.cn) and 国家发改委 (ndrc.gov.cn) --
and, crucially, a STATISTICAL CLAIM extractor. Every statistical claim records its indicator, value,
UNIT, PERIOD, statistical basis (口径: 同比/环比/累计/不变价/现价…), and REVISION state (初步核算/最终
核实/修订). A claim only becomes a FACT when it comes from an official (A0/A1) source -- numbers seen in
media are recorded as claims but never promoted to facts (不从媒体数字形成事实).

Deterministic parse; the real HTTP fetch is the T031 HttpFetcher. NOT_DEPLOYED. Real DOM confirmed on
stats.gov.cn/sj/zxfb (e.g. "2026年二季度和上半年国内生产总值初步核算结果").
"""
from __future__ import annotations
import dataclasses, hashlib, html as _html, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import official_connector as OC
import official_identity as OI

INDICATORS = ["国内生产总值", "GDP", "居民消费价格", "CPI", "工业生产者出厂价格", "PPI",
              "规模以上工业增加值", "社会消费品零售总额", "固定资产投资", "居民人均可支配收入",
              "货物进出口总额", "城镇调查失业率"]
UNITS = ["万亿元", "亿元", "万元", "百分点", "万人", "万吨", "元", "%"]
BASIS = ["比上年同期", "比上年", "同比", "环比", "累计", "当月", "当季", "不变价", "现价", "可比价", "两年平均"]
REVISION = ["初步核算", "初步统计", "最终核实", "修订", "初步预计"]
_NUM = r"\d[\d,]*(?:\.\d+)?"


@dataclasses.dataclass(frozen=True)
class StatClaim:
    indicator: str
    value: str
    unit: str
    period: str | None
    basis: str | None            # 口径
    revision: str | None
    source_id: str
    authority_level: str
    is_fact: bool                # True only when the source is official (A0/A1)


def _period_from(title, text):
    for pat in [r"(\d{4}年(?:[一二三四]季度)?(?:上半年|下半年|全年)?)", r"(\d{4}年\d{1,2}月)"]:
        m = re.search(pat, title) or re.search(pat, text)
        if m:
            return m.group(1)
    return None


def _revision_from(title, text):
    for r in REVISION:
        if r in title or r in text:
            return r
    return None


def extract_stat_claims(text, source_id, authority_level, title=""):
    """Extract statistical claims. A claim = an indicator + a value + a unit, with the nearest 口径
    marker and the release's revision state. Only official sources (A0/A1) yield facts."""
    text = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)))
    period = _period_from(title, text)
    revision = _revision_from(title, text)
    is_official = authority_level in ("A0", "A1")
    claims, seen = [], set()
    ind_alt = "|".join(map(re.escape, INDICATORS))
    unit_alt = "|".join(map(re.escape, UNITS))
    # form: <indicator> ... <value><unit> ... optional <basis>增长 <value>%
    for m in re.finditer(rf"({ind_alt})[^。，]{{0,20}}?({_NUM})\s*({unit_alt})", text):
        ind, val, unit = m.group(1), m.group(2), m.group(3)
        window = text[max(0, m.start() - 30):m.end() + 30]
        basis = next((b for b in BASIS if b in window), None)
        key = (ind, val, unit, basis)
        if key in seen:
            continue
        seen.add(key)
        claims.append(StatClaim(ind, val, unit, period, basis, revision, source_id, authority_level, is_official))
    return claims


def claims_to_facts(claims):
    """不从媒体数字形成事实: only official-source claims are facts."""
    return [c for c in claims if c.is_fact]


class OfficialStatConnector(OC.OfficialConnector):
    def __init__(self, source_id, listing, host, fetcher=None):
        self.source_id = source_id
        self.authority_level = "A0"
        self.listing = listing
        self.host = host
        self.fetcher = fetcher or OC.HttpFetcher(timeout=20)

    def health(self):
        return OC.HealthResult(True, f"{self.source_id} adapter", self.listing)

    def fetch(self, url, fetched_at):
        return self.fetcher.get(url, fetched_at)

    def discover(self, cursor):
        html = self.fetcher.get(self.listing, "listing").body.decode("utf-8", "ignore")
        items, seen = [], set()
        for m in re.finditer(r'href="([^"]*t(\d{8})_\d+\.html)"[^>]*>\s*([^<]{6,60})', html):
            url, ymd, title = m.group(1), m.group(2), _html.unescape(m.group(3)).strip()
            d = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}"
            if url in seen:
                continue
            seen.add(url)
            items.append(OC.DiscoverItem(url, title, d))
        if cursor and cursor.last_date:
            items = [it for it in items if (it.hint_date or "") > cursor.last_date]
        return items

    def verify(self, item, fetched):
        r = OI.verify_identity({"source_id": self.source_id, "url": self.host, "category": "china_official",
                                "id_code": "bm36000002"})
        return OC.VerifyResult(r["verified"], r["authority_level"], r["evidence"]["official_domain"], tuple(r["reasons"]))

    def normalize(self, item, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        title = _html.unescape(title.group(1)).split(" - ")[0].split("_")[0].strip() if title else ""
        claims = extract_stat_claims(html, self.source_id, "A0", title)
        return OC.NormalizedDoc(self.source_id, item.url if isinstance(item, OC.DiscoverItem) else item, title,
                                None, item.hint_date if isinstance(item, OC.DiscoverItem) else None,
                                _revision_from(title, html), "A0",
                                body_text=f"{len(claims)} stat claims", attachments=(),
                                canonical_hint="ttl:" + hashlib.sha256(title.encode()).hexdigest()[:16])

    def attachments(self, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        return [OC.Attachment(u, u.rsplit(".", 1)[-1].lower())
                for u in re.findall(r'href="([^"]+\.(?:pdf|docx?|xlsx?|csv))"', html, re.I)]

    def cursor(self, docs):
        dates = [d.doc_date for d in docs if d.doc_date]
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=max(dates) if dates else None)


def build_registry(fetcher=None):
    reg = OC.AdapterRegistry()
    reg.register(OfficialStatConnector("stats-gov", "https://www.stats.gov.cn/sj/zxfb/", "https://www.stats.gov.cn/", fetcher))
    reg.register(OfficialStatConnector("ndrc-gov", "https://www.ndrc.gov.cn/xxgk/", "https://www.ndrc.gov.cn/", fetcher))
    return reg


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--source-id", default="stats-gov")
    ap.add_argument("--authority", default="A0")
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    claims = extract_stat_claims(text, args.source_id, args.authority, args.title)
    print(json.dumps({"claims": [dataclasses.asdict(c) for c in claims], "facts": len(claims_to_facts(claims))},
                     ensure_ascii=False, indent=2))
