# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `Alpha`
- Path: `Alpha`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:strategy-tournament-v0, MOD-002:risk-score-v0, MOD-003:pre-trade-gate-v0, +6`
- Parameter profile versions: `agent_loop:agent-loop-v0, paper_broker_defaults:paper-broker-v0, strategy_tournament_constants:strategy-tournament-v0, +1`
- Current iteration: `ITER-20260620-ALPHA-001`
- Current phase: `E`
- Current gate: `GOV-G4-ALPHA-REQUIRED`
- Model count: `9`
- Formula count: `9`
- Parameter count: `55`
- Task count: `8`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `3`
- Semantic coverage: `planned`
- Semantic rollout task: `GOV-SEMANTIC-ALPHA-001`

## Latest Run

- Event: `EVENT-ALPHA-20260620-002`
- Task: `GOV-G4-ALPHA-PROMOTE-001`
- Summary: Verified Alpha governance baseline and promoted Alpha enforcement from advisory to required.
- Model delta: UNKNOWN
- Parameter delta: UNKNOWN
- Tests: python scripts/validate_project_governance.py --project Alpha, python -m pytest tests/test_policy.py tests/test_live_broker_fail_closed.py tests/test_strategy_iteration.py tests/test_paper_trading_loop.py -q, python scripts/validate_project_governance.py --all, git diff --check
- Evidence: Alpha/docs/governance/DEVELOPMENT_LEDGER.md, governance/projects.yaml
- Result: `PASS`
- Rollback: Set Alpha ci_mode back to advisory and restore Alpha governance task status if promotion is reverted.

## Current Blockers

live execution policy and production validation remain blocked under `TASK-ALPHA-B-001`.

## Semantic Coverage

- Status: `planned`
- Target: Add machine source selectors for active parameters and implementation fingerprints for active formulas.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ALPHA-001; evidence_ref: Alpha/docs/governance/OWNER_STATUS.md; owner: project owner; rationale: Review6-D rollout guard; semantic extractors are not yet implemented for Alpha.; status: planned; target: Add machine source selectors for active parameters and implementation fingerprints for active formulas.; +1 more

## Next Task

`TASK-ALPHA-B-001` - Resolve production validation and execution-policy UNKNOWN items before release readiness.

- Status: `blocked`
- Acceptance: ACC-ALPHA-B-001
- Selection rationale: status=blocked; phase=B; current_phase=E; unmet_dependencies=none; score=152
