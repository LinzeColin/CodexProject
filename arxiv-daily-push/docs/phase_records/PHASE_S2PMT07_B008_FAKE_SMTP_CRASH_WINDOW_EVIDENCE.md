# PHASE S2PMT07 B-008 FAKE SMTP CRASH WINDOW EVIDENCE

- task_id: `S2PMT07`
- evidence_scope: `B-008`
- severity: `P0`
- status: `fake_smtp_crash_window_evidence_ready_independent_review_required_no_closure`
- date: `2026-06-27`

## Scope

This receipt adds runner-boundary-style fake SMTP crash-window evidence for inherited V7.1 audit finding `B-008`: SMTP accepted but local state not committed.

The new harness is deterministic and local-only. It simulates SMTP accept followed by runner kill before local commit, then restart reconciliation with and without a durable provider accept reference. It does not send real SMTP, alter SMTP transport, enable scheduler operation, install launchd, mutate production queue state, change public schema, change `CURRENT`, edit V7.1 or V7.2 contracts, or claim integrated production acceptance.

## Implementation Evidence

- `arxiv_daily_push.stage2_lease_fencing.simulate_fake_smtp_accept_after_kill`
  - creates an idempotent outbox message with stable `mail_key` and `message_id`;
  - claims the outbox row using the existing lease/fencing claim path;
  - marks the message as `ACCEPTED_PENDING_COMMIT`;
  - records a crash marker at `after_smtp_accept_before_local_commit`;
  - runs restart reconciliation through `reconcile_smtp_accept_crash`;
  - blocks duplicate resend when no durable `provider_accept_ref` exists;
  - converges to `SENT` with `retry_safe=false` when a durable fake provider ref exists.

## Regression Evidence

Focused validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_b008_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_lease_fencing.py arxiv-daily-push/tests/test_stage2_stress_e2e.py arxiv-daily-push/tests/test_smtp_delivery.py -q
```

Observed result:

```text
Ran 41 tests
OK
```

Key new tests:

- `test_fake_smtp_accept_after_kill_blocks_restart_without_provider_ref`
- `test_fake_smtp_accept_after_kill_reconciles_with_provider_ref_without_retry`

## Closure Rule

This strengthens `B-008` evidence beyond the previous model-level crash-window simulation, but inherited P0 closure still requires independent S2PMT07 review and any required reviewer decision on whether local fake SMTP crash injection is sufficient. Current inherited counts remain `P0=8` and `P1=37`; no production state changes are claimed.

