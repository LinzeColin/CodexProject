# DEVELOPMENT_LEDGER

Project: `Serenity-Alipay`
Product version: `0.1.0`
Governance spec version: `1.0.0`

This ledger is human-readable. The append-only machine event stream is
`development_events.jsonl`.

## Current State

- Product version: `0.1.0`
- Product version status: `provisional`
- Current phase: `CF-L2`
- Current gate: `ACC-CF-L2-20260710-PASSED`
- Confirmed iteration count: 4
- Reconstructed development event count: 2
- Current task: `CF-L2-20260710` completed; existing semantic and S3PCT03 evidence remains preserved.
- Blockers: empirical calibration, live OpenD/email/trading readiness, and owner production-readiness approval remain unresolved; S3PCT03 is lifecycle-contract evidence only.

machine_summary:

- model_count: 5
- formula_count: 12
- parameter_count: 50
- task_count: 10

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Discovery and baseline | completed | Governance files exist and validator passes for Serenity-Alipay | `ITER-20260621-001` |
| B | Model and data specification | in_progress | Calibration, sensitivity, and semantic extractor gaps are closed or explicitly deferred | `TASK-B-001`, `TASK-B-002`, `TASK-B-003` |
| C | Implementation | planned | Future behavior changes update governance in the same run | `TASK-C-001` |
| D | Verification and hardening | ready | Focused model tests and governance validator pass | `TASK-D-001` |
| E | Delivery and operation | planned | CI required mode can be enabled without advisory drift | `TASK-E-001` |

## Confirmed Iterations

Do not infer iteration count from Git commit count.

### `ITER-20260629-SERENITY-MAIL-FREQUENCY`

- Date: 2026-06-29
- Fact level: VERIFIED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `b4a97ff2`
- Result commit: `PENDING`
- Task IDs: `SERENITY-MAIL-FREQUENCY-CONTROL`
- Goal: stop repeated production actionable emails by comparing the current action conclusion with the last successfully sent actionable email and enforcing a Beijing-day cap.
- Assumptions: action conclusion identity must be based on action fields only, not run id, run time, source timestamps, or ordinary evidence prose.
- Files read: `app/core/mail_policy.py`, `app/core/notification.py`, `app/core/pipeline.py`, `app/db.py`, `tests/test_notification.py`, and current `HANDOFF.md`.
- Files changed: mail policy, notification sender, pipeline sender, notification_log schema migration, notification regression tests, changelog, handoff, bug regression log, feature list, model spec, and rendered development record.
- Model changes: no candidate scoring, ranking, allocation, risk gate, benchmark, scheduler slot, or trading model behavior changed.
- Parameter changes: no active PARAM-001 through PARAM-049 value changed; runtime notification safety constants are documented as post-baseline mail-suppression controls.
- Commands run: `py_compile` for edited runtime/test files; focused pytest set for notification, integration, automation tick, Serenity priority, and OpenD lifecycle.
- Test results: `tests/test_notification.py` first failed against old behavior for duplicate and daily-cap cases; after implementation, focused set passed with 22 tests.
- Successes: duplicate actionable signature suppresses across slots and days, third Beijing-day actionable mail suppresses, maintain/info outcomes suppress, and suppressed rows retain audit fields in `notification_log`.
- Failures: none after implementation. Initial root-cwd notification pytest failed because sample data expects project cwd; rerunning from `Serenity-Alipay` cwd passed.
- Decisions: keep email frequency as an action-conclusion policy; reports, homepage data, and database rows continue updating every run even when mail is suppressed.
- Remaining risks: real Apple Mail delivery remains dependent on local macOS Mail automation and credentials; this task validates policy and logging, not external provider uptime.
- Rollback: revert the mail policy, notification/pipeline sender changes, schema columns, and focused notification tests together.
- Next step: observe the next production actionable run and verify `notification_log.suppress_reason` values match the policy before considering real-mail noise fully closed.

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: no `VERSION` file; `pyproject.toml` declared `0.1.0`
- Version after: `0.1.0`
- Base commit: `9516776`
- Result commit: `PENDING`
- Task IDs: `GOV-G3-SERENITY-MIGRATE-001`, `TASK-A-001`
- Goal: create the first CodexProject-auditable Serenity-Alipay governance baseline without changing scoring, ranking, gate, parameter, data, or business behavior.
- Assumptions: use only current code, tests, README, HANDOFF, old governance entry files, small manual CSV headers/samples, and limited Git history.
- Files read: root governance standard, root project registry, Serenity README, HANDOFF, old governance files, `app/core/scoring.py`, `app/core/pipeline.py`, `app/core/metrics.py`, `app/core/comparison.py`, `app/core/discipline.py`, `app/scheduler.py`, focused tests.
- Files changed: Serenity governance docs, `VERSION`, `CHANGELOG.md`, README governance entry, and old governance entry indexes.
- Model changes: no runtime model change; governance IDs assigned to current behavior.
- Parameter changes: no active parameter value change; current constants were registered as PARAM-001 through PARAM-049.
- Commands run: validation is recorded in the final run report.
- Test results: pending at the time this ledger entry was created.
- Successes: scoring, ranking, MDD, recovery, Top5, comparison, discipline, and schedule rules are traceable to code and tests.
- Failures: none recorded before validation.
- Decisions: old `模型参数文件`, `开发记录`, and `功能清单` become indexes into `docs/governance/`.
- Remaining risks: empirical calibration and sensitivity evidence are not proven; see `TASK-B-001` and `TASK-B-002`.
- Rollback: remove `docs/governance/` and restore edited Serenity root files from pre-run state.
- Next step: `GOV-G3-SERENITY-VERIFY-001`.

### `ITER-20260621-002`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `ef0ee041325f3c2cfb19e0e9f81c99e95a43c96b`
- Result commit: `PENDING`
- Task IDs: `GOV-REVIEW6-B-SERENITY-SEMANTIC-EXTRACT-001`, `TASK-B-003`
- Goal: add a machine-verifiable Serenity semantic extraction pilot without changing scoring, ranking, gate, parameter, data, or business behavior.
- Assumptions: Python AST and bounded text-regex selectors are sufficient to verify the current Serenity active parameters and formula implementation symbols.
- Files read: root governance standard, root project registry, Serenity governance files, `app/config.py`, `app/core/scoring.py`, `app/core/pipeline.py`, `app/core/metrics.py`, `app/core/comparison.py`, `app/core/discipline.py`, `app/scheduler.py`, `app/core/scheduler_runner.py`, `app/core/automation_tick.py`, and focused tests.
- Files changed: Serenity governance registries, delivery records, version matrix, changelog, root semantic validator, root standard/templates, and governance tests.
- Model changes: no runtime model change; active formula implementation fingerprints are recorded for FORM-001 through FORM-012.
- Parameter changes: no active parameter value change; PARAM-001 through PARAM-049 now include machine source selectors, extracted values, verification commit/time, and evidence hashes.
- Commands run: `python3 scripts/validate_semantic_extractors.py Serenity-Alipay`; `python3 scripts/validate_project_governance.py --project Serenity-Alipay --semantic`; `python3 scripts/validate_project_governance.py --all --semantic --drift-report`; `python3 -m pytest tests/governance -q`; `python3 -m py_compile scripts/validate_project_governance.py scripts/validate_governance_sync.py scripts/validate_semantic_extractors.py`; `cd Serenity-Alipay && PYTHONPATH=. python3 -m pytest -q tests/test_scoring.py tests/test_pipeline_serenity_priority.py tests/test_risk_gate_regression.py tests/test_metrics.py tests/test_discipline.py tests/test_comparison.py tests/test_scheduler.py tests/test_timezones.py`.
- Test results: semantic extractor PASS with 49 parameters and 12 formulas checked; Serenity semantic validator PASS with errors 0 warnings 0; full semantic validator PASS with errors 0 warnings 0; governance tests PASS with 28 passed; py_compile PASS; focused Serenity tests PASS with 22 passed from project cwd.
- Successes: registry active values now fail validation when they diverge from extractable code defaults/literals; formula implementation symbols now fail validation when AST fingerprints drift.
- Failures: FORM-008 semantic check proves final post-renormalization weights can exceed the 0.30 cap for 1, 2, 3, and 4 candidate scenarios; current business tests cover only the 5-candidate target-weight scenario. A root-cwd focused pytest invocation failed because scheduler tests expect `Path.cwd()` to be `Serenity-Alipay`; rerunning the same focused set from project cwd passed.
- Decisions: record FORM-008 caveat as machine-observed governance evidence and defer algorithm or business-test changes to a separate non-governance-behavior task.
- Remaining risks: semantic extractor coverage is a Serenity pilot; other projects remain structurally governed until separately migrated.
- Rollback: revert this iteration's governance metadata, root semantic extractor, root standard/template updates, tests, and run manifest together.
- Next step: `GOV-REVIEW6-C-OWNER-STATUS-001`.

### `ITER-20260624-SERENITY-S3PCT03`

- Date: 2026-06-24
- Fact level: VERIFIED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `4319f9b7999e65ec955ead5f3394fa103fcef508`
- Result commit: `PENDING`
- Task IDs: `S3PCT03`, `ACC-S3PCT03`
- Goal: verify Serenity OpenD auto-wake ownership, delivery package atomicity, launchd tick wrapper behavior, and close-cleanup contracts without real external side effects.
- Assumptions: mocked socket/workbench/process state and temporary package directories are sufficient for lifecycle-contract proof; they do not prove live OpenD, email, trading, empirical calibration, or production readiness.
- Files read: `app/core/moomoo_lifecycle.py`, `app/core/packaging.py`, `scripts/serenity_launchd_tick.sh`, existing OpenD/package tests, and Other8 S3PC evidence patterns.
- Files changed: S3PCT03 lifecycle unittest, S3PC evidence files, Serenity governance docs, PARAM-027 through PARAM-032 selector evidence rebind, rendered `开发记录`, root governance manifest test, and run manifest.
- Model changes: no scoring, ranking, gate, scheduler, or investment model behavior changed.
- Parameter changes: no active parameter value changed; PARAM-027 through PARAM-032 source selectors/evidence hashes were re-bound to the current `pipeline.py` line layout.
- Commands run: bundled-python S3PCT03 unittest, py_compile for the new test, roadmap pytest command, rendered governance checks, semantic extractor validation, root governance test, and changed-only governance validation.
- Test results: lifecycle unittest exit 0 with 4 tests OK; py_compile exit 0; roadmap pytest command blocked locally by missing pytest; remaining validation recorded in the S3PCT03 manifest.
- Successes: mocked tool-owned OpenD cleanup terminates only the recorded process, user-owned OpenD is not killed, failed package build preserves the previous zip and cleans temp files, and launchd tick wrapper records child status while exiting 0.
- Failures: pytest is not installed in the bundled runtime, so the roadmap pytest command remains blocked locally.
- Decisions: keep all lifecycle evidence mocked or temporary; do not start live OpenD, send mail, place trades, or touch production data/package paths.
- Remaining risks: empirical calibration, live OpenD readiness, real email delivery, trading readiness, owner production approval, and delivery readiness remain unresolved.
- Rollback: revert S3PCT03 test, stage-gate evidence, Serenity governance docs, rendered human entry files, root governance manifest test, and run manifest.
- Next step: continue S3PD tasks and do not close S3PC/S3 until remaining dependent tasks are completed.

## Reconstructed Development Events

- `EVENT-RECON-20260612-001`: MVP scoring, dry-run automation, OpenD/MooMoo lifecycle, and local-first safety behavior reconstructed from `HANDOFF.md` and current tests. Fact level: RECONSTRUCTED.
- `EVENT-RECON-20260614-001`: delivery package, app entry, history-integrity, and production-readiness evidence reconstructed from `HANDOFF.md`. Fact level: RECONSTRUCTED.

## Unknown Historical Periods

- Exact iteration boundaries before `ITER-20260621-001` are UNKNOWN and are not inferred from Git commit count.
- Exact stdout for every historical test command in `HANDOFF.md` is not fully re-executed by this governance migration.
- Remote `LinzeColin/Serenity-Alipay` main HEAD mentioned in `HANDOFF.md` is not verified in this run.

## Validation History

| Command | Result | Evidence |
|---|---|---|
| `python scripts/validate_project_governance.py --project Serenity-Alipay` | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 scripts/validate_project_governance.py --project Serenity-Alipay` | PASS | exit 0; errors 0, warnings 0 |
| `python scripts/validate_project_governance.py --all` | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 scripts/validate_project_governance.py --all` | PASS_WITH_EXTERNAL_WARNINGS | exit 0; warnings 5 from EEI only |
| `python -m pytest` focused Serenity tests | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 -m pytest` focused Serenity tests | PASS | exit 0; 20 passed |
| `git diff --check` | PASS | exit 0 |

## ITER-20260710-SERENITY-CF-L2

- Date: 2026-07-10
- Fact level: VERIFIED for local build, scan, compatibility tests, responsive rendering, dry-run, permanent workers.dev deployment and HTTP checks.
- Version before/after: `0.1.0` / `0.1.0`.
- Task / Acceptance: `CF-L2-20260710` / `ACC-CF-L2-20260710`.
- Goal: add an isolated read-only public cockpit with a hard boundary against Alipay, MooMoo/OpenD, Apple Mail, notifications, trades, launchd, and external accounts.
- Result: static build, 13 compatibility tests, private dist scan, desktop/mobile QA and Wrangler 4.110.0 dry-run passed; permanent deployment `bf27bdbc-c199-4e39-9009-8250ae2eb7df` is live at `https://serenity-alipay.linzezhang35.workers.dev`, with root and `public-surface.json` HTTP 200.
- Model and parameter boundary: no scoring, ranking, risk gate, scheduler, account, mail, notification, or trading behavior changed; `PARAM-050` only records the public adapter compatibility contract.
- Rollback: remove `app/cloudflare-public` and this bounded governance slice; the private Serenity runtime remains unchanged.
- Next gate: optional `serenity.linzezhang.com` binding only; no Alipay, broker, mail, notification, scheduler or trading action is enabled.
