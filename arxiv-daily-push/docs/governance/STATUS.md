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
- Current iteration: `ITER-20260621-034`
- Current phase: `E`
- Current gate: `GOV-SEMANTIC-ADP-EXPANDED`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `32`
- Unbound event count: `41`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `80`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-041`
- Task: `GOV-SEMANTIC-ADP-001`
- Summary: Expanded arXiv Daily Push semantic coverage to 72 active parameters and all 31 active formulas while leaving 80 active parameters HUMAN_REVIEW_REQUIRED.
- Model delta: No runtime model behavior change.
- Parameter delta: Added implementation/config/test-backed semantic selectors for 27 more active parameters; 80 active parameters remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-ADP-001.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_expand_final python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_project_final python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_root_final python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_arxiv_final PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_dashboard_final python3 scripts/generate_governance_dashboard.py --write, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_semantic_changed_final python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main, +3 more
- Evidence: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-002.json, arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml
- Result: `pass`
- Rollback: Remove the second ArXiv semantic extractor expansion, semantic run manifest/event, generated status/dashboard changes, and the root governance test update.

## Current Blockers

Semantic coverage is now in progress with 72 machine-checked active parameters and all 31 active formulas; 80 active parameters remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. PR #28 is merged to `main`; production launch remains blocked by missing explicit launch confirmation and missing durable readiness refs for `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref`; no GitHub Actions workflow runs or combined status checks exist for merge commit `cc893e4e11ffe690a8f0d6010053c7a1ab5a09b4`; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `in_progress`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-002.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks 72 active parameters and all 31 active formulas while 80 active parameters remain HUMAN_REVIEW_REQUIRED under the same task.; status: in_progress; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`GOV-SEMANTIC-ADP-001` - Plan machine semantic coverage for arXiv Daily Push active parameter values and formula implementation fingerprints under the latest CodexProject governance standard.

- Status: `in_progress`
- Acceptance: ACC-SEMANTIC-ADP-001
- Selection rationale: status=in_progress; phase=E; current_phase=E; unmet_dependencies=none; score=120
