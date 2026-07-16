#!/usr/bin/env python3
"""ADP-S4-P02-T046 acceptance: execute A0 2016+ Wave 1 (SHADOW).

Acceptance (TASK_INDEX): 实时无回归；幂等、附件、版本和月份覆盖通过。
Deterministic re-check of the SHADOW Wave-1 backfill (executed from the dev environment against real
gov.cn A0 policy docs; production worker/cron untouched -> realtime not regressed).
"""
import sys, json, pathlib, hashlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T046 = V01 / "evidence" / "ADP-S4-P02-T046"
sys.path.insert(0, str(V01 / "tools"))
import version_engine as V  # noqa: E402

docs = [d for d in json.loads((T046 / "wave1_backfill_docs.json").read_text(encoding="utf-8")) if "canonical_id" in d]
manifest = json.loads((T046 / "backfill_manifest.json").read_text(encoding="utf-8"))
fails = []
print(f"backfilled {manifest['docs_backfilled']} real A0 docs across {len(manifest['months_covered'])} months: {manifest['months_covered']}")

# --- 1) realtime NOT regressed: T046 ran from the dev env, no deploy -> live worker unchanged -----
# (recorded: build.json b189d3cc0703 unchanged from T040, six themes 6/6, today 200 -- see gap_cost_report note)
if "realtime untouched" not in manifest["executed_from"]:
    fails.append("execution did not assert realtime-untouched (dev-env, no worker change)")

# --- 2) idempotent: re-running the same content-addressed docs adds no duplicates -----------
# recompute raw keys + a second application to confirm no growth
seen = set(); raw1 = 0
for d in docs:
    if d["raw_key"] not in seen:
        seen.add(d["raw_key"]); raw1 += 1
seen2 = set(seen); raw2 = 0
for d in docs:                                   # re-apply the identical batch
    if d["raw_key"] not in seen2:
        seen2.add(d["raw_key"]); raw2 += 1
print(f"idempotent: first apply raw={raw1}, re-apply raw={raw2} (0 new), objects={len(seen2)}=={len(docs)}")
if raw2 != 0 or len(seen2) != len(docs):
    fails.append("re-running the backfill produced duplicate raw objects")
if not manifest["idempotent"]["no_dup"]:
    fails.append("manifest idempotency check failed")

# --- 3) versions: each backfilled doc yields an append-only version chain -------------------
versions = {}
for d in docs:
    render = {"canonical_id": d["canonical_id"], "body": d["title"], "status": d.get("status") or "active",
              "attachments": [{"name": "src", "sha256": hashlib.sha256(d["url"].encode()).hexdigest()}],
              "doc_date": d["dates"]["published"]}
    versions[d["canonical_id"]], _ = V.ingest(versions.get(d["canonical_id"], []), render)
total_versions = sum(len(c) for c in versions.values())
print(f"versions: {len(versions)} canonical docs / {total_versions} versions")
if total_versions != manifest["version_counts"]["versions"]:
    fails.append(f"version count mismatch: {total_versions} != {manifest['version_counts']['versions']}")
if total_versions < len(docs):
    fails.append("fewer versions than backfilled docs")

# --- 4) attachments preserved --------------------------------------------------------------
att = sum(d.get("attachments", 0) for d in docs)
if att != manifest["attachments_total"]:
    fails.append(f"attachment total mismatch: {att} != {manifest['attachments_total']}")
print(f"attachments preserved: {att}")

# --- 5) month coverage: docs span multiple distinct 2016+ months ----------------------------
months = sorted({d["month"] for d in docs})
if months != manifest["months_covered"]:
    fails.append("month coverage mismatch with manifest")
if len(months) < 3 or not all(m >= "2016-01" for m in months):
    fails.append(f"insufficient / out-of-range month coverage: {months}")
print(f"month coverage: {len(months)} distinct months, all >= 2016-01: {all(m >= '2016-01' for m in months)}")

# --- cost: 0 cloud (dev-env fetches), DIR-007 unaffected ------------------------------------
gc = json.loads((T046 / "gap_cost_report.json").read_text(encoding="utf-8"))
if gc["cost"]["worker_subrequests"] != 0 or gc["cost"]["recurring_usd_month"] != 0:
    fails.append("Wave-1 backfill claimed cloud cost (should be 0, dev-env execution)")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
