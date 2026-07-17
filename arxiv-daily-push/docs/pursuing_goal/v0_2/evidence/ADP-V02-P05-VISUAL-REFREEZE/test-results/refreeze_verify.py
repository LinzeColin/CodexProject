#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-V02-P05 acceptance: the six-theme visual/motion gate is REAL again.

Two defects are fixed here and both are verified with LOAD-BEARING negative controls:
  A. the T077 baseline was stale (approved+deployed T079/T080/T082 drift) so run_ci BLOCKed
     unconditionally -- including against HEAD itself. A gate that blocks on everything carries
     no information.
  B. visual_regression_ci.py had NO __main__: `python3 visual_regression_ci.py` exited 0 with zero
     output, so anything "running the gate" as a script got a vacuous pass.

The re-freeze is NOT a rubber stamp: it refuses to emit a baseline if ANY drifted element is not
attributable to an approved+deployed task, and refuses if the Owner-signed per-theme identity moved.
"""
import json
import pathlib
import subprocess
import sys

# this file lives at v0_2/evidence/<TASK>/test-results/ -> v0_2 is parents[3]
V02 = pathlib.Path(__file__).resolve().parents[3]
V01 = V02.parent / "v0_1"
TOOLS01 = V01 / "tools"
WORKER = V02.parents[2] / "deploy" / "cloudflare" / "worker_cloud.js"
GATE = TOOLS01 / "visual_regression_ci.py"
REFREEZE = V02 / "tools" / "visual_baseline_refreeze.py"
NEW_BASELINE = V02 / "evidence" / "ADP-V02-P05-VISUAL-REFREEZE" / "visual_baseline_manifest.json"
OLD_BASELINE = V01 / "evidence" / "ADP-S7-P01-T077" / "visual_baseline_manifest.json"

fails = []


def run(args, **kw):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=str(TOOLS01), **kw)


# ---- B: the gate now has a real entry point with a load-bearing exit code ----
clean = run([str(GATE)])
if clean.returncode != 0 or "PASS" not in clean.stdout:
    fails.append(f"gate should PASS(exit 0) on the committed worker vs the re-frozen baseline: rc={clean.returncode} {clean.stdout[:120]}")

src = WORKER.read_text(encoding="utf-8")
# NC1: an unapproved keyframe edit must BLOCK with a non-zero exit
mut = src.replace("@keyframes frise{", "@keyframes frise{/*unapproved*/", 1)
assert mut != src, "mutation anchor missing -- test would be vacuous"
p1 = pathlib.Path("/tmp/_p05_mut1.js"); p1.write_text(mut, encoding="utf-8")
nc1 = run([str(GATE), "--candidate", str(p1)])
if nc1.returncode == 0 or "BLOCK" not in nc1.stdout:
    fails.append(f"NC1 vacuous: an unapproved keyframe change must BLOCK with non-zero exit, got rc={nc1.returncode}")

# NC2: deleting a theme's signature motion must BLOCK
mut2 = src.replace("@keyframes meteor", "@keyframes _removed_meteor", 1)
assert mut2 != src, "mutation anchor missing"
p2 = pathlib.Path("/tmp/_p05_mut2.js"); p2.write_text(mut2, encoding="utf-8")
nc2 = run([str(GATE), "--candidate", str(p2)])
if nc2.returncode == 0 or "BLOCK" not in nc2.stdout:
    fails.append(f"NC2 vacuous: deleting a signature motion must BLOCK, got rc={nc2.returncode}")

# ---- A: the OLD baseline demonstrably blocked unconditionally (why the re-freeze was needed) ----
old = run([str(GATE), "--baseline", str(OLD_BASELINE)])
if old.returncode == 0:
    fails.append("the stale T077 baseline was expected to BLOCK even against HEAD (that is the defect being fixed)")

# ---- the re-freeze refuses to bless unexplained drift ----
sys.path.insert(0, str(V02 / "tools"))
import visual_baseline_refreeze as RF  # noqa: E402

rep, unexplained, themes_ok = RF.build("204c97eb5406")
if unexplained:
    fails.append(f"unexplained drift present: {unexplained}")
if not themes_ok:
    fails.append("per-theme identity changed -- must not be re-frozen without an Owner visual gate")
if sorted(rep["drifted_since_t077"]) != ["base_css", "keyframes", "master_visual"]:
    fails.append(f"unexpected drift set: {rep['drifted_since_t077']}")
# NC3: the refuse-path must be real END-TO-END -- not just RF.drift() as a pure function.
# Drive the actual main() with a poisoned T077 baseline and assert it EXITS 2 and does NOT write,
# even with --write. (An earlier version of this test only exercised the helper and therefore did not
# establish the claim it made; the reviewer caught that.)
poisoned_path = pathlib.Path("/tmp/_p05_poisoned_t077.json")
frozen_full = json.loads(OLD_BASELINE.read_text(encoding="utf-8"))
frozen_full["asset_hashes"] = dict(frozen_full["asset_hashes"])
frozen_full["asset_hashes"]["theme_js"] = "UNAPPROVED_DRIFT"   # an element NOT in ATTRIBUTION
poisoned_path.write_text(json.dumps(frozen_full), encoding="utf-8")

before = NEW_BASELINE.read_bytes()
saved_frozen, saved_argv = RF.FROZEN_T077, sys.argv
try:
    RF.FROZEN_T077 = poisoned_path                       # pretend theme_js drifted with no approval
    sys.argv = ["visual_baseline_refreeze.py", "--live-build-id", "204c97eb5406", "--write"]
    code = RF.main()                                     # drive the REAL entry point, --write included
finally:
    RF.FROZEN_T077, sys.argv = saved_frozen, saved_argv
if code != 2:
    fails.append(f"NC3 vacuous: unattributable drift must make main() ABORT with 2, got {code}")
if NEW_BASELINE.read_bytes() != before:
    fails.append("NC3: ABORT must NOT write a baseline, but the manifest changed on disk despite --write")

# ---- the new baseline is bound to the live build ----
nb = json.loads(NEW_BASELINE.read_text(encoding="utf-8"))
if nb.get("live_build_id") != "204c97eb5406" or nb.get("release_mode") != "PRODUCTION":
    fails.append(f"new baseline not bound to the live production build: {nb.get('live_build_id')}/{nb.get('release_mode')}")
if nb.get("supersedes", {}).get("live_build_id") != "b189d3cc0703":
    fails.append("new baseline must record what it supersedes")

print("gate on committed worker vs re-frozen baseline: PASS (exit 0)")
print(f"NC1 unapproved keyframe edit      -> {nc1.stdout.splitlines()[1] if len(nc1.stdout.splitlines())>1 else ''} (exit {nc1.returncode})")
print(f"NC2 deleted signature motion      -> {nc2.stdout.splitlines()[1] if len(nc2.stdout.splitlines())>1 else ''} (exit {nc2.returncode})")
print(f"stale T077 baseline vs HEAD       -> BLOCK (exit {old.returncode})  <- the defect being fixed")
print(f"drift since T077                  -> {rep['drifted_since_t077']} (all attributable)")
print(f"per-theme identity unchanged      -> {themes_ok}  <- the six themes the Owner signed are byte-identical")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: the gate now has a real __main__ with a load-bearing exit code (was: exit 0, no output), and "
      "is bound to a baseline re-frozen onto the LIVE build 204c97eb5406. Every element that drifted since "
      "T077 is attributable to an approved+deployed task (T079/T080 base_css, T082 keyframes, master_visual "
      "aggregate); the Owner-signed per-theme identity is byte-identical, and the re-freeze ABORTS rather "
      "than blessing any unattributable drift.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
