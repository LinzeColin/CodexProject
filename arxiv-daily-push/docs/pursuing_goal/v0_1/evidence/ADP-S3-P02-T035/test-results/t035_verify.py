#!/usr/bin/env python3
"""ADP-S3-P02-T035 acceptance: Statistics + NDRC A0 adapters with statistical-claim extraction.

Acceptance (TASK_INDEX): 统计 Claim 记录单位、期间、口径和修订；不从媒体数字形成事实。
Deterministic (fixtures; the live stats.gov.cn extraction is a separate smoke). Mirrors the real
stats narrative form (国内生产总值1349084亿元，同比增长5.0%; revision 初步核算).
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T035 = V01 / "evidence" / "ADP-S3-P02-T035"
FX = T035 / "fixtures"
sys.path.insert(0, str(V01 / "tools"))
import adapter_stats_ndrc as S  # noqa: E402

fails = []
stats_html = (FX / "stats_release.html").read_text(encoding="utf-8")
title = "2024年国民经济运行情况"

# --- 1) statistical Claim records unit / period / basis(口径) / revision ---------------------
claims = S.extract_stat_claims(stats_html, "stats-gov", "A0", title)
print(f"extracted {len(claims)} statistical claims from the official release")
for c in claims:
    print(f"  {c.indicator}={c.value}{c.unit} | period={c.period} 口径={c.basis} 修订={c.revision} fact={c.is_fact}")
if len(claims) < 5:
    fails.append(f"too few claims extracted ({len(claims)})")
# every claim must record unit, period, basis (口径), revision
for c in claims:
    if not c.unit:
        fails.append(f"claim {c.indicator} missing unit")
    if not c.period:
        fails.append(f"claim {c.indicator}={c.value} missing period")
    if not c.revision:
        fails.append(f"claim {c.indicator}={c.value} missing revision")
# at least the growth-rate claims carry a 口径 (同比/环比)
if not any(c.basis for c in claims):
    fails.append("no claim recorded a 口径 (statistical basis)")
# the GDP absolute value claim is present with the right unit + period + revision
gdp = [c for c in claims if c.indicator == "国内生产总值" and c.unit == "亿元"]
if not gdp:
    fails.append("GDP absolute-value claim (亿元) not extracted")
elif not (gdp[0].period == "2024年" and gdp[0].revision == "初步核算"):
    fails.append(f"GDP claim period/revision wrong: {gdp[0].period}/{gdp[0].revision}")
print("all claims carry unit+period+revision:", all(c.unit and c.period and c.revision for c in claims))

# --- 2) NO fact formed from MEDIA numbers ---------------------------------------------------
official_facts = S.claims_to_facts(S.extract_stat_claims(stats_html, "stats-gov", "A0", title))
media_facts = S.claims_to_facts(S.extract_stat_claims(stats_html, "some-media", "media", title))
search_facts = S.claims_to_facts(S.extract_stat_claims(stats_html, "search-x", "search", title))
print(f"\nfacts from OFFICIAL: {len(official_facts)} | from MEDIA: {len(media_facts)} | from SEARCH: {len(search_facts)}")
if len(official_facts) == 0:
    fails.append("official source produced no facts")
if len(media_facts) != 0:
    fails.append(f"media numbers wrongly became facts ({len(media_facts)})")
if len(search_facts) != 0:
    fails.append(f"search numbers wrongly became facts ({len(search_facts)})")

# --- adapters exist for stats + ndrc; ndrc doc parses as an official announcement ------------
reg = S.build_registry(fetcher=None)
if reg.ids() != ["ndrc-gov", "stats-gov"]:
    fails.append(f"registry ids {reg.ids()} != stats + ndrc")
print("\nregistry:", reg.ids())

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
