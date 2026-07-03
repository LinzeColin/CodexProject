# KMFA v0.1.4 S01-P2 Risk Register

| Risk | Severity | Status | Control |
|---|---|---|---|
| Raw/private package payload accidentally copied into Git | High | controlled | S01-P2 sync selects only S01-P1 public-source SHA256 entries and normalized repo targets; validator blocks forbidden binary/raw extensions. |
| Source package internal entry names reveal raw/private structure | Medium | controlled | Baseline manifest stores labels, hashes and normalized target paths; source package internal entry names are not committed. |
| S01-P2 scope expands into S01-P3 or Stage review | Medium | controlled | Manifest and validator require `s01_p3_started=false`, `stage_review_performed=false`, `github_upload_performed=false`. |
| Time reference used as quality waiver | Medium | controlled | Chinese entries and manifest record quality-over-time rule: quality gate failure blocks delivery. |

No raw inbox read/list/mutation was required for this phase.
