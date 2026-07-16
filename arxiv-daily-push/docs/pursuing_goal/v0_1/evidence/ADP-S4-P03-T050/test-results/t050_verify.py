#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T050 acceptance: batched provincial (A1) backfill.

Acceptance (TASK_INDEX): 每批通过后才进入下一批；失败省隔离不阻塞全局。
Checks the cached live run (coverage_report.json + province_backfill_docs.json), and adds a
DETERMINISTIC negative control proving the batch gate genuinely blocks progression: if a batch fails
its gate, the run halts and the next batch never runs.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import adapter_a1_province as A
import province_backfill as PB

T050 = V01 / "evidence" / "ADP-S4-P03-T050"
fails = []

cov = json.loads((T050 / "coverage_report.json").read_text(encoding="utf-8"))
docs = json.loads((T050 / "province_backfill_docs.json").read_text(encoding="utf-8"))
rs = cov["run_summary"]
gates = cov["gates"]
isolated = cov["isolated_failures"]
print(f"completed_batches={rs['completed_batches']} halted_at={rs['halted_at']} total_docs={rs['total_docs']} "
      f"idempotent={rs['idempotent_rerun_no_new']}")
for g in gates:
    print(f"  batch {g['batch']} {g['source_ids']} provinces_ok={g['provinces_ok']} gate={g['gate_passed']}")
print(f"isolated_failures={isolated}")

# --- 1) each batch passed before the next (>=2 batches ran, all in order gate_passed, no halt) ----
if rs["completed_batches"] < 2:
    fails.append(f"fewer than 2 batches completed ({rs['completed_batches']})")
if rs["halted_at"] is not None:
    fails.append(f"run halted at batch {rs['halted_at']} (a batch gate failed)")
for i, g in enumerate(gates):
    if g["batch"] != i:
        fails.append(f"batch order broken at index {i}")
    if not g["gate_passed"]:
        fails.append(f"batch {g['batch']} did not pass its gate but the run continued")

# --- 2) failed province ISOLATED (recorded, did NOT block its batch) ------------------------------
iso_ids = {x["source_id"] for x in isolated}
if "guangdong-gov" not in iso_ids:
    fails.append("the blocked province (guangdong-gov) was not isolated/recorded")
# the batch that contained the isolated province must still have passed (isolation != blocking)
b0 = next((g for g in gates if "guangdong-gov" in g["source_ids"]), None)
if not b0 or not b0["gate_passed"]:
    fails.append("the batch containing the isolated province did not pass -> isolation blocked the batch")

# --- 3) real A1 docs backfilled with content-addressed ids, months, and CORRECT (non-render) dates -
if len(docs) < 6:
    fails.append(f"too few province docs backfilled ({len(docs)})")
bad = [d for d in docs if not (d["canonical_id"] and d["authority_level"] == "A1" and d["month"])]
if bad:
    fails.append(f"{len(bad)} docs missing canonical_id / A1 / month")
# dates must be the document dates fixed in T049 (not the <meta Maketime> render timestamp)
EXPECT = {"jiangsu-gov": "2026-07-14", "shandong-gov": "2026-07-09", "beijing-gov": "2026-07-14"}
for sid, exp in EXPECT.items():
    ds = [d["doc_date"] for d in docs if d["source_id"] == sid]
    if exp not in ds:
        fails.append(f"{sid}: expected a doc dated {exp} (real publish date), got {sorted(set(ds))}")
if not rs["idempotent_rerun_no_new"]:
    fails.append("re-running the backfill produced new canonical ids (not idempotent)")

# --- 4) NEGATIVE CONTROL: a failed batch must HALT the run (deterministic, offline) ---------------
empty = A.FixtureFetcher({})              # every fetch -> empty -> 0 docs -> batch gate fails
nb = PB.plan_batches([{"batch": 0, "source_id": "jiangsu-gov", "profile": A.PROFILES["jiangsu-gov"]},
                      {"batch": 1, "source_id": "beijing-gov", "profile": A.PROFILES["beijing-gov"]}])
neg = PB.orchestrate(nb, lambda m: A.A1ProvinceConnector(m["profile"], empty))
control_halts = (neg["halted_at"] == 0 and len(neg["batches"]) == 1 and neg["completed_batches"] == 0)
print(f"negative control (failed batch 0): halted_at={neg['halted_at']} batches_run={len(neg['batches'])} "
      f"-> gate genuinely blocks progression = {control_halts}")
if not control_halts:
    fails.append("batch gate is not enforced: a failed batch 0 did not halt the run before batch 1")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
