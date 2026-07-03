# Query Examples

The local `query_examples.sql` file was generated under WDA_MetaData. These
repo-safe examples avoid selecting raw message text.

```sql
SELECT 'messages' AS table_name, COUNT(*) AS row_count FROM messages
UNION ALL SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL SELECT 'contacts', COUNT(*) FROM contacts
UNION ALL SELECT 'subjects', COUNT(*) FROM subjects;
```

```sql
SELECT s.subject_id, s.subject_label, COUNT(msl.message_id) AS message_count
FROM subjects s
LEFT JOIN message_subject_links msl ON msl.subject_id = s.subject_id
GROUP BY s.subject_id, s.subject_label
ORDER BY s.subject_id;
```

```sql
SELECT message_type, COUNT(*) AS message_count
FROM messages
GROUP BY message_type
ORDER BY message_count DESC, message_type;
```

```sql
SELECT result, COUNT(*) AS event_count
FROM validation_events
GROUP BY result
ORDER BY result;
```
