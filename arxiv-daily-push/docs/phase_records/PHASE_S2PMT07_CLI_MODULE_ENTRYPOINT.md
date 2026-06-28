# S2PMT07 CLI Module Entrypoint

## Metadata

- Task ID: `S2PMT07-CLI-MODULE-ENTRYPOINT`
- Parent task: `S2PMT07`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-29T08:46:12+10:00`
- Status: `cli_module_entrypoint_verified_s2plt04_blocked_no_production`
- Product version: `0.23.1`

## Scope

Make the existing ADP CLI executable through Python module invocation:

```bash
python3 -B -m arxiv_daily_push.cli plan-final-bundle-prerequisites --json
```

This fixes a reproducibility gap in the final-bundle proof chain. Before this change, direct `main([...])` calls worked, but `python -m arxiv_daily_push.cli ...` exited without dispatching because the module lacked a `__main__` entrypoint.

## Current Facts

- The module invocation now dispatches to `main()`.
- `plan-final-bundle-prerequisites --json` returns blocked JSON and exit code `2`.
- `next_required_step=S2PLT04_COMPLETION_REPORT`.
- `integrated_production_accepted=false`.
- `real_smtp_send_enabled=false`.
- `scheduler_install_enabled=false`.
- `plan_validation_errors=[]`.

## Validation

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_cli_entry_red PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - Failed as expected because module invocation returned exit code `0` with no JSON.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_cli_entry_green PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - `19 OK`.
- Manual proof: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_cli_entry_manual PYTHONPATH=arxiv-daily-push/src python3 -B -m arxiv_daily_push.cli plan-final-bundle-prerequisites --json`
  - Returned blocked JSON with `next_required_step=S2PLT04_COMPLETION_REPORT` and exit code `2`.

## Boundaries

This change does not create `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json`, does not execute final commands, does not create next-agent handoff, does not create independent review signoff, does not create final manifest, does not close inherited P0/P1 top-level stop gates, does not enable SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance, and does not change CURRENT/V7 contracts, public schema, DB migration, production queue, source adapters, or ranking.

## Next Required Action

Continue the existing pursuing goal with `S2PMT07-S2PLT04-COMPLETION-REPORT`: produce and validate the real S2PLT04 completion report before final command execution, handoff, independent signoff, manifest, or production acceptance can proceed.
