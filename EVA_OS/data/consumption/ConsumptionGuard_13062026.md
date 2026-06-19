# EVA_OS Consumption Guard 2026-06-13

## Summary
- System: `EVA_OS`
- Status: `MissingConsumptionEvidence`
- Generated At: `2026-06-13T16:32:50`
- Counted Spend: `0`
- Impulse Spend: `0`
- Fixed Cost: `0`
- Investable Cashflow Pressure: `None`

## Action Queue
| priority | status | action | source |
| --- | --- | --- | --- |
| P0 | Open | 录入至少一条消费事件，并附上账单、截图、导出 CSV 或可复核说明。 | Consumption Evidence |

## Category Totals
| category | amount | high_risk_amount | count |
| --- | --- | --- | --- |


## Events
| event_date | event_type | category | amount | risk_level | review_status | evidence_status | merchant |
| --- | --- | --- | --- | --- | --- | --- | --- |


## Assumptions
- Only Reviewed events with evidence_link or evidence_path are counted in spend, impulse, fixed-cost, and pressure summaries.
- PendingReview, Rejected, or missing-evidence events stay in the ledger but do not affect guard metrics.
- monthly_investable_budget is a user-supplied planning value; it is not read from bank, payroll, Alipay, tax, or brokerage systems.
- Risk scores are behavior-review aids, not medical, legal, financial, investment, or payment advice.
- No payment, transfer, bank action, investment order, or external account action is executed.
