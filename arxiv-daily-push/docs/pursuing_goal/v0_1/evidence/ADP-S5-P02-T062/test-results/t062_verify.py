#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T062 acceptance: version timeline / as-of / old-vs-new diff API.

Acceptance (TASK_INDEX row 62): 增删改可定位；模板噪声不显示；旧版可回放。
  (additions/deletions/modifications locatable; template noise not shown; old versions replayable.)

Deterministic. Re-derives everything from the TOOL (version_asof_api) + the generator fixtures --
never trusts version_asof_report.json. Includes negative controls that PROVE discrimination:
  * a noise-only re-render must yield an EMPTY diff and NOT add a version -- and a raw (un-stripped)
    diff of the same pair MUST surface the noise, proving the stripping is load-bearing;
  * an as-of query must NEVER resolve to a future version -- proven over a >=100-sample battery
    against an independent oracle, AND a deliberately-future resolver must be caught by that battery.
"""
import difflib
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import version_asof_api as API
import coverage_asof as CA

T062 = V01 / "evidence" / "ADP-S5-P02-T062"
spec = importlib.util.spec_from_file_location("bva", str(T062 / "build_version_asof.py"))
bva = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bva)

fails = []

# =============================================================== 1) 增删改可定位 (locatable adds/deletes/modifies)
tl = API.version_timeline([bva.R_V1, bva.R_V2])
if len(tl) != 2:
    fails.append(f"substantive timeline should have 2 versions, got {len(tl)}")

dp = API.diff_payload(bva.R_V1, bva.R_V2)
print("diff counts:", dp["counts"], "changed:", dp["changed"])
if dp["counts"] != {"add": 1, "delete": 1, "modify": 1}:
    fails.append(f"expected exactly 1 add + 1 delete + 1 modify, got {dp['counts']}")
if not dp["changed"]:
    fails.append("substantive change reported as unchanged")

# every change must be LOCATABLE: carry a concrete line number and the exact text
adds = [c for c in dp["line_changes"] if c["op"] == "add"]
dels = [c for c in dp["line_changes"] if c["op"] == "delete"]
mods = [c for c in dp["line_changes"] if c["op"] == "modify"]
if not (adds and adds[0]["new_line"] and "第四条" in (adds[0]["new_text"] or "")):
    fails.append(f"add not locatable to the new article: {adds}")
if not (dels and dels[0]["old_line"] and "第二条" in (dels[0]["old_text"] or "")):
    fails.append(f"delete not locatable to the removed article: {dels}")
if not (mods and mods[0]["old_line"] and mods[0]["new_line"]
        and "健全" not in (mods[0]["old_text"] or "") and "健全" in (mods[0]["new_text"] or "")):
    fails.append(f"modify not locatable to the amended article (old->new): {mods}")

# =============================================================== 2) 模板噪声不显示 (template noise never shown)
dp_noise = API.diff_payload(bva.R_V1, bva.R_V1_NOISE)
if dp_noise["changed"] or not dp_noise["noise_only"]:
    fails.append("a noise-only re-render was reported as a substantive change")
if dp_noise["line_changes"]:
    fails.append(f"noise-only diff surfaced line changes: {dp_noise['line_changes']}")

# no noise string may appear anywhere in the substantive diff or the replayed body
def _all_text(dp_obj):
    out = []
    for c in dp_obj["line_changes"]:
        out += [c.get("old_text") or "", c.get("new_text") or ""]
    return "\n".join(out)
diff_text = _all_text(dp)
for nz in bva.NOISE_LINES:
    core = nz.split()[0]
    if core in diff_text:
        fails.append(f"template noise leaked into the substantive diff: {nz!r}")

# real content must NOT be stripped (the tool suppresses chrome, not substance)
replay1 = API.replay_version(tl, 1)
if "第一条" not in replay1["body"] or "第三条" not in replay1["body"]:
    fails.append("real article text was stripped from the replayed body")
for nz in bva.NOISE_LINES:
    if nz.split()[0] in replay1["body"]:
        fails.append(f"template noise leaked into the replayed body: {nz!r}")

# NEGATIVE CONTROL: the stripping is load-bearing. A RAW (un-stripped) diff of the SAME pair MUST
# surface the noise -- if it didn't, the noise-only pass above would be vacuous.
raw_old = bva.R_V1["body"].split("\n")
raw_new = bva.R_V1_NOISE["body"].split("\n")
raw_added = [raw_new[j] for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=raw_old, b=raw_new, autojunk=False).get_opcodes()
             if tag in ("insert", "replace") for j in range(j1, j2)]
if not any(nz in raw_added for nz in bva.NOISE_LINES):
    fails.append("raw diff did not surface the noise -> the noise-suppression test is vacuous")
print(f"raw diff surfaces {len(raw_added)} noise lines; stripped diff surfaces 0 (discrimination OK)")

# NEGATIVE CONTROL: noise-only re-render must NOT create a new version in the timeline
tl_noise = API.version_timeline([bva.R_V1, bva.R_V1_NOISE])
if len(tl_noise) != 1:
    fails.append(f"noise-only re-render created a spurious version: timeline={len(tl_noise)}")

# ---- 2b) NOISE-CLASS BOUNDARY: verify the DISCLOSED behavior (not merely assert it) ----------
# T026's canonical noise contract has two families with DIFFERENT guards; this read layer inherits
# them verbatim (single source of truth -- not forked here). We verify each honestly:
#   (i)  the 发布于-family is content-GUARDED (leading-digit requirement), so a genuine sentence
#        beginning 发布于 is preserved as real content -- it MUST surface in the diff/replay;
#   (ii) 来源/责任编辑/编辑/审核/校对 are editorial-credit / reprint-attribution chrome, stripped
#        WHOLE-LINE by design, so a change confined solely to such a line is, by T026's definition,
#        NOT a substantive change and is correctly NOT surfaced (showing it would violate 模板噪声不显示).
# (i) a 发布于-with-content line is real content -> shows up as an add
pub_content = {"canonical_id": bva.CID, "body": bva.V1_BODY + "\n发布于顶级期刊：Nature 发表了新的政策评估。",
               "status": "published", "observed_at": "2026-05-01"}
dp_pub = API.diff_payload(bva.R_V1, pub_content)
if not dp_pub["changed"]:
    fails.append("a genuine 发布于-content line was wrongly stripped as noise (guard failed)")
if not any("发布于顶级期刊" in (c.get("new_text") or "") for c in dp_pub["line_changes"]):
    fails.append("the 发布于-content line did not surface in the diff (guard failed)")
if "发布于顶级期刊" not in API.replay_version(API.version_timeline([bva.R_V1, pub_content]), 2)["body"]:
    fails.append("the 发布于-content line did not survive into the replayed body (guard failed)")
# (ii) a change confined to a 来源 attribution line is T026-noise -> no substantive change, no version
attr_v1 = {"canonical_id": bva.CID, "body": bva.V1_BODY + "\n来源：甲省数据局", "status": "published", "observed_at": "2026-03-01"}
attr_v2 = {"canonical_id": bva.CID, "body": bva.V1_BODY + "\n来源：乙省数据局", "status": "published", "observed_at": "2026-06-01"}
dp_attr = API.diff_payload(attr_v1, attr_v2)
if dp_attr["changed"]:
    fails.append("a 来源 attribution-only change was surfaced -> violates 模板噪声不显示 (T026 classes it as chrome)")
if len(API.version_timeline([attr_v1, attr_v2])) != 1:
    fails.append("a 来源 attribution-only change created a spurious version")
print("noise-class boundary: 发布于-content preserved; 来源/责任编辑 attribution treated as chrome (per T026)")

# =============================================================== 3) 旧版可回放 (old versions replayable)
# exact reconstruction of the old body
import version_engine as VE
if replay1["body"] != VE.strip_noise(bva.R_V1["body"]):
    fails.append("replayed v1 body does not equal the noise-stripped original v1 body")
replay2 = API.replay_version(tl, 2)
if replay2["body"] != VE.strip_noise(bva.R_V2["body"]):
    fails.append("replayed v2 body does not equal the noise-stripped original v2 body")
# idempotent replay (3x identical)
idem = API.replay_is_idempotent(tl, 1, times=3)
if not idem["identical"]:
    fails.append("replay of an old version is not idempotent across 3 runs")

# as-of never returns a FUTURE version
if API.as_of(tl, "2026-02-01") is not None:
    fails.append("as-of before the first version should be None")
av = API.as_of(tl, "2026-04-15")
if not av or av["version_no"] != 1:
    fails.append(f"as-of 2026-04-15 should resolve to v1 (v2 is future), got {av and av['version_no']}")
av2 = API.as_of(tl, "2026-07-01")
if not av2 or av2["version_no"] != 2:
    fails.append(f"as-of 2026-07-01 should resolve to v2, got {av2 and av2['version_no']}")

# as-of NO-FUTURE-LEAKAGE battery (>=100 samples) vs an independent oracle
corpus = bva.build_asof_corpus()
query_dates = [f"2026-{mm:02d}-{dd}" for mm in range(1, 13) for dd in ("01", "15", "28")]
samples, leaks, disagree = 0, 0, 0
for cid, renders in corpus.items():
    timeline = API.version_timeline(sorted(renders, key=lambda r: r["observed_at"]))
    for qd in query_dates:
        samples += 1
        hit = API.as_of(timeline, qd)
        # oracle: greatest observed_at <= qd by parsed date
        elig = sorted((v for v in timeline if CA._parse_date(v["observed_at"]) <= CA._parse_date(qd)),
                      key=lambda v: CA._parse_date(v["observed_at"]))
        oracle = elig[-1] if elig else None
        if hit is not None and CA._parse_date(hit["observed_at"]) > CA._parse_date(qd):
            leaks += 1
        if (hit or {}).get("version_no") != (oracle or {}).get("version_no"):
            disagree += 1
print(f"as-of battery: samples={samples} future_leakage={leaks} oracle_disagreements={disagree}")
if samples < 100:
    fails.append(f"as-of battery too small: {samples} < 100")
if leaks != 0:
    fails.append(f"as-of returned a FUTURE version {leaks} times")
if disagree != 0:
    fails.append(f"as-of disagreed with the independent oracle {disagree} times")

# NEGATIVE CONTROL: the battery must be able to CATCH a leaky resolver. A deliberately-future
# resolver (returns the LAST version regardless of date) must trip the leak check.
def _leaky_as_of(timeline, qd):
    return timeline[-1] if timeline else None
caught = 0
for cid, renders in corpus.items():
    timeline = API.version_timeline(sorted(renders, key=lambda r: r["observed_at"]))
    for qd in query_dates:
        hit = _leaky_as_of(timeline, qd)
        if hit is not None and CA._parse_date(hit["observed_at"]) > CA._parse_date(qd):
            caught += 1
if caught == 0:
    fails.append("leak battery failed to catch a deliberately-future resolver -> battery is vacuous")
print(f"leak battery catches a future resolver on {caught} samples (discrimination OK)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
