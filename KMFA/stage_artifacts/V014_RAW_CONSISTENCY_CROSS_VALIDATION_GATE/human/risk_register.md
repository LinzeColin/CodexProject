# KMFA v0.1.4 Raw Consistency Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| RAW-CV-001 | Source container identity could be confused with business-value consistency | Keep separate flags and leave business value consistency false | controlled |
| RAW-CV-002 | Public artifacts could leak raw identifiers | Validator scans new evidence for raw paths, raw names, raw hashes and business values | controlled |
| RAW-CV-003 | Upload or app reinstall could be inferred from a baseline lock | Keep Go/No-Go as NO_GO and all release gates false | blocked |
