# KMFA v0.1.4 Stage 4 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |
| Basic tool tests could be mistaken for business-value correctness. | Manifest keeps raw value matching, lineage full check, formal report, delivery and business execution false. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts and validator status only; raw/private and secret scans are required before commit. | controlled |
