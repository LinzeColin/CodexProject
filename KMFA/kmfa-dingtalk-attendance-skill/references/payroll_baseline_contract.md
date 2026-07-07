# Payroll Baseline Contract

## Purpose

Define when KMFA attendance data may become the payroll calculation baseline input and standard.

## Promotion rule

A target month may be promoted to payroll baseline only when:

1. The natural month has ended.
2. Stage-2 ran on days 1-5 of the following month in evening automation.
3. All five canonical snapshot hashes are exactly identical.
4. Data quality is Q5.
5. No unresolved P0/P1 exception exists.
6. Payroll baseline certificate exists in database and private runtime.

## Payroll baseline candidate fields

Each baseline row must include:

- target_month
- employee_internal_id
- employee_dingtalk_userid
- work_date
- shift_id / shift_name when applicable
- required attendance state
- actual attendance state
- first_in_time
- last_out_time
- late_minutes
- early_leave_minutes
- absent_flag
- missing_punch_count
- leave_or_approval_reference
- location_result
- location_distance_meters when calculable
- trajectory_evidence_count
- source_event_ids
- policy_version_id
- canonical_snapshot_hash
- stage2_certificate_id

## Standardization rule

Payroll calculation should consume the database table or view generated after Q5 acceptance, not employee-level report text.

## Reversal rule

If a post-acceptance correction appears:

1. Record a new import batch.
2. Generate a new canonical snapshot.
3. Mark previous payroll baseline version superseded.
4. Re-run controlled consensus protocol or run a separately approved correction protocol.
5. Keep both versions traceable.
