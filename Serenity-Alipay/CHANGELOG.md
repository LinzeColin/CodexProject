# Changelog

## Unreleased - Immutable Pool Entry Guard

- Fixed `record_asset_pool_entries()` so first candidate/holding/observation pool entry facts are resolved from historical `recommendation_snapshot + run_log` before insertion, instead of blindly using the current run.
- Restored the regression expectation that a fund first entering Top5 in an older run keeps the original `first_run_id`, `first_rank`, `first_run_time_bj`, and `first_run_created_at` even when later runs rank it higher.
- Verified the focused app/UI/benchmark/indicator/history test set passes without running production analysis, sending mail, starting OpenD/MooMoo, or modifying historical SQLite rows.

No historical snapshot, report, immutable creation timestamp, first pool entry timestamp, or prior analysis record was rewritten by this change.

## Unreleased - Other8 S3PCT03 Lifecycle Evidence

- Added focused S3PCT03 lifecycle coverage for mocked OpenD auto-wake ownership, tool-owned cleanup, user-owned OpenD protection, delivery package atomic failure recovery, and launchd tick wrapper behavior.
- Recorded S3PC stage-gate evidence for Serenity lifecycle, process cleanup, and package recovery without starting real OpenD, sending real mail, trading, or touching production data.
- Re-bound stale machine source selectors and evidence hashes for PARAM-027 through PARAM-032 to the current `pipeline.py` line layout without changing active values.

No scoring result, ranking result, gate logic, parameter value, empirical calibration, live account readiness, or production delivery readiness changed.

## Unreleased - App Entry and Manual Review Regression Hardening

- Recorded the repeated app/manual-review bug cluster in `DEVELOPMENT_BUG_REGRESSION_LOG.md` so future agents have an explicit GitHub development record and regression contract.
- Fixed manual-review todo semantics: a saved valid decision outcome now removes the review item immediately even while the background Serenity refresh is still `running`.
- Fixed app entry behavior: the macOS launcher opens only the final local homepage URL once and no longer relies on `downloads-entry.html` bootstrap navigation.
- Fixed Dock bouncing behavior: the launcher no longer waits on the Python server process; it starts the local server in the background when needed, opens the homepage after health readiness, and exits.
- Added/kept regression coverage for review save handling, launcher content, and application server routes.
- Restored missing GitHub-sync source/test files for all-market candidate expansion, fund rule autofill, and indicator discipline so `pipeline`, `preflight`, `cli`, and `history-integrity` imports work from a fresh GitHub checkout.

No historical snapshot, report, immutable creation timestamp, first pool entry timestamp, or prior analysis record was rewritten by this change.

## Unreleased - Review6 Semantic Extraction

- Added machine source selectors, extracted values, verification timestamps, and evidence hashes for 49 active Serenity parameters.
- Added AST implementation fingerprints for 12 active Serenity formulas.
- Recorded the FORM-008 post-renormalization cap caveat: final weights can exceed 0.30 for 1, 2, 3, and 4 candidate scenarios under the current algorithm, while existing target-weight tests cover only the 5-candidate scenario.

No scoring result, ranking result, gate logic, parameter value, data, or business behavior changed.

## 0.1.0 - Governance Baseline

- Added CodexProject governance baseline for Serenity-Alipay.
- Registered current scoring, ranking, hard-gate, MDD, recovery, Top5, comparison, discipline, and scheduler rules without changing runtime behavior.
- Added version separation in `docs/governance/VERSION_MATRIX.yaml`.
- Preserved legacy project files as compatibility indexes.

No scoring result, ranking result, gate logic, parameter value, data, or business behavior changed in this governance-only baseline.
