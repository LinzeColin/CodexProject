# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.19`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +26`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +26`
- Current iteration: `ITER-20260621-037`
- Current phase: `E`
- Current gate: `GOV-SEMANTIC-ADP-MACHINE-VERIFIED`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `33`
- Unbound event count: `44`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-044`
- Task: `GOV-SEMANTIC-ADP-001`
- Summary: Completed arXiv Daily Push machine semantic coverage for all 152 active parameters and all 31 active formulas without changing runtime behavior.
- Model delta: No arXiv Daily Push runtime model behavior change; root semantic extractor selector behavior expanded for governance validation only.
- Parameter delta: Added selector-backed semantic metadata for the final 21 active parameters; no active parameter values changed.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_selector_tests python3 -m unittest tests.governance.test_project_governance_validator.ProjectGovernanceValidatorTests.test_review6_selector_options_can_check_contains_filter_and_order -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_selector_probe python3 - <<'PY' ... selector probe ... PY, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_extract python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_project python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic5_arxiv PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, +6 more
- Evidence: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json, scripts/validate_semantic_extractors.py, arxiv-daily-push/docs/governance/parameter_registry.csv
- Result: `pass`
- Rollback: Revert final selector transform changes, remove the fifth ArXiv semantic extractor expansion, semantic run manifest/event, generated status/dashboard changes, and the root governance test update.

## Current Blockers

Semantic coverage is machine_verified with 152 machine-checked active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. PR #31 is merged to `main` and main Project Governance CI passed for merge commit `d7ad354519374946c70440abae213410c2cb061d`; production launch remains blocked by missing explicit launch confirmation and missing durable readiness refs for `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref`; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127
