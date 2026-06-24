import asyncio
import threading
import time

from backend.app.services.agent_runtime import AutoPaperAgentRuntime


def paper_loop_result(symbol: str = "TLT"):
    return {
        "run_id": f"run_{symbol.lower()}",
        "status": "completed",
        "intent": {"symbol": symbol, "strategy_id": f"momentum_{symbol}_20d"},
        "risk_check": {"status": "approved_for_owner_review"},
        "approval_queue": {"ticket": {"status": "pending_owner_approval"}},
        "paper_order": {"status": "filled"},
        "paper_portfolio": {"trade_count": 1, "total_equity": 10000.0},
    }


class FakePaperLoop:
    def run_once(self):
        return paper_loop_result("TLT")


class SlowCountingPaperLoop:
    def __init__(self, *, delay_seconds: float = 0.05) -> None:
        self.delay_seconds = delay_seconds
        self.started = threading.Event()
        self.completed = 0

    def run_once(self):
        self.started.set()
        time.sleep(self.delay_seconds)
        self.completed += 1
        return paper_loop_result("SPY")


def test_auto_paper_agent_runtime_runs_immediate_cycle_and_stops():
    runtime = AutoPaperAgentRuntime()

    async def exercise():
        runtime.start(loop_factory=FakePaperLoop, interval_seconds=60)
        for _ in range(50):
            snapshot = runtime.snapshot()
            if snapshot["run_count"] >= 1:
                break
            await asyncio.sleep(0.01)
        running = runtime.snapshot()
        stopped = await runtime.stop()
        return running, stopped

    running, stopped = asyncio.run(exercise())

    assert running["task_running"] is True
    assert running["run_count"] == 1
    assert running["error_count"] == 0
    assert running["status"] == "sleeping"
    assert running["last_result_summary"]["intent_symbol"] == "TLT"
    assert stopped["status"] == "stopped"
    assert stopped["task_running"] is False
    assert stopped["stopping"] is False
    assert stopped["last_stopped_at"] is not None


def test_auto_paper_agent_runtime_drains_current_cycle_before_stopped():
    runtime = AutoPaperAgentRuntime()
    loop = SlowCountingPaperLoop(delay_seconds=0.05)

    async def exercise():
        runtime.start(loop_factory=lambda: loop, interval_seconds=60)
        for _ in range(50):
            if loop.started.is_set():
                break
            await asyncio.sleep(0.01)
        stopped = await runtime.stop(timeout_seconds=1)
        await asyncio.sleep(0.08)
        return stopped, runtime.snapshot(), loop.completed

    stopped, after_wait, completed = asyncio.run(exercise())

    assert stopped["status"] == "stopped"
    assert stopped["task_running"] is False
    assert stopped["run_count"] == 1
    assert completed == 1
    assert after_wait["run_count"] == 1
    assert after_wait["task_running"] is False


def test_auto_paper_agent_runtime_stop_timeout_does_not_claim_stopped():
    runtime = AutoPaperAgentRuntime()
    loop = SlowCountingPaperLoop(delay_seconds=0.12)

    async def exercise():
        runtime.start(loop_factory=lambda: loop, interval_seconds=60)
        for _ in range(50):
            if loop.started.is_set():
                break
            await asyncio.sleep(0.01)
        timed_out = await runtime.stop(timeout_seconds=0.01)
        final = await runtime.stop(timeout_seconds=1)
        return timed_out, final

    timed_out, final = asyncio.run(exercise())

    assert timed_out["status"] == "stop_timeout"
    assert timed_out["task_running"] is True
    assert timed_out["stopping"] is True
    assert timed_out["stop_timeout_count"] == 1
    assert final["status"] == "stopped"
    assert final["task_running"] is False
    assert final["stopping"] is False
