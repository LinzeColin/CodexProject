# PHASE S2PKT01 MAIL CONTRACT

## Status

- status: `completed_local_validation`
- phase: `S2PK`
- task_id: `S2PKT01`
- acceptance_id: `ACC-S2PKT01-MAIL-CONTRACT`
- model_id: `MOD-ADP-089`
- formula_id: `FORM-ADP-091`
- parameter_ids: `PARAM-ADP-701` through `PARAM-ADP-716`
- completed_at: `2026-06-26T06:20:00+10:00`

## Scope

S2PKT01 adds local-only M1-M4 shared `EMAIL_LEARNING_V1` mail contract readiness evidence. The report checks S2PHT05, S2PIT04, and S2PJT03 dependency readiness, M1-M4 contract identity, template version, board differentiation, B4/B5/B6 cross-cutting boards, three reading layers, evidence labels, feedback actions, allowed no-send statuses, deterministic per-mail and aggregate hashes, and all production side-effect flags.

## Non Scope

This phase does not change runtime mail templates/frontstage, SMTP transport, scheduler triggers, Release upload, source adapters, ranking, queue algorithms, public schema, DB migrations, `CURRENT`, V7.1 history, V7.2 shared contract files, or any production acceptance state.

## Evidence

- `governance/run_manifests/ADP-S2PKT01-MAIL-CONTRACT-20260626.json`
- `arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py`
- `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- `arxiv-daily-push/tests/test_stage2_sources.py`

## Validation

- `py_compile`: PASS
- `test_stage2_sources.py`: 150 tests OK
- Full ADP unittest: 379 tests OK
- Semantic extractor: 91 formulas / 699 parameters checked
- V7.2 validator: PASS
- ADP project governance: errors 0 warnings 0
- Changed-only governance semantic: errors 0 warnings 0
- Lean check-render: drift_count 0 reference_issue_count 0
- JSONL/YAML/CSV/manifest parse: OK
- git diff --check: PASS

## Remaining Risks

- Future mail entrypoints must keep using the same Email V1 contract/readiness gate and must not bypass S2PKT01 evidence.
- Inherited V7.1 P0=8/P1=37 plus S2PMT07 still block real restore, real SMTP, scheduler installation, Release/final production claims, and `INTEGRATED_PRODUCTION_ACCEPTED`.
