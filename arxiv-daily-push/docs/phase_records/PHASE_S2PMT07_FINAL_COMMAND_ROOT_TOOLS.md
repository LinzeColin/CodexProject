# S2PMT07 Final Command Root Tools

- Timestamp: `2026-06-29T19:06:06+10:00`
- Task ID: `S2PMT07-FINAL-COMMAND-ROOT-TOOLS`
- Parent task: `S2PMT07`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Contract: `ADP-PRODUCT-CONTRACT-V7.2`
- Status: `blocked_final_command_root_tools_ready_bundle_still_incomplete_no_production`

## What Changed

The S2PMT07 final-command contract names two repository-root commands:

```bash
python tools/validate_task_pack.py --root .
python tools/verify_acceptance_bundle.py --require-zero P0 P1
```

This run adds those root entrypoints so the future independent final reviewer can execute the exact contracted command strings from the CodexProject root.

`tools/validate_task_pack.py` validates the active ADP V7.2 contract and ADP project governance from the repository root.

`tools/verify_acceptance_bundle.py` validates the root `FINAL_ACCEPTANCE_BUNDLE/` through the ADP final bundle validator and additionally requires P0/P1 zero proof.

## Current Verified State

- `python tools/validate_task_pack.py --root .`: exits `0`, `status=PASS`.
- `python tools/verify_acceptance_bundle.py --require-zero P0 P1`: exits `2`, `status=FAIL`.
- P0 zero check: `true`.
- P1 zero check: `true`.
- Missing required zero severities: `[]`.
- Final bundle status: `blocked`.
- Remaining final bundle blockers:
  - `final_acceptance_bundle_manifest_missing`
  - `s2plt04_completion_evidence_missing`
  - `independent_review_signoff_missing`
  - `independent_final_command_execution_missing`
  - `next_agent_handoff_missing`

## Boundary

This change does not create `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`, does not record final command execution, does not create `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json`, does not create `FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml`, does not create `FINAL_ACCEPTANCE_BUNDLE/manifest.json`, and does not create `HANDOFF/00_下一Agent先读.md`.

It does not enable SMTP, scheduler, Release, production restore, DAILY_OPERATION, public schema migration, production queue mutation, source adapter changes, ranking changes, CURRENT/V7 edits, S2PLT02 acceptance, S2PLT04 completion, final bundle acceptance, or Stage2/S3 production acceptance.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_root_tool_pycache PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_final_command_root_tools.py -q`
  - Result: `2 tests OK`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_root_tool_pycache PYTHONPATH=arxiv-daily-push/src python3 tools/validate_task_pack.py --root .`
  - Result: `exit 0`, `status=PASS`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_root_tool_pycache PYTHONPATH=arxiv-daily-push/src python3 tools/verify_acceptance_bundle.py --require-zero P0 P1`
  - Result: `exit 2`, `status=FAIL`, P0/P1 zero checks pass, final bundle remains blocked.
