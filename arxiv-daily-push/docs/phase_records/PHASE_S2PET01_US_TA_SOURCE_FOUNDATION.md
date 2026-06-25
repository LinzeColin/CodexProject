# PHASE S2PET01 US-TA Source Foundation

## Scope

S2PET01 defines a metadata-only D4 US official technology-agency source foundation for NSF, DARPA, DOE, NIH, NASA, NIST, USPTO, and FDA. The report builder validates required agency coverage, required signal-type coverage, accepted official identity states, source URL and published-date traceability, evidence refs, and no-production side-effect flags.

This is not live source fetching, not D4 production inclusion, not a public schema migration, not real queue mutation, and not an Email V1 runtime or frontstage change. It does not send SMTP, install schedulers, upload Releases, change V7.1/V7.2 contract files, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Implementation

- Added `S2PET01` constants, builder, validator, runner, and report persistence in `stage2_sources.py`.
- Added `stage2-us-ta-source-foundation` CLI in `cli.py`.
- Added focused tests for valid official agency metadata, blocking unofficial/missing trace/side-effect records, persistence, and CLI JSON output.
- Added model/formula/parameter governance entries for `MOD-ADP-075`, `FORM-ADP-077`, and `PARAM-ADP-560` through `PARAM-ADP-568`.

## Gates

- `agency_coverage_gate`: NSF, DARPA, DOE, NIH, NASA, NIST, USPTO, and FDA are observed.
- `signal_type_gate`: grant, program, research-project, standard, patent, and regulatory-science signal types are observed.
- `official_identity_gate`: every row uses an accepted official identity state and official domain/source URL.
- `document_traceability_gate`: every row has required trace fields, title, and evidence refs.
- `metadata_only_gate`: every row remains metadata-only with PDF/full-text, production, queue, and SMTP side effects disabled.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pet01_compile python3 -m py_compile arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py arxiv-daily-push/src/arxiv_daily_push/cli.py` PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pet01_tests PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py` PASS, 91 tests OK.
- Full arxiv-daily-push unittest PASS, 320 tests OK.
- Semantic extractor PASS, 77 formulas / 551 parameters checked.
- V7.2 validator PASS.
- ADP project governance PASS, errors 0 / warnings 0.
- Changed-only governance semantic PASS, errors 0 / warnings 0.
- Lean render check PASS, drift 0 / reference issues 0.
- JSON/YAML/JSONL/CSV parse PASS, 84 structured files parsed.

## Acceptance

`ACC-S2PET01-US-TA` is accepted only as metadata-only D4 US-TA official source foundation evidence. It proves official agency coverage, signal taxonomy, traceability, and no side effects without granting source-domain production inclusion, public schema migration, production ranking changes, queue mutation, SMTP, scheduler, Release, or `INTEGRATED_PRODUCTION_ACCEPTED`.
