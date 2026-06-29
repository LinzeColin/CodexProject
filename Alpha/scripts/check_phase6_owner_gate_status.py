from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.phase6_owner_gate import (  # noqa: E402
    DEFAULT_RUNTIME_EVIDENCE_ROOT,
    DEFAULT_SOAK_HISTORY_PATH,
    build_phase6_owner_gate_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查 Alpha Phase 6 OWNER-GATE-01 当前证据状态。")
    parser.add_argument("--evidence-root", default=str(DEFAULT_RUNTIME_EVIDENCE_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_SOAK_HISTORY_PATH))
    parser.add_argument("--duration-hours", type=int, default=48)
    parser.add_argument("--max-sample-gap-seconds", type=int, default=900)
    parser.add_argument("--max-sample-age-seconds", type=int, default=900)
    parser.add_argument("--require-fresh", action="store_true", help="要求最新 sampler 样本未过期，否则返回非 0。")
    parser.add_argument("--require-ready", action="store_true", help="要求 ready_for_owner_gate，否则返回非 0。")
    args = parser.parse_args()

    report = build_phase6_owner_gate_status(
        evidence_root=args.evidence_root,
        history_path=args.history_path,
        duration_hours=args.duration_hours,
        max_sample_gap_seconds=args.max_sample_gap_seconds,
        max_sample_age_seconds=args.max_sample_age_seconds,
        live_authorization_path=ROOT / "runtime" / "LIVE_AUTHORIZATION.json",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready_for_owner_gate":
        return 1
    if not report["live_authorization_absent"]:
        return 2
    if args.require_fresh and report["sampler_freshness_status"] != "pass":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
