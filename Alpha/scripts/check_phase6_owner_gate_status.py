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
    build_owner_gate_closeout,
    build_soak_validation_report,
    read_soak_samples,
)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查 Alpha Phase 6 OWNER-GATE-01 当前证据状态。")
    parser.add_argument("--evidence-root", default=str(DEFAULT_RUNTIME_EVIDENCE_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_SOAK_HISTORY_PATH))
    parser.add_argument("--duration-hours", type=int, default=48)
    parser.add_argument("--require-ready", action="store_true", help="要求 ready_for_owner_gate，否则返回非 0。")
    args = parser.parse_args()

    evidence_root = Path(args.evidence_root)
    samples = read_soak_samples(args.history_path)
    paper_shadow = _read_json(evidence_root / "paper_shadow_report_latest.json")
    shadow_constraints = _read_json(evidence_root / "shadow_live_constraints_latest.json")
    soak = build_soak_validation_report(samples=samples, duration_hours=args.duration_hours)
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=shadow_constraints,
    )
    report = {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_status",
        "status": closeout["status"],
        "blocking_conditions": closeout["blocking_conditions"],
        "sample_count": soak["sample_count"],
        "observed_hours": soak["observed_hours"],
        "duration_hours_required": soak["duration_hours_required"],
        "paper_shadow_status": paper_shadow.get("status", "missing"),
        "shadow_live_constraints_status": shadow_constraints.get("status", "missing"),
        "live_authorization_absent": not (ROOT / "runtime" / "LIVE_AUTHORIZATION.json").exists(),
        "evidence_root": str(evidence_root),
        "history_path": str(Path(args.history_path)),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready_for_owner_gate":
        return 1
    if not report["live_authorization_absent"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
