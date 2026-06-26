# PFIOS Codex Task Pack

## Objective

Upgrade PFIOS into the PFI_OS mother-system entry and validation layer for personal investment research while preserving independent subsystem operation.

## Current Scope

- Data Trust audit.
- Entity registry.
- ResearchBus interoperability.
- Report and evidence traceability.

## Non-Goals

- No live trading.
- No real order placement.
- No account password storage.
- No fabricated market data.

## Next Task

Move from daily readiness to deeper report decision support and real-data refresh reliability.

Acceptance:

- Keep final integration audit at `Pass`.
- Keep Data Trust audit with no `NEEDS_REVIEW` or `REJECTED` records.
- Keep Daily Readiness available as a read-only pre-use gate with JSON/Markdown/PDF outputs.
- Keep no-live-trading boundary as Pass.
- Do not convert `InsufficientData` validation placeholders into positive strategy evidence.

## Completed This Run

Entity Registry now derives `TradableSymbol`, `ProxyMapped`, and `MissingSymbol` records from holdings without mutating the holdings book. It can export JSON, CSV, and Markdown artifacts under `data/entityRegistry`.

Workflow Layer now exposes a read-only `workflow_inputs_frame()` across chat inputs and direct API requests, syncs chat status with linked request status, keeps holding/trade candidates in `PendingReview`, rejects malformed API payloads, and preserves processed dropbox files on retries.

Report Evidence Layer now writes `PFIOSReportEvidenceV1` into Word reports and RunMetadata JSON, including data quality, cross-source validation, entity status, workflow lineage, cost assumptions, risk gate status, decision quality status, and missing evidence downgrade policy.

Final integration audit now exists as `scripts/auditPFIIntegration.sh --no-write`; current actual project smoke returns `Review` with no `Fail` after read-only SQLite compatibility fixes.

Entity Registry artifacts have now been generated from confirmed holdings under `data/entityRegistry`; the final integration audit reports EntityRegistry as `Pass`.

At least one new backtest report has now been generated with `PFIOSReportEvidenceV1` in RunMetadata; the final integration audit reports ReportEvidence as `Pass`.

ResearchBus SQLite read-only access now falls back to immutable mode after a sandboxed read probe failure, and a 10,000,000,000-row local worker-pool checksum run has been recorded. The final integration audit reports ResearchBusInterop as `Pass`.

Data Trust now passes with 145 records. Stale empty lock files are classified as archived run residue, a strategy-change confirmation policy is recorded, and legacy experiment validation gaps are explicitly captured as `InsufficientData` instead of being fabricated as successful out-of-sample or walk-forward validation.

Final integration audit now reports `Pass` with `6 Pass / 0 Review / 0 Fail`.

Daily Readiness now reports `ReadyForResearch` for the current local state and writes `PFIOSDailyReadiness_07062026.json`, `.md`, and `.pdf` under `data/systemAudit`. It is read-only and does not refresh market data, start OpenD, mutate holdings, open Streamlit, or place orders.

PFI_OS identity is now the user-facing master-system entry. The generated macOS app bundle is `PFI_OS.app`, the display name is `PFI_OS`, and PFIOS remains the embedded quantitative research subsystem.



Report Decision Support Index is now implemented as the Report Layer decision-readiness audit. It scans RunMetadata and linked Word reports, classifies each report as `ContinueResearch`, `WatchOnly`, `NeedsMoreEvidence`, or `DoNotUse`, and writes `data/reportDecision/ReportDecisionSupportIndex_*` JSON/CSV/Markdown/PDF outputs.

Report Evidence Gap Task Generator is now implemented. It reads report decision support gaps, creates deduped validation tasks for data quality, cross-source validation, risk gate, parameter stability, train/test, walk-forward and report evidence gaps, writes `data/reportDecision/ReportEvidenceGapTasks_*` outputs, and appends only new tasks to `data/validationQueue/ValidationTasks.json`.

Validation Priority Plan is now implemented. It reads `data/validationQueue/ValidationTasks.json`, ranks tasks into `RunFirst`, `PrepareInputs`, `BatchValidate`, `ManualReview`, `Paused`, and `Completed`, writes `data/validationQueue/ValidationTaskPriorityPlan_*` JSON/CSV/Markdown/PDF outputs, and does not mutate the original queue.

Validation Task Execution is now implemented. It executes the top-priority `CrossSourceValidation` task, writes `data/validationQueue/ValidationTaskExecution_*` JSON/CSV/Markdown/PDF outputs, saves underlying `CrossValidation_*` evidence when validation runs, and records `Blocked` when fewer than two real providers are available.
