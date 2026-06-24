# Alpha Decision Log

## 2026-06-13: GitHub Is Authoritative

Decision: Use `https://github.com/LinzeColin/Alpha` as the authoritative project backup and continuity surface.

Reason: Future agents need a stable, inspectable state source for code, docs, tests, rules, and handoff.

Consequence: Every meaningful run must commit and push code/docs/test evidence unless blocked.

## 2026-06-13: Execution Boundary

Decision: Alpha will automate paper trading, risk checks, approval queues, and broker-ready order tickets. It will not autonomously submit real-money broker orders.

Reason: Trading systems must preserve owner control at the real-money execution boundary.

Consequence: Committed defaults keep `live_trading.enabled: false`; live candidates enter an approval queue as tickets.

## 2026-06-13: Five-Minute Candidate Refresh

Decision: The order-intent loop has a default refresh cadence of 300 seconds.

Reason: The user requires timely candidate updates while still keeping risk checks and review gates explicit.

Consequence: `paper_trading_loop.run_forever()` remains available for CLI use, and the FastAPI dashboard lifecycle starts an app-managed automatic paper loop that runs immediately and then sleeps for the configured interval.

## 2026-06-13: Ticket Freshness Is Actionability

Decision: Only unexpired `pending_owner_approval` tickets count as owner-actionable live candidates.

Reason: Broker-ready tickets can become stale; a candidate older than its TTL should remain auditable but should not be treated as executable.

Consequence: `ApprovalQueue.summary()` separates fresh pending, expired pending, blocked, and total tickets. The dashboard shows actionability, freshness, and seconds until expiry.

## 2026-06-13: App Bundle Entrypoints

Decision: Alpha should ship a macOS `.app` entrypoint in Downloads and Applications, backed by the same dashboard start script.

Reason: The user needs a stable local webpage workspace entry that behaves like a normal app instead of requiring terminal commands.

Consequence: `outputs/applications/Alpha.applescript` generates `Alpha.app`, and copies were installed to Downloads, user Applications, and system `/Applications`.

## 2026-06-13: Strategy Iteration Requires Walk-Forward Evidence

Decision: Strategy tournament candidates must expose simple out-of-sample evidence: walk-forward return, hit rate, and validation window count.

Reason: Last-window momentum ranking is too weak for strategy promotion. Even fixture-level MVP strategy iteration should show whether a signal had repeated one-step-ahead confirmation.

Consequence: `run_strategy_tournament()` now returns `validation_summary`, and each candidate includes `oos_return`, `hit_rate`, and `validation_windows`. The dashboard tournament table displays these fields.

## 2026-06-24: Persisted Paper State Requires Locked Atomic Writes

Decision: ApprovalQueue and PaperBroker persisted JSON updates must run through a shared lock and atomic temp-file replace rather than direct read-modify-write.

Reason: Concurrent manual and automatic paper-loop actions can otherwise overwrite queue tickets or paper portfolio state.

Consequence: S3PBT01 adds `atomic_json_store`, `ApprovalQueue.enqueue` transactions, `PaperBroker.submit_order_to_path`, and paper-loop persisted-state integration. Shutdown, cancellation, PID cleanup, and live broker readiness remain out of scope.

## 2026-06-24: Runtime Stop Must Preserve Lifecycle Truth

Decision: `AutoPaperAgentRuntime.stop()` must wait for the current paper cycle to drain before reporting `stopped`, and must report `stop_timeout` with `task_running=true` if a cycle remains active after the timeout.

Reason: Cancelling an `asyncio.to_thread()` wait cannot stop the underlying Python worker thread, so claiming `stopped` on timeout can hide writes that are still in progress.

Consequence: S3PBT02 records stopping state, last stopped time, and timeout count in the runtime snapshot. Dashboard start/stop scripts keep PID files until process exit is confirmed, escalating TERM to KILL only after a bounded wait.
