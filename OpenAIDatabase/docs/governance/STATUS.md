# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- CI mode: `required`
- Product version: `0.2.0`
- Model versions: `MOD-001:memory-candidate-v0, MOD-002:redaction-policy-v0, MOD-003:active-memory-v0, +8`
- Parameter profile versions: `codex_sync:codex-sync-parameters-v0, memory_analysis:memory-analysis-parameters-v0, memory_atlas:memory-atlas-parameters-v0, +2`
- Current iteration: `ITER-20260621-OAI-003`
- Current phase: `C`
- Current gate: `TASK-OAI-C-002-PERSONALIZATION-ARCHITECTURE`
- Model count: `11`
- Formula count: `11`
- Parameter count: `92`
- Task count: `9`
- Unbound event count: `4`

## Latest Run

- Event: `ITER-20260621-OAI-003`
- Task: `TASK-OAI-C-002`
- Summary: Add truthful sync-run baseline evidence and require each configured run-log category to contain JSONL records.
- Model delta: `UNKNOWN`
- Parameter delta: `UNKNOWN`
- Tests: `['python3 scripts/evaluate_personalization_context.py --database-dir .', 'python3 -m unittest tests.test_personalization_architecture -q', 'python3 scripts/validate_project_governance.py --project OpenAIDatabase', 'python3 scripts/validate_project_governance.py --all']`
- Evidence: `['OpenAIDatabase/data/run_logs/sync_runs/2026-06-21.jsonl', 'OpenAIDatabase/data/run_logs/evaluation_runs/2026-06-21.jsonl', 'OpenAIDatabase/scripts/evaluate_personalization_context.py']`
- Result: `PASS: evaluation PASS with failures empty and run_log_records included; personalization architecture unittest exit 0 with 2 tests OK; project governance validator exit 0 errors 0 warnings 0; all-project governance validator exit 0 errors 0 warnings 0`
- Rollback: UNKNOWN

## Current Blockers

calibration evidence for heuristic weights is UNKNOWN and tracked by `TASK-OAI-B-001`

## Next Task

`TASK-OAI-B-001`
