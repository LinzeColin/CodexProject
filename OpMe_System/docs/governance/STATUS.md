# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `OpMe_System`
- Path: `OpMe_System`
- CI mode: `required`
- Product version: `1.0.0`
- Model versions: `MOD-001:mod-001-v0, MOD-002:mod-002-v0, MOD-003:mod-003-v0, +4`
- Parameter profile versions: `llm_router:opme-router-v0, offline_rules:opme-rules-v0`
- Current iteration: `ITER-20260620-OPME-001`
- Current phase: `E`
- Current gate: `GOV-G4-OPME-REQUIRED`
- Model count: `7`
- Formula count: `7`
- Parameter count: `49`
- Task count: `5`
- Unbound event count: `2`

## Latest Run

- Event: `EVENT-OPME-20260620-002`
- Task: `GOV-G4-OPME-PROMOTE-001`
- Summary: Verified OpMe_System governance baseline and promoted OpMe_System enforcement from advisory to required.
- Model delta: `UNKNOWN`
- Parameter delta: `UNKNOWN`
- Tests: `['python scripts/validate_project_governance.py --project OpMe_System', 'python -m pytest tests/test_analysis.py -q', 'python -m pytest tests/test_api.py -q', 'python scripts/validate_project_governance.py --all', 'git diff --check']`
- Evidence: `['OpMe_System/docs/governance/DEVELOPMENT_LEDGER.md', 'governance/projects.yaml']`
- Result: `PASS_WITH_BLOCKED_ADDITIONAL_CHECK`
- Rollback: Set OpMe_System ci_mode back to advisory and restore OpMe_System governance task status if promotion is reverted.

## Current Blockers

`TASK-OPME-B-001` for calibration, prompt/provider governance, and signoff evidence.

## Next Task

`TASK-OPME-B-001`
