# PFIOS Plans

## PFI-001 Active Transition Plan

Current approved direction: controlled migration from legacy `PFI_OS` /
`PFIOS` to `PFI OS`.

PFI-001 through PFI-004 are complete. Phase A data foundation and the first
Phase B vertical workflows are complete. Phase C now has the cached workflow
runtime read model, local scheduler/retry/60-second acceptance slice, and
Web Shell workflow-card rendering implemented and covered by focused tests.
Phase D local deployment readiness now has its first read-only contract slice.

Execution order:

1. `PFI-001`: write product contracts and contract tests. Complete.
2. `PFI-002`: remove retired value-ledger and non-core active entrances without deleting user runtime data. Complete.
3. `PFI-003`: migrate identity, directory, namespace, env vars, scripts, app names, and artifact prefixes to PFI. Complete.
4. `PFI-004`: create the new PFI Web Shell with six workspaces, global context, task center, evidence drawer, and consistent feedback. Complete.
5. `Phase A`: establish the local operational store and migrate read models slice by slice. Complete for the data-boundary gate.
6. `Phase B`: promote Strategy Lab, Markets, Research + Policy, and Portfolio into Operational Store-backed vertical workflow contracts. Complete for the first four vertical slices.
7. `Phase C`: promote Phase B workflows into cached runtime cards, scheduler jobs, retry/backoff, 60-second local cache acceptance, and Web Shell workflow-card rendering. Active.
8. `Phase D`: establish local deployment, backup/restore, and local-model readiness contracts. Active.

Current PFI decisions:

- PFI OS is the target product; PFI_OS is legacy input.
- Primary navigation is fixed to six workspaces: 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统.
- Strategy backtesting is a core workflow, not a legacy side page.
- Market-feel training is retained as `策略实验室 -> 训练模式`.
- ResearchBus becomes an internal event/workflow compatibility layer, not a second user-facing product or fact source.
- PFI OS remains research-only and human-reviewed; no autonomous live trading, payments, betting, or broker order submission.
- The current development record, open backlog, key file map, and parameter
  contracts live in `docs/development/PFI_PHASE_0_TO_A_RECORD.md`.

## Current Delivery Focus

0. PFI_OS Main Entry: keep PFIOS as the operating entry while exposing the master-system identity, subsystem map, shared foundation, and launcher name.
0.1. Executive Command Center: aggregate readiness, integration, business runtime summaries, latest report, risk gates, and action queue as the first daily entry.
1. Data Trust Layer: classify local evidence, source files, providers, strategies, experiments, and reports.
2. Entity Layer: unify holdings, symbols, proxies, reports, and validation targets into one derived registry.
3. Workflow Layer: make every chat/system input traceable through ResearchBus.
4. Report Layer: keep Word/PDF outputs tied to data quality, cross-source checks, cost assumptions, and risk gates.
4.1. Report Decision Support: classify each report as ContinueResearch, WatchOnly, NeedsMoreEvidence, or DoNotUse from RunMetadata evidence.
4.2. Report Evidence Gap Tasks: convert missing report evidence into deduped validation-queue tasks without running validation or mutating reports.
4.3. Validation Priority Plan: rank validation tasks by evidence value, blockers, and executable next action without mutating the queue.
4.4. Validation Task Execution: execute one prioritized validation task and write traceable Pass/Review/Blocked/Error evidence without mutating the queue.

## Current Status

- Data Trust Layer is implemented as a read-only audit with JSON/CSV/Markdown/PDF outputs.
- Entity Layer now derives `PFIOSEntityRegistryV1`, classifies holdings as `TradableSymbol`, `ProxyMapped`, or `MissingSymbol`, writes JSON/CSV/Markdown artifacts, and does not mutate the holdings book.
- Workflow Layer now exposes `workflow_inputs_frame()`, syncs chat status with linked requests, keeps holding/trade candidates in `PendingReview`, rejects malformed API payloads, and preserves processed dropbox evidence on retry.
- Report Evidence Layer now writes `PFIOSReportEvidenceV1` into Word reports and RunMetadata JSON, including data quality, cross-source validation, entity status, workflow lineage, cost assumptions, risk gate status, decision quality status, and missing evidence downgrade policy.
- Final integration audit now checks Data Trust, Entity Registry, Workflow Inputs, Report Evidence, ResearchBus interoperability, and no-live-trading boundary together.
- Entity Registry artifacts now exist under `data/entityRegistry` and pass final integration audit.
- A new sample backtest report now writes `PFIOSReportEvidenceV1` into RunMetadata, and ReportEvidence passes final integration audit.
- ResearchBus interoperability now uses a read-only SQLite fallback for sandboxed directories and has a 10,000,000,000-row local worker-pool checksum evidence record; ResearchBusInterop passes final integration audit.
- Data Trust now passes with 145 local evidence records, no `NEEDS_REVIEW`, and no `REJECTED`; legacy experiment validation gaps are recorded as explicit `InsufficientData` rather than fabricated pass results.
- Current stabilization target is complete: final integration audit is `Pass` with `6 Pass / 0 Review / 0 Fail`.
- Daily Readiness now provides a read-only pre-use gate with JSON/Markdown/PDF outputs, summarizing core audit gates, provider setup, latest report, and action items.
- PFI_OS identity is now represented in code, docs, health checks, final acceptance checks, Streamlit page title, and macOS app launcher generation. The app bundle name is `PFI_OS.app`; the display name is `PFI_OS`.
- Report Decision Support Index now scans RunMetadata and linked Word reports, writes JSON/CSV/Markdown/PDF snapshots under `data/reportDecision`, and downgrades reports with missing evidence instead of overstating decision readiness.
- Report Evidence Gap Task Generator now converts `NeedsMoreEvidence` and `DoNotUse` report gaps into deduped tasks in `data/validationQueue/ValidationTasks.json`, while preserving existing tasks and not running validation.
- Validation Priority Plan now ranks the validation queue into `RunFirst`, `PrepareInputs`, `BatchValidate`, and `ManualReview` buckets, writes JSON/CSV/Markdown/PDF outputs, and does not mutate task status or queue data.
- Validation Task Execution now attempts the highest-priority `CrossSourceValidation` task, writes traceable execution artifacts, and records `Blocked` instead of fabricating a pass when fewer than two real providers are available.
- Phase C workflow runtime now promotes the four Phase B workflow records into cached cards, task-center rows, background-job rows, Fast Path metadata, and private-safe Operational Store runtime evidence.
- Phase C scheduler now writes idempotent local cache-refresh jobs, executes cached runtime refreshes, records 60-second acceptance metadata, retries with bounded `[1, 5, 15]` backoff, and fails closed after exhausted attempts without provider, broker, LLM, network, order-execution, or holding-mutation dependencies.
- Phase C Web Shell now renders workflow cards from cached runtime JSON, updates the Fast Path badge, opens private-safe evidence drawer payloads, and keeps loading/error states hidden until user action.
- Phase D deployment readiness now checks required repo surfaces, data-home/Operational SQLite boundaries, backup/restore path plans, and DisabledProvider/local-model optionality without creating directories, starting services, or probing networks.
- Next product target is Phase D backup/restore acceptance and Phase 5 packaging while keeping research-only boundaries.

## Execution Rules

- Keep PFIOS research-only.
- Do not connect to live trading.
- Do not place real orders.
- Do not overwrite holdings from empty or unconfirmed sources.
- Treat OCR, videos, chat inputs, and imported files as candidates until confirmed or reconciled.
- Prefer one independently testable change per run.

## Current Acceptance Checks

- Full test suite passes.
- Data Trust audit has no `NEEDS_REVIEW` or `REJECTED` records.
- Final integration audit passes all six layers.
- Daily Readiness returns `ReadyForResearch` or clear review/blocking action items before daily use.
- Real-data conclusions cite provider, date range, quality checks, and limitations.
- Cross-system changes update ResearchBus documentation or handoff notes.
- macOS launchers use `~/Desktop/PFI_OS.app`, `~/Downloads/PFI_OS.app`, and `/Applications/PFI_OS.app`.
- Executive Command Center outputs exist under `data/commandCenter`, default navigation opens `总控驾驶舱`, and status downgrades to `NeedsReview` or `Blocked` when evidence is incomplete.
- Report Decision Support outputs exist under `data/reportDecision`, Report Center exposes `证据索引`, and missing report evidence downgrades to `NeedsMoreEvidence` or `DoNotUse`.
- Report Evidence Gap Task outputs exist under `data/reportDecision`, Report Center can append missing-evidence validation tasks, repeated runs dedupe cleanly, and the generator never refreshes data or modifies reports.
- Validation Priority Plan outputs exist under `data/validationQueue`, Report Center exposes priority generation, and data-dependent tasks with missing symbol or market are routed to `PrepareInputs`.
- Validation Task Execution outputs exist under `data/validationQueue`, Report Center exposes execution, and blocked/provider-insufficient runs remain `NeedsMoreEvidence`.
