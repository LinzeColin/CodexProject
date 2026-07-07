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

Current offline implementation path:

1. `scripts/inspect_raw_archive_month.py` validates private OneDrive archive
   manifest/raw count parity, raw SHA-256 parity, seed-raw isolation, and
   location evidence coverage.
2. `scripts/prepare_raw_replay_day_fact_bundle.py` materializes private day
   facts and raw-detail linkage from that replay.
3. `scripts/prepare_stage2_source_from_raw_replay.py` converts the private day
   facts into a Stage-2 source snapshot using hashed employee identifiers.
4. `scripts/resolve_stage2_source.py` can call that bridge during eligible
   evening automation when `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact`.

This path proves replay and raw-to-derived linkage only. Database commit and
verification gates remain false until the approved PostgreSQL execution guard
has actually run against a non-production target.
