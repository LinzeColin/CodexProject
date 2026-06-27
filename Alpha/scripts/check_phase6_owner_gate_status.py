from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _latest_sample_freshness(samples: list[dict], *, max_age_seconds: int) -> dict:
    if not samples:
        return {
            "latest_sample_generated_at": None,
            "latest_sample_age_seconds": None,
            "max_sample_age_seconds": max_age_seconds,
            "sampler_freshness_status": "missing",
        }
    latest_sample = max(samples, key=lambda item: item.get("generated_at") or "")
    latest_generated_at = latest_sample.get("generated_at")
    latest_time = _parse_iso_datetime(latest_generated_at)
    if latest_time is None:
        return {
            "latest_sample_generated_at": latest_generated_at,
            "latest_sample_age_seconds": None,
            "max_sample_age_seconds": max_age_seconds,
            "sampler_freshness_status": "invalid_timestamp",
        }
    age_seconds = max(0, int((datetime.now(timezone.utc) - latest_time).total_seconds()))
    return {
        "latest_sample_generated_at": latest_time.isoformat(),
        "latest_sample_age_seconds": age_seconds,
        "max_sample_age_seconds": max_age_seconds,
        "sampler_freshness_status": "pass" if age_seconds <= max_age_seconds else "stale",
    }


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

    evidence_root = Path(args.evidence_root)
    samples = read_soak_samples(args.history_path)
    paper_shadow = _read_json(evidence_root / "paper_shadow_report_latest.json")
    shadow_constraints = _read_json(evidence_root / "shadow_live_constraints_latest.json")
    soak = build_soak_validation_report(
        samples=samples,
        duration_hours=args.duration_hours,
        max_sample_gap_seconds=args.max_sample_gap_seconds,
    )
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=shadow_constraints,
    )
    freshness = _latest_sample_freshness(samples, max_age_seconds=args.max_sample_age_seconds)
    report = {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_status",
        "status": closeout["status"],
        "blocking_conditions": closeout["blocking_conditions"],
        "sample_count": soak["sample_count"],
        "observed_hours": soak["observed_hours"],
        "duration_hours_required": soak["duration_hours_required"],
        "window_start": soak.get("window_start"),
        "window_end": soak.get("window_end"),
        "continuous_sample_count": soak.get("continuous_sample_count"),
        "max_sample_gap_seconds": soak.get("max_sample_gap_seconds"),
        "max_observed_gap_seconds": soak.get("max_observed_gap_seconds"),
        "gap_violation_count": soak.get("gap_violation_count"),
        "last_gap_violation": soak.get("last_gap_violation"),
        "paper_shadow_status": paper_shadow.get("status", "missing"),
        "shadow_live_constraints_status": shadow_constraints.get("status", "missing"),
        "live_authorization_absent": not (ROOT / "runtime" / "LIVE_AUTHORIZATION.json").exists(),
        "evidence_root": str(evidence_root),
        "history_path": str(Path(args.history_path)),
        **freshness,
    }
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
