# v0.1.4 S02-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| Quality gate bypass allows preview or report without evidence | Q0-Q5 to A-D release gate is locked and missing evidence blocks release | Controlled |
| A grade report is shown without Q5, zero-delta, closed differences, or human confirmation | Grade A requires Q5 plus zero-delta, closed critical differences, and human confirmation | Controlled |
| Protocol evidence is mistaken for a formal report | Manifest keeps `formal_report_allowed=false` and `business_decision_basis_allowed=false` | Controlled |
| Raw/private source data is exposed while documenting quality policy | Phase boundary records no raw read/list/inventory/mutation and forbids plaintext values | Controlled |
| Stage upload is triggered too early | `github_main_upload_allowed=false`; upload deferred until v1.4 Stage 1-18 overall review | Controlled |

Residual risk: this phase defines and validates release-gate policy only. It does not validate real raw values, Q5 authority data, lineage completeness, zero-delta runtime, or formal report readiness.
