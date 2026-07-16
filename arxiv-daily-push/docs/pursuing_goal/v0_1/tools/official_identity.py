#!/usr/bin/env python3
"""ADP V0.1 official identity verifier + A0 marking (ADP-S3-P01-T033).

Verifies a source's officialness from four evidence signals and assigns an authority level:
  1. official domain      -- a central-government .gov.cn domain;
  2. host organization    -- footer 主办 / 主办单位 (e.g. 国务院办公厅);
  3. government directory  -- listed in the government website directory (provided/checked flag);
  4. website ID code       -- 网站标识码 (e.g. bm01000001) in the footer.

Hard rules (enforced, not advisory):
  - an UNVERIFIED source cannot be enabled as an authoritative source (goes to manual_review);
  - search engines and media are DISCOVERY-ONLY: they never receive A0, no matter the domain -- the
    document must resolve back to an official original (that resolution is T038).

Levels: A0 (central national official), A1/A2 (official but not central), media / search / aggregator
(discovery only), unofficial. No network in the verifier itself; a caller may pass fetched HTML so the
host-org / ID-code / ICP evidence can be extracted from the real footer. Deterministic.
"""
from __future__ import annotations
import re

# central national government hosts (A0-eligible). Extend as adapters land (T034+).
CENTRAL_GOV_HOSTS = {
    "www.gov.cn", "gov.cn", "www.stats.gov.cn", "stats.gov.cn", "www.ndrc.gov.cn", "ndrc.gov.cn",
    "www.cac.gov.cn", "cac.gov.cn", "www.nda.gov.cn", "nda.gov.cn", "www.npc.gov.cn", "npc.gov.cn",
    "www.court.gov.cn", "www.spp.gov.cn", "www.miit.gov.cn", "www.pbc.gov.cn", "www.mof.gov.cn",
}
DISCOVERY_ONLY = {"media", "search", "aggregator"}

HOST_ORG_RE = re.compile(r"主办[单位]*[:：]?\s*([一-龥A-Za-z（）()·]{2,40})")
ID_CODE_RE = re.compile(r"网站标识码[:：]?\s*([A-Za-z0-9]{6,20})")
ICP_RE = re.compile(r"((?:京|沪|粤|浙|苏|津|渝)?ICP备[0-9]{4,}号(?:-\d+)?)")


def _host(url_or_host: str) -> str:
    h = url_or_host.strip().lower()
    h = re.sub(r"^https?://", "", h).split("/")[0].split("?")[0]
    return h


def is_official_domain(url_or_host: str) -> bool:
    h = _host(url_or_host)
    return h in CENTRAL_GOV_HOSTS or h.endswith(".gov.cn")


def is_central_domain(url_or_host: str) -> bool:
    return _host(url_or_host) in CENTRAL_GOV_HOSTS


def extract_evidence(html: str) -> dict:
    html = html or ""
    org = HOST_ORG_RE.search(html)
    code = ID_CODE_RE.search(html)
    icp = ICP_RE.search(html)
    return {"host_org": org.group(1).strip() if org else None,
            "id_code": code.group(1).strip() if code else None,
            "icp": icp.group(1).strip() if icp else None}


def verify_identity(source: dict, html: str = None) -> dict:
    """source: {source_id, url|host, category, host_org?, id_code?, gov_directory_listed?}.
    Optional html supplies footer evidence (host_org / id_code / icp)."""
    sid = source.get("source_id", "?")
    category = (source.get("category") or "").lower()
    host = source.get("url") or source.get("host") or ""
    ev = {"official_domain": is_official_domain(host), "central_domain": is_central_domain(host),
          "host_org": source.get("host_org"), "id_code": source.get("id_code"),
          "gov_directory_listed": bool(source.get("gov_directory_listed")), "icp": None}
    if html:
        for k, v in extract_evidence(html).items():
            ev[k] = ev.get(k) or v

    reasons = []
    # RULE: search / media / aggregator are discovery-only -- never A0.
    if category in DISCOVERY_ONLY:
        reasons.append(f"category '{category}' is discovery-only; never A0 even on a gov domain")
        return {"source_id": sid, "authority_level": category, "verified": False,
                "can_enable": False, "discovery_only": True, "manual_review": False,
                "evidence": ev, "reasons": reasons}

    # official category path: needs an official domain + at least one strong official marker.
    strong_markers = sum(bool(ev[k]) for k in ("host_org", "id_code", "gov_directory_listed"))
    if not ev["official_domain"]:
        reasons.append("claims official but not on a .gov.cn domain -> unofficial, not enabled")
        return {"source_id": sid, "authority_level": "unofficial", "verified": False,
                "can_enable": False, "discovery_only": False, "manual_review": False,
                "evidence": ev, "reasons": reasons}
    if strong_markers == 0:
        reasons.append("official domain but no host_org / id_code / directory evidence -> manual_review, not enabled")
        return {"source_id": sid, "authority_level": "pending", "verified": False,
                "can_enable": False, "discovery_only": False, "manual_review": True,
                "evidence": ev, "reasons": reasons}

    level = "A0" if ev["central_domain"] else "A1"
    reasons.append(f"official .gov.cn domain + {strong_markers} official marker(s) "
                   f"({'central' if ev['central_domain'] else 'non-central'}) -> {level}")
    return {"source_id": sid, "authority_level": level, "verified": True,
            "can_enable": True, "discovery_only": False, "manual_review": False,
            "evidence": ev, "reasons": reasons}


def main():
    import argparse, json, pathlib
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True, help="JSON list of source specs")
    ap.add_argument("--out")
    args = ap.parse_args()
    sources = json.loads(pathlib.Path(args.sources).read_text(encoding="utf-8"))
    results = [verify_identity(s) for s in sources]
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{"source_id": r["source_id"], "authority_level": r["authority_level"],
                       "can_enable": r["can_enable"], "discovery_only": r["discovery_only"],
                       "manual_review": r["manual_review"]} for r in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
