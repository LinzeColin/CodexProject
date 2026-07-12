# Risk Register

| Risk | Control | Status |
|---|---|---|
| Readiness recheck could be mistaken for source-map completion. | Go/No-Go remains NO_GO and reapplication_performed=false. | controlled |
| Private template details could leak into public evidence. | Public artifacts contain aggregate counts and refs only; private diagnostic remains git-ignored. | controlled |
| Raw/private data could be modified. | Raw inbox access and mutation flags remain false; this phase does not touch raw data. | controlled |
