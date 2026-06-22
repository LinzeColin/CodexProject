# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.12.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +29`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-all-arxiv-scan-parameters:adp-all-arxiv-scan-parameters-v1, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, +29`
- Current iteration: `ITER-20260621-047`
- Current phase: `E`
- Current gate: `ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-PASS`
- Model count: `32`
- Formula count: `34`
- Parameter count: `176`
- Task count: `42`
- Unbound event count: `54`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-054`
- Task: `ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-031`
- Summary: Upgraded scheduled input from legacy cs.AI-only defaults to all-arXiv scanning with ROI-ranked candidate queue, daily lead selection, Release-hosted video artifact link gating, and email queue summary.
- Model delta: Added MOD-ADP-032 adp-all-arxiv-scan-v1.
- Parameter delta: Added PARAM-ADP-170 through PARAM-ADP-176 for all-arXiv scan, queue, ROI, and mail video-link policy.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_phase12_pycache_all5 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_phase12_pycache_semantic_project3 python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_phase12_pycache_root3 python3 -m unittest tests.governance.test_project_governance_validator.ProjectGovernanceValidatorTests.test_arxiv_owner_status_uses_latest_event_manifest tests.governance.test_project_governance_validator.ProjectGovernanceValidatorTests.test_arxiv_daily_push_phase12_manifest_records_all_arxiv_queue_delivery -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_phase12_pycache_gov3 python3 scripts/validate_project_governance.py --changed-only --enforce-sync, git diff --check
- Evidence: governance/run_manifests/ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_12_ALL_ARXIV_QUEUE_DELIVERY.md, arxiv-daily-push/src/arxiv_daily_push/global_scan.py, .github/workflows/arxiv-daily-push-scheduled.yml, arxiv-daily-push/tests/test_global_scan.py
- Result: `pass`
- Rollback: Remove global_scan.py, Phase 12 CLI commands, workflow updates, delivery-package gates, tests, runbook/config/governance updates, and restore version 0.11.27.

## Current Blockers

Phase 12 all-arXiv scan, candidate queue, ROI ranking, daily lead selection, Release-hosted video artifact link gating, and email queue summary pass focused local tests. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, missing passing owner-run provisioning audit and artifact review evidence, missing default-branch Phase 12 workflow evidence, and disabled production variables. Full production acceptance still requires owner-provisioned runner/secret/Release/workflow refs, a passing default-branch trial start workflow run, live all-arXiv source ingest pass on the runner, real SMTP and Release refs, Release-hosted video artifact/MP4 evidence, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE12-PRODUCTION-ENABLEMENT-032` - Run Phase 12 on the owner-provisioned default branch runner and enable production variables only after all-arXiv scan, queue, Release video link, and SMTP evidence pass.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE12-PRODUCTION-ENABLEMENT
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=owner_provisioning_and_ci; score=132
