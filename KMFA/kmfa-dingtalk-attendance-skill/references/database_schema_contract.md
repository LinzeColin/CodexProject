# Database Schema Contract

## Database target

Use PostgreSQL-compatible schema for the long-term KMFA attendance database.

SQLite can remain as local transition ledger/cache. The durable payroll-facing design should be PostgreSQL because stage-2 and payroll workflows need transactional writes, constraints, indexes, and multi-user review.

## Required schema properties

| Property | Requirement |
|---|---|
| Raw preservation | Store raw API payload JSONB unchanged. |
| Idempotency | Unique source keys and raw hashes prevent double import. |
| Traceability | Derived records link to raw source IDs, import batch, policy version. |
| Versioned rules | Policy and rule config snapshots are versioned by effective period. |
| Location evidence | Store latitude/longitude/address/base site/trajectory points. |
| Payroll baseline | Baseline candidate rows derive only from accepted stage-2 state. |
| Auditability | Every stage-2 run and consensus certificate is recorded. |

## Current validation level

The repo includes an offline contract dry-run validator:

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_database_contract.py \
  --schema KMFA/kmfa-dingtalk-attendance-skill/database/postgres_schema.sql \
  --views KMFA/kmfa-dingtalk-attendance-skill/database/views_payroll_baseline.sql \
  --print-json
```

This validator checks required PostgreSQL objects and simulates the accepted
stage-2 certificate -> payroll baseline query path in memory. It does not open
a PostgreSQL connection, mutate a database, read private raw data, or call live
DWS. Real PostgreSQL migration and ingest remain separate gated work.

## Core entities

```text
raw_import_batch
employee_identity_map
raw_attendance_result
raw_attendance_detail
attendance_trajectory_point
attendance_group_snapshot
shift_snapshot
attendance_day_fact
attendance_punch_fact
policy_version
rule_config_snapshot
classification_result
exception_case
stage2_shadow_run
stage2_consensus_certificate
payroll_baseline_attendance
payroll_export_audit
integrity_audit_log
```

## Primary design principle

```text
raw evidence is immutable
normalized facts are reproducible
classification is policy-versioned
stage-2 consensus is hash-based
payroll baseline is generated only from Q5 target month state
```
