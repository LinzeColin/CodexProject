# KMFA v0.1.4 S16-P3 Risk Register

- task_id: `KMFA-V014-S16-P3-CUSTOMER-BUSINESS-ANALYSIS-20260705`

| Risk | Control | Status |
| --- | --- | --- |
| 客户摘要被误用为正式经营结论 | `formal_report_allowed=false` and `business_decision_basis_allowed=false` | controlled |
| 客户价值信号被误用为自动排名 | `automatic_customer_ranking_allowed=false` | controlled |
| 催收或法务动作越界 | `collection_action_allowed=false` and `legal_collection_decision_allowed=false` | controlled |
| raw/private 信息进入公开证据 | validator and scans block raw identifiers, headers, values, workbooks and credentials | controlled |
| S16-P3 越界进入 Stage 16 review 或 upload | `stage16_review_scope_included=false` and `github_upload_scope_included=false` | controlled |
