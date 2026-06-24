from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class AutoPaperAgentRuntime:
    """Owns the app-level automatic paper trading loop."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._loop_factory: Callable[[], Any] | None = None
        self._interval_seconds = 300
        self._stop_timeout_seconds = 5.0
        self._enabled = False
        self._stopping = False
        self._status = "stopped"
        self._started_at: datetime | None = None
        self._last_stopped_at: datetime | None = None
        self._last_run_started_at: datetime | None = None
        self._last_run_completed_at: datetime | None = None
        self._next_run_at: datetime | None = None
        self._run_count = 0
        self._error_count = 0
        self._stop_timeout_count = 0
        self._last_error: str | None = None
        self._last_result_summary: dict | None = None

    def start(self, *, loop_factory: Callable[[], Any], interval_seconds: int = 300) -> dict:
        if self._task and not self._task.done():
            return self.snapshot()
        if self._task and self._task.done():
            self._task = None
            self._stop_event = None
        self._loop_factory = loop_factory
        self._interval_seconds = int(interval_seconds)
        self._enabled = True
        self._stopping = False
        self._status = "starting"
        self._started_at = _utc_now()
        self._last_stopped_at = None
        self._next_run_at = None
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run())
        return self.snapshot()

    async def stop(self, *, timeout_seconds: float | None = None) -> dict:
        self._enabled = False
        if not self._task:
            self._status = "stopped"
            self._stopping = False
            self._next_run_at = None
            self._last_stopped_at = _utc_now()
            return self.snapshot()

        if self._task.done():
            await self._finalize_task(self._task)
            return self.snapshot()

        self._stopping = True
        self._status = "stopping"
        self._next_run_at = None
        if self._stop_event:
            self._stop_event.set()

        timeout = self._stop_timeout_seconds if timeout_seconds is None else float(timeout_seconds)
        done, _ = await asyncio.wait({self._task}, timeout=timeout)
        if not done:
            self._stop_timeout_count += 1
            self._status = "stop_timeout"
            return self.snapshot()

        await self._finalize_task(self._task)
        return self.snapshot()

    async def _run(self) -> None:
        if not self._loop_factory or not self._stop_event:
            self._status = "stopped"
            return
        try:
            while not self._stop_event.is_set():
                self._status = "running_cycle"
                self._last_run_started_at = _utc_now()
                try:
                    result = await asyncio.to_thread(self._run_cycle)
                    self._last_run_completed_at = _utc_now()
                    self._run_count += 1
                    self._last_error = None
                    self._last_result_summary = self._summarize_result(result)
                    self._status = "sleeping"
                except Exception as exc:  # pragma: no cover - defensive runtime guard
                    self._last_run_completed_at = _utc_now()
                    self._error_count += 1
                    self._last_error = str(exc)
                    self._status = "error_sleeping"

                if self._stop_event.is_set():
                    break
                self._next_run_at = _utc_now() + timedelta(seconds=self._interval_seconds)
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval_seconds)
                except asyncio.TimeoutError:
                    continue
        finally:
            self._status = "stopped"
            self._stopping = False
            self._next_run_at = None
            self._last_stopped_at = _utc_now()

    async def _finalize_task(self, task: asyncio.Task) -> None:
        try:
            await task
        except asyncio.CancelledError:
            self._status = "stopped"
            self._last_stopped_at = _utc_now()
        except Exception as exc:  # pragma: no cover - defensive shutdown guard
            self._error_count += 1
            self._last_error = str(exc)
            self._status = "stopped"
            self._last_stopped_at = _utc_now()
        finally:
            if self._task is task:
                self._task = None
                self._stop_event = None
            self._stopping = False
            self._next_run_at = None

    def _run_cycle(self) -> dict:
        if not self._loop_factory:
            raise RuntimeError("agent loop factory is not configured")
        loop = self._loop_factory()
        result = loop.run_once()
        if not isinstance(result, dict):
            raise TypeError("paper loop result must be a dict")
        return result

    def _summarize_result(self, result: dict) -> dict:
        ticket = result.get("approval_queue", {}).get("ticket", {})
        portfolio = result.get("paper_portfolio", {})
        intent = result.get("intent", {})
        return {
            "run_id": result.get("run_id"),
            "status": result.get("status"),
            "intent_symbol": intent.get("symbol"),
            "intent_strategy_id": intent.get("strategy_id"),
            "risk_status": result.get("risk_check", {}).get("status"),
            "ticket_status": ticket.get("status"),
            "paper_order_status": result.get("paper_order", {}).get("status"),
            "paper_trade_count": portfolio.get("trade_count"),
            "paper_total_equity": portfolio.get("total_equity"),
        }

    def snapshot(self) -> dict:
        task_running = bool(self._task and not self._task.done())
        return {
            "enabled": self._enabled,
            "status": self._status,
            "stopping": self._stopping,
            "task_running": task_running,
            "interval_seconds": self._interval_seconds,
            "started_at": _iso(self._started_at),
            "last_stopped_at": _iso(self._last_stopped_at),
            "last_run_started_at": _iso(self._last_run_started_at),
            "last_run_completed_at": _iso(self._last_run_completed_at),
            "next_run_at": _iso(self._next_run_at),
            "run_count": self._run_count,
            "error_count": self._error_count,
            "stop_timeout_count": self._stop_timeout_count,
            "last_error": self._last_error,
            "last_result_summary": self._last_result_summary,
        }


AUTO_PAPER_AGENT = AutoPaperAgentRuntime()
