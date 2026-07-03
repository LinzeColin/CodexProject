# Raw Import Contract Coverage

## Contract Files

| Contract artifact | Present | Rows | Sprint 2O action |
|---|---|---:|---|
| `import_manifest.json` | yes | n/a | ingest as import batch metadata |
| `messages.jsonl` | yes | 500 | ingest into `messages` only after schema validation |
| `conversations.jsonl` | yes | 5 | ingest into `conversations` |
| `contacts.jsonl` | yes | 23 | ingest into `contacts` |
| `media_index.csv` | yes | 0 | create empty media table or skip rows with explicit placeholder |

## Required Message Fields

All required message fields are present:

- `message_id`
- `conversation_id`
- `sender_id`
- `direction`
- `timestamp_ms`
- `message_type`
- `text`
- `media_refs`
- `redaction_state`
- `source_record_ref`

Additional observed fields may be stored as nullable metadata or ignored in
Sprint 2O:

- `receiver_ids`
- `reply_to_message_id`
- `language`
- `content_hash`
- `import_notes`

## Readiness Decision

Schema coverage is sufficient for a minimal local Data Core seed. Sprint 2O
must keep the import bounded to the existing 500-row pack and must not infer
full production readiness.

