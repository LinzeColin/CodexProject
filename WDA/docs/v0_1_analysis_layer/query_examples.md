# Query Examples

Repo-safe query examples avoid selecting raw message text.

```sql
SELECT s.subject_id, s.subject_label, COUNT(msl.message_id) AS message_count,
       COUNT(DISTINCT m.conversation_id) AS conversation_count
FROM subjects s
LEFT JOIN message_subject_links msl ON msl.subject_id = s.subject_id
LEFT JOIN messages m ON m.message_id = msl.message_id
GROUP BY s.subject_id, s.subject_label
ORDER BY s.subject_id;
```

```sql
SELECT s.subject_id, m.direction, COUNT(*) AS message_count
FROM subjects s
JOIN message_subject_links msl ON msl.subject_id = s.subject_id
JOIN messages m ON m.message_id = msl.message_id
GROUP BY s.subject_id, m.direction
ORDER BY s.subject_id, m.direction;
```

```sql
SELECT s.subject_id, m.timestamp_ms, m.message_id, m.conversation_id, m.direction, m.message_type
FROM subjects s
JOIN message_subject_links msl ON msl.subject_id = s.subject_id
JOIN messages m ON m.message_id = msl.message_id
ORDER BY s.subject_id, m.timestamp_ms
LIMIT 50;
```
