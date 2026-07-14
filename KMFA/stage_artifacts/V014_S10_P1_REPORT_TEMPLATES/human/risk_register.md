# KMFA v0.1.4 S10-P1 Risk Register

| Risk | Status | Mitigation |
|---|---|---|
| Report templates are mistaken for formal reports | blocked | Manifest keeps formal_report_allowed=false and export_artifact_count=0. |
| v1.4 UIUX baseline is ignored | controlled | Manifest records v1.4 HTML/UIUX audit refs and FAIL=0 baseline; UI runtime is deferred. |
| Raw/private source details leak into public evidence | blocked | Evidence is aggregate/ref/status only and raw inbox read/write flags are false. |
| GitHub upload is incorrectly triggered per stage | blocked | Upload is deferred until v1.4 Stage 1-18 overall review and fixes. |
