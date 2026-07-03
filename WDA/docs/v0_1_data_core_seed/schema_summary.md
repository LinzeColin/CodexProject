# Schema Summary

## Tables

| table_name | purpose |
| --- | --- |
| sources | source file checksum and row metadata |
| import_runs | one local import run and bounded gate state |
| conversations | 5 imported conversations |
| contacts | 23 imported contacts |
| messages | 500 imported messages stored locally |
| subjects | 5 first-batch subjects |
| message_subject_links | 500 message-to-subject links |
| media_index | header-only media placeholder, zero rows |
| validation_events | source and DB validation evidence |

## Basic Indexes

| index_name | columns |
| --- | --- |
| idx_messages_timestamp | messages(timestamp_ms) |
| idx_messages_conversation_id | messages(conversation_id) |
| idx_messages_sender_id | messages(sender_id) |
| idx_contacts_contact_id | contacts(contact_id) |
| idx_message_subject_links_subject_id | message_subject_links(subject_id) |
| idx_subjects_subject_id | subjects(subject_id) |

## Notes

The `messages.text` column exists only in the local SQLite database under
WDA_MetaData. Repo-safe docs do not include message text or contact values.
