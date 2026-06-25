# PHASE S2PGT02 Knowledge Graph Spine

## Scope

S2PGT02 defines a private cross-source identity-resolution and knowledge-graph relation spine after S2PGT01. The report builder normalizes DOI, PMID, arXiv, Chinese document number, Federal Register document number, and CIK identifiers, merges overlapping identifiers into deterministic canonical entities, validates evidence-backed relation edges, and proves idempotent graph-state hashing.

This is not a public schema migration and not a production graph deployment. It does not mutate queues, install schedulers, send SMTP, upload Releases, change V7.2 contract files, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Implementation

- Added `S2PGT02` constants, builder, validator, runner, and report persistence in `stage2_sources.py`.
- Added `stage2-knowledge-graph-spine` CLI in `cli.py`.
- Added focused tests for pass, duplicate-canonical conflict, missing relation evidence, persistence, and CLI JSON output.
- Added model/formula/parameter governance entries for `MOD-ADP-071`, `FORM-ADP-073`, and `PARAM-ADP-516` through `PARAM-ADP-524`.

## Gates

- `identifier_coverage_gate`: all required identifier types are observed.
- `canonical_dedupe_gate`: duplicate canonical declarations are zero.
- `relation_evidence_gate`: every relation has required fields and evidence refs.
- `idempotent_update_gate`: relation idempotency keys are unique and graph-state hash is deterministic.
- `no_side_effect_gate`: schema migration, queue mutation, SMTP, scheduler, Release, production, and V7.2 contract side effects remain false.

## Validation

- `PYTHONPATH=arxiv-daily-push/src python3 -m py_compile arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py arxiv-daily-push/src/arxiv_daily_push/cli.py arxiv-daily-push/tests/test_stage2_sources.py` PASS.
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q` PASS, 75 tests OK.
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q` PASS, 304 tests OK.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push` PASS, 73 formulas / 507 parameters checked.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push` PASS, errors 0 warnings 0.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main` PASS, errors 0 warnings 0.
- `PYTHONPATH=arxiv-daily-push/src python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2` PASS.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/lean_governance.py check-render --project arxiv-daily-push` PASS, drift 0 reference issues 0.
- JSON/YAML/JSONL/CSV parse checks PASS.
- `git diff --check` PASS.

## Acceptance

`ACC-S2PGT02-KG` is accepted only as private knowledge-graph spine evidence. It proves duplicate canonical count 0, evidence-backed relation edges, and idempotent deterministic graph updates for the focused S2PGT02 fixtures; it does not grant public schema migration, production queue mutation, source-domain production inclusion, SMTP, scheduler, Release, or `INTEGRATED_PRODUCTION_ACCEPTED`.
