# Ingest Validation Report

| check | result | detail |
| --- | --- | --- |
| input_required_files | pass | 7/7 present |
| input_checksums | pass | 12 entries checked |
| messages_ingested | pass | 500 |
| conversations_ingested | pass | 5 |
| contacts_ingested | pass | 23 |
| subjects_preserved | pass | 5 |
| message_subject_links | pass | 500 |
| media_rows | pass | 0 |
| foreign_key_check | pass | 0 violations |
| integrity_check | pass | ok |
| noise_exclusion | pass | explicit noise term hits=0 |
| repo_raw_data_commit | pass | no raw pack or DB files staged by generator |

Validation result: `pass`.

This report intentionally excludes raw message text, contact values, and private
conversation identifiers.
