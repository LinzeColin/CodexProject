# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:075a0e30f6373607cd845134cdf957ae8af897ff4465d7813b9ab7a45d5b65a1`
- snapshot_event_time: `2026-06-23T04:05:00Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-A202-RELEASE-DECISION-INTAKE-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 76`
- Active formulas/parameters: `11 / 76`
- Machine checked formulas/parameters: `11 / 76`

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
- Release gate: `TASK-T1301-A202-RELEASE-DECISION-INTAKE-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `45`
- Tree-bound events: `0`
- Commit-bound events: `13`
- Legacy unbound events: `17`
- Unresolved fact IDs: `3`

## A209 Background Soak Update

- T1307/A209 24h operator soak is running as background production-stability evidence and remains non-blocking for other MVP development.
- Latest repository heartbeat: `EEI/artifacts/tests/a209/t1307_operator_soak_background_progress.json` reports operator PID `12478` RUNNING, watchdog PID `62233` RUNNING, `92/288` windows PASS, `0` failed, `196` remaining, `31.94%` complete, generated at `2026-06-23T18:21:13Z`.
- Monitor contract: `EEI/scripts/monitor_operator_soak.py` reports `release_gate_closed_by_monitor=false`; supervisor contract `EEI/scripts/supervise_operator_soak.py` reports `release_gate_closed_by_supervisor=false`, observes the live PID without double-starting, dry-runs recovery by default, and is included in clean-room release packaging. Watchdog contract `EEI/scripts/watch_operator_soak.py` reports `release_gate_closed_by_watchdog=false`, resumes only paused successful checkpoints when launched with `--execute --auto-resume`, and reports stale live PIDs without killing them. Heartbeat contract `EEI/scripts/record_operator_soak_heartbeat.py` reports `release_gate_closed_by_background_heartbeat=false` and keeps A209 `IN_PROGRESS`. A209 remains `IN_PROGRESS` until full 24h summary and checkpoint evidence validate.

## T1303 Model Config Apply Update

- `scripts/apply_model_config.py` is now a fail-closed A204/A205 operator entrypoint: `--dry-run` emits hash-bound preview evidence without writes; `--execute` requires PostgreSQL and delegates draft creation, transactional activation and score recompute enqueue to `DomainRepository`.
- `artifacts/model_config_import_preview.json` records `release_gate_closed_by_apply_model_config=false`; A204/A205 remain `IN_PROGRESS` until final release-manager activation has real A202, A026/A027, A209 and A210 gate evidence.
- `scripts/validate_release_manager_activation.py` now validates both blocked and ready preflight states from evidence. The committed repository preflight remains `RELEASE_MANAGER_ACTIVATION_BLOCKED`; a READY preflight can validate only when A202 signed clearance, A026/A027 production gold labels, A209 24h soak and A210 brand clearance artifacts all report release-ready evidence.
- The release-manager preflight now also binds `EEI/artifacts/tests/a209/t1307_operator_soak_background_progress.json` as source-hashed background progress context. This exposes `92/288` A209 windows and `counts_as_release_ready=false` to the activation gate without replacing final 24h validator evidence.

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
- A202 remains `IN_PROGRESS` until a real signed A202 intake or release-decision bundle passes validation and the release manager later sees all external gates ready. A209 24h soak continues as an independent background gate.
