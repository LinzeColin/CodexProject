# PHASE_S2PMT03_WATCHDOG_RECOVERY_B003

- Status: `completed_local_validation`
- Phase: `S2PM`
- Task ID: `S2PMT03-WATCHDOG-RECOVERY-B003`
- Canonical parent task: `S2PMT03`
- Finding ID: `B-003`
- Finding title: `watchdog only reports stale lock and lacks provably safe recovery`
- Acceptance ID: `ACC-S2PMT03-LEASE-FENCING-OUTBOX`
- Completed at: `2026-06-26T21:52:49+10:00`
- Contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record adds a local, pure decision gate for watchdog stale-lock recovery.
The gate proves the watchdog must not take over a stale-looking lease while the
current lease owner is still known live, and may only recover an expired lock
for a dead owner through the existing `claim_leased_item` row-version and
fencing-token path.

## Decisions

- Live owner policy: if `lease_owner` is present in `live_owner_ids`, watchdog
  recovery is blocked even when `lease_until_ms` is older than `now_ms`.
- Dead owner policy: if the lease has expired and the owner is not live,
  watchdog takeover must use the same compare-and-swap/fencing update path as
  normal lease claims.
- Active lease policy: if `lease_until_ms > now_ms`, recovery is blocked even
  when the owner is not live.
- Production policy: this is local evidence only. It does not install or change
  a real watchdog, launchd service, scheduler, SMTP transport, Release upload,
  public schema, DB migration, production queue, source adapter, ranking model,
  CURRENT pointer, V7.1 historical baseline, or V7.2 contract file.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py`
- Tests: `arxiv-daily-push/tests/test_stage2_lease_fencing.py`
- Manifest: `governance/run_manifests/ADP-S2PMT03-WATCHDOG-RECOVERY-B003-20260626.json`

## Validation

- `py_compile`: PASS for `stage2_lease_fencing.py` and `test_stage2_lease_fencing.py`.
- Focused unittest: `test_stage2_lease_fencing.py` ran 9 tests OK.
- Source/board user-center root gate regression: `test_user_center_candidate_pool.py` and `test_owner_controls.py` ran 14 tests OK.
- Full ADP unittest: 526 tests OK.
- V7.2 validator: PASS.
- ADP project governance: 0 errors / 0 warnings.
- Changed-only governance semantic: 0 errors / 0 warnings.
- Governance sync validator: 0 errors / 0 warnings.
- Lean render check: drift_count 0, reference_issue_count 0.
- JSON/JSONL/CSV/YAML parse: OK.
- `git diff --check`: PASS.
- Full semantic extractor: NOT COMPLETED after local interrupt at more than 60 seconds; changed-only semantic governance is the active local closeout gate for this run.

## Remaining Blockers

- This record does not close inherited P0/P1 findings; inherited V7.1 P0=8 and
  P1=37 remain open until independent review closes them.
- `S2PMT07` remains blocked by independent reviewer proof, inherited P0/P1 zero
  state, S2PLT04 completion, final acceptance bundle, independent signoff, and
  final command execution.
- Real production watchdog behavior remains a later production gate and is not
  claimed here.

## Rollback

Revert the S2PMT03 watchdog recovery function, focused tests, this phase record,
run manifest, and governance records. No production runtime state was changed.
