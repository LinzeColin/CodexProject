# KMFA v0.1.4 S07-P2 Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| WPS adapter evidence could be mistaken for raw WPS import. | Manifest keeps raw inbox read false and publishes only refs/fingerprints/counts. | controlled |
| Native WPS files could be treated as directly parsed. | Conversion guidance keeps native WPS parse status as conversion required. | controlled |
| Adapter evidence could be mistaken for Stage 7 completion. | Manifest keeps S07-P3 and Stage 7 review false. | controlled |
