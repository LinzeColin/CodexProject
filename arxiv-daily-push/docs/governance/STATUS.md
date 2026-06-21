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
- Current iteration: `ITER-20260621-031`
- Current phase: `E`
- Current gate: `GOV-SEMANTIC-ADP-PLANNED`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `31`
- Unbound event count: `38`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `planned`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-038`
- Task: `GOV-SEMANTIC-ADP-001`
- Summary: Merged latest main governance requirements and added a planned semantic_coverage rollout contract for arXiv Daily Push without claiming machine-verified semantic extraction or changing runtime behavior.
- Model delta: No runtime model behavior change; semantic coverage remains planned, not machine_verified.
- Parameter delta: No active parameter value change; future extractor work must prove active values before machine verification.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_semantic_project python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_semantic_dashboard python3 scripts/generate_governance_dashboard.py --write, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_semantic_changed python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_semantic_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_semantic_project_tests PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, git diff --check, +2 more
- Evidence: governance/projects.yaml, arxiv-daily-push/docs/governance/delivery_tasks.yaml, governance/run_manifests/GOV-SEMANTIC-ADP-PLANNED-001.json
- Result: `pass`
- Rollback: Remove arXiv semantic_coverage block, GOV-SEMANTIC-ADP-001 task, generated OWNER_STATUS/status changes, run manifest, and this ledger/event update.

## Current Blockers

Semantic coverage remains planned and not machine verified; production launch remains blocked while PR #14 is draft and unmerged; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Semantic Coverage

- Status: `planned`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-PLANNED-001.json; owner: project owner; rationale: Main branch governance now requires every required project to carry a semantic coverage rollout contract. arXiv Daily Push does not yet claim machine-verified semantic extraction, so coverage remains planned and task-bound.; status: planned; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`GOV-SEMANTIC-ADP-001` - Plan machine semantic coverage for arXiv Daily Push active parameter values and formula implementation fingerprints under the latest CodexProject governance standard.

- Status: `planned`
- Acceptance: ACC-SEMANTIC-ADP-001
- Selection rationale: status=planned; phase=E; current_phase=E; unmet_dependencies=none; score=112
