# Project Governance Status

## Snapshot Metadata

- source_base_commit: `d80785a099d1ff7f16798381c3716e8793b2ffae`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:075a0e30f6373607cd845134cdf957ae8af897ff4465d7813b9ab7a45d5b65a1`
- snapshot_event_time: `2026-06-23T20:34:26Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1307-A209-BACKGROUND-HEARTBEAT-REFRESH-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 82`
- Active formulas/parameters: `11 / 82`
- Machine checked formulas/parameters: `11 / 82`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T1303-EXTERNAL-RELEASE-EVIDENCE-BUNDLE-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `46`
- Tree-bound events: `0`
- Commit-bound events: `14`
- Legacy unbound events: `17`
- Unresolved fact IDs: `3`

## A209 Background Soak Update

- T1307/A209 24h operator soak is running as background production-stability evidence and remains non-blocking for other MVP development.
- Latest working-tree heartbeat: `EEI/artifacts/tests/a209/t1307_operator_soak_background_progress.json` is a pre-commit point-in-time artifact from `2026-06-24T11:07:43Z` with the clean restarted run at `3/288` windows PASS, `0` failed, `285` remaining and `1.04%` complete. The previous CI-attested heartbeat from commit `7afcb9da0f31b26e33b935ac9e843f2eafd8bdcd` remains `128/288` PASS; its original operator PID `12478` and watchdog PID `62233` are no longer live and must not be reused as current-process evidence.
- Crash-recovery audit: the prior 24h attempt reached `135/288` PASS at `2026-06-23T21:56:53Z`, paused without failed windows, then an attempted resume produced a failed window at `2026-06-24T10:43:46Z` because the fixed Playwright browser path was missing. The failed checkpoint was preserved at `/private/tmp/eei-a209-failed-20260624T104346.checkpoints.jsonl` and is not release-ready evidence.
- Current clean 24h attempt: after reinstalling Playwright Chromium at `/private/tmp/eei-ms-playwright`, host-permission probe passed at `2026-06-24T10:51:12Z`; the clean run started at `2026-06-24T10:52:04Z`, reached `3/288` PASS at `2026-06-24T11:07:16Z`, and is running with operator PID `57281` and host-level detached watchdog PID `17163`. This is live background evidence and is not treated as release closure.
- Monitor contract: `EEI/scripts/monitor_operator_soak.py` reports `release_gate_closed_by_monitor=false`; supervisor contract `EEI/scripts/supervise_operator_soak.py` reports `release_gate_closed_by_supervisor=false`, observes the live PID without double-starting, dry-runs recovery by default, and is included in clean-room release packaging. Watchdog contract `EEI/scripts/watch_operator_soak.py` reports `release_gate_closed_by_watchdog=false`, resumes only paused successful checkpoints when launched with `--execute --auto-resume`, and reports stale live PIDs without killing them. Heartbeat contract `EEI/scripts/record_operator_soak_heartbeat.py` reports `release_gate_closed_by_background_heartbeat=false` and keeps A209 `IN_PROGRESS`. A209 remains `IN_PROGRESS` until full 24h summary and checkpoint evidence validate.

## T1307 A209 Finalization Preflight Update

- `scripts/finalize_operator_soak_evidence.py` now generates and validates `EEI/artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json`.
- The artifact reports `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL`, `downstream_release_gate_refresh_allowed=false`, `a209_evidence_ready_for_release_manager=false` and `release_gate_closed_by_finalizer=false` while the detached 24h soak continues.
- Current source heartbeat is `3/288` windows PASS, `0` failed and `285` remaining for the clean restarted attempt; downstream A203, release-manager and MVP release-gate regeneration is allowed only after the final 24h evidence reaches `288/288` with zero failed windows and the evidence validator reports release-manager-ready evidence.
- Added `PARAM-079` for `soak.finalization_preflight_schema_version` and `PARAM-082` for `soak.background_heartbeat_counts_as_release_ready=false`; no scoring formula, graph traversal formula, extraction model, model weight, business threshold or runtime API behavior changed.

## T1303 External Release Evidence Bundle Update

- `scripts/validate_external_release_evidence_bundle.py` now generates and validates `EEI/artifacts/tests/a205/t1303_external_release_evidence_bundle_preflight.json`.
- The artifact reports `EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED`, `external_release_evidence_ready=false`, `release_manager_preflight_refresh_allowed=false`, `mvp_release_gate_refresh_allowed=false` and `release_gate_closed_by_bundle_preflight=false`.
- Missing external inputs are explicit: A202 source/license/passage/owner/legal release, A210 brand legal/market clearance or risk waiver, A026 entity-resolution production gold set, A027 relationship-extraction production gold set, and A209 24h operator-soak finalization.
- Added `PARAM-080` for `external_release_evidence_bundle.preflight_schema_version`; no scoring formula, graph traversal formula, extraction model, model weight, business threshold or runtime API behavior changed.

## T1301 A202 Signed-Intake Preflight Update

- `scripts/validate_a202_signed_intake_preflight.py` now generates and validates `EEI/artifacts/tests/a202/t1301_a202_signed_intake_preflight.json`.
- The committed artifact reports `A202_SIGNED_INTAKE_MISSING`, `a202_clearance_complete=false`, `relationship_publication_allowed=false`, `release_gate_closed_by_preflight=false` and `release_ready=false`.
- Missing signed inputs are explicit: source-license reviews, passage-level relationship reviews, production owner sign-offs, legal release clearance or risk waiver, and final attestation.
- Added `PARAM-081` for `release_decision_intake.preflight_schema_version`; no scoring formula, graph traversal formula, extraction model, model weight, business threshold or runtime API behavior changed.

## T1303 Model Config Apply Update

- `scripts/apply_model_config.py` is now a fail-closed A204/A205 operator entrypoint: `--dry-run` emits hash-bound preview evidence without writes; `--execute` requires PostgreSQL and delegates draft creation, transactional activation and score recompute enqueue to `DomainRepository`.
- `artifacts/model_config_import_preview.json` records `release_gate_closed_by_apply_model_config=false`; A204/A205 remain `IN_PROGRESS` until final release-manager activation has real A202, A026/A027, A209 and A210 gate evidence.
- `scripts/validate_release_manager_activation.py` now validates both blocked and ready preflight states from evidence. The committed repository preflight remains `RELEASE_MANAGER_ACTIVATION_BLOCKED`; a READY preflight can validate only when A202 signed clearance, A026/A027 production gold labels, A209 24h soak and A210 brand clearance artifacts all report release-ready evidence.
- The release-manager preflight now also binds `EEI/artifacts/tests/a209/t1307_operator_soak_background_progress.json` as source-hashed background progress context. This exposes `3/288` A209 clean-restart windows and `counts_as_release_ready=false` to the activation gate without replacing final 24h validator evidence.

## T1302 A203 Production API Release Preflight Update

- `scripts/validate_production_api_release_preflight.py` now generates and validates `EEI/artifacts/tests/a203/t1302_production_api_release_preflight.json`.
- The committed artifact reports `api_surface_ready=true` for the implemented graph, path, catalog, scoring explanation and evidence detail APIs, but `release_ready=false`, `production_graph_publication_allowed=false` and `score_publication_allowed=false`.
- A203 remains `IN_PROGRESS` until A202 relationship publication clearance, A204/A205 release-manager activation and A209 24h operator soak evidence are real and current.
- Clean-room and release artifacts have been refreshed after the current T1301/A202 signed-intake preflight files became staged: expected fresh-checkout counts are `package_paths=437`, release `manifest_paths=444` and `checksum_paths=443`.

## T1303 MVP Release Gate Preflight Update

- `scripts/validate_mvp_release_gate.py` now generates and validates `EEI/artifacts/tests/a205/t1303_mvp_release_gate_preflight.json` as the final fail-closed v0.1 release-gate aggregator.
- The committed artifact reports `MVP_RELEASE_BLOCKED`, `release_ready=false`, `production_publication_allowed=false`, `score_publication_allowed=false` and `public_brand_launch_allowed=false`.
- Missing gates are explicit: A202 relationship publication clearance, A203 production API release preflight, A204/A205 release-manager activation, A209 24h operator soak, A210 brand clearance or risk waiver, A026 entity-resolution production gold set and A027 relationship-extraction production gold set.
- The A209 heartbeat is included only as background progress context: working-tree evidence now reports `3/288` clean-restart windows PASS, `0` failed and `counts_as_release_ready=false`; live local files may advance beyond that, but no heartbeat closes A209.
- Added `PARAM-078` for `mvp_release_gate.preflight_schema_version`; no scoring formula, graph traversal formula, extraction model, model weight, business threshold or runtime API behavior changed.

## T904 Gold-Label Intake Template Update

- `scripts/validate_gold_quality_evaluation.py generate-template` now writes `EEI/artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json` with the exact A026/A027 production-label metadata fields, minimum case counts, case schemas and validation commands.
- The template status is `TEMPLATE_ONLY`, with `release_gate_closure_allowed=false`, `production_claim_allowed=false` and `relationship_publication_allowed=false`; it is an operator intake artifact, not production gold-set evidence.
- A026 and A027 remain `IN_PROGRESS` until a real operator-supplied production gold label payload passes `--allow-production-gold-set` validation and the release manager later sees all external gates ready.

## T1309 Brand-Clearance Intake Template Update

- `scripts/validate_brand_clearance.py generate-template` now writes `EEI/artifacts/tests/a210/t1309_brand_clearance_intake_template.json` with the exact A210 evidence fields for CN/US/EU/UK/AU trademark knockout, company/domain/social/app-store/GitHub/npm/PyPI searches, Chinese/English phonetic-semantic review, legal/owner decision and final attestation.
- The template status is `TEMPLATE_ONLY`, with `release_gate_closure_allowed=false`, `public_brand_launch_allowed=false` and `template_counts_as_clearance=false`; it is an operator/legal intake artifact, not formal legal advice, trademark clearance, market clearance or public-launch approval.
- A210 remains `IN_PROGRESS` until a real signed brand-clearance or risk-waiver bundle passes validation and the release manager later sees all external gates ready.

## T1301 A202 Release-Decision Intake Template Update

- `scripts/validate_release_decision_bundle.py generate-template` now writes `EEI/artifacts/tests/a202/t1301_a202_release_decision_intake_template.json` with exact A202 source-license, passage-level relationship review, production owner sign-off, legal release clearance and attestation fields for Golden Vertical relationship candidates `GV-FACT-001..002`.
- The template status is `TEMPLATE_ONLY`, with `release_gate_closure_allowed=false`, `relationship_publication_allowed=false` and `template_counts_as_clearance=false`; it is an operator/legal intake artifact, not source-license approval, passage approval, owner approval, legal clearance, relationship publication or A202 closure.
- The A202 signed-intake preflight is generated from the template by default and remains `A202_SIGNED_INTAKE_MISSING`; a future operator-supplied signed intake can validate A202 clearance but still leaves A210, A026/A027, A209 and release-manager activation open.
- A202 remains `IN_PROGRESS` until a real signed A202 intake or release-decision bundle passes validation and the release manager later sees all external gates ready. A209 24h soak continues as an independent background gate.

## Latest CI Binding

- `EVENT-20260624-024` is now CI-attested by commit `7afcb9da0f31b26e33b935ac9e843f2eafd8bdcd`.
- GitHub Actions evidence: Project Governance run `28059597753` / job `83070396547` PASS; EEI validation run `28059597696` / job `83070396099` PASS, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.
- The CI-attested repository heartbeat remains a point-in-time `128/288` evidence artifact; A209 is still `IN_PROGRESS` until the final 24h summary and checkpoint validation pass at `288/288`.
