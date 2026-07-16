#!/usr/bin/env python3
"""ADP V0.1 STATUS drift check (ADP-S1-P01-T011).

CI-usable check that the generated status is the single truth:
  1. STATUS_GENERATED.md matches the deployment manifest (commit, cron, registry,
     schema hash) -- generated status is not stale vs the manifest;
  2. docs/v03/STATUS.yaml's R6 (tunnel/Mac mirror) is marked superseded_by
     J5_cloud_native -- a hand-written old architecture cannot claim to be current.

Exit 0 => PASS (no drift). Exit 1 => DRIFT. Read-only.

Usage: python3 check_status_drift.py
"""
import json, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
ADP_ROOT = HERE.parents[3]
MANIFEST = V01 / "deployment_manifest.sample.json"
STATUS_GEN = V01 / "STATUS_GENERATED.md"
STATUS_V03 = ADP_ROOT / "docs/v03/STATUS.yaml"


def main():
    problems = []
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    b = m["binding"]
    gen = STATUS_GEN.read_text(encoding="utf-8") if STATUS_GEN.exists() else ""
    if not gen:
        problems.append("STATUS_GENERATED.md missing")
    else:
        # 1. generated status must carry the manifest's current facts
        for label, val in [("commit", b["commit"]), ("cron", b["cron"]),
                           ("registry", b["sources"].get("registry_ver") or ""),
                           ("content_hash", m["content_hash"])]:
            if val and val not in gen:
                problems.append(f"STATUS_GENERATED.md missing manifest {label} ({val})")
        if "无 Cloudflare Tunnel" not in gen and "no Cloudflare Tunnel" not in gen:
            problems.append("STATUS_GENERATED.md does not assert tunnel/Mac is retired")

    # 2. docs/v03/STATUS.yaml R6 must be marked superseded
    if STATUS_V03.exists():
        s = STATUS_V03.read_text(encoding="utf-8")
        # find the R6 block
        if "\n  R6:" in s:
            r6 = s.split("\n  R6:", 1)[1]
            # next top-level-2-space stage key ends the block
            import re
            nxt = re.search(r"\n  [A-Za-z0-9_]+:", r6)
            r6block = r6[: nxt.start()] if nxt else r6
            if "superseded_by" not in r6block:
                problems.append("docs/v03/STATUS.yaml R6 (tunnel/Mac) not marked superseded_by -> contradicts J5 cloud-native")
        else:
            problems.append("docs/v03/STATUS.yaml has no R6 block to check (unexpected)")
    else:
        problems.append("docs/v03/STATUS.yaml missing")

    print("STATUS drift check")
    print(f"  manifest: {MANIFEST.name} (content_hash {m['content_hash'][:20]}...)")
    if problems:
        print("RESULT: DRIFT")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("RESULT: PASS (generated status matches manifest; R6 tunnel/Mac superseded; no drift)")
    sys.exit(0)


if __name__ == "__main__":
    main()
