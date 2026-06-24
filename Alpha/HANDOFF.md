# Alpha Handoff

Timestamp: 2026-06-13 Australia/Sydney

## Current Goal

Build Alpha as a GitHub-backed personal quant agent workspace with automatic paper trading, strategy iteration foundations, risk checks, approval queue, broker-ready order tickets, and dashboard visibility.

## Current State

- GitHub remote confirmed: `https://github.com/LinzeColin/Alpha`
- Local repo initialized on `main`
- Seed implementation and docs imported from the provided Alpha delivery pack
- Safety boundary recorded in `AGENTS.md`
- Default committed live trading config remains disabled
- MVP paper loop now generates `OrderIntent`, runs `pre_trade_risk_check`, fills a paper order, queues a `BrokerReadyOrderTicket`, and exposes dashboard state.
- Dashboard is available at `/dashboard`; API state is available at `/dashboard/state`.
- Paper portfolio state now persists through `PaperBroker.save/load`.
- Strategy iteration now runs a fixture momentum tournament and selects the best tradable candidate under risk/notional limits.
- Strategy iteration now includes walk-forward one-step OOS return, hit rate, and validation window counts.
- Dashboard state includes `paper_portfolio` and `strategy_tournament`.
- Local launcher scripts exist at `scripts/start_alpha_dashboard.sh` and `scripts/stop_alpha_dashboard.sh`.
- Dashboard startup now starts the app-managed `AutoPaperAgentRuntime`: one immediate paper cycle, then 300-second refreshes.
- `/agent/loop/status` exposes automatic loop state, run count, last result summary, next run time, and errors.
- `scripts/start_alpha_dashboard.sh` now performs a startup health check and removes stale pid files on failure.
- Approval queue now derives ticket freshness from `expires_at`; only fresh `pending_owner_approval` tickets count as owner-actionable.
- S3PBT01 now serializes ApprovalQueue and PaperBroker persisted JSON writes through locked atomic storage so concurrent local paper-loop runs do not overwrite queue or portfolio state.
- S3PBT02 now makes `AutoPaperAgentRuntime.stop()` drain the current cycle before reporting stopped, report `stop_timeout` truthfully when a cycle does not drain, and expose `stopping`, `last_stopped_at`, and `stop_timeout_count` in runtime status.
- Dashboard lifecycle scripts now validate/archived stale PID files, write PID files atomically, escalate TERM to KILL on shutdown timeout, preserve PID files while a process remains active, and keep `Alpha/scripts/*.sh` pinned to LF.
- S3PBT03 now proves atomic JSON replace failure and forced writer termination preserve the previous valid JSON, `AutoPaperAgentRuntime.stop()` produces no writes after stopped, and lifecycle scripts archive reused non-dashboard PIDs instead of trusting or killing them.
- AppleScript `Alpha.app` is installed at `/Users/linzezhang/Downloads/Alpha.app`, `/Users/linzezhang/Applications/Alpha.app`, and `/Applications/Alpha.app`.
- GitHub connector backup now contains the core runtime/dashboard/code/test changes from this run.
- Repo launcher exists at `outputs/applications/Alpha.command`; an older external copy was observed at `/Users/linzezhang/Downloads/applicatioins/Alpha.command`.

## Key Decisions

- The system will automate paper trading and order ticket generation.
- The system will not autonomously submit real-money broker orders.
- Broker-ready real-money candidates flow through `OrderIntent -> risk check -> approval queue -> BrokerReadyOrderTicket`.
- Refresh cadence target is 300 seconds by default.
- Use one app-managed paper loop; do not start a second external agent process beside the dashboard.
- Persisted queue/broker JSON writes must use `atomic_json_store`; do not reintroduce direct file read-modify-write for these state files.
- Stopping the app-managed loop must not claim stopped while the current cycle is still running; timeout is reported as `stop_timeout` until the task drains.
- Dashboard PID files are process-lifecycle evidence; scripts delete them only after confirming process exit.
- Dashboard PID files must identify an Alpha uvicorn `backend.app.main:app` process before start/stop scripts trust or terminate the PID; reused unrelated PIDs are archived as stale evidence.

## Files To Read First

- `AGENTS.md`
- `README.md`
- `HANDOFF.md`
- `docs/decision_log.md`
- `configs/trading_governor_policy.yaml`
- `backend/app/services/atomic_json_store.py`
- `backend/app/services/paper_trading_loop.py`
- `backend/app/services/strategy_iteration.py`
- `backend/app/services/paper_broker.py`
- `backend/app/services/agent_runtime.py`
- `outputs/applications/Alpha.applescript`
- `outputs/applications/Alpha.app`
- `scripts/start_alpha_dashboard.sh`
- `scripts/stop_alpha_dashboard.sh`

## Validation Commands

```bash
python -m pytest tests -q
python -m backend.app.services.paper_trading_loop --once
```

Latest validation:

```text
python -m pip install -e .[dev] -> passed
python -m pytest tests -q -> 20 passed
python -m backend.app.services.paper_trading_loop --once -> generated pending_owner_approval ticket and filled paper order
two-cycle smoke -> persisted paper portfolio trade_count=2 and cash=9816.10
curl /health -> ok, refresh_interval_seconds=300
curl /dashboard/state -> pending ticket, paper_portfolio, and strategy_tournament visible
curl /agent/loop/status -> app-managed loop visible with run_count=1, status=sleeping, next_run_at=300 seconds later, error_count=0
curl /dashboard -> contains Paper Portfolio, Strategy Tournament, Run Paper Cycle, and 300000ms refresh
scripts/start_alpha_dashboard.sh -> starts the local dashboard, app-managed paper loop, and writes runtime/alpha_dashboard.pid/log
scripts/stop_alpha_dashboard.sh -> waits for uvicorn shutdown and releases port 8000 cleanly
uvicorn foreground runtime check -> /agent/loop/status showed enabled=true, task_running=true, interval_seconds=300, run_count=1, next_run_at populated, error_count=0
freshness validation -> pytest 20 passed; isolated paper loop generated ticket.expires_at matching intent.expires_at
app launcher validation -> plutil -lint passed for repo, Downloads, user Applications, and system Applications Alpha.app copies
app launch validation -> open -n /Users/linzezhang/Downloads/Alpha.app started dashboard; /agent/loop/status returned task_running=true, interval_seconds=300, run_count=1, error_count=0
approval queue freshness API -> /orders/approval-queue returned fresh_pending_count=3, expired_pending_count=11, and fresh/expired actionability fields
strategy tournament validation -> 9 candidates, 9 validated, winner momentum_QQQ_20d, hit_rate=1.0, oos_return=0.025701, validation_windows=9
Dashboard HTML/API fallback -> contains System Snapshot, Paper Portfolio, Strategy Tournament, Approval Queue, Run Paper Cycle, 300000ms refresh, OOS Return, Hit Rate, Windows, Fresh Tickets, Expired Tickets, and Seconds Left
Repo launcher -> outputs/applications/Alpha.command exists and is executable
External app launchers -> /Users/linzezhang/Downloads/Alpha.app, /Users/linzezhang/Applications/Alpha.app, and /Applications/Alpha.app exist and pass plist validation
S3PBT01 atomic storage smoke -> threaded queue/broker concurrency passed and Windows cross-process queue/broker concurrency passed
S3PBT01 pytest target -> not run locally because pytest is unavailable: No module named pytest
S3PBT02 py_compile -> agent_runtime and runtime/lifecycle tests compile
S3PBT02 bash syntax -> start_alpha_dashboard.sh and stop_alpha_dashboard.sh parse with /bin/bash -n after LF enforcement
S3PBT02 runtime lifecycle smoke -> graceful drain, stop_timeout truthfulness, no second cycle after stopped, PID atomic-write assertions, TERM-to-KILL assertions, and PID-preservation assertions passed
S3PBT02 pytest target -> not run locally because pytest is unavailable: No module named pytest
S3PBT03 py_compile -> agent_runtime, atomic_json_store, shutdown fault tests, and lifecycle tests compile
S3PBT03 bash syntax -> start_alpha_dashboard.sh and stop_alpha_dashboard.sh parse with /bin/bash -n
S3PBT03 shutdown fault injection -> 5 unittest tests passed for disk-error preservation, forced termination preservation, no write after stopped, reused PID archiving, and start script dashboard identity checks
S3PBT03 pytest target -> not run locally because pytest is unavailable: No module named pytest
```

## Unresolved Risks

- Current market data is fixture-only.
- Broker paper integration is not connected yet.
- Dashboard is local MVP only.
- Approval queue and paper broker JSON writes are atomic for local file use, but they are still not a durable production database.
- S3PB technical hardening is complete-technical for local atomic storage, lifecycle/PID cleanup, and shutdown fault injection, but real uvicorn termination in this Windows workspace and production durability remain outside this evidence.
- Real broker live order submission remains intentionally out of scope.
- Strategy tournament is still fixture-level; it now has simple walk-forward/OOS metrics, but not multi-year OOS, cost-model, slippage-model, or walk-forward portfolio validation.
- Local `git push -u origin main` is blocked by missing HTTPS credentials (`could not read Username`); GitHub connector synced core runtime files, but older `docs/seed_pack/**` and `docs/task_pack_seed/**` still need a normal authenticated push or follow-up connector sync.

## Next Step

Resume only at `TASK-ALPHA-B-001` when production validation and execution-policy decisions are available; real-money live submission remains out of scope.
