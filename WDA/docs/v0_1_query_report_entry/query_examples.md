# Query Examples

Query examples are available locally at:

`/Users/linzezhang/Downloads/WDA_MetaData/v0_1/query_report_entry/query_examples.sql`

Repo-safe shape:

```sql
SELECT s.subject_id, s.subject_label, COUNT(msl.message_id) AS message_count,
       COUNT(DISTINCT m.conversation_id) AS conversation_count
FROM subjects s
LEFT JOIN message_subject_links msl ON msl.subject_id = s.subject_id
LEFT JOIN messages m ON m.message_id = msl.message_id
GROUP BY s.subject_id, s.subject_label
ORDER BY s.subject_id;
```

The query examples do not select raw message text.
