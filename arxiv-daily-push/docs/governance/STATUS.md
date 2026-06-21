# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.20`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +27`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +27`
- Current iteration: `ITER-20260621-039`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED`
- Model count: `30`
- Formula count: `32`
- Parameter count: `159`
- Task count: `34`
- Unbound event count: `46`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-046`
- Task: `ADP-PHASE11-PRODUCTION-REFS-BUNDLE-023`
- Summary: Added a no-secret production refs readiness bundle for runner, SMTP secret-name, Release target, and workflow variable refs, and wired passing reports into production launch readiness while keeping real launch blocked until owner-provisioned refs and confirmation exist.
- Model delta: Added MOD-ADP-030 adp-production-refs-v1 and kept production launch/acceptance fail-closed.
- Parameter delta: Added PARAM-ADP-154 through PARAM-ADP-159 for production refs validator id, required SMTP secret names, workflow var names, ref keys, secret-like key blocklist, and no-side-effect safety.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m pytest -q arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_launch.py, PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, python3 -m json.tool arxiv-daily-push/schemas/production_refs.schema.json, PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, +1 more
- Evidence: governance/run_manifests/ADP-PHASE11-PRODUCTION-REFS-BUNDLE-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_REFS_READINESS.md, arxiv-daily-push/src/arxiv_daily_push/production_refs.py, arxiv-daily-push/tests/test_production_refs.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Revert production refs gate, CLI integration, schema, tests, runbook/phase record/governance updates, and restore version 0.11.19.

## Current Blockers

Semantic coverage is machine_verified with 158 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. A no-secret production refs bundle gate now exists for runner, SMTP secret-name, Release target, and workflow variable readiness refs, and PR #32 remains merged to `main` at merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560`; however production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127
