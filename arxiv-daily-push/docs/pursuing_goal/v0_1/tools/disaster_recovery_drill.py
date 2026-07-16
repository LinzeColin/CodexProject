#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P01-T086 -- production rollback & disaster-recovery drill.

For each of the SIX production components -- Worker, D1, R2, Source Registry, content bundle, prediction
-- this drill identifies the recover-to KNOWN POINT and the recovery MECHANISM, PERFORMS the recovery in
an ISOLATED throwaway sandbox (in-memory SQLite / tmp dir -- never touching production or issuing a live
rollback), measures RTO/RPO actuals + an evidence hash, and classifies any component that cannot be
recovered to a consistent known state as a RELEASE BLOCKER.

Recovery mechanisms (all recover to an OPEN, committed, or content-addressed point -- no vendor lock-in):
  - Worker:   BUILD self-hash reproduces the declared build_id => any committed worker version is
              identifiable + integrity-verifiable, so `wrangler versions deploy <build_id>` can roll back
              to a known point (live b189d3cc0703 == T040). Stateless code => RPO 0.
  - D1:       restore a month from the T027 open monthly snapshot into an isolated in-memory SQLite
              (T029 restore_drill). Published versions are append-only/permanent => permanent-record RPO 0.
  - R2:       raw artifacts are content-addressed + immutable (T021); identical bytes re-derive the
              identical object key => recoverable by content, RPO 0.
  - Registry: recompile source_registry.json => registry_hash reproduces d63cf6bd (git is the known point).
  - Content:  L0-L3 render bundle is deterministically regenerable from raw + code (T018) => RPO 0.
  - Predict:  baselines re-benchmark reproduces the committed report; the forecast ledger is append-only
              (T073) => RPO 0.

Deterministic for the recoverability/hash assertions (no clock/network/randomness there). RTO is a
measured wall-time actual (perf_counter) reported for information; it is NOT asserted for an exact value.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time

V01 = pathlib.Path(__file__).resolve().parent.parent
TOOLS = V01 / "tools"
EVID = V01 / "evidence"
sys.path.insert(0, str(TOOLS))
import full_chain_rehearsal as FCR   # noqa: E402  reuse committed anchors + LIVE_BUILD_T040
import restore_drill as RD           # noqa: E402  T029 D1 restore
import r2_artifact_key as RK         # noqa: E402  T021 content-addressed key

WORKER = V01.parent.parent.parent / "deploy" / "cloudflare" / "worker_cloud.js"
T027_LOGICAL = EVID / "ADP-S2-P03-T027" / "logical_snapshot"
RESTORE_MONTHS = ["2016-01", "2020-07", "2026-07"]
# Frozen COMMITTED known-good recovery points. Every component recovers to one of THESE committed values;
# a re-derivation that diverges (code or input drift) is NOT recoverable => release blocker. This is what
# makes recoverable falsifiable -- it is never a same-run self-comparison / determinism tautology.
KNOWN = json.loads((EVID / "ADP-S8-P01-T086" / "recovery_known_points.json").read_text("utf-8"))
COMMITTED_T029 = json.loads((EVID / "ADP-S2-P03-T029" / "restore_report.json").read_text("utf-8"))


def _sha16(o):
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def worker_self_build_id(src):
    """Recompute the BUILD self-hash: blank build_id (12 zeros) + source_sha256 (64 zeros), sha256 the
    whole file, build_id = hash[:12]. Reproducing the declared build_id proves the recover-to version is
    identifiable and integrity-verifiable."""
    reset = re.sub(r"build_id: '[0-9a-f]{12}'", "build_id: '" + "0" * 12 + "'", src, count=1)
    reset = re.sub(r"source_sha256: '[0-9a-f]{64}'", "source_sha256: '" + "0" * 64 + "'", reset, count=1)
    return hashlib.sha256(reset.encode("utf-8")).hexdigest()[:12]


def _timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, round(time.perf_counter() - t0, 4)


def drill_worker():
    src = WORKER.read_text("utf-8")
    declared = re.search(r"build_id: '([0-9a-f]{12})'", src).group(1)
    (recovered, rto) = _timed(lambda: worker_self_build_id(src))
    ok = recovered == declared
    return {"component": "worker", "retention_class": "REGENERABLE (stateless code in git)",
            "known_point": f"source build_id {declared}; live deployed b189d3cc0703 (T040, rollback target)",
            "recovery_mechanism": "wrangler versions deploy <build_id> to a prior committed version; self-hash verifies integrity",
            "rpo": "0 (stateless code; every version in git)", "rto_seconds": rto,
            "known_hash": declared, "recovered_hash": recovered, "recoverable": ok,
            "note": "actual live rollback NOT executed (would touch production); drill proves the target is identifiable + integrity-verifiable"}


def drill_d1():
    (rep, rto) = _timed(lambda: RD.drill(str(T027_LOGICAL), str(FCR.RAW_EVIDENCE), RESTORE_MONTHS))
    known_pm = KNOWN["d1_restore_per_month"]
    # anchor to the COMMITTED T029 per-month counts (not just same-run ground truth): a snapshot that
    # lost/gained rows would restore a different month count and fail this.
    per_month_match = all(rep["per_month"][m]["versions"] == known_pm[m]["versions"]
                          and rep["per_month"][m]["month_documents"] == known_pm[m]["month_documents"]
                          for m in RESTORE_MONTHS)
    ok = rep["counts_consistent"] and rep["orphan_versions"] == 0 and per_month_match
    ev = _sha16([rep["per_month"][m]["result_hash"] for m in RESTORE_MONTHS])
    return {"component": "d1", "retention_class": "PERMANENT (published DocumentVersion, append-only) + REGENERABLE (mirror views)",
            "known_point": "T027 open monthly snapshot (498 docs / 500 versions); published versions append-only",
            "recovery_mechanism": "restore a month from the open snapshot into an isolated in-memory SQLite (T029)",
            "rpo": "0 for the permanent append-only record; open-format monthly snapshot is the portable recovery point",
            "rto_seconds": rto, "known_hash": "counts_consistent + committed T029 per-month", "recovered_hash": ev,
            "recoverable": ok,
            "detail": {"counts_consistent": rep["counts_consistent"], "orphans": rep["orphan_versions"],
                       "permanent_deletes": rep["permanent_delete_count"],
                       "per_month_matches_committed_t029": per_month_match,
                       "restored_versions": sum(v["versions"] for v in rep["per_month"].values())},
            "note": "restored into a throwaway :memory: SQLite; per-month counts compared to the committed T029 restore report; production D1 untouched"}


def drill_r2(content_override=None, source_override=None):
    raw = json.loads(FCR.RAW_EVIDENCE.read_text("utf-8"))
    it = raw[0]
    content = content_override if content_override is not None else \
        (it.get("summary") or it.get("title") or str(it.get("id"))).encode("utf-8")
    src_id = source_override or it.get("source_id") or "src"
    (k1, rto) = _timed(lambda: RK.object_key(src_id, content)[0])
    k_diff = RK.object_key(src_id, content + b" x")[0]   # different bytes => different key (addressing works)
    known = KNOWN["r2_object_key"]
    ok = (k1 == known) and (k1 != k_diff)   # recover to the COMMITTED content-addressed key, not a self-compare
    return {"component": "r2", "retention_class": "PERMANENT (raw content-addressed artifact, never deleted)",
            "known_point": f"committed content-addressed object key {known}",
            "recovery_mechanism": "content-addressed immutable key; identical bytes re-derive the committed key",
            "rpo": "0 (immutable content-addressed; addressable by content)", "rto_seconds": rto,
            "known_hash": known, "recovered_hash": k1, "recoverable": ok,
            "note": "no production R2 read/write; key derived locally and compared to the committed known point"}


def drill_registry(registry_path=None):
    reg = registry_path or str(FCR.REGISTRY)
    work = pathlib.Path(tempfile.mkdtemp(prefix="t086_reg_"))
    def _recompile():
        subprocess.run(["python3", str(TOOLS / "compile_registry.py"), "--registry", reg, "--out-dir", str(work)],
                       capture_output=True, text=True, check=True)
        return (work / "registry_hash.txt").read_text("utf-8").strip()
    (rh, rto) = _timed(_recompile)
    ok = rh == FCR.COMMITTED_REGISTRY_HASH
    return {"component": "source_registry", "retention_class": "REGENERABLE (compiled from the committed registry in git)",
            "known_point": f"registry_hash {FCR.COMMITTED_REGISTRY_HASH}",
            "recovery_mechanism": "recompile source_registry.json (git revert to a prior registry is the known point)",
            "rpo": "0 (registry versioned in git)", "rto_seconds": rto,
            "known_hash": FCR.COMMITTED_REGISTRY_HASH, "recovered_hash": rh, "recoverable": ok}


def drill_content(items_path=None, fs_path=None):
    items = items_path or str(EVID / "ADP-S8-P01-T085/data-samples/items_500.json")
    fs = fs_path or str(EVID / "ADP-S8-P01-T085/data-samples/fs_500.json")
    work = pathlib.Path(tempfile.mkdtemp(prefix="t086_content_"))
    def _render():
        out = work / "render.json"
        subprocess.run(["python3", str(TOOLS / "build_render_payload.py"), "--items", items,
                        "--factsheets", fs, "--build-id", "DR-DRILL", "--out", str(out)],
                       capture_output=True, text=True, check=True)
        return _sha16(json.loads(out.read_text("utf-8")))
    (h, rto) = _timed(_render)
    known = KNOWN["content_bundle_render_sha16"]
    ok = h == known   # recover to the COMMITTED known-good bundle hash, not a same-run self-comparison
    return {"component": "content_bundle", "retention_class": "REGENERABLE (L0-L3 render, deterministically rebuilt from raw + code)",
            "known_point": f"committed render bundle hash {known}",
            "recovery_mechanism": "re-derive the L0-L3 render payloads from the permanent raw items + code (T018); must reproduce the committed bundle",
            "rpo": "0 (regenerable from permanent raw evidence)", "rto_seconds": rto,
            "known_hash": known, "recovered_hash": h, "recoverable": ok}


def drill_prediction():
    sys.path.insert(0, str(FCR.BASELINES_DRIVER))
    import build_baselines as BB   # noqa: E402
    import baselines as BL         # noqa: E402
    (report, rto) = _timed(lambda: BL.benchmark(BB.TARGETS, BB.HISTORY, BB.EVAL))
    committed = json.loads((FCR.BASELINES_DRIVER / "baselines_report.json").read_text("utf-8"))["report"]
    ok = _sha16(FCR._json_norm(report)) == _sha16(FCR._json_norm(committed)) \
        and report["G1"]["has_reproducible_baseline"] and report["G2"]["has_reproducible_baseline"]
    return {"component": "prediction", "retention_class": "REGENERABLE (baselines) + PERMANENT (append-only forecast ledger T073)",
            "known_point": "committed baselines report (G1/G2 reproducible); append-only forecast ledger",
            "recovery_mechanism": "re-benchmark baselines from the committed history/eval; the forecast ledger is append-only",
            "rpo": "0 (regenerable baselines; append-only ledger)", "rto_seconds": rto,
            "known_hash": _sha16(FCR._json_norm(committed)), "recovered_hash": _sha16(FCR._json_norm(report)),
            "recoverable": ok}


DRILLS = {"worker": drill_worker, "d1": drill_d1, "r2": drill_r2,
          "source_registry": drill_registry, "content_bundle": drill_content, "prediction": drill_prediction}


def run_dr_drill(components=None):
    names = components or list(DRILLS)
    results = [DRILLS[n]() for n in names]
    for r in results:
        r["is_release_blocker"] = not r["recoverable"]
    blockers = [r["component"] for r in results if r["is_release_blocker"]]
    return {
        "iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S8-P01-T086",
        "components": results,
        "all_recoverable": all(r["recoverable"] for r in results),
        "release_blockers": blockers,
        "rto_rpo_actuals": [{"component": r["component"], "rto_seconds": r["rto_seconds"], "rpo": r["rpo"]} for r in results],
        "evidence_hashes": {r["component"]: r["recovered_hash"] for r in results},
        "isolation": "every recovery runs in an isolated tmp dir / in-memory SQLite; no live rollback; no production D1/R2/network write; live worker unchanged",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    rep = run_dr_drill()
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in rep["components"]:
        print(f"  {r['component']:<16} recoverable={r['recoverable']} blocker={r['is_release_blocker']} "
              f"rto={r['rto_seconds']}s rpo={r['rpo'][:32]!r} hash={str(r['recovered_hash'])[:16]}")
    print(f"ALL_RECOVERABLE={rep['all_recoverable']} RELEASE_BLOCKERS={rep['release_blockers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
