#!/usr/bin/env python3
"""ADP-S3-P02-T034 acceptance: State Council policy / laws A0 adapter.

Acceptance (TASK_INDEX): 官方原文和附件可回放；日期类型不混淆；历史游标可恢复。
Deterministic (fixtures; no network -- the live gov.cn parse is a separate smoke). Fixtures span
2016 / 2020 / 2024 / current; the 2020 fixture mirrors the real gov.cn doc (国办发〔2020〕50号,
成文 2020-12-07 vs 发布 2020-12-21).
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T034 = V01 / "evidence" / "ADP-S3-P02-T034"
FX, EXP = T034 / "fixtures", T034 / "expected"
sys.path.insert(0, str(V01 / "tools"))
import adapter_gov_policy as A, official_connector as OC  # noqa: E402

conn = A.GovCnPolicyConnector(source_id="gov-cn-policy", listing="listing.html", fetcher=A.FixtureFetcher(FX))
ERAS = ["policy_2016.html", "policy_2020.html", "policy_2024.html", "policy_current.html"]
# the raw values authored into the fixtures, to prove dates are not swapped
FIXTURE_DATES = {
    "policy_2016.html": ("2016-03-08", "2016-03-20"),   # (成文 written, 发布 published)
    "policy_2020.html": ("2020-12-07", "2020-12-21"),
    "policy_2024.html": ("2024-02-18", "2024-03-01"),
    "policy_current.html": ("2026-06-30", "2026-07-10"),
}
fails = []

# --- 1) official original + attachments REPLAYABLE (parse == golden; deterministic re-parse) ----
for fx in ERAS:
    golden = json.loads((EXP / fx.replace(".html", ".json")).read_text(encoding="utf-8"))
    fr = conn.fetch(fx, "2026-07-17T00:00:00+10:00")
    p1 = conn.parse_policy(fr)
    p2 = conn.parse_policy(conn.fetch(fx, "later"))     # replay -> identical
    replay_ok = (p1 == p2 == golden)
    atts_ok = p1["attachments"] == golden["attachments"]
    print(f"{fx}: doc_number={p1['doc_number']} atts={len(p1['attachments'])} replay==golden={replay_ok}")
    if not replay_ok:
        fails.append(f"{fx}: parse not replayable/!=golden")
    if not atts_ok:
        fails.append(f"{fx}: attachments not replayable")

# --- 2) DATE TYPES NOT CONFUSED (written == 成文, published == 发布; never swapped) --------------
for fx in ERAS:
    p = conn.parse_policy(conn.fetch(fx, "x"))
    want_written, want_pub = FIXTURE_DATES[fx]
    ok = p["dates"]["written"] == want_written and p["dates"]["published"] == want_pub
    if p["dates"]["written"] == p["dates"]["published"]:
        fails.append(f"{fx}: written and published collapsed to the same value")
    if not ok:
        fails.append(f"{fx}: date types confused -> written={p['dates']['written']} published={p['dates']['published']} (want {want_written}/{want_pub})")
    # the canonical NormalizedDoc.doc_date must be the PUBLISHED date, not 成文
    nd = conn.normalize(OC.DiscoverItem(fx, "", None), conn.fetch(fx, "x"))
    if nd.doc_date != want_pub:
        fails.append(f"{fx}: NormalizedDoc.doc_date {nd.doc_date} is not the published date {want_pub}")
print("date types not confused (written=成文, published=发布, doc_date=published):", not any("date types" in f or "collapsed" in f or "doc_date" in f for f in fails))

# --- 3) HISTORICAL CURSOR RECOVERABLE (resume after a past date; advance to latest) -------------
all_items = conn.discover(OC.Cursor())
print("\ndiscover (no cursor):", len(all_items), "items ->", [i.hint_date for i in all_items])
resumed = conn.discover(OC.Cursor(last_date="2020-12-21"))
print("discover (cursor last_date=2020-12-21):", len(resumed), "items ->", [i.hint_date for i in resumed])
if len(all_items) != 4:
    fails.append(f"discover found {len(all_items)} items, expected 4 across eras")
if [i.hint_date for i in resumed] != ["2024-03-01", "2026-07-10"]:
    fails.append(f"cursor resume wrong: {[i.hint_date for i in resumed]} (expected only post-2020-12-21)")
adv = conn.cursor([conn.normalize(it, conn.fetch(it.url.split('/')[-1], 'x')) if False else OC.NormalizedDoc('s', it.url, '', None, it.hint_date, None, 'A0', '') for it in all_items])
if adv.last_date != "2026-07-10":
    fails.append(f"cursor did not advance to the latest date, got {adv.last_date}")
print("cursor advanced to latest:", adv.last_date)

# registry has both policy + fagui sources
reg = A.build_registry(A.FixtureFetcher(FX))
if reg.ids() != ["gov-cn-fagui", "gov-cn-policy"]:
    fails.append(f"registry ids {reg.ids()} != policy + fagui")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
