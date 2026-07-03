# Raw Artifact Shape Report

This report describes raw JSONL schema shape only. It does not include message
text, contact values, talker IDs, sender IDs, or raw row samples.

| source_file | subject_id | row_count | field_count | field_names |
| --- | --- | --- | --- | --- |
| raw_sensitive_subject_exports/01_S1_mxr_yan_export_raw.jsonl | S1_mxr_yan | 100 | 17 | base_kind;chat_type;content_summary;create_time;create_time_human;is_from_me;kind_name;local_id;message_content;message_content_parsed;sender_display_name;sender_wxid;server_id;server_id_str;subtype;talker;talker_display_name |
| raw_sensitive_subject_exports/02_S2_spouse_export_raw.jsonl | S2_spouse | 100 | 17 | base_kind;chat_type;content_summary;create_time;create_time_human;is_from_me;kind_name;local_id;message_content;message_content_parsed;sender_display_name;sender_wxid;server_id;server_id_str;subtype;talker;talker_display_name |
| raw_sensitive_subject_exports/03_S3_payment_invoice_amount_export_raw.jsonl | S3_payment_invoice_amount | 100 | 17 | base_kind;chat_type;content_summary;create_time;create_time_human;is_from_me;kind_name;local_id;message_content;message_content_parsed;sender_display_name;sender_wxid;server_id;server_id_str;subtype;talker;talker_display_name |
| raw_sensitive_subject_exports/04_S4_recent_high_frequency_export_raw.jsonl | S4_recent_high_frequency | 100 | 17 | base_kind;chat_type;content_summary;create_time;create_time_human;is_from_me;kind_name;local_id;message_content;message_content_parsed;sender_display_name;sender_wxid;server_id;server_id_str;subtype;talker;talker_display_name |
| raw_sensitive_subject_exports/05_S5_weak_noise_sample_export_raw.jsonl | S5_weak_noise_sample | 100 | 17 | base_kind;chat_type;content_summary;create_time;create_time_human;is_from_me;kind_name;local_id;message_content;message_content_parsed;sender_display_name;sender_wxid;server_id;server_id_str;subtype;talker;talker_display_name |

Common source fields observed:

`base_kind`, `chat_type`, `content_summary`, `create_time`,
`create_time_human`, `is_from_me`, `kind_name`, `local_id`,
`message_content`, `sender_display_name`, `sender_wxid`, `server_id`,
`server_id_str`, `subtype`, `talker`, `talker_display_name`.
