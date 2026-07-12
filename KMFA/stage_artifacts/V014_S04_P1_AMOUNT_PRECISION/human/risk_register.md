# KMFA v0.1.4 S04-P1 Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| `RISK-V014-S04P1-001` | Amount normalization evidence uses synthetic values only and does not prove raw business values. | Keep S04-P1 scoped to tool capability and require later raw-authorized mapping phases before business use. | `controlled` |
| `RISK-V014-S04P1-002` | Any business money float use can create precision drift. | `check_no_float_money.py` scans KMFA Python code and the S04-P1 validator requires a forbidden-fixture finding count of 3 plus repository zero findings. | `controlled` |
| `RISK-V014-S04P1-003` | Blank, dash, hash, or abnormal symbols could be interpreted as zero. | Rejection cases require these inputs to raise `AmountNormalizationError`; no silent zero conversion is allowed. | `controlled` |
| `RISK-V014-S04P1-004` | S04-P1 could be mistaken for Stage 4 review or upload readiness. | Manifest locks S04-P2/S04-P3/Stage 4 review/GitHub upload as false and points next step to S04-P2 only. | `controlled` |
