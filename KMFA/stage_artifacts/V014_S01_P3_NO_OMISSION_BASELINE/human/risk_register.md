# KMFA v0.1.4 S01-P3 Risk Register

| Risk | Severity | Status | Control |
|---|---:|---|---|
| v1.4 roadmap tasks are only partially represented | High | controlled | Validator requires 18 stages, 54 phases and 162 tasks parsed from the v1.4 roadmap baseline. |
| P0/P1 requirements are not bound to tasks/tests/evidence | High | controlled | Validator checks legacy P0/P1 matrix and v1.4 overlay rows all have covered stages, task bindings, acceptance gates, tests and evidence refs. |
| S01-P3 expands into Stage review or S02 | Medium | controlled | Manifest and validator require `stage_review_performed=false`, `s02_started=false` and local-only no-upload state. |
| Raw/private data leaks through evidence | High | controlled | This phase does not read/list raw inbox; validator and scans reject raw/private paths, binary raw artifacts and forbidden evidence text. |
