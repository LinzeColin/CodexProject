# Next Sprint 2L Plan

## Recommended Next Sprint

Sprint 2L: broader bounded coverage and import-readiness plan.

## Goal

Decide the next bounded increase in coverage before any RAG/Web/Matrix buildout.

## Proposed Scope

- Keep raw outputs under WDA_MetaData only.
- Continue using repo-safe summaries only.
- Validate a broader but still bounded sample, such as:
  - more conversations
  - a larger but capped message count
  - selected subject/time windows
  - media-path readiness as a separate optional lane
- Preserve explicit stop conditions before any larger export.

## Stop Conditions

- Any command requires full export before bounded validation.
- Any step requires transferring key material, DBs, broad logs, or tool state.
- Any tool writes outside approved WDA_MetaData paths.
- Media enrichment blocks text/message repeatability.
- Any command attempts upload, message sending, or UI automation.

## Gate

Full Raw Gate Go should remain blocked until Sprint 2L or later proves broader
coverage, repeatability, and safe local import behavior.

