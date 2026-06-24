# QuantLab Plans

## Current Delivery Focus

0. EVA_OS Main Entry: keep QuantLab as the operating entry while exposing the master-system identity, subsystem map, shared foundation, and launcher name.
0.1. Executive Command Center: aggregate readiness, integration, value ledger, latest report, risk gates, and action queue as the first daily entry.
1. Data Trust Layer: classify local evidence, source files, providers, strategies, experiments, and reports.
2. Entity Layer: unify holdings, symbols, proxies, reports, and validation targets into one derived registry.
3. Workflow Layer: make every chat/system input traceable through ResearchBus.
4. Report Layer: keep Word/PDF outputs tied to data quality, cross-source checks, cost assumptions, and risk gates.
4.1. Report Decision Support: classify each report as ContinueResearch, WatchOnly, NeedsMoreEvidence, or DoNotUse from RunMetadata evidence.
4.2. Report Evidence Gap Tasks: convert missing report evidence into deduped validation-queue tasks without running validation or mutating reports.
4.3. Validation Priority Plan: rank validation tasks by evidence value, blockers, and executable next action without mutating the queue.
4.4. Validation Task Execution: execute one prioritized validation task and write traceable Pass/Review/Blocked/Error evidence without mutating the queue.
5. Value Layer: register formal outputs into the EVA_OS Token ROI Ledger without fabricating financial value.

## Current Status

- Data Trust Layer is implemented as a read-only audit with JSON/CSV/Markdown/PDF outputs.
- Entity Layer now derives `QuantLabEntityRegistryV1`, classifies holdings as `TradableSymbol`, `ProxyMapped`, or `MissingSymbol`, writes JSON/CSV/Markdown artifacts, and does not mutate the holdings book.
- Workflow Layer now exposes `workflow_inputs_frame()`, syncs chat status with linked requests, keeps holding/trade candidates in `PendingReview`, rejects malformed API payloads, and preserves processed dropbox evidence on retry.
- Report Evidence Layer now writes `QuantLabReportEvidenceV1` into Word reports and RunMetadata JSON, including data quality, cross-source validation, entity status, workflow lineage, cost assumptions, risk gate status, decision quality status, and missing evidence downgrade policy.
- Final integration audit now checks Data Trust, Entity Registry, Workflow Inputs, Report Evidence, ResearchBus interoperability, and no-live-trading boundary together.
- Entity Registry artifacts now exist under `data/entityRegistry` and pass final integration audit.
- A new sample backtest report now writes `QuantLabReportEvidenceV1` into RunMetadata, and ReportEvidence passes final integration audit.
- ResearchBus interoperability now uses a read-only SQLite fallback for sandboxed directories and has a 10,000,000,000-row local worker-pool checksum evidence record; ResearchBusInterop passes final integration audit.
- Data Trust now passes with 145 local evidence records, no `NEEDS_REVIEW`, and no `REJECTED`; legacy experiment validation gaps are recorded as explicit `InsufficientData` rather than fabricated pass results.
- Current stabilization target is complete: final integration audit is `Pass` with `6 Pass / 0 Review / 0 Fail`.
- Daily Readiness now provides a read-only pre-use gate with JSON/Markdown/PDF outputs, summarizing core audit gates, provider setup, latest report, and action items.
- EVA_OS identity is now represented in code, docs, health checks, final acceptance checks, Streamlit page title, and macOS app launcher generation. The app bundle name is `EVA_OS.app`; the display name is `EVA_OS`.
- Token ROI Ledger MVP now scans `data/systemAudit` and the research report root, registers 140 local audit/report/metadata assets into JSON/CSV/Markdown/PDF outputs under `data/value`, and keeps all financial fields unquantified until real measured value is supplied.
- Executive Command Center MVP now appears as the first Streamlit page and writes JSON/Markdown/PDF snapshots under `data/commandCenter`, aggregating Daily Readiness, Integration Audit, Data Trust, Token ROI, latest reports, risk gates, and action queue.
- Report Decision Support Index now scans RunMetadata and linked Word reports, writes JSON/CSV/Markdown/PDF snapshots under `data/reportDecision`, and downgrades reports with missing evidence instead of overstating decision readiness.
- Report Evidence Gap Task Generator now converts `NeedsMoreEvidence` and `DoNotUse` report gaps into deduped tasks in `data/validationQueue/ValidationTasks.json`, while preserving existing tasks and not running validation.
- Validation Priority Plan now ranks the validation queue into `RunFirst`, `PrepareInputs`, `BatchValidate`, and `ManualReview` buckets, writes JSON/CSV/Markdown/PDF outputs, and does not mutate task status or queue data.
- Validation Task Execution now attempts the highest-priority `CrossSourceValidation` task, writes traceable execution artifacts, and records `Blocked` instead of fabricating a pass when fewer than two real providers are available.
- Next product target is deeper report decision support and real-data refresh reliability while keeping research-only boundaries.

## Execution Rules

- Keep QuantLab research-only.
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
- macOS launchers use `~/Desktop/EVA_OS.app`, `~/Downloads/EVA_OS.app`, and `/Applications/EVA_OS.app`.
- Token ROI Ledger outputs exist under `data/value` and do not fabricate `revenue_generated`, `cost_saved`, `loss_avoided`, `asset_reuse_value`, or `roi_score`.
- Executive Command Center outputs exist under `data/commandCenter`, default navigation opens `总控驾驶舱`, and status downgrades to `NeedsReview` or `Blocked` when evidence is incomplete.
- Report Decision Support outputs exist under `data/reportDecision`, Report Center exposes `证据索引`, and missing report evidence downgrades to `NeedsMoreEvidence` or `DoNotUse`.
- Report Evidence Gap Task outputs exist under `data/reportDecision`, Report Center can append missing-evidence validation tasks, repeated runs dedupe cleanly, and the generator never refreshes data or modifies reports.
- Validation Priority Plan outputs exist under `data/validationQueue`, Report Center exposes priority generation, and data-dependent tasks with missing symbol or market are routed to `PrepareInputs`.
- Validation Task Execution outputs exist under `data/validationQueue`, Report Center exposes execution, and blocked/provider-insufficient runs remain `NeedsMoreEvidence`.
