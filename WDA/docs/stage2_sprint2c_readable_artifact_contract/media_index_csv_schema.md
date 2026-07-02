# `media_index.csv` Schema

Generated: 2026-07-03T09:12:39+10:00

`media_index.csv` is required only when `messages.jsonl` contains media references.

## Columns

| Column | Required | Rule |
|---|---:|---|
| `media_ref` | Yes | Stable identifier referenced by `messages.jsonl.media_refs`. |
| `message_id` | Yes | Message that references this media item. |
| `media_type` | Yes | One of `image`, `video`, `audio`, `file`, `link`, `unknown`. |
| `relative_path` | Conditional | Relative path within an approved artifact folder; blank if not provided. |
| `sha256` | Conditional | Required when a media file is included. |
| `size_bytes` | Conditional | Required when a media file is included. |
| `mime_type` | Optional | MIME type if known. |
| `redaction_state` | Yes | One of `none`, `partial`, `full`, `unknown`. |
| `source_record_ref` | Optional | Non-sensitive source reference. |

## Validation Rules

- CSV must be UTF-8 with a header row.
- `media_ref` values must be unique.
- `relative_path` must not be absolute and must not traverse upward with `..`.
- Media files are not required for Sprint 2D sample validation unless explicitly approved.
- Do not include raw cache directories such as `msg/file`, `msg/attach`, or `msg/video` as source paths.
