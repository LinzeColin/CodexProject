# Validation Report

| check | result | detail |
| --- | --- | --- |
| sqlite_seed_opened_read_only | pass | mode=ro; PRAGMA query_only=ON |
| expected_table_counts | pass | {"messages": 500, "conversations": 5, "contacts": 23, "subjects": 5, "message_subject_links": 500, "media_index": 0} |
| subject_count | pass | 5 subjects represented |
| timeline_rows | pass | 500 |
| keyword_signal_rows_local | pass | 514 |
| candidate_rows_link_message_subject | pass | todo=50 opportunity=30 risk=16 |
| full_sensitive_reports_local | pass | 5 |
| noise_exclusion | pass | 李晶工作交接 hits=0 |
| forbidden_actions | pass | no upload; no exporter; no external drive; no RAG/Web/Matrix; no OpenAI API |
