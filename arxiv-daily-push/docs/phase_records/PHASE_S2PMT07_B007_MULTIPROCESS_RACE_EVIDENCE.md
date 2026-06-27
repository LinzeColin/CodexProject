# PHASE S2PMT07 B-007 MULTIPROCESS RACE EVIDENCE

- task_id: `S2PMT07`
- evidence_scope: `B-007`
- severity: `P0`
- status: `multiprocess_race_evidence_ready_independent_review_required_no_closure`
- date: `2026-06-27`

## Scope

This receipt adds runner-boundary-style multiprocess race evidence for inherited V7.1 audit finding `B-007`: missing production-grade race test for dual scheduler, dual worker, and repeated triggers.

The new harness is deterministic and local-only. It uses multiple local processes to compete for one cycle's M1-M4 active revisions, proving that 100 repeated triggers per product leave only one active revision per mail product and block duplicate claims. It does not install or enable a scheduler, run launchd, send SMTP, mutate production queue state, change public schema, change `CURRENT`, edit V7.1 or V7.2 contracts, or claim integrated production acceptance.

## Implementation Evidence

- `arxiv_daily_push.stage2_stress_e2e.simulate_multiprocess_dual_scheduler_race`
  - uses Python `multiprocessing` with spawn context to cross a local process boundary;
  - fans out 400 trigger attempts for one cycle across M1-M4;
  - protects active revision claims with a shared lock;
  - records one active revision for each of M1, M2, M3, and M4;
  - records 396 blocked duplicate race attempts;
  - records worker exit codes and keeps scheduler installed/enabled flags false.

## Regression Evidence

Focused validation command on `origin/main@c4d5897e23c07bfb1875b08d788bfdf39f182f02`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_b007_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_stress_e2e.py -q
```

Observed result:

```text
Ran 20 tests
OK
```

Key new test:

- `test_multiprocess_dual_scheduler_race_keeps_one_active_revision_per_mail_product`

## Closure Rule

This strengthens `B-007` evidence beyond the previous single-process deterministic simulation, but inherited P0 closure still requires independent S2PMT07 review and any required reviewer decision on whether local multiprocess race evidence is sufficient or real scheduler / multi-host proof remains required. Current inherited counts remain `P0=8` and `P1=37`; `S2PMT07`, `S2PLT04`, `DAILY_OPERATION`, and integrated production acceptance remain blocked.
