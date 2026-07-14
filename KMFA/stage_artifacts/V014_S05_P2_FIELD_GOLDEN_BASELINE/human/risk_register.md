# KMFA v0.1.4 S05-P2 Risk Register

| risk_id | risk | control | status |
| --- | --- | --- | --- |
| V014-S05P2-R01 | Field candidates are not Q4/Q5 authority records yet. | Keep Q4/Q5 counts at 0 and require S05-P3 separate run. | controlled |
| V014-S05P2-R02 | Raw source values or locators could leak into public evidence. | Validator rejects raw files, source headers, sheet/member names, row/cell values and business values. | controlled |
| V014-S05P2-R03 | Excel workbook candidate cannot be promoted without owner handling. | Active owner/authorized downgrade keeps Excel fields cross-source support only. | controlled |

- next_required_phase: `S05-P3`
- github_upload_status: `not_uploaded_deferred_until_v014_stage1_18_complete`
