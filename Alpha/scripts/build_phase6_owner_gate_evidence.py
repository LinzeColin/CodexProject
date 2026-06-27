from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.paper_trading_loop import build_default_loop  # noqa: E402
from backend.app.services.phase6_owner_gate import (  # noqa: E402
    DEFAULT_EVIDENCE_ROOT,
    DEFAULT_SOAK_HISTORY_PATH,
    append_soak_sample,
    build_phase6_evidence_manifest,
    build_owner_decision_markdown,
    build_owner_gate_closeout,
    build_phase6_closeout_report_markdown,
    build_paper_shadow_report,
    build_shadow_live_constraints_report,
    build_soak_validation_report,
    read_soak_samples,
    verify_phase6_evidence_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Alpha Phase 6 OWNER-GATE-01 证据骨架。")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_SOAK_HISTORY_PATH))
    parser.add_argument("--sample-count", type=int, default=1)
    parser.add_argument("--duration-hours", type=int, default=48)
    args = parser.parse_args()

    evidence_root = Path(args.evidence_root)
    samples = read_soak_samples(args.history_path)
    latest_report = {}
    latest_constraints = {}
    for _ in range(max(1, args.sample_count)):
        run_result = build_default_loop(interval_seconds=300).run_once()
        latest_report = build_paper_shadow_report(
            run_result=run_result,
            output_path=evidence_root / "paper_shadow_report_latest.json",
        )
        latest_constraints = build_shadow_live_constraints_report(
            output_path=evidence_root / "shadow_live_constraints_latest.json",
        )
        samples.append(
            append_soak_sample(
                paper_shadow_report=latest_report,
                shadow_live_constraints=latest_constraints,
                history_path=args.history_path,
            )
        )

    soak = build_soak_validation_report(
        samples=samples,
        duration_hours=args.duration_hours,
        output_path=evidence_root / "soak_validation_latest.json",
    )
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=latest_report,
        shadow_live_constraints=latest_constraints,
        output_path=evidence_root / "phase6_closeout.json",
    )
    build_owner_decision_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=latest_report,
        shadow_live_constraints=latest_constraints,
        output_path=evidence_root / "OWNER_DECISION.md",
    )
    build_phase6_closeout_report_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=latest_report,
        shadow_live_constraints=latest_constraints,
        output_path=evidence_root / "PHASE6_CLOSEOUT_REPORT.md",
    )
    build_phase6_evidence_manifest(
        evidence_root=evidence_root,
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=latest_report,
        shadow_live_constraints=latest_constraints,
        output_path=evidence_root / "EVIDENCE_MANIFEST.json",
    )
    verify_phase6_evidence_package(
        evidence_root=evidence_root,
        output_path=evidence_root / "EVIDENCE_PACKAGE_VERIFICATION.json",
    )
    print(json.dumps(closeout, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
