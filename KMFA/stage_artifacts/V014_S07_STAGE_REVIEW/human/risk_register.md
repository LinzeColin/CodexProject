# KMFA v0.1.4 Stage 7 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |
| Structural adapters could be mistaken for Q5 calculation or formal report readiness. | Manifest keeps Q5 allowed count and formal report allowed count at zero, release blocked, and delivery false. | controlled |
| Redcircle future templates could be mistaken for live connector readiness. | Manifest keeps automatic connector and live connector gates false. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
