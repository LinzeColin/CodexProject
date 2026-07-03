# Manual Artifact Route Deprecated

## Decision

Manual user-prepared readable artifacts are deprecated for WDA core viability.

Sprint 2F remains useful as an intake schema reference, but it is no longer the
primary WDA route because the user requires fully automatic message
acquisition.

## Still Valid From Sprint 2F

- WDA Raw Import Pack shape:
  - `import_manifest.json`
  - `messages.jsonl`
  - `conversations.jsonl`
  - `contacts.jsonl`
  - `media_index.csv`
- Validation concepts:
  - checksum verification
  - privacy classification
  - owner authorization evidence
  - no raw data committed to git

## Deprecated For Core Goal

- Asking the user to manually create `messages.jsonl`.
- Treating manual readable artifact upload as the next default execution step.
- Proceeding to RAG/Web/Matrix without automated message-level acquisition.

## Result

WDA must select and trial an automated acquisition route before Raw Gate can
advance.

