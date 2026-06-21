# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.25`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +27`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +27`
- Current iteration: `ITER-20260621-044`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED`
- Model count: `30`
- Formula count: `32`
- Parameter count: `165`
- Task count: `39`
- Unbound event count: `51`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-051`
- Task: `ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-028`
- Summary: Added a GitHub-hosted no-secret provisioning audit workflow that runs before private-runner trial-start dispatch and uploads a production refs readiness artifact.
- Model delta: No new runtime model; MOD-ADP-030 now includes a GitHub-hosted no-secret provisioning audit workflow before private-runner trial-start dispatch.
- Parameter delta: Added PARAM-ADP-165 for the GitHub-hosted production provisioning audit workflow.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_cli.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push discover-production-refs --generated-at 2026-06-22T23:00:00+10:00 --json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_semantic python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_project python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_provisioning_audit_arxiv PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, +4 more
- Evidence: governance/run_manifests/ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_PROVISIONING_AUDIT_WORKFLOW.md, .github/workflows/arxiv-daily-push-provisioning-audit.yml, arxiv-daily-push/tests/test_production_refs.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove provisioning audit workflow, workflow test, PARAM-ADP-165, phase record, manifest, and related governance records, then restore version 0.11.24.

## Current Blockers

Semantic coverage is machine_verified with 164 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Production refs provisioning now has a no-secret owner-fillable template, a GitHub metadata discovery command for provisioned runners, and a GitHub-hosted no-secret provisioning audit workflow that can run before private-runner trial-start dispatch. Trial-start/scheduled production workflows declare machine-checked `contents: write` permission for controlled draft Release evidence, and trial-start now runs production refs discovery plus launch readiness before source, SMTP, Release, or start-gate work. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, missing passing provisioning audit evidence, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127
