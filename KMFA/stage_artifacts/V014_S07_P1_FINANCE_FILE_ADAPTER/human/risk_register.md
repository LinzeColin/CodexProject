# KMFA v0.1.4 S07-P1 Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Adapter evidence could be mistaken for raw-data reconciliation. | Manifest keeps raw inbox read false and Q5/formal report counts at zero. | controlled |
| Adapter evidence could be mistaken for Stage 7 completion. | Manifest keeps S07-P2, S07-P3 and Stage 7 review false. | controlled |
| Public evidence could leak private source details. | Outputs use refs, fingerprints and aggregate counts only, followed by safety scans. | controlled |
