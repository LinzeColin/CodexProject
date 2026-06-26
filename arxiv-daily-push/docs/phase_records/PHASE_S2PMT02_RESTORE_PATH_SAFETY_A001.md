# PHASE S2PMT02 Restore Path Safety A001

## Summary

- phase: `S2PM`
- task_id: `S2PMT02-RESTORE-PATH-SAFETY-A001`
- parent_task_id: `S2PMT02`
- acceptance_id: `ACC-S2PMT02-ATOMIC-RECOVERY`
- finding_id: `A-001`
- model_id: `MOD-ADP-110`
- formula_id: `FORM-ADP-112`
- parameter_ids: `PARAM-ADP-935` through `PARAM-ADP-939`
- status: `completed_local_validation_no_production`
- generated_at: `2026-06-27T08:05:48+10:00`

This record refreshes inherited P0 finding `A-001` with dedicated current evidence. It uses real Stage 1 restore probes to verify that restore rejects relative path traversal, absolute path escape, and symlink escape, and that a blocked invalid restore preserves an existing target database.

## Probe Results

| Probe | Expected result | Current result |
|---|---|---|
| `relative_path_traversal` | blocked with `backup database path traversal is not allowed`; target not created | pass |
| `absolute_path_escape` | blocked with `backup database path traversal is not allowed`; target not created | pass |
| `symlink_escape` | blocked with `backup database path escapes backup root`; target not created | pass |
| `target_preserved_on_block` | blocked restore preserves existing target bytes | pass |

## Evidence

- [A-001 run manifest](../../../governance/run_manifests/ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json)
- [stage1_runtime.py](../../src/arxiv_daily_push/stage1_runtime.py)
- [stage2_atomic_recovery.py](../../src/arxiv_daily_push/stage2_atomic_recovery.py)
- [test_stage2_atomic_recovery.py](../../tests/test_stage2_atomic_recovery.py)
- [Owner-facing scan page](../../用户中心/恢复路径安全扫描.md)

## Boundaries

No production restore was executed. This record does not send SMTP, install or enable scheduler, upload Release assets, change public schema, run DB migration, mutate production queues, change ranking or source adapters, edit `CURRENT`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Remaining Gate

`A-001` remains open until S2PMT07 independent review inspects or reruns this evidence and explicitly closes the finding. This local evidence refresh does not change inherited P0/P1 counters.
