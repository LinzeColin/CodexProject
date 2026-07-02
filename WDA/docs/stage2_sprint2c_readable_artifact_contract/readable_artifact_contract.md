# Readable Artifact Contract

Generated: 2026-07-03T09:12:39+10:00

## Contract Goal

Define the minimum owner-authorized artifact set that WDA can validate in a future run without touching protected WeChat stores or raw encrypted DB containers.

## Required Files

| File | Required | Purpose |
|---|---:|---|
| `import_manifest.json` | Yes | Declares owner authorization, source method, scope, checksums, redaction, and allowed use. |
| `messages.jsonl` | Yes for message import | One JSON object per message. Not produced in Sprint 2C. |
| `conversations.jsonl` | Yes for message import | One JSON object per conversation/session/thread. |
| `contacts.jsonl` | Recommended | One JSON object per contact/account/person entity when available. |
| `media_index.csv` | Conditional | Required only when messages reference external media files. |

## Acceptance Boundary

A future artifact may be accepted for validation only if:
- The owner explicitly authorizes the artifact for WDA local validation.
- The artifact is already readable and does not require decryption, key extraction, protected-store bypass, or SQLCipher key attempts.
- The artifact is local and is not uploaded.
- The artifact includes a manifest with checksums and scope.
- The first validation run is shape-only and sample-count-limited.

## Rejection Boundary

Reject the route if it requires:
- Opening protected WeChat DBs directly.
- Opening `key_info`, login, MMKV, KVDB, or key-value stores.
- Running third-party WeChat export/decrypt tools.
- Selecting message/contact/business rows from protected DB bundles.
- Copying the full old WeChat cache.
- Uploading raw data.

## Gate Result

This contract does not make Raw Gate Go. Raw Gate remains `Conditional Investigation` until a later approved validation run proves a real readable artifact can be safely accepted.
