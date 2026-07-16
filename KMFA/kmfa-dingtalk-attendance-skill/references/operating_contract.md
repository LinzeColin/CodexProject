# Operating Contract

## Goal

Create one stable operating contract for KMFA DingTalk attendance so any agent or automation run can execute the same sequence and produce comparable outputs.

## Required invariants

| Invariant | Requirement |
|---|---|
| Repo identity | `/Users/linzezhang/CodexProject` is the configured cwd and private-state location; repo state is diagnostic only. |
| Production release | Natural attendance runs only the verified immutable `attendance-production/current` release. |
| Repository diagnostics | Branch, HEAD, origin HEAD, and dirty paths are recorded but never block attendance. |
| Target month | Stage-2 target month is always the previous natural month when local date is day 1-5. |
| Timezone | Attendance month boundary defaults to `Asia/Shanghai` unless repo config overrides. |
| Morning run | No stage-2 acceptance. |
| Evening run | May run monthly stage-2 gate if eligible. |
| Output determinism | Canonical snapshots must be stable under key ordering, timestamp noise, path changes, and run IDs. |

## OneDrive and runtime paths

```text
OneDrive raw root:
  /Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/

Private runtime root:
  KMFA/metadata/dingtalk_attendance/private_runtime/

Recommended stage-2 runtime path:
  KMFA/metadata/dingtalk_attendance/private_runtime/stage2/YYYYMM/run_01/
  KMFA/metadata/dingtalk_attendance/private_runtime/stage2/YYYYMM/run_02/
  KMFA/metadata/dingtalk_attendance/private_runtime/stage2/YYYYMM/run_03/
  KMFA/metadata/dingtalk_attendance/private_runtime/stage2/YYYYMM/run_04/
  KMFA/metadata/dingtalk_attendance/private_runtime/stage2/YYYYMM/run_05/
```

## Run sequence

```text
preflight
  -> inspect runtime
  -> acquire or load raw
  -> validate raw schema
  -> ingest database transaction
  -> derive normalized facts
  -> apply policy version
  -> classify results
  -> detect exceptions
  -> build canonical snapshot
  -> write run manifest
  -> if stage-2 eligible, compare consensus
```

## Stop conditions

Stop and report if any of these occurs:

1. Target month cannot be resolved.
2. Production release is incomplete, its fingerprint fails, or the live prompt does not match.
3. DWS/API acquisition returns partial data without a complete retry/audit marker.
4. Required employees cannot be mapped.
5. Required location/detail fields are missing beyond configured thresholds.
6. Database transaction fails or cannot be verified.
7. Any unresolved P0/P1 exception remains.
8. Rule drift is detected.
9. Stage-2 run is attempted outside day 1-5 or outside evening slot.
10. Five-run consensus is not exact.

## Run manifest minimum fields

```json
{
  "run_id": "YYYYMMDDTHHMMSSZ-uuid",
  "skill_name": "kmfa-dingtalk-attendance-skill",
  "run_slot": "morning|evening|manual",
  "target_month": "YYYYMM",
  "run_index": 1,
  "source_batches": [],
  "raw_hashes": [],
  "database_transaction_marker": "...",
  "canonical_snapshot_hash": "sha256:...",
  "quality_grade": "Q0|Q1|Q2|Q3|Q4|Q5",
  "unresolved_exceptions": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
  "stage2_status": "not_eligible|pending|accepted|failed",
  "next_action": "..."
}
```
