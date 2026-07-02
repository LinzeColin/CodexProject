# `contacts.jsonl` Schema

Generated: 2026-07-03T09:12:39+10:00

Format: UTF-8 JSON Lines, one JSON object per line.

## Required Fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `contact_id` | string | Yes | Stable within the artifact. Must not be empty. |
| `display_name` | string or null | Yes | Owner-approved readable name or null/redacted. |
| `contact_type` | string | Yes | One of `person`, `group`, `account`, `system`, `unknown`. |
| `aliases` | array | Yes | Empty array if unavailable. |
| `redaction_state` | string | Yes | One of `none`, `partial`, `full`, `unknown`. |

## Optional Fields

| Field | Type | Rule |
|---|---|---|
| `profile_ref` | string or null | Non-sensitive reference, not a protected DB path. |
| `first_seen_ms` | integer or null | Unix epoch milliseconds or null. |
| `last_seen_ms` | integer or null | Unix epoch milliseconds or null. |
| `import_notes` | string or null | Non-sensitive artifact notes. |

## Validation Rules

- `contact_id` must be unique.
- `aliases` must be an array.
- Do not include phone numbers, emails, handles, avatars, or profile fields unless the owner explicitly authorizes them.
- Do not include keys, login material, MMKV/KVDB content, or protected-store data.
