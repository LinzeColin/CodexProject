# Export Scope Policy

## Sprint 2M Hard Limits

- Max first-batch subject targets: `5`
- Max messages per subject or conversation: `100`
- Max total messages: `500`
- `include_media_paths=false`
- No full-contact export
- No all-history export
- No media DB enhancement
- No RAG/Web/Matrix

## Export Rules

- One bounded export per selected subject conversation by default.
- If a subject has multiple plausible identity candidates, choose the highest
  confidence candidate first.
- Only split one subject into multiple candidate conversations if doing so stays
  within the 5 target and 500 total message cap.
- Stop immediately if a command requires full export or all-history traversal.
- Keep raw outputs under WDA_MetaData only.
- Transfer only the bounded export bundle and repo-safe reports needed for
  Sprint 2M-B validation.

## Media Policy

Sprint 2M must use `include_media_paths=false`.

Reason: Sprint 2K-B proved message-level import with media refs empty. Media DB
key coverage and media path readiness remain separate future work.

