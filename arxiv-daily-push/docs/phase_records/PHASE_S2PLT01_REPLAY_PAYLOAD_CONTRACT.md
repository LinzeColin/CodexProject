# PHASE S2PLT01 Replay Payload Contract

Task: `S2PLT01-REPLAY-PAYLOAD-CONTRACT`

Parent task: `S2PLT01`

Acceptance: `ACC-S2PLT01-30D`

## Scope

This run adds a no-production payload envelope for explicit S2PLT01 replay evidence before that evidence is consumed by the replay evidence gate and entry precheck.

The payload contract requires:

- `payload_id`, `generated_at`, `generated_by`, and `evidence_mode`
- non-empty payload-level `evidence_refs`
- deterministic `payload_hash`
- replay evidence for 30 independent days, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, D1-D4 source domains, B1-B6 reading boards, and D1-D4 terminal source states
- zero future leakage and zero replay P0/P1 counters in the provided records
- every production, CURRENT, and V7 baseline side-effect flag false

## Non-Scope

This run does not execute the real 30-day replay payload, accept `S2PLT01`, complete `S2PLT04`, close inherited V7.1 P0/P1 findings, enable SMTP, install scheduler, upload Release assets, mutate public schema/DB/production queue, change source adapters or ranking, edit CURRENT or V7.1/V7.2 contract files, enable `DAILY_OPERATION`, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Validation

- py_compile: PASS
- focused `test_stage2_replay_gate.py`: 12 OK
- full ADP unittest: 469 OK
- V7.2 validator: PASS
- project governance: 0 errors / 0 warnings
- changed-only semantic governance: 0 errors / 0 warnings
- lean render: drift_count 0, reference_issue_count 0
- JSONL/CSV/manifest parse: OK
- `git diff --check`: PASS
- production-side-effect forbidden scan: no true/enabling hits
- full semantic extractor: NOT COMPLETED after local interrupt at >150 seconds during full-table AST parsing

## Remaining Blockers

- inherited V7.1 P0 findings: 8
- inherited V7.1 P1 findings: 37
- actual S2PLT01 30-day replay payload execution: available as local no-production evidence via `ADP-S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626`
- independent S2PLT01 replay review: available as local no-production evidence via `ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626`
- S2PLT01 acceptance: blocked
- S2PLT04: incomplete
- S2PMT07 final independent production gate: blocked

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage2_replay_gate.py`
- `arxiv-daily-push/tests/test_stage2_replay_gate.py`
- `governance/run_manifests/ADP-S2PLT01-REPLAY-PAYLOAD-CONTRACT-20260626.json`
