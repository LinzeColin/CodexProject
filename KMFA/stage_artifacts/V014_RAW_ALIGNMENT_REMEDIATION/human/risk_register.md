# KMFA v0.1.4 Raw Alignment Remediation Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| RAW-ID-001 | Local raw container hash/size does not match registered source package | Keep NO_GO and require owner source identity decision | open |
| RAW-ID-002 | Public artifacts could leak raw identifiers | Validator scans evidence for raw/private tokens and raw extensions | controlled |
| RAW-ID-003 | Lineage closure could proceed from unconfirmed raw identity | Gate lineage full check behind owner source identity confirmation | blocked |
