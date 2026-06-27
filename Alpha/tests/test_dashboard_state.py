import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.api import routes
from backend.app.services.approval_queue import ApprovalQueue


def _write_phase6_runtime(tmp_path, monkeypatch) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    evidence_root = tmp_path / "phase6_owner_gate_latest"
    evidence_root.mkdir(parents=True)
    history_path = tmp_path / "phase6_soak_history.jsonl"
    live_authorization_path = tmp_path / "LIVE_AUTHORIZATION.json"
    paper_shadow = {
        "status": "pass",
        "generated_at": now.isoformat(),
        "shadow": {"order_type": "limit"},
    }
    shadow_constraints = {
        "status": "pass",
        "generated_at": now.isoformat(),
        "health": {"live_trading_enabled": False, "kill_switch_active": False},
    }
    (evidence_root / "paper_shadow_report_latest.json").write_text(json.dumps(paper_shadow), encoding="utf-8")
    (evidence_root / "shadow_live_constraints_latest.json").write_text(json.dumps(shadow_constraints), encoding="utf-8")
    history_path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "fail_count": 0,
                "paper_shadow_report": paper_shadow,
                "shadow_live_constraints": shadow_constraints,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(routes, "PHASE6_EVIDENCE_ROOT", evidence_root)
    monkeypatch.setattr(routes, "PHASE6_HISTORY_PATH", history_path)
    monkeypatch.setattr(routes, "LIVE_AUTHORIZATION_PATH", live_authorization_path)


def test_dashboard_state_exposes_agent_portfolio_strategy_and_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(routes, "QUEUE_PATH", tmp_path / "approval_queue.json")
    monkeypatch.setattr(routes, "PAPER_STATE_PATH", tmp_path / "paper_portfolio.json")
    monkeypatch.setattr(routes, "DATA_PATH", Path("data/sample_prices.csv"))
    _write_phase6_runtime(tmp_path, monkeypatch)

    run_result = routes.paper_run_once()
    state = routes.dashboard_state()

    assert run_result["status"] == "completed"
    assert state["health"]["refresh_interval_seconds"] == 300
    assert state["agent_status"]["status"] == "ready"
    assert state["paper_portfolio"]["trade_count"] == 1
    assert state["strategy_tournament"]["candidate_count"] > 0
    assert state["strategy_tournament"]["validation_summary"]["validated_count"] > 0
    assert "hit_rate" in state["strategy_tournament"]["winner"]
    assert state["approval_queue"]["count"] == 1
    assert state["owner_base_files_readability"]["status"] == "pass"
    assert state["owner_base_files_readability"]["score_text"] == "100/100"
    assert {item["filename"] for item in state["owner_base_files_readability"]["files"]} == {"功能清单", "开发记录", "模型参数文件"}
    assert all(item["score_text"] == "100/100" for item in state["owner_base_files_readability"]["files"])
    assert state["phase6_owner_gate"]["status"] == "blocked_not_ready_for_owner_gate"
    assert state["phase6_owner_gate"]["paper_shadow_status"] == "pass"
    assert state["phase6_owner_gate"]["sampler_freshness_status"] == "pass"


def test_phase6_owner_gate_status_endpoint_is_read_only_and_fail_closed(tmp_path, monkeypatch):
    _write_phase6_runtime(tmp_path, monkeypatch)

    status = routes.phase6_owner_gate_status()

    assert status["status"] == "blocked_not_ready_for_owner_gate"
    assert status["live_authorization_absent"] is True
    assert status["shadow_live_constraints_status"] == "pass"
    assert status["blocking_conditions"] == ["phase6_48h_soak_validation"]
    assert "continuous_sample_count" in status
    assert "remaining_hours" in status
    assert "estimated_ready_at" in status
    assert not (tmp_path / "LIVE_AUTHORIZATION.json").exists()


def test_dashboard_html_contains_phase6_owner_gate_panel():
    html = routes.dashboard()

    assert "Phase 6 OWNER-GATE" in html
    assert "三基文件中文可读性" in html
    assert "renderOwnerBaseFiles" in html
    assert "renderPhase6" in html
    assert "连续观察" in html
    assert "剩余观察" in html
    assert "预计达标" in html


def test_agent_status_reports_app_runtime_loop_state(tmp_path, monkeypatch):
    loop_state = {
        "enabled": True,
        "status": "sleeping",
        "task_running": True,
        "interval_seconds": 300,
        "run_count": 1,
        "error_count": 0,
    }
    monkeypatch.setattr(routes.AUTO_PAPER_AGENT, "snapshot", lambda: loop_state)
    monkeypatch.setattr(routes, "QUEUE_PATH", tmp_path / "approval_queue.json")

    status = routes.agent_status()

    assert status["loop"] == loop_state
    assert status["loop"]["task_running"] is True
    assert status["pending_tickets"] == 0


def test_owner_summary_counts_only_fresh_pending_tickets(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    queue_path = tmp_path / "approval_queue.json"
    queue = ApprovalQueue(queue_path)
    queue.enqueue(
        {
            "ticket_id": "ticket_expired",
            "status": "pending_owner_approval",
            "created_at": now.isoformat(),
            "intent": {"expires_at": (now - timedelta(seconds=1)).isoformat()},
            "broker_payload": {},
            "risk_check": {},
        }
    )
    monkeypatch.setattr(routes, "QUEUE_PATH", queue_path)

    summary = routes.owner_summary()
    api_queue = routes.approval_queue()

    assert summary["pending_order_tickets"] == 0
    assert summary["expired_order_tickets"] == 1
    assert api_queue["count"] == 0
    assert api_queue["summary"]["total_count"] == 1
    assert api_queue["summary"]["expired_pending_count"] == 1
