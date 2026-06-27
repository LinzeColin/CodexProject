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
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="只读发布 Alpha Phase 6 runtime evidence 到 GitHub 可备份 docs evidence。"
    )
    parser.add_argument("--source-evidence-root", default=str(DEFAULT_RUNTIME_EVIDENCE_ROOT))
    parser.add_argument("--target-evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_SOAK_HISTORY_PATH))
    parser.add_argument("--duration-hours", type=int, default=48)
    parser.add_argument("--max-sample-gap-seconds", type=int, default=DEFAULT_MAX_SAMPLE_GAP_SECONDS)
    args = parser.parse_args()

    report = publish_phase6_owner_gate_evidence(
        source_evidence_root=args.source_evidence_root,
        target_evidence_root=args.target_evidence_root,
        history_path=args.history_path,
        duration_hours=args.duration_hours,
        max_sample_gap_seconds=args.max_sample_gap_seconds,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not report["live_authorization_absent"]:
        return 2
    if report["verification_status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
