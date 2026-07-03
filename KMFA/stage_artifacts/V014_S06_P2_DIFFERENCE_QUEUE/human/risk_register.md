# Risk Register

| Risk | Control | Status |
|---|---|---|
| Synthetic queue passes but actual business source conflict is unresolved | Manifest marks actual business difference validation false and keeps D/NO_GO | controlled |
| S06-P3 metadata quality is accidentally written early | Generator writes only stage evidence and flags metadata_quality_written false | controlled |
| Unclosed difference is treated as A-grade-ready | Report grade gate blocks A until manual closure | controlled |
| Raw data exposure | Evidence contains synthetic public-safe refs only and no raw inbox access | controlled |
