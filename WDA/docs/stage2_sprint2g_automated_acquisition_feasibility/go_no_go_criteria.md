# Go / No-Go Criteria

## Current Gate

Raw Gate: `Conditional Investigation`.

Sprint 2G does not move Raw Gate to Go.

## Sprint 2H Trial Go Criteria

A controlled acquisition trial may start only if:

- The user approves the exact tool, host, and sensitive operations.
- The route can run local-only.
- The route can write only under WDA_MetaData.
- The route can produce deterministic output files.
- The route has a rollback plan.
- The trial scope is minimal and explicit.
- Raw outputs will not be committed to git.

## Raw Gate Go Criteria

Raw Gate can be reconsidered only after a later approved step produces and
validates:

- `messages.jsonl`
- `conversations.jsonl`
- `contacts.jsonl` or documented equivalent contact identifiers
- `import_manifest.json`
- checksums
- privacy and provenance metadata

## No-Go Criteria

- No automated route is accepted.
- macOS WeChat 4.1.11 is unsupported by the selected route.
- The route requires unapproved key extraction, decryption, protected-store
  bypass, or process-memory access.
- The route uploads raw data.
- The route cannot produce message-level output.
- The route cannot be constrained to local WDA_MetaData output.

## Viability Statement

If no automated acquisition route is accepted, WDA core is not viable as a fully
automatic WeChat message intelligence system.

