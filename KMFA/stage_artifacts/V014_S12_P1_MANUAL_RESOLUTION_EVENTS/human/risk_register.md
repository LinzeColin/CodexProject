# v0.1.4 S12-P1 Risk Register

| Risk | Control |
|---|---|
| Event UI appears to change source data | Manifest and validator require raw/source writes to remain false |
| Approved event is edited silently | Approved event requires immutable flag and reverse event chain |
| S12-P1 accidentally performs impact preview/rerun | Phase boundaries and quality gate keep S12-P2/S12-P3 false |
| Public evidence leaks raw/private data | Validator and safety scans forbid raw values, raw paths, files, and credentials |
