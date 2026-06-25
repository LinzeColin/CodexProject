# PHASE S2PGT03 Source Board Routing

## Scope

S2PGT03 defines a private D1-D4 to B1-B6 multi-label routing evidence layer after S2PGT01. The report builder validates source-domain coverage, B1-B3 primary board coverage, B4-B6 cross-cutting board coverage, route reason codes, route explanations, evidence references, and no-production/no-schema side-effect gates.

This is not a public schema migration and not a production routing deployment. It does not mutate queues, install schedulers, send SMTP, upload Releases, change V7.2 contract files, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Implementation

- Added `S2PGT03` constants, builder, validator, runner, and report persistence in `stage2_sources.py`.
- Added `stage2-source-board-routing` CLI in `cli.py`.
- Added focused tests for pass, missing route fields, unsupported board, side-effect blocking, persistence, and CLI JSON output.
- Added model/formula/parameter governance entries for `MOD-ADP-072`, `FORM-ADP-074`, and `PARAM-ADP-525` through `PARAM-ADP-535`.

## Gates

- `source_domain_coverage_gate`: D1-D4 source domains are observed.
- `primary_board_coverage_gate`: B1-B3 primary reading boards are observed.
- `cross_cutting_board_coverage_gate`: B4-B6 cross-cutting reading boards are observed.
- `route_reason_gate`: every routing record has source domain, source id, primary board, cross-cutting board, reason code, explanation, and evidence refs.
- `no_side_effect_gate`: schema migration, queue mutation, SMTP, scheduler, Release, production, and V7.2 contract side effects remain false.

## Validation

- `PYTHONPATH=arxiv-daily-push/src python3 -m py_compile arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py arxiv-daily-push/src/arxiv_daily_push/cli.py arxiv-daily-push/tests/test_stage2_sources.py` PASS.
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q` PASS, 79 tests OK.
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q` PASS, 308 tests OK.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push` PASS, 74 formulas / 518 parameters checked.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push` PASS, errors 0 warnings 0.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main` PASS, errors 0 warnings 0.
- `PYTHONPATH=arxiv-daily-push/src python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2` PASS.
- `PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/lean_governance.py check-render --project arxiv-daily-push` PASS, drift_count 0 reference_issue_count 0.
- JSON/YAML/JSONL/CSV parse PASS with `/opt/anaconda3/bin/python`.
- `git diff --check` PASS.

## Acceptance

`ACC-S2PGT03-ROUTING` is accepted only as private source-to-reading-board routing evidence. It proves each important fixture content row has source domain, primary board, cross-cutting board, reason code, explanation, and evidence reference; it does not grant public schema migration, production queue mutation, source-domain production inclusion, SMTP, scheduler, Release, or `INTEGRATED_PRODUCTION_ACCEPTED`.
