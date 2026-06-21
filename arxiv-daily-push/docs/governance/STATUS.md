# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.6.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +3`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +3`
- Current iteration: `ITER-20260621-006`
- Current phase: `C`
- Current gate: `ADP-PHASE6-LESSON-PASS`
- Model count: `6`
- Formula count: `8`
- Parameter count: `36`
- Task count: `8`
- Unbound event count: `13`

## Latest Run

- Event: `EVENT-20260621-ADP-013`
- Task: `ADP-PHASE6-LESSON-001`
- Summary: Validated Phase 6 deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence with claim ID linkage and unsupported-claim exclusion.
- Model delta: `Activated MOD-ADP-006 deterministic evidence-linked Chinese lesson generator.`
- Parameter delta: `Activated PARAM-ADP-035 and PARAM-ADP-036 as lesson generation parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_06.md', 'arxiv-daily-push/src/arxiv_daily_push/lesson.py', 'arxiv-daily-push/tests/test_lesson.py', 'arxiv-daily-push/tests/fixtures/lesson_input.json']`
- Result: `pass`
- Rollback: Revert the Phase 6 commit and restore arxiv-daily-push to version 0.5.0.

## Current Blockers

Later phases still need narration/TTS resource validation, real mail transport validation, and later media/runner readiness.

## Next Task

`ADP-PHASE7-TTS-001`
