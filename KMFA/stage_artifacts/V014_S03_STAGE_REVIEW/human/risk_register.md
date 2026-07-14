# v0.1.4 Stage 3 Review Risk Register

| Risk | Status | Control |
|---|---|---|
| Treating Stage 3 review as GitHub upload gate | controlled | `github_upload_performed=false`; upload deferred until v1.4 Stage 1-18 complete overall review. |
| Re-reading raw inbox during review | controlled | review uses public-safe phase manifests and validators only; review raw-read flags remain false. |
| Mistaking S03 source priority for value reconciliation | controlled | raw value matching, field mapping, lineage full check and formal report remain false. |
| Automatically choosing a cross-source conflict side | controlled | `auto_selection_allowed=false`; conflicts stay in manual difference queue. |
| Starting S04 within the review run | controlled | `s04_p1_started=false`; next phase is recommendation only. |
