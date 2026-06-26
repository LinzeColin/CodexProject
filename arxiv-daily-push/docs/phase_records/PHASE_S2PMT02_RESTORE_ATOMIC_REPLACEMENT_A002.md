# PHASE S2PMT02 Restore Atomic Replacement A002

## Summary

- phase: `S2PM`
- task_id: `S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002`
- parent_task_id: `S2PMT02`
- acceptance_id: `ACC-S2PMT02-ATOMIC-RECOVERY`
- finding_id: `A-002`
- model_id: `MOD-ADP-111`
- formula_id: `FORM-ADP-113`
- parameter_ids: `PARAM-ADP-940` through `PARAM-ADP-944`
- status: `completed_local_validation_no_production`
- generated_at: `2026-06-27T08:34:18+10:00`

This record refreshes inherited P0 finding `A-002` with dedicated current evidence. It uses real Stage 1 backup and restore probes to verify atomic restore replacement behavior without enabling production restore.

## Probe Results

| Probe | Expected result | Current result |
|---|---|---|
| `valid_restore_new_target` | Valid backup restores into a new target database and the target SHA-256 matches the backup | pass |
| `valid_overwrite_with_previous_backup` | Valid overwrite restore creates a previous-target backup, preserves the old target SHA-256 in that backup, and replaces the target with the backup SHA-256 | pass |
| `invalid_overwrite_preserves_target` | Invalid overwrite restore is blocked, existing target SHA-256 is preserved, and temporary restore files are cleaned | pass |

## Evidence

- [A-002 run manifest](../../../governance/run_manifests/ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json)
- [stage1_runtime.py](../../src/arxiv_daily_push/stage1_runtime.py)
- [stage2_atomic_recovery.py](../../src/arxiv_daily_push/stage2_atomic_recovery.py)
- [test_stage2_atomic_recovery.py](../../tests/test_stage2_atomic_recovery.py)
- [Owner-facing scan page](../../用户中心/恢复原子替换扫描.md)

## Boundaries

No production restore was executed. This record does not send SMTP, install or enable scheduler, upload Release assets, change public schema, run DB migration, mutate production queues, change ranking or source adapters, edit `CURRENT`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Remaining Gate

`A-002` remains open until S2PMT07 independent review inspects or reruns this evidence and explicitly closes the finding. This local evidence refresh does not change inherited P0/P1 counters.
