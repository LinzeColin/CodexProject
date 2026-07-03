# Data Core Minimum Table Plan

Sprint 2O should create the smallest local schema that preserves the Raw Import
Pack without enabling product features prematurely.

## Required Tables

| Table | Purpose | Minimum source |
|---|---|---|
| `import_batches` | one row per imported Raw Import Pack | `import_manifest.json` |
| `import_files` | source file names, row counts, checksums, validation status | `validation_checksums.sha256`, inventory |
| `conversations` | normalized conversation records | `conversations.jsonl` |
| `contacts` | normalized contact records | `contacts.jsonl` |
| `conversation_participants` | conversation-to-contact participant links | `conversations.participant_ids` |
| `messages` | normalized message rows | `messages.jsonl` |
| `message_media_refs` | message-to-media references; expected empty in 2O | `messages.media_refs`, `media_index.csv` |
| `media_index` | media placeholder table; expected zero rows | `media_index.csv` |
| `import_validation_events` | validation results and stop-condition evidence | `validation_manifest.csv` |

## Minimum Constraints

- primary keys for `message_id`, `conversation_id`, `contact_id`, and import
  batch ID
- foreign key from `messages.conversation_id` to `conversations`
- sender reference validation against `contacts` or explicit allowed fallback
- media references must be empty for Sprint 2O
- no RAG embeddings, vector tables, web tables, matrix tables, or ChatGPT Pack
  tables

## Not Yet Tables

Do not add tables for full export lineage, media extraction, search indexes,
embeddings, web sessions, Matrix, or ChatGPT Pack in Sprint 2O.

