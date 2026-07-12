# KMFA v0.1.4 S04-P2 Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| `RISK-V014-S04P2-001` | Field standardization evidence uses synthetic values only and does not prove raw business header mapping. | Keep S04-P2 scoped to public-safe tool capability; raw value matching and authorized mapping remain later blocked work. | `controlled` |
| `RISK-V014-S04P2-002` | Missing or invalid fields could be silently skipped. | Validator requires five quality-status records for incomplete synthetic replay and `field_skipped_silently=false`. | `controlled` |
| `RISK-V014-S04P2-003` | Source aliases could leak raw headers. | Mapping evidence stores alias hash/key only and the public boundary forbids raw source field/header plaintext publication. | `controlled` |
| `RISK-V014-S04P2-004` | S04-P2 could be mistaken for Stage 4 review or upload readiness. | Manifest locks S04-P3/Stage 4 review/GitHub upload as false and points next step to S04-P3 only. | `controlled` |
