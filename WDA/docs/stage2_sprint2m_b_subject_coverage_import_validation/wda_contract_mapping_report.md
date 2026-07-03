# WDA Contract Mapping Report

## Mapping Result

Mapping succeeded.

Generated local WDA Raw Import Pack under:

`/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2m_b_subject_coverage_import_validation/`

- `messages.jsonl`: `500` rows
- `conversations.jsonl`: `5` rows
- `contacts.jsonl`: `23` rows
- `media_index.csv`: `0` media rows, header-only placeholder

## Field Mapping

| WDA field | Source mapping |
| --- | --- |
| message_id | `server_id_str` / `server_id`; duplicate fallback appends source duplicate suffix |
| conversation_id | `talker` |
| sender_id | `sender_wxid`, with `LOCAL_ACCOUNT` / `UNKNOWN_SENDER` fallback |
| direction | `is_from_me` and `kind_name` |
| timestamp_ms | `create_time` seconds converted to epoch milliseconds |
| message_type | `kind_name` with `base_kind` fallback |
| text | `message_content` |
| media_refs | empty array because `include_media_paths=false` |
| redaction_state | `none` in local full-sensitive pack |
| source_record_ref | bundle file and JSONL line reference |

## Message Type Counts

| message_type | count |
| --- | --- |
| card | 2 |
| file | 25 |
| forward_chat | 6 |
| image | 74 |
| location | 2 |
| quote | 12 |
| sticker | 12 |
| system | 20 |
| text | 342 |
| video | 2 |
| voip | 3 |

## Direction Counts

| direction | count |
| --- | --- |
| inbound | 317 |
| outbound | 163 |
| system | 20 |

## Required Field Validation

| Artifact | Missing required fields | Validation |
|---|---|---|
| `messages.jsonl` | none | pass |
| `conversations.jsonl` | none | pass |
| `contacts.jsonl` | none | pass |
| `media_index.csv` | none | pass |

Cross-file validation result: pass.
