# Raw Artifact Shape Report

## Parse Result

- Raw bounded export files: `5`
- Parsed JSONL files: `5`
- Parse errors: `0`
- Total source rows: `100`
- Unique message id candidates: `100`
- Duplicate message id candidates: `0`

## Source Row Counts

| File | Rows | Parse errors |
|---|---:|---:|
| `export_01_raw.jsonl` | 20 | 0 |
| `export_02_raw.jsonl` | 20 | 0 |
| `export_03_raw.jsonl` | 20 | 0 |
| `export_04_raw.jsonl` | 20 | 0 |
| `export_05_raw.jsonl` | 20 | 0 |
| `TOTAL` | 100 | 0 |

## Source Field Names

- `base_kind`
- `chat_type`
- `content_summary`
- `create_time`
- `create_time_human`
- `is_from_me`
- `kind_name`
- `local_id`
- `message_content`
- `message_content_parsed`
- `sender_display_name`
- `sender_wxid`
- `server_id`
- `server_id_str`
- `subtype`
- `talker`
- `talker_display_name`

## Source Type Counts

| Field | Type counts |
|---|---|
| `base_kind` | int: 100 |
| `chat_type` | str: 100 |
| `content_summary` | str: 100 |
| `create_time` | int: 100 |
| `create_time_human` | str: 100 |
| `is_from_me` | bool: 100 |
| `kind_name` | str: 100 |
| `local_id` | int: 100 |
| `message_content` | str: 100 |
| `message_content_parsed` | dict: 44 |
| `sender_display_name` | str: 90 |
| `sender_wxid` | str: 100 |
| `server_id` | int: 100 |
| `server_id_str` | str: 100 |
| `subtype` | int: 100 |
| `talker` | str: 100 |
| `talker_display_name` | str: 100 |

## Distribution Summary

- Source `chat_type`: group 40, official_account 20, private 40.
- Source `kind_name`: file 1, image 2, link 40, location 1, system 11, text 44, video 1.
- Source `base_kind`: 1=44, 3=2, 43=1, 48=1, 49=41, 10000=11.
- Mapped directions: inbound 81, outbound 8, system 11.

No raw message text, contact values, or chat names are printed in this report.

