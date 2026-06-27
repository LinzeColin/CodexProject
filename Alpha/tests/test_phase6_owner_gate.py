from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.services.approval_queue import ApprovalQueue
from backend.app.services.paper_trading_loop import PaperTradingLoop
from backend.app.services.phase6_owner_gate import (
    append_soak_sample,
    build_owner_decision_markdown,
    build_owner_gate_closeout,
    build_phase6_closeout_report_markdown,
    build_paper_shadow_report,
    build_shadow_live_constraints_report,
    build_soak_validation_report,
    read_soak_samples,
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
    start = datetime.now(timezone.utc).replace(microsecond=0)
    samples = [
        {
            "generated_at": start.isoformat(),
            "fail_count": 0,
            "paper_shadow_report": {**paper_shadow, "status": "pass", "shadow": {**paper_shadow["shadow"], "order_type": "limit"}},
            "shadow_live_constraints": constraints,
        },
        {
            "generated_at": (start + timedelta(hours=48)).isoformat(),
            "fail_count": 0,
            "paper_shadow_report": {**paper_shadow, "status": "pass", "shadow": {**paper_shadow["shadow"], "order_type": "limit"}},
            "shadow_live_constraints": constraints,
        },
    ]

    report = build_soak_validation_report(samples=samples)

    assert report["status"] == "pass"
    assert report["observed_hours"] == 48.0


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
    start = datetime.now(timezone.utc).replace(microsecond=0)
    samples = [
        {
            "generated_at": start.isoformat(),
            "fail_count": 0,
            "paper_shadow_report": paper_shadow,
            "shadow_live_constraints": constraints,
        },
        {
            "generated_at": (start + timedelta(hours=48)).isoformat(),
            "fail_count": 0,
            "paper_shadow_report": paper_shadow,
            "shadow_live_constraints": constraints,
        },
    ]
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
