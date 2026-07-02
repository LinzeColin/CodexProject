# `import_manifest.json` Schema

Generated: 2026-07-03T09:12:39+10:00

Format: one UTF-8 JSON object.

## Required Fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `artifact_id` | string | Yes | Stable identifier for this artifact package. |
| `artifact_version` | string | Yes | Contract version, initially `wda-readable-artifact-v0`. |
| `owner_authorization` | object | Yes | Must declare who authorized local validation and when. |
| `source_description` | string | Yes | Human-readable source route, excluding secrets and protected-store details. |
| `source_method` | string | Yes | One of `owner_provided_export`, `official_export`, `manual_redacted_sample`, `synthetic_fixture`, `other_owner_authorized`. |
| `device_scope` | array | Yes | Device labels included, for example `old_computer` or `new_computer`. |
| `account_scope` | array | Yes | Owner-approved account identifiers or redacted labels. |
| `time_range` | object | Yes | `{ \"start_ms\": integer|null, \"end_ms\": integer|null }`. |
| `files` | array | Yes | File entries with path, role, sha256, and size. |
| `redaction_policy` | object | Yes | Describes redaction and excluded fields. |
| `allowed_use` | array | Yes | Must include `local_validation`; must not imply upload. |
| `forbidden_use` | array | Yes | Must include upload, decryption, key extraction, protected-store bypass. |

## Required File Entry Fields

| Field | Type | Rule |
|---|---|---|
| `path` | string | Relative artifact path. |
| `role` | string | One of `messages`, `conversations`, `contacts`, `media_index`, `media_file`, `notes`. |
| `sha256` | string | SHA-256 checksum. |
| `size_bytes` | integer | File size in bytes. |
| `required` | boolean | Whether validation requires the file. |

## Validation Rules

- Manifest must be present before any artifact validation.
- Every declared required file must exist in the artifact package.
- Checksums must match before any JSONL/CSV shape validation.
- Manifest must not contain keys, passwords, protected-store material, or raw DB blobs.
