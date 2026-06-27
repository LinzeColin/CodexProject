from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.services.approval_queue import ApprovalQueue
from backend.app.services.paper_trading_loop import PaperTradingLoop
from backend.app.services.phase6_owner_gate import (
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
from backend.app.services.policy import GovernorPolicy


def _paper_run(tmp_path: Path) -> dict:
    loop = PaperTradingLoop(
        policy=GovernorPolicy.load(Path("configs/trading_governor_policy.yaml")),
        price_path=Path("data/sample_prices.csv"),
        approval_queue=ApprovalQueue(tmp_path / "queue.json"),
        paper_state_path=tmp_path / "portfolio.json",
    )
    return loop.run_once()


def _soak_sample(generated_at: datetime, paper_shadow: dict, constraints: dict) -> dict:
    return {
        "generated_at": generated_at.isoformat(),
        "fail_count": 0,
        "paper_shadow_report": paper_shadow,
        "shadow_live_constraints": constraints,
    }


def _continuous_soak_samples(start: datetime, end: datetime, paper_shadow: dict, constraints: dict, *, step_minutes: int = 15) -> list[dict]:
    samples = []
    current = start
    while current < end:
        samples.append(_soak_sample(current, paper_shadow, constraints))
        current += timedelta(minutes=step_minutes)
    samples.append(_soak_sample(end, paper_shadow, constraints))
    return samples


def test_paper_shadow_report_passes_limit_order_contract(tmp_path):
    run = _paper_run(tmp_path)
    report = build_paper_shadow_report(run_result=run)

    assert report["status"] == "pass"
    checks = {item["id"]: item["status"] for item in report["hard_gate_checks"]}
    assert checks["broker_ready_limit_order"] == "pass"
    assert all(item["status"] == "pass" for item in report["schema_checks"])
    assert report["safety_boundary"]["broker_mutation_allowed"] is False


def test_shadow_live_constraints_pass_with_live_disabled(tmp_path):
    report = build_shadow_live_constraints_report(
        health={"live_trading_enabled": False, "kill_switch_active": False},
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
    )

    assert report["status"] == "pass"
    assert {item["id"]: item["status"] for item in report["checks"]}["live_authorization_absent"] == "pass"


def test_soak_validation_observes_until_48h_coverage(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(hours=48)
    samples = _continuous_soak_samples(start, end, paper_shadow, constraints)

    report = build_soak_validation_report(samples=samples)

    assert report["status"] == "pass"
    assert report["observed_hours"] == 48.0
    assert report["window_start"] == start.isoformat()
    assert report["window_end"] == end.isoformat()
    assert report["max_observed_gap_seconds"] == 900
    assert report["gap_violation_count"] == 0


def test_soak_validation_resets_window_after_stale_gap(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    start = datetime.now(timezone.utc).replace(microsecond=0)
    samples = [
        _soak_sample(start, paper_shadow, constraints),
        _soak_sample(start + timedelta(seconds=1800), paper_shadow, constraints),
        _soak_sample(start + timedelta(seconds=2400), paper_shadow, constraints),
    ]

    report = build_soak_validation_report(samples=samples, duration_hours=1, max_sample_gap_seconds=900)

    assert report["status"] == "observing"
    assert report["observed_seconds"] == 600
    assert report["window_start"] == (start + timedelta(seconds=1800)).isoformat()
    assert report["window_end"] == (start + timedelta(seconds=2400)).isoformat()
    assert report["max_observed_gap_seconds"] == 1800
    assert report["gap_violation_count"] == 1
    assert {item["id"]: item["status"] for item in report["checks"]}["sample_gap_coverage"] == "pass"


def test_owner_gate_closeout_blocks_until_all_acceptance_pass(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    soak = build_soak_validation_report(samples=[])

    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
    )

    assert closeout["status"] == "blocked_not_ready_for_owner_gate"
    assert "phase6_48h_soak_validation" in closeout["blocking_conditions"]
    assert "limit_order_contract" not in closeout["blocking_conditions"]


def test_owner_decision_markdown_contains_owner_choices_and_blockers(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    soak = build_soak_validation_report(samples=[])
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
    )
    output_path = tmp_path / "OWNER_DECISION.md"

    document = build_owner_decision_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=output_path,
    )

    assert output_path.read_text(encoding="utf-8") == document
    assert "### A." in document
    assert "### B." in document
    assert "### C." in document
    assert "phase6_48h_soak_validation" in document
    assert "Paper/Shadow schema 状态" in document
    assert "runtime/LIVE_AUTHORIZATION.json" in document
    assert "不提交真实 broker order" in document


def test_phase6_closeout_report_maps_acceptance_to_evidence(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    soak = build_soak_validation_report(samples=[])
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
    )
    output_path = tmp_path / "PHASE6_CLOSEOUT_REPORT.md"

    document = build_phase6_closeout_report_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=output_path,
    )

    assert output_path.read_text(encoding="utf-8") == document
    assert "验收标准逐项审计" in document
    assert "48 小时自然日 soak validation 通过" in document
    assert "至少一个合格交易日 Paper/Shadow 报告通过 schema 和 hard gate" in document
    assert "OWNER_DECISION.md 可供 owner 选择 A/B/C" in document
    assert "停在 OWNER-GATE-01，不进入 MICRO_LIVE" in document
    assert "尚不可提交 OWNER-GATE-01" in document


def test_phase6_evidence_manifest_checks_artifacts_and_status(tmp_path):
    run = _paper_run(tmp_path)
    evidence_root = tmp_path / "phase6_closeout_latest"
    paper_shadow = build_paper_shadow_report(
        run_result=run,
        output_path=evidence_root / "paper_shadow_report_latest.json",
    )
    constraints = build_shadow_live_constraints_report(
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        output_path=evidence_root / "shadow_live_constraints_latest.json",
    )
    sample = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fail_count": 0,
        "paper_shadow_report": paper_shadow,
        "shadow_live_constraints": constraints,
    }
    soak = build_soak_validation_report(samples=[sample], output_path=evidence_root / "soak_validation_latest.json")
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "phase6_closeout.json",
    )
    build_owner_decision_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "OWNER_DECISION.md",
    )
    build_phase6_closeout_report_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "PHASE6_CLOSEOUT_REPORT.md",
    )

    manifest = build_phase6_evidence_manifest(
        evidence_root=evidence_root,
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "EVIDENCE_MANIFEST.json",
    )

    assert manifest["status"] == "blocked_not_ready_for_owner_gate"
    assert manifest["all_artifacts_present"] is True
    assert {item["path"] for item in manifest["artifact_checks"]} == {
        "OWNER_DECISION.md",
        "PHASE6_CLOSEOUT_REPORT.md",
        "paper_shadow_report_latest.json",
        "phase6_closeout.json",
        "shadow_live_constraints_latest.json",
        "soak_validation_latest.json",
    }
    assert all(item["sha256"] for item in manifest["artifact_checks"])
    assert manifest["paper_shadow"]["schema_status"] == "pass"
    assert manifest["paper_shadow"]["hard_gate_status"] == "pass"


def test_phase6_evidence_package_verifier_preserves_owner_gate_block(tmp_path):
    run = _paper_run(tmp_path)
    evidence_root = tmp_path / "phase6_closeout_latest"
    paper_shadow = build_paper_shadow_report(
        run_result=run,
        output_path=evidence_root / "paper_shadow_report_latest.json",
    )
    constraints = build_shadow_live_constraints_report(
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        output_path=evidence_root / "shadow_live_constraints_latest.json",
    )
    sample = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fail_count": 0,
        "paper_shadow_report": paper_shadow,
        "shadow_live_constraints": constraints,
    }
    soak = build_soak_validation_report(samples=[sample], output_path=evidence_root / "soak_validation_latest.json")
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "phase6_closeout.json",
    )
    build_owner_decision_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "OWNER_DECISION.md",
    )
    build_phase6_closeout_report_markdown(
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "PHASE6_CLOSEOUT_REPORT.md",
    )
    build_phase6_evidence_manifest(
        evidence_root=evidence_root,
        closeout=closeout,
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        output_path=evidence_root / "EVIDENCE_MANIFEST.json",
    )

    report = verify_phase6_evidence_package(
        evidence_root=evidence_root,
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        output_path=evidence_root / "EVIDENCE_PACKAGE_VERIFICATION.json",
    )
    ready_report = verify_phase6_evidence_package(
        evidence_root=evidence_root,
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        require_ready=True,
    )

    assert report["verification_status"] == "pass"
    assert report["owner_gate_status"] == "blocked_not_ready_for_owner_gate"
    assert (evidence_root / "EVIDENCE_PACKAGE_VERIFICATION.json").exists()
    assert ready_report["verification_status"] == "fail"


def test_soak_history_appends_jsonl_samples(tmp_path):
    run = _paper_run(tmp_path)
    paper_shadow = build_paper_shadow_report(run_result=run)
    constraints = build_shadow_live_constraints_report(live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json")
    history_path = tmp_path / "soak.jsonl"

    sample = append_soak_sample(
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=constraints,
        history_path=history_path,
    )
    samples = read_soak_samples(history_path)

    assert sample["fail_count"] == 0
    assert len(samples) == 1
    assert samples[0]["paper_shadow_report"]["status"] == "pass"


def test_owner_gate_status_cli_reports_ready_from_runtime_evidence(tmp_path, monkeypatch, capsys):
    from scripts import check_phase6_owner_gate_status

    run = _paper_run(tmp_path)
    evidence_root = tmp_path / "phase6_owner_gate_latest"
    history_path = tmp_path / "soak.jsonl"
    paper_shadow = build_paper_shadow_report(
        run_result=run,
        output_path=evidence_root / "paper_shadow_report_latest.json",
    )
    constraints = build_shadow_live_constraints_report(
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        output_path=evidence_root / "shadow_live_constraints_latest.json",
    )
    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(hours=48)
    samples = _continuous_soak_samples(start, end, paper_shadow, constraints)
    history_path.write_text("\n".join(json.dumps(sample) for sample in samples) + "\n", encoding="utf-8")
    monkeypatch.setattr(check_phase6_owner_gate_status, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_phase6_owner_gate_status.py",
            "--evidence-root",
            str(evidence_root),
            "--history-path",
            str(history_path),
            "--duration-hours",
            "48",
            "--require-ready",
        ],
    )

    assert check_phase6_owner_gate_status.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready_for_owner_gate"
    assert payload["live_authorization_absent"] is True
    assert payload["sampler_freshness_status"] == "pass"
    assert payload["latest_sample_generated_at"] == end.isoformat()
    assert payload["gap_violation_count"] == 0
    assert payload["continuous_sample_count"] == len(samples)


def test_owner_gate_status_cli_detects_stale_sampler_sample(tmp_path, monkeypatch, capsys):
    from scripts import check_phase6_owner_gate_status

    run = _paper_run(tmp_path)
    evidence_root = tmp_path / "phase6_owner_gate_latest"
    history_path = tmp_path / "soak.jsonl"
    paper_shadow = build_paper_shadow_report(
        run_result=run,
        output_path=evidence_root / "paper_shadow_report_latest.json",
    )
    constraints = build_shadow_live_constraints_report(
        live_authorization_path=tmp_path / "LIVE_AUTHORIZATION.json",
        output_path=evidence_root / "shadow_live_constraints_latest.json",
    )
    sample = {
        "generated_at": "2000-01-01T00:00:00+00:00",
        "fail_count": 0,
        "paper_shadow_report": paper_shadow,
        "shadow_live_constraints": constraints,
    }
    history_path.write_text(json.dumps(sample) + "\n", encoding="utf-8")
    monkeypatch.setattr(check_phase6_owner_gate_status, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_phase6_owner_gate_status.py",
            "--evidence-root",
            str(evidence_root),
            "--history-path",
            str(history_path),
            "--max-sample-age-seconds",
            "1",
            "--require-fresh",
        ],
    )

    assert check_phase6_owner_gate_status.main() == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["sampler_freshness_status"] == "stale"
    assert payload["latest_sample_age_seconds"] > 1
