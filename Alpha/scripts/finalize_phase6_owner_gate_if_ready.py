from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.phase6_owner_gate import (  # noqa: E402
    DEFAULT_EVIDENCE_ROOT,
    DEFAULT_MAX_SAMPLE_GAP_SECONDS,
    DEFAULT_RUNTIME_EVIDENCE_ROOT,
    DEFAULT_SOAK_HISTORY_PATH,
    publish_phase6_owner_gate_evidence,
    utc_now_iso,
    verify_phase6_evidence_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="只读发布并验收 Alpha Phase 6 OWNER-GATE-01；未达 48h 时明确返回 not_ready。"
    )
    parser.add_argument("--source-evidence-root", default=str(DEFAULT_RUNTIME_EVIDENCE_ROOT))
    parser.add_argument("--target-evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_SOAK_HISTORY_PATH))
    parser.add_argument("--duration-hours", type=int, default=48)
    parser.add_argument("--max-sample-gap-seconds", type=int, default=DEFAULT_MAX_SAMPLE_GAP_SECONDS)
    parser.add_argument("--output", default=None, help="可选：写出 finalize JSON 报告；默认写到 target evidence root。")
    args = parser.parse_args()

    publish_report = publish_phase6_owner_gate_evidence(
        source_evidence_root=args.source_evidence_root,
        target_evidence_root=args.target_evidence_root,
        history_path=args.history_path,
        duration_hours=args.duration_hours,
        max_sample_gap_seconds=args.max_sample_gap_seconds,
    )
    ready_report = verify_phase6_evidence_package(
        evidence_root=args.target_evidence_root,
        require_ready=True,
    )
    ready = ready_report["verification_status"] == "pass" and ready_report["owner_gate_status"] == "ready_for_owner_gate"
    live_authorization_absent = publish_report["live_authorization_absent"] and ready_report["live_authorization_absent"]
    report = {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_finalize",
        "generated_at": utc_now_iso(),
        "status": "ready_for_owner_gate" if ready else "not_ready_for_owner_gate",
        "status_zh": "可提交 OWNER-GATE-01" if ready else "未达 OWNER-GATE-01",
        "blocking_conditions": ready_report.get("blocking_conditions", []),
        "source_evidence_root": args.source_evidence_root,
        "target_evidence_root": args.target_evidence_root,
        "history_path": args.history_path,
        "publish_report": publish_report,
        "require_ready_verification": ready_report,
        "live_authorization_absent": live_authorization_absent,
    }
    output = Path(args.output) if args.output else Path(args.target_evidence_root) / "FINALIZE_STATUS.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not live_authorization_absent:
        return 2
    if publish_report["verification_status"] != "pass":
        return 3
    if not ready:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
