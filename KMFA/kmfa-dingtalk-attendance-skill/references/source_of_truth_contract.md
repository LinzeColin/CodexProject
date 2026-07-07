# Source of Truth Contract

## Source hierarchy

| Layer | Role | Use in pipeline |
|---|---|---|
| DingTalk API raw payload | Acquired evidence | Stored unchanged and hashed. |
| OneDrive raw archive | Durable monthly raw mirror | Used for replay, audit, and recovery. |
| PostgreSQL raw tables | Queryable raw evidence | Used for joins, constraints, repeatability. |
| PostgreSQL derived facts | Payroll-facing normalized facts | Generated from raw + policy version. |
| Canonical snapshot | Stage-2 comparison artifact | Must be identical across 5 evening runs. |
| Payroll baseline candidate | Calculation input standard | Emitted after accepted stage-2 consensus. |

## Required DingTalk sources

Collect at least two categories:

1. Attendance result records: scheduled/result-level records.
2. Attendance detail records: detail-level records including location evidence.

The pipeline must store full source payloads even when the normalized columns cover the known fields. Unknown fields are not discarded; they remain available in `raw_payload` JSONB.

## Required location and trajectory evidence

For strict attendance standards, store these fields whenever DingTalk returns them:

| Field group | Examples |
|---|---|
| User coordinate | `userLatitude`, `userLongitude` |
| User address | `userAddress` |
| Base coordinate | `baseLatitude`, `baseLongitude` |
| Base address | `baseAddress` |
| Result fields | `locationResult`, `timeResult` |
| Punch timing | `userCheckTime`, `baseCheckTime`, `checkType` |
| Device/source | `sourceType`, `deviceId`, device/source descriptors if present |
| Approval link | `procInstId`, `approveId`, correction/approval IDs if present |
| Raw evidence | full JSON payload for each record |

If a source only returns one GPS point for a punch, represent it as a trajectory point with `point_index = 0`. If a source returns multiple movement/path points, store all points with sequence and timestamp.

## Missing evidence handling

Do not fill missing GPS, address, device, approval, or trajectory fields by inference.

Required behavior:

1. Store null in the normalized column.
2. Keep raw payload.
3. Add a data-quality issue with employee, date, source endpoint, and missing field.
4. Block stage-2 acceptance if the missing evidence violates configured payroll-grade thresholds.

## Replay principle

A target month must be replayable from raw archive and policy version:

```text
raw payloads + employee map + policy version + rule config snapshot
  -> normalized facts
  -> classification results
  -> canonical snapshot
  -> payroll baseline candidate
```
