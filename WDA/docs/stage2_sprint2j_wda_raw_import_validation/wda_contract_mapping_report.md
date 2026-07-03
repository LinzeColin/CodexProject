# WDA Contract Mapping Report

## Mapping Result

Mapping succeeded.

Generated local WDA Raw Import Pack:

- `messages.jsonl`: `1` row
- `conversations.jsonl`: `1` row
- `contacts.jsonl`: `2` rows
- `media_index.csv`: `0` media rows, header-only placeholder

## Message Mapping

| WDA field | Source mapping |
|---|---|
| `message_id` | `server_id_str` / `server_id` / `local_id` |
| `conversation_id` | `talker` |
| `sender_id` | `sender_wxid`, or `SYSTEM` / `UNKNOWN` fallback |
| `direction` | `base_kind` and `is_from_me` |
| `timestamp_ms` | `create_time` seconds converted to epoch milliseconds |
| `message_type` | `base_kind` |
| `text` | `message_content` |
| `media_refs` | empty array for this no-media sample |
| `redaction_state` | `none` in local full-sensitive pack |
| `source_record_ref` | source JSONL line reference |

## Required Field Validation

| Artifact | Missing required fields | Validation |
|---|---|---|
| `messages.jsonl` | none | pass |
| `conversations.jsonl` | none | pass |
| `contacts.jsonl` | none | pass |
| `media_index.csv` | none | pass |

## Cross-File Validation

- Message references an existing conversation.
- Sender/contact references are satisfiable by generated contacts or allowed
  fallback identifiers.
- `media_refs` is an array and empty.
- No validation errors were reported.

