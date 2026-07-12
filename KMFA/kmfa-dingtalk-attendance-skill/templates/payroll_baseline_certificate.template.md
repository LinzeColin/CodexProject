# KMFA Payroll Baseline Certificate - {{target_month}}

status: {{stage2_status}}
quality_grade: {{quality_grade}}
canonical_snapshot_hash: {{canonical_snapshot_hash}}
stage2_certificate_id: {{stage2_certificate_id}}

## Acceptance basis

- Five evening stage-2 runs completed: {{five_runs_completed}}
- Five canonical hashes identical: {{five_hashes_identical}}
- P0 unresolved: {{p0_unresolved}}
- P1 unresolved: {{p1_unresolved}}
- Location evidence threshold: {{location_evidence_status}}
- Trajectory evidence threshold: {{trajectory_evidence_status}}
- Database reconciliation: {{database_reconciliation_status}}

## Payroll baseline table/view

{{payroll_baseline_relation}}

## Source batches

{{source_batches}}
