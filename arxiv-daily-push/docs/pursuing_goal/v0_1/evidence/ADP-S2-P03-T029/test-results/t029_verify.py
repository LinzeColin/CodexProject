#!/usr/bin/env python3
"""ADP-S2-P03-T029 acceptance: backup-restore + data-lifecycle drill.

Acceptance (TASK_INDEX): 证明 2016/2020/当前月可恢复；随机正文、附件、关系、计数一致；
原始官方证据和发布版本不得删除。
Self-contained from committed evidence: T027 logical_snapshot + this task's raw_evidence_sample.
Deterministic; restores into an isolated in-memory SQLite (T025 schema); production untouched.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
LOGICAL = V01 / "evidence" / "ADP-S2-P03-T027" / "logical_snapshot"
RAW = V01 / "evidence" / "ADP-S2-P03-T029" / "raw_evidence_sample.json"
sys.path.insert(0, str(V01 / "tools"))
import restore_drill as R   # noqa: E402

MONTHS = ["2016-01", "2020-07", "2026-07"]
fails = []
rep = R.drill(str(LOGICAL), str(RAW), MONTHS)

print("isolation:", rep["isolation"])
for m in MONTHS:
    pm = rep["per_month"][m]
    print(f"restored {m}: month_documents={pm['month_documents']} versions={pm['versions']} "
          f"docs_with_closure={pm['documents_restored_with_closure']} result_hash={pm['result_hash'][:22]}")

# 1) 2016 / 2020 / current all recoverable (each restored with >0 versions)
for m in MONTHS:
    if rep["per_month"][m]["versions"] < 1:
        fails.append(f"{m} not recoverable (0 versions restored)")

# 2) counts consistent with the snapshot ground truth
if not rep["counts_consistent"]:
    fails.append("restored counts != snapshot ground truth")
    print("  counts detail:", {m: (rep['per_month'][m], rep['ground_truth'][m]) for m in MONTHS})

# 3) relationship consistent (no orphan versions)
if rep["orphan_versions"] != 0:
    fails.append(f"{rep['orphan_versions']} orphan versions after restore (relationship broken)")

# 4) random body + attachment consistent
if not rep["random_body_consistent"]:
    fails.append("random body not consistent (recomputed content_hash != restored)")
if not rep["random_attachment_consistent"]:
    fails.append("random attachment not consistent (raw artifact key not in restored version)")
print(f"random checks: body {rep['body_samples']} samples consistent={rep['random_body_consistent']} | "
      f"attachment {rep['attachment_samples']} samples consistent={rep['random_attachment_consistent']}")

# 5) original official evidence + published versions NOT deleted
perm_classes = [r for r in rep["retention_matrix"] if r["retention"] == "PERMANENT"]
raw_perm = any("raw official artifact" in r["data_class"] and r["delete_policy"] == "never" for r in perm_classes)
ver_perm = any("published DocumentVersion" in r["data_class"] and r["delete_policy"] == "never" for r in perm_classes)
if not (raw_perm and ver_perm):
    fails.append("retention matrix does not mark raw official evidence AND published versions as PERMANENT/never")
if not rep["permanent_stores_unchanged"]:
    fails.append("permanent stores changed during the drill (must be read-only)")
if rep["permanent_delete_count"] != 0:
    fails.append(f"drill deleted {rep['permanent_delete_count']} permanent records (must be 0)")
print("retention: raw+versions PERMANENT/never =", raw_perm and ver_perm,
      "| permanent stores unchanged =", rep["permanent_stores_unchanged"],
      "| permanent deletes =", rep["permanent_delete_count"])

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
