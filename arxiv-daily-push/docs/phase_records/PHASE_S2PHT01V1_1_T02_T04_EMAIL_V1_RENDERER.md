# S2PHT01V1.1-T02-T04 EMAIL_LEARNING_V1 Renderer

## Scope

This run implements the V7.2/V1.1 Email Learning V1 renderer for audited ADP mail paths after T01 path audit.

Changed runtime paths:

- `src/arxiv_daily_push/mail_templates.py`
- `src/arxiv_daily_push/global_scan.py`
- `src/arxiv_daily_push/stage1_b1_report.py`
- `src/arxiv_daily_push/scheduled_execution.py`
- `src/arxiv_daily_push/local_runner.py`

Changed tests:

- `tests/test_mail_templates.py`
- `tests/test_global_scan.py`
- `tests/test_stage1_b1_report.py`
- `tests/test_stage1_historical_previews.py`
- `tests/test_scheduled_execution.py`
- `tests/test_local_runner.py`
- `tests/test_stage2_sources.py`

## What Changed

- Added the private `EMAIL_LEARNING_V1` content object and renderer.
- Routed current daily delivery, Stage1 B1 report email, local runner previews, scheduled production readiness checks, and Stage2 shadow previews through the same renderer.
- Added `mail_product_id` support for `M1`, `M2`, `M3`, and `M4`.
- Added V1 fail-closed validation for required content sections, ChatGPT new-chat links, HTML template marker, M1-M4 ids, and forbidden visible markers.
- Preserved arXiv messages with arXiv abstract and PDF links. Non-arXiv shadow previews keep the same V1 structure with source/detail links and remain non-production.
- Removed obsolete daily email helper paths from `global_scan.py` so future work cannot accidentally reattach the old V2 frontstage.

## Explicit Non-Scope

- No SMTP transport change.
- No scheduler trigger or production enablement change.
- No Release upload change.
- No source adapter, ranking, ROI scoring, queue model, public schema, DB, migration, or state-machine change.
- No V7.1 historical baseline file modification.
- No CURRENT pointer change.

## Acceptance Mapping

- `S2PHT01V1.1-T02`: content object accepted locally.
- `S2PHT01V1.1-T03`: renderer and audited integration paths accepted locally.
- `S2PHT01V1.1-T04`: focused golden/regression tests accepted locally.

This does not claim integrated production acceptance, production restore, scheduler enablement, Release readiness, or final M1-M4 live operations.

## Validation

Current local evidence:

- `python3 -m py_compile` passed for `mail_templates.py`, `global_scan.py`, `stage1_b1_report.py`, `scheduled_execution.py`, and `local_runner.py`.
- Focused email chain unittest passed: 80 tests OK.
- Current `src/` and `tests/` scan found no remaining old V2 visible template strings or old daily email helper names.

Full unit, semantic, governance, render, and diff-check gates are recorded in the paired run manifest after final validation.

## Rollback

Revert:

- the five runtime files listed above;
- the seven test files listed above;
- this phase record;
- `governance/run_manifests/ADP-S2PHT01V1-1-T02-T04-EMAIL-V1-RENDERER-20260625.json`;
- related governance registry/status/event updates.

Rollback does not require data migration because this run did not change public schemas, DB, queue, SMTP, scheduler, Release, or production state.
