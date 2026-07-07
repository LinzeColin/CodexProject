# DWS Contract

## Role

DWS is the optional live acquisition layer for DingTalk data. The attendance pipeline must also support replay from OneDrive raw files and database raw tables.

## Required behavior

1. Prefer dry/config inspection before live calls.
2. Every live acquisition must write raw payloads and response metadata.
3. Every raw payload must be hashed.
4. Pagination and retry status must be recorded.
5. API endpoint, request time range, employee set, and response count must be written to batch metadata.
6. Attendance result and attendance detail endpoints must both be represented.

## Required acquisition outputs

```text
OneDrive/dingtalk_attendance/YYYYMM/
  raw/
    attendance_result/*.json
    attendance_detail/*.json
  manifest/
    import_batch_YYYYMMDDTHHMMSS.json
    raw_hashes_YYYYMMDDTHHMMSS.sha256
  derived/
    canonical_snapshot_YYYYMM.json
```

## API coverage

The live acquisition adapter must collect:

- attendance result records
- attendance detail records with user coordinates and addresses when available
- attendance group metadata when needed for site/geofence validation
- shift metadata when needed for schedule validation
- report columns when used by payroll baseline logic

## Fail behavior

If API response indicates delay, pagination uncertainty, partial response, or permission failure, the run must mark data quality below Q4 until a later run proves completeness.
