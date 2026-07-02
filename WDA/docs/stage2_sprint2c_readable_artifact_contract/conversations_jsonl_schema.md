# `conversations.jsonl` Schema

Generated: 2026-07-03T09:12:39+10:00

Format: UTF-8 JSON Lines, one JSON object per line.

## Required Fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `conversation_id` | string | Yes | Stable within the artifact. Must not be empty. |
| `conversation_type` | string | Yes | One of `direct`, `group`, `system`, `unknown`. |
| `participant_ids` | array | Yes | Contact/account identifiers. Empty only when unknown. |
| `created_at_ms` | integer or null | Yes | Unix epoch milliseconds or null. |
| `last_message_at_ms` | integer or null | Yes | Unix epoch milliseconds or null. |
| `message_count_declared` | integer or null | Yes | Declared count if available; null otherwise. |
| `display_title` | string or null | Yes | Owner-approved readable title or null/redacted. |
| `redaction_state` | string | Yes | One of `none`, `partial`, `full`, `unknown`. |

## Optional Fields

| Field | Type | Rule |
|---|---|---|
| `owner_account_id` | string or null | Local account identifier. |
| `source_record_ref` | string or null | Non-sensitive source reference. |
| `import_notes` | string or null | Non-sensitive artifact notes. |

## Validation Rules

- `conversation_id` must be unique.
- `participant_ids` must be an array.
- Timestamps must be numeric or null.
- The file must not contain protected DB paths, keys, passwords, or raw blobs.
