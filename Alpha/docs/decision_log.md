# Alpha Decision Log

## 2026-06-13: GitHub Is Authoritative

Decision: Superseded on 2026-06-27. Use `https://github.com/LinzeColin/CodexProject`, project path `Alpha/`, as the authoritative project backup and continuity surface.

Reason: Future agents need a stable, inspectable state source for code, docs, tests, rules, and handoff.

Consequence: Every meaningful run must commit and push code/docs/test evidence through `LinzeColin/CodexProject/Alpha` unless blocked. Standalone `LinzeColin/Alpha` and old local shadow folders are not authoritative delivery roots.

## 2026-06-27: Phase 6 Owner Gate Evidence Must Be Canonical

Decision: Alpha G6 Phase 6 evidence must be generated from the canonical `CodexProject/Alpha` root and must not be inferred from older shadow folders.

Reason: The current canonical dashboard is in research/paper order-intent review mode with live trading disabled. Older local shadow outputs are not a safe source for owner-gate claims.

Consequence: Phase 6 remains blocked until canonical evidence proves 48-hour Paper/Shadow soak, a qualified trading-day report, Shadow live constraints, limit-order contract, and closeout readiness. `runtime/LIVE_AUTHORIZATION.json` must remain absent.

## 2026-06-27: OWNER_DECISION Must Be Evidence-Generated

Decision: `docs/evidence/phase6_closeout_latest/OWNER_DECISION.md` is generated from the same Phase 6 closeout, soak, Paper/Shadow, and Shadow live constraint evidence used for `phase6_closeout.json`.

Reason: OWNER-GATE-01 is an owner decision surface. It must not drift from machine-readable evidence or manually imply readiness before the 48-hour soak is proven.

Consequence: Running `scripts/build_phase6_owner_gate_evidence.py` refreshes both JSON evidence and the human-readable A/B/C owner decision file. Until `phase6_closeout.json` reports `ready_for_owner_gate`, option A remains a continue-evidence path, not MICRO_LIVE authorization.

## 2026-06-27: Phase 6 Closeout Report Must Map Acceptance To Evidence

Decision: `docs/evidence/phase6_closeout_latest/PHASE6_CLOSEOUT_REPORT.md` is generated from the same Phase 6 evidence set and must map every OWNER-GATE acceptance item to a concrete evidence file and current status.

Reason: The owner needs a human-readable closeout report, not only raw JSON, and future agents must not infer completion from partial evidence.

Consequence: Running `scripts/build_phase6_owner_gate_evidence.py` refreshes the closeout report alongside JSON evidence and `OWNER_DECISION.md`. The report must continue to state that Alpha is not ready when 48-hour natural-day soak coverage is incomplete.

## 2026-06-27: Phase 6 Evidence Manifest Must Hash Required Artifacts

Decision: `docs/evidence/phase6_closeout_latest/EVIDENCE_MANIFEST.json` is generated with every Phase 6 OWNER-GATE evidence build and records required artifact presence, SHA-256 hashes, acceptance status, soak progress, and live authorization absence.

Reason: OWNER-GATE handoff needs a machine-checkable package index so future agents can verify evidence integrity without guessing from filenames or partial reports.

Consequence: Missing artifacts, changed hashes, incomplete soak coverage, or a present `runtime/LIVE_AUTHORIZATION.json` must remain visible before owner review. The manifest does not promote Alpha to MICRO_LIVE.

## 2026-06-27: Phase 6 Evidence Package Verification Is Separate From Readiness

Decision: `scripts/verify_phase6_evidence_package.py` and `docs/evidence/phase6_closeout_latest/EVIDENCE_PACKAGE_VERIFICATION.json` verify package integrity independently from OWNER-GATE readiness.

Reason: Alpha needs to distinguish "all evidence artifacts are present and internally consistent" from "48-hour soak is complete and closeout is ready." These are related but not identical gates.

Consequence: The verifier can pass package integrity while still reporting `owner_gate_status=blocked_not_ready_for_owner_gate`. Running it with `--require-ready` must fail until `phase6_closeout.json` is truly `ready_for_owner_gate`.

## 2026-06-27: Phase 6 Soak Evidence Must Show Observation Window

Decision: `soak_validation_latest.json` records `window_start` and `window_end` from the first and latest accepted Paper/Shadow samples.

Reason: OWNER-GATE review needs the concrete observed time window, not only elapsed hours, so the 48-hour natural-day claim can be inspected without reconstructing JSONL history.

Consequence: Runtime and committed evidence can remain `blocked_not_ready_for_owner_gate` while still showing exactly how much of the 48-hour observation window has accrued.

## 2026-06-27: Phase 6 Status Must Detect Stale Sampler Evidence

Decision: `scripts/check_phase6_owner_gate_status.py` reports latest sampler sample age and supports `--require-fresh` as a read-only watchdog gate.

Reason: During the 48-hour natural-day soak, Alpha must detect a stopped or stale sampler before the owner relies on incomplete observation evidence.

Consequence: Freshness monitoring can fail independently from OWNER-GATE readiness. It does not create `runtime/LIVE_AUTHORIZATION.json`, does not submit broker orders, and does not promote Alpha to MICRO_LIVE.

## 2026-06-27: Phase 6 Soak Uses Continuous Window Coverage

Decision: `build_soak_validation_report` measures the current continuous Paper/Shadow observation window and resets the 48-hour clock after stale sample gaps.

Reason: A first-to-last timestamp span can overstate real observation if the sampler stopped for a long interval. OWNER-GATE needs proof of continuous natural-day observation, not only elapsed wall-clock distance.

Consequence: Historical gap violations remain visible in evidence, but readiness depends on a fresh continuous window reaching 48 hours with passing Paper/Shadow and Shadow live constraints.

## 2026-06-27: Dashboard Shows Phase 6 OWNER-GATE Read-Only Status

Decision: `/dashboard/state` and the dashboard page expose the same Phase 6 OWNER-GATE status report used by the CLI checker.

Reason: The owner must be able to see current blocker, continuous observation window, sampler freshness, Paper/Shadow status, Shadow live constraints, and live authorization absence without reading raw JSON files.

Consequence: Dashboard visibility is read-only. It does not create `runtime/LIVE_AUTHORIZATION.json`, does not submit broker orders, and does not promote Alpha to MICRO_LIVE or OWNER-GATE readiness.

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

## 2026-06-24: Shutdown Faults Must Preserve Local State And PID Truth

Decision: Atomic JSON writes must preserve the previous committed target on replace failure or forced writer termination, `AutoPaperAgentRuntime.stop()` must produce no further writes after it reports stopped, and dashboard lifecycle scripts must verify that a PID belongs to the Alpha uvicorn process before trusting or terminating it.

Reason: S3PB must preserve governance truth during failures: a stale PID that points to an unrelated process is not dashboard evidence, and a failed local write must not corrupt paper queue or broker state.

Consequence: S3PBT03 adds shutdown fault-injection tests for disk-error preservation, forced termination before replace, no write after stopped, reused PID archiving, and start script dashboard identity checks. This closes the S3PB technical fault-injection gate without enabling live broker execution or production readiness.

## 2026-06-27: Phase 6 Runtime Evidence Must Be Published To Docs Evidence

Decision: `scripts/publish_phase6_owner_gate_evidence.py` publishes the current read-only Phase 6 runtime evidence into `docs/evidence/phase6_closeout_latest` without running a paper cycle, appending soak history, creating `LIVE_AUTHORIZATION.json`, or touching any broker mutation path.

Reason: The LaunchAgent sampler must keep high-frequency runtime evidence local, while GitHub handoff and OWNER-GATE-01 review need a committed docs evidence package that can be refreshed from runtime state on demand.

Consequence: `docs/evidence/phase6_closeout_latest` can be refreshed as the canonical owner decision package whenever the soak window progresses. Package verification may pass while OWNER-GATE readiness still remains blocked by `phase6_48h_soak_validation`.

## 2026-06-27: Phase 6 Soak Evidence Exposes Remaining Time And ETA

Decision: Phase 6 soak validation, owner-gate status, evidence manifest, OWNER_DECISION, closeout report, and dashboard now expose `remaining_seconds`, `remaining_hours`, and `estimated_ready_at`.

Reason: OWNER-GATE reviewers and follow-on agents need a concrete human-readable estimate for the 48-hour natural-day observation window instead of manually subtracting timestamps from JSONL history.

Consequence: ETA improves progress visibility only. It does not mark Phase 6 ready, bypass sample freshness, override gap resets, create live authorization, or change any broker execution path.

## 2026-06-27: Phase 6 Finalize Is A Read-Only Ready Gate

Decision: `scripts/finalize_phase6_owner_gate_if_ready.py` is the one-command Phase 6 closeout gate: it publishes runtime evidence into docs evidence, runs `require_ready` verification, and returns `ready_for_owner_gate` only when the full evidence package satisfies OWNER-GATE-01.

Reason: After the natural 48-hour soak window completes, a follow-on agent needs a deterministic finalization command that cannot silently convert partial evidence into readiness.

Consequence: Before 48 hours, the command returns `not_ready_for_owner_gate` with `phase6_48h_soak_validation` as the blocker and writes `docs/evidence/phase6_closeout_latest/FINALIZE_STATUS.json` as the latest fixed closeout-attempt status. It does not create `runtime/LIVE_AUTHORIZATION.json`, enable live trading, run a broker mutation, or enter MICRO_LIVE.
