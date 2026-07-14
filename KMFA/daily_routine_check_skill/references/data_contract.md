# DWS Output Data Contract

This skill consumes one complete DWS output zip as its only upstream input. It does not fetch DingTalk itself and does not copy or extract the package to local disk.

## Primary Input Zip

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

Expected group folders inside the zip, with or without a top-level `DWS_Outputs/` prefix:

```text
付款请示群/
生产管理群/
```

Each group folder should contain these members:

```text
_manifest/manifest.csv
_manifest/status.md
_manifest/missing_media.csv
_analysis/recent_30d_file_records.csv
_analysis/similar_recent_30d.csv
chat_records/chat_records.csv
chat_records/chat_records.jsonl
chat_records/raw_messages.jsonl
files/MMDD/*
```

A disk `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/`
folder is normally absent and is never an input. Do not probe, create,
materialize, copy, extract, or fall back to it. The `DWS_Outputs/<群>/...`
layout above refers only to member paths inside the zip. Stream required
members in place and do not automatically evict the zip after each run.

## Required Manifest Fields

`_manifest/manifest.csv` should be parsed with tolerant headers. Known fields from current DWS output:

```text
group_name
open_conversation_id
message_id
message_time
sender_name
sender_id
msg_type
resource_type
resource_id
original_filename
local_archive_path
output_path
sha256
size_bytes
download_method
status
error_reason
attempt_count
first_failed_at
last_failed_at
```

## Required Chat Record Fields

`chat_records/chat_records.csv` known fields:

```text
group_name
open_conversation_id
open_message_id
message_time
sender_name
sender_id
content
quoted_message_id
quoted_sender
quoted_content
resource_count
resource_types
```

## Normalized Source Message

The reader should normalize every input row into:

```json
{
  "source_run_id": "...",
  "group_name": "付款请示群",
  "message_id": "...",
  "message_time": "2026-07-07T10:30:00+08:00",
  "sender_name": "杨婷",
  "sender_id_hash": "hash-only-if-needed",
  "content": "...",
  "resource_count": 1,
  "resource_types": ["image"],
  "source_path": "...",
  "ingested_at": "..."
}
```

## Normalized Source File

```json
{
  "source_run_id": "...",
  "group_name": "付款请示群",
  "message_id": "...",
  "message_time": "2026-07-07T10:30:00+08:00",
  "sender_name": "杨婷",
  "resource_type": "image",
  "original_filename": "...",
  "output_path": "files/0707/...png",
  "absolute_path": "zip:///Users/.../DWS_Outputs.zip!/DWS_Outputs/付款请示群/files/0707/...png",
  "sha256": "...",
  "size_bytes": 123456,
  "status": "downloaded|duplicate|missing|failed",
  "error_reason": "..."
}
```

## Idempotency Keys

Routine check event:

```text
routine:{check_date}:{rule_id}:{group_name}:{due_time}
```

Document candidate:

```text
doc:{sha256}:{document_type}:{message_id}
```

Cash risk event:

```text
cash-risk:{report_date}:{risk_level}:{source_sha256}
```

Notification event:

```text
notify:{event_type}:{event_key}:{target_label}
```

## Missing Data Behavior

- Missing group member prefix inside the zip: create `SOURCE_MISSING_GROUP` issue.
- Missing manifest: create `SOURCE_MISSING_MANIFEST` issue.
- Missing chat records: create `SOURCE_MISSING_CHAT_RECORDS` issue.
- Missing file referenced by manifest: create `SOURCE_MISSING_FILE` issue.
- Latest source message earlier than `check_date`: create `SOURCE_STALE` issue.
- Do not crash the whole automation if one group is missing.
- Missing source can itself trigger a notification if the due check cannot be performed.
