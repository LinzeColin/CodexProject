# Import Readiness Criteria

## Sprint 2M-B Can Pass If

- Transfer bundle checksums pass.
- No forbidden sensitive material is included.
- All selected subject export JSONL files parse.
- Row count is within limits:
  - `<= 100` per subject/conversation
  - `<= 500` total
- WDA Raw Import Pack is generated locally.
- Required fields are present:
  - `message_id`
  - `conversation_id`
  - `sender_id`
  - `direction`
  - `timestamp_ms`
  - `message_type`
  - `text`
  - `media_refs`
  - `redaction_state`
  - `source_record_ref`
- Cross-file references validate.
- Conversion errors are `0`.
- Repo-safe reports contain no private message/contact values.

## Sprint 2M-B Must Not Claim

- full Raw Gate Go
- full-history readiness
- full contact readiness
- media readiness
- RAG/Web/Matrix readiness
- production import readiness

## Minimum Decision Upgrade

If Sprint 2M-B succeeds, the next Raw Gate label may become:

`Bounded Subject Coverage Proven`

This would still not be full Raw Gate Go.

