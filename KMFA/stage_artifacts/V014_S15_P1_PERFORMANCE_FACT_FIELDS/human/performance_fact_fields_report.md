# KMFA v0.1.4 S15-P1 Performance Fact Fields

- task_id: `KMFA-V014-S15-P1-PERFORMANCE-FACT-FIELDS-20260705`
- status: `completed_validated_local_only_no_go_upload_deferred_performance_fact_fields_locked`
- phase_scope: `v014_s15_p1_performance_fact_fields_only`
- field_definition_count: `6`
- field_binding_count: `6`
- manual_review_field_count: `4`
- performance_fact_table_count: `0`
- salary_calculation_count: `0`
- bonus_approval_count: `0`
- payroll_export_count: `0`
- github_upload_performed: `false`
- next_phase: `S15-P2`

## Fields

- invoice_amount
- gross_margin_rate
- settlement_speed
- collection_speed
- audit_variance
- customer_relationship_rate

## Manual Review Fields

- settlement_speed
- collection_speed
- audit_variance
- customer_relationship_rate

## Boundary

This phase only locks field slots, source refs, hash refs and manual-review markers.
It does not output the review list, salary calculation, bonus approval, payroll export,
final payment, formal report, GitHub upload or business execution.
