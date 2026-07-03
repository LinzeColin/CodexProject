# WDA Contract Mapping Report

## Mapping Result

Mapping succeeded.

Generated local WDA Raw Import Pack:

- `messages.jsonl`: `100` rows
- `conversations.jsonl`: `5` rows
- `contacts.jsonl`: `21` rows
- `media_index.csv`: `0` media rows, header-only placeholder

## Field Mapping

| WDA field | Source mapping |
|---|---|
| `message_id` | `server_id_str` / `server_id` |
| `conversation_id` | `talker` |
| `sender_id` | `sender_wxid`, or `SYSTEM` / `LOCAL_ACCOUNT` / `UNKNOWN` fallback |
| `direction` | `kind_name`, `base_kind`, and `is_from_me` |
| `timestamp_ms` | `create_time` seconds converted to epoch milliseconds |
| `message_type` | `kind_name` and `base_kind` |
| `text` | `message_content` |
| `media_refs` | empty array because `include_media_paths=false` |
| `redaction_state` | `none` in local full-sensitive pack |
| `source_record_ref` | source JSONL file and line reference |

## Generated Message Type Counts

| Message type | Count |
|---|---:|
| `file` | 1 |
| `image` | 2 |
| `link` | 40 |
| `system` | 11 |
| `text` | 44 |
| `unknown` | 1 |
| `video` | 1 |

## Required Field Validation

| Artifact | Missing required fields | Validation |
|---|---|---|
| `messages.jsonl` | none | pass |
| `conversations.jsonl` | none | pass |
| `contacts.jsonl` | none | pass |
| `media_index.csv` | none | pass |

## Cross-File Validation

- Every message references an existing conversation.
- Sender references are satisfiable by generated contacts or allowed fallback
  identifiers.
- `media_refs` is an array for every message and is empty because media paths
  were disabled.
- Conversion errors: `0`.
- Validation errors: `0`.

