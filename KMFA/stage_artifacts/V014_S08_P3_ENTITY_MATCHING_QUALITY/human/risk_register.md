# KMFA v0.1.4 S08-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| Matching quality evidence is mistaken for final entity resolution | medium/high risk cases require manual review; no-auto-merge queue remains locked | controlled |
| Quality report is mistaken for formal operating report | `quality_report_is_formal_report=false`; formal report remains blocked | controlled |
| Stage 8 review starts too early | `stage8_review_scope_included=false`; review must be a separate run | controlled |
| Raw/private data leaks into public evidence | v0.1.4 manifest stores aggregate counts only; semantic and secret scans required | controlled |
| GitHub upload starts too early | `github_upload_deferred_until_v014_stage1_18_complete=true` | controlled |
