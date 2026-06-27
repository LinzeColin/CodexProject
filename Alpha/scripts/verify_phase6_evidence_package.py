from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.phase6_owner_gate import (  # noqa: E402
    DEFAULT_EVIDENCE_ROOT,
    verify_phase6_evidence_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="只读校验 Alpha Phase 6 OWNER-GATE-01 证据包完整性。")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--output", default=None, help="可选：写出 JSON 校验报告。")
    parser.add_argument("--require-ready", action="store_true", help="要求 closeout ready_for_owner_gate，否则返回非 0。")
    args = parser.parse_args()

    report = verify_phase6_evidence_package(
        evidence_root=args.evidence_root,
        require_ready=args.require_ready,
        output_path=args.output,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not report["live_authorization_absent"]:
        return 2
    if report["verification_status"] != "pass":
        return 1
    if args.require_ready and report["owner_gate_status"] != "ready_for_owner_gate":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
