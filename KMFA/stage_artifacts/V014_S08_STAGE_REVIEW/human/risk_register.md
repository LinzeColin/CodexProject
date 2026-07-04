# KMFA v0.1.4 Stage 8 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |
| Public-safe identity and entity evidence could be mistaken for raw value matching. | Manifest keeps raw value matching, lineage full check and formal report gates false. | controlled |
| Medium or high risk entity matches could be merged automatically. | Manifest requires manual review and keeps review queue auto merge allowed count at zero. | controlled |
| Legacy upload evidence could be mistaken for current upload gate. | Stage 8 review records legacy upload artifacts as non-current and current upload as not performed. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
