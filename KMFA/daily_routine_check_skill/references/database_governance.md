# Database And Log Governance

## Goal

This system should support future work, KPI, and behavior-analysis data needs. It must preserve evidence and data lineage without turning GitHub into a raw data store.

## Storage Plan

### Active Local Runtime

```text
KMFA/metadata/daily_routine_check/private_runtime/
  daily_routine_check.sqlite
  daily_routine_check.sqlite-wal
  daily_routine_check.sqlite-shm
  .env.local
  notification_targets.local.json
```

The active SQLite database stays local to avoid OneDrive sync-lock conflicts during writes.

### OneDrive Durable Archive

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/YYYYMM/
  run_log_YYYYMM.jsonl
  routine_check_results_YYYYMM.jsonl
  ocr_jobs_YYYYMM.jsonl
  ocr_extractions_YYYYMM.jsonl
  cash_account_snapshots_YYYYMM.jsonl
  cash_flow_entries_YYYYMM.jsonl
  cash_risk_results_YYYYMM.jsonl
  notification_events_YYYYMM.jsonl
  data_quality_issues_YYYYMM.jsonl
  db_snapshots/daily_routine_check_YYYYMMDD.sqlite.gz
  cleanup/cleanup_report_YYYYMMDD.json
```

### GitHub Public Metadata

```text
KMFA/metadata/daily_routine_check/
```

GitHub stores rules, manifests, schema descriptions, templates, and public-safe evidence. GitHub should not store live SQLite or raw DWS exports.

## SQLite Tables

Recommended tables:

```text
source_runs
source_messages
source_files
document_candidates
routine_rules_snapshot
routine_check_results
ocr_jobs
ocr_extractions
cash_account_snapshots
cash_flow_entries
cash_risk_results
notification_events
data_quality_issues
run_log
git_sync_events
cleanup_events
```

## Data Retention

Default retention:

```text
Active SQLite: current + recent months, compact weekly
JSONL logs in OneDrive: 24 months
OCR raw text cache: 12 months or until reprocessed into structured extraction
Image thumbnails/cache: 90 days if recreated from DWS output
Notification logs: 24 months
DB snapshots: daily for 30 days, month-end for 24 months
```

Retention must be configurable.

## Cleanup Rules

The system must provide cleanup commands:

```bash
python3 -m KMFA.tools.daily_routine_check.main --cleanup --dry-run
python3 -m KMFA.tools.daily_routine_check.main --cleanup --apply
```

Cleanup should:

- checkpoint SQLite WAL
- vacuum SQLite when safe
- write a `cleanup_events` ledger row
- keep future hooks for expired OCR raw cache deletion, JSONL compression, local log rotation, and OneDrive cleanup reports
- never delete the source DWS output folder

## Accuracy And Auditability

Each result must preserve:

- run_at_beijing
- check_date
- trigger_window
- rules_evaluated
- rules_skipped
- rule id
- check date
- group name
- sender requirement
- matched sender
- matched message id
- matched file sha256
- OCR/LLM model/provider if used
- parser version
- confidence
- data quality status
- notification status

## Non-Developer Management

All routine rules and thresholds live in YAML:

```text
KMFA/metadata/daily_routine_check/routine_rules.public.yaml
KMFA/metadata/daily_routine_check/cash_monitor.public.yaml
```

A non-developer should be able to change due time, sender, keyword alias, or threshold without editing Python.
