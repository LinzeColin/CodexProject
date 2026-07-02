# `messages.jsonl` Schema

Generated: 2026-07-03T09:12:39+10:00

Sprint 2C defines this schema only. It does not create `messages.jsonl`.

Format: UTF-8 JSON Lines, one JSON object per line.

## Required Fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `message_id` | string | Yes | Stable within the artifact. Must not be empty. |
| `conversation_id` | string | Yes | Must match a `conversations.jsonl` `conversation_id` when conversations are supplied. |
| `sender_id` | string | Yes | Must refer to a contact/account identifier or `UNKNOWN`. |
| `direction` | string | Yes | One of `inbound`, `outbound`, `system`, `unknown`. |
| `timestamp_ms` | integer | Yes | Unix epoch milliseconds. |
| `message_type` | string | Yes | One of `text`, `image`, `video`, `audio`, `file`, `link`, `system`, `mixed`, `unknown`. |
| `text` | string or null | Conditional | Present for readable text messages; null when absent or redacted. |
| `media_refs` | array | Yes | Empty array if no media. Values must reference `media_index.csv` rows when media is supplied. |
| `redaction_state` | string | Yes | One of `none`, `partial`, `full`, `unknown`. |
| `source_record_ref` | string or null | Yes | Non-sensitive reference into the artifact source, not a protected DB path. |

## Optional Fields

| Field | Type | Rule |
|---|---|---|
| `receiver_ids` | array | Contact/account identifiers. |
| `reply_to_message_id` | string or null | Must reference another message when present. |
| `language` | string or null | BCP-47 tag if known. |
| `content_hash` | string or null | Hash of normalized readable content if owner allows it. |
| `import_notes` | string or null | Non-sensitive artifact notes. |

## Validation Rules

- No line may be invalid JSON.
- `message_id` must be unique.
- `timestamp_ms` must be numeric.
- `media_refs` must be an array.
- No field may contain keys, passwords, protected-store material, or raw DB blobs.
- Shape validation may count and inspect field names/types only unless the owner separately approves content validation.
