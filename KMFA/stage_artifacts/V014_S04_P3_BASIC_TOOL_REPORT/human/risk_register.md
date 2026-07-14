# KMFA v0.1.4 S04-P3 Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| `RISK-V014-S04P3-001` | Synthetic boundary cases validate tool behavior but do not prove raw business source correctness. | Keep S04-P3 scoped to public-safe tool tests; raw value matching and authoritative baseline work remain out of scope. | `controlled` |
| `RISK-V014-S04P3-002` | Tool report could be mistaken for Stage 4 review or upload readiness. | Manifest locks Stage 4 review/upload/S05/GitHub upload as false and points next step to a separate Stage 4 review run. | `controlled` |
| `RISK-V014-S04P3-003` | Amount/date/period edge cases could drift from tool implementation. | Validator recomputes all 22 synthetic cases and requires 22/22 PASS before accepting evidence. | `controlled` |
