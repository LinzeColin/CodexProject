# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.12.1`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +30`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-all-arxiv-scan-parameters:adp-all-arxiv-scan-parameters-v1, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, +30`
- Current iteration: `ITER-20260621-048`
- Current phase: `E`
- Current gate: `ADP-PHASE12-PRODUCTION-ENABLEMENT-CLOUD-GATED`
- Model count: `33`
- Formula count: `35`
- Parameter count: `180`
- Task count: `43`
- Unbound event count: `55`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-055`
- Task: `ADP-PHASE12-PRODUCTION-ENABLEMENT-032`
- Summary: Prepared and cloud-verified Phase 12 production enablement for GitHub-hosted execution by removing self-hosted workflow targeting, proving live all-arXiv dry-run coverage, rendering a real lightweight MP4 artifact, and requiring Release .mp4 links before email video evidence can pass.
- Model delta: Added MOD-ADP-033 adp-phase12-cloud-enablement-v1 for cloud dry-run, real MP4, GitHub-hosted workflow, and side-effect gates.
- Parameter delta: Added PARAM-ADP-177 through PARAM-ADP-180 for live dry-run model id, MP4 render model id, cloud free-disk threshold, and GitHub-hosted runner requirement.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_cloud_pycache_focus3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_video.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cloud_dry_run_workflow.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_cloud_pycache_workflows PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_bootstrap.py arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_cloud_dry_run_workflow.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_cloud_pycache_all2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, workflow grep for self-hosted runner references, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_cloud_pycache_gov python3 scripts/validate_project_governance.py --changed-only --enforce-sync, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_cloud_pycache_refs_cloud PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_launch.py -q, +7 more
- Evidence: governance/run_manifests/ADP-PHASE12-PRODUCTION-ENABLEMENT-CLOUD-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_12_PRODUCTION_ENABLEMENT_CLOUD.md, .github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml, .github/workflows/arxiv-daily-push-scheduled.yml, .github/workflows/arxiv-daily-push-trial-start.yml, arxiv-daily-push/src/arxiv_daily_push/video.py, +2 more
- Result: `pass`
- Rollback: Revert version 0.12.1 changes remove cloud dry-run workflow and MP4 render command restore 0.12.0 workflow contracts and keep production variables disabled.

## Current Blockers

Phase 12 all-arXiv scan, candidate queue persistence, ROI ranking, daily lead selection, Release-hosted video artifact link gating, and email queue summary pass focused local tests. Production launch remains blocked by PR CI completion, owner-provisioned default-branch runner networking/TLS, durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, explicit launch confirmation, default-branch Phase 12 workflow evidence, real Gmail SMTP evidence to `linzezhang35@gmail.com`, real GitHub Release video-link evidence, resource telemetry, replay/recovery evidence, 30 unique daily production entries, and explicitly disabled production variables.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127
