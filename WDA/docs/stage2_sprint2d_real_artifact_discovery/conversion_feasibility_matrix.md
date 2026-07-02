# Conversion Feasibility Matrix

Generated: 2026-07-03T09:34:23+10:00

| Conversion feasibility | Candidate rows |
|---|---:|
| `not_message_artifact_report_only` | 12 |

| Source root | Candidate rows in report |
|---|---:|
| `LOCAL_METADATA_ROOT` | 12 |

Interpretation:
- `high_if_owner_authorized_and_checksum_valid`: already resembles the Sprint 2C contract filename set, but still requires separate validation.
- `medium_requires_separate_content_safe_conversion_review`: message/chat-like readable file candidate; conversion must be separately approved and must avoid committing raw content.
- `low_requires_owner_review`: weak path/folder signal only.
- `not_message_artifact_report_only`: useful as evidence or planning context, but not a message-level artifact.

Sprint 2D does not convert any candidate. If a real readable candidate is selected, run a separate approved conversion sprint that creates contract outputs locally and validates checksums/schema first.
