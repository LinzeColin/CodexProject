# KMFA v0.1.4 Stage 9 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v0.1.4 Stage 1-18 complete overall review. | controlled |
| Public-safe cost and reconciliation evidence could be mistaken for raw value matching. | Manifest keeps raw value matching, lineage full check and formal report gates false. | controlled |
| Pending reconciliation could be bypassed by derived rerun. | Manifest keeps confirmed resolution count at zero and derived metric rerun allowed count at zero. | controlled |
| Legacy Stage 9 upload or batch gate evidence could be mistaken for current upload gate. | Stage 9 review records legacy upload artifacts as non-current and current upload as not performed. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
