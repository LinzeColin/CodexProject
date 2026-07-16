#!/usr/bin/env python3
"""ADP-S3-P01-T033 acceptance: official identity verification + A0 marking.

Acceptance (TASK_INDEX): 未验证 source 不能 enabled；搜索/媒体只能作为 discovery，不得获得 A0。
Deterministic; no network (the live gov.cn extraction is a separate smoke). Uses fixture footers.
"""
import sys, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import official_identity as OI  # noqa: E402

OFFICIAL_FOOTER = "主办单位：国务院办公厅 网站标识码bm01000001 京ICP备05070218号"
BARE_GOV_FOOTER = "版权所有 中国某地方站"  # gov domain but no host_org/id_code/directory

CASES = [
    # (name, source, html, expect_level, expect_can_enable, expect_discovery_only, expect_manual_review)
    ("central official + markers", {"source_id": "gov-cn", "url": "https://www.gov.cn/zhengce/", "category": "china_official"}, OFFICIAL_FOOTER, "A0", True, False, False),
    ("central official id_code only", {"source_id": "stats", "url": "https://www.stats.gov.cn/", "category": "china_official", "id_code": "bm36000002"}, None, "A0", True, False, False),
    ("non-central official + marker", {"source_id": "prov", "url": "https://www.hubei.gov.cn/", "category": "china_official", "host_org": "湖北省政府"}, None, "A1", True, False, False),
    ("media on gov domain -> discovery only, NO A0", {"source_id": "gov-media", "url": "https://www.gov.cn/", "category": "media"}, OFFICIAL_FOOTER, "media", False, True, False),
    ("search -> discovery only, NO A0", {"source_id": "baidu-news", "url": "https://news.baidu.com/", "category": "search"}, None, "search", False, True, False),
    ("aggregator -> discovery only, NO A0", {"source_id": "rsshub", "url": "https://rsshub.app/", "category": "aggregator"}, None, "aggregator", False, True, False),
    ("official domain, no markers -> manual_review, not enabled", {"source_id": "bare-gov", "url": "https://x.gov.cn/", "category": "china_official"}, BARE_GOV_FOOTER, "pending", False, False, True),
    ("claims official but not gov domain -> unofficial, not enabled", {"source_id": "fake", "url": "https://gov-cn.example.com/", "category": "china_official"}, OFFICIAL_FOOTER, "unofficial", False, False, False),
]

fails = []
for name, src, html, exp_level, exp_enable, exp_disc, exp_manual in CASES:
    r = OI.verify_identity(src, html=html)
    ok = (r["authority_level"] == exp_level and r["can_enable"] == exp_enable
          and r["discovery_only"] == exp_disc and r["manual_review"] == exp_manual)
    print(f"{'OK ' if ok else 'XX '}{name}: level={r['authority_level']} enable={r['can_enable']} "
          f"discovery_only={r['discovery_only']} manual_review={r['manual_review']}")
    if not ok:
        fails.append(f"{name}: got level={r['authority_level']} enable={r['can_enable']} disc={r['discovery_only']} manual={r['manual_review']}")

# --- the two hard rules, stated explicitly -------------------------------------------------
# RULE 1: unverified (manual_review OR unofficial OR pending) cannot be enabled
unverified = [OI.verify_identity(s, html=h) for (_n, s, h, *_r) in CASES if _r[0] in ("pending", "unofficial")]
if any(u["can_enable"] for u in unverified):
    fails.append("an unverified source was enabled (RULE 1 broken)")
# RULE 2: no search/media/aggregator ever gets A0
for _n, s, h, *_r in CASES:
    if (s.get("category") or "") in OI.DISCOVERY_ONLY:
        rr = OI.verify_identity(s, html=h)
        if rr["authority_level"] == "A0" or rr["can_enable"]:
            fails.append(f"{s['source_id']}: discovery-only category got A0/enabled (RULE 2 broken)")

print("\nRULE 1 (unverified not enabled): OK" if not any(f.startswith("an unverified") for f in fails) else "\nRULE 1 BROKEN")
print("RULE 2 (search/media never A0): OK" if not any("RULE 2" in f for f in fails) else "RULE 2 BROKEN")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
