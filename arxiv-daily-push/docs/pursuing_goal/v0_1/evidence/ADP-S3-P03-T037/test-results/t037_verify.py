#!/usr/bin/env python3
"""ADP-S3-P03-T037 acceptance: Board 3 eligibility gate + date/status extractors.

Acceptance (TASK_INDEX): 政策视图抽样 200 条污染率 <1%；关键日期准确率 >=99%。
Deterministic. The 200-sample is 85 REAL board3 media items (news noise) + 115 synthetic official
policy docs with known 成文/发布/施行/失效 dates. The gate must exclude the news noise before ranking.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T037 = V01 / "evidence" / "ADP-S3-P03-T037"
sys.path.insert(0, str(V01 / "tools"))
import board3_gate as G  # noqa: E402

sample = json.loads((T037 / "board3_policy_sample_200.json").read_text(encoding="utf-8"))
fails = []
print(f"policy-view sample: {len(sample)} = media/news {sum(1 for s in sample if s['label']=='news')} + official {sum(1 for s in sample if s['label']=='official')}")

res = G.gate_board3(sample)
admitted = res["admitted"]
print(f"gate: in {res['counts']['in']} | admitted {res['counts']['admitted']} | rejected {res['counts']['rejected']}")

# --- 1) pollution rate of the ADMITTED policy view < 1% ------------------------------------
polluted = [a for a in admitted if a["label"] == "news"]
pollution_rate = len(polluted) / max(1, len(admitted))
print(f"pollution in admitted view: {len(polluted)}/{len(admitted)} = {pollution_rate*100:.3f}%  (required < 1%)")
if pollution_rate >= 0.01:
    fails.append(f"pollution rate {pollution_rate*100:.3f}% >= 1%")
# every real board3 media item must be rejected (news noise excluded before ranking)
media_admitted = [a for a in admitted if a["category"] == "media"]
if media_admitted:
    fails.append(f"{len(media_admitted)} media items admitted (news noise not excluded)")

# --- 2) key date accuracy on admitted official docs >= 99% ---------------------------------
ok, tot, mism = 0, 0, []
for a in admitted:
    if a["label"] != "official":
        continue
    tot += 1
    pd = G.extract_dates_status(a["html"], a["title"])
    got = {"written": pd.written, "published": pd.published, "effective": pd.effective, "expired": pd.expired, "status": pd.status}
    exp = a["expected_dates"]
    if all(got[k] == exp[k] for k in ("written", "published", "effective", "expired", "status")):
        ok += 1
    else:
        mism.append((a["title"][:20], got, exp))
acc = ok / max(1, tot)
print(f"key date accuracy (成文/发布/施行/失效/状态) on admitted official: {ok}/{tot} = {acc*100:.3f}%  (required >= 99%)")
for t, g, e in mism[:3]:
    print("  mismatch:", t, g, "vs", e)
if acc < 0.99:
    fails.append(f"date accuracy {acc*100:.3f}% < 99%")

# --- extractor covers all four date types + status on a spot doc ---------------------------
spot = next(a for a in admitted if a["expected_dates"]["effective"] and a["label"] == "official")
pd = G.extract_dates_status(spot["html"], spot["title"])
print(f"\nspot doc dates: 成文={pd.written} 发布={pd.published} 施行={pd.effective} 失效={pd.expired} 状态={pd.status}")
if not (pd.written and pd.published and pd.effective and pd.status):
    fails.append("extractor did not populate all present date types + status on the spot doc")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
