# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.8.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +5`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +5`
- Current iteration: `ITER-20260621-008`
- Current phase: `D`
- Current gate: `ADP-PHASE8-VIDEO-DRY-RUN-PASS`
- Model count: `8`
- Formula count: `10`
- Parameter count: `44`
- Task count: `9`
- Unbound event count: `15`

## Latest Run

- Event: `EVENT-20260621-ADP-015`
- Task: `ADP-PHASE8-VIDEO-001`
- Summary: Implemented Phase 8 Storyboard/video dry-run JSON generation and media gate while keeping rendering, media writes, and asset downloads blocked.
- Model delta: `Activated MOD-ADP-008 deterministic Storyboard and video dry-run media gate.`
- Parameter delta: `Activated PARAM-ADP-041 through PARAM-ADP-044 as video dry-run parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_08.md', 'arxiv-daily-push/src/arxiv_daily_push/video.py', 'arxiv-daily-push/tests/test_video.py', 'arxiv-daily-push/tests/fixtures/video_input.json']`
- Result: `pass`
- Rollback: Revert the Phase 8 commit and restore arxiv-daily-push to version 0.7.0.

## Current Blockers

Later phases still need local pipeline orchestration, real mail transport validation, runner automation, release readiness, and 30-day acceptance evidence.

## Next Task

`ADP-PHASE9-LOCAL-PIPELINE-001`
