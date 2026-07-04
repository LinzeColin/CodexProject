# KMFA v0.1.4 S08-P2 Risk Register

| Risk | Control | Status |
|---|---|---|
| Business entity schema is mistaken for a fact layer | `fact_layer_scope_included=false`; S09 remains required | controlled |
| Relationship schema is mistaken for raw value matching | `relationship_values_schema_only=true`; S08-P3 remains required | controlled |
| Lifecycle statuses are used as release approval | `formal_report_allowed=false`; `business_execution_allowed=false` | controlled |
| Raw/private data leaks into public evidence | semantic scan plus raw/private extension and secret scans | controlled |
| Stage 8 review or GitHub upload starts too early | `stage8_review_scope_included=false`; upload deferred to Stage 1-18 completion | controlled |
