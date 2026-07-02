# Stage 3 Implications

Generated: 2026-07-03T09:04:48+10:00

Stage 3 must not start as message-level RAG/Web/Matrix implementation yet.

## Blocked Until Raw Gate Advances

The following remain blocked:
- Message RAG indexing.
- Web UI over message/search results.
- Matrix/network views based on contacts, conversations, or message edges.
- Timeline analytics from message content.
- Any import job that emits production-like message records.

## Allowed Before Raw Gate Go

The following are allowed if scoped as non-message-data work:
- Product definition and user workflow decisions.
- Import contract design.
- Empty-state UI planning.
- Governance docs, validation scripts, and local-only manifest checks.
- Synthetic fixture design that is clearly labeled synthetic and not derived from WeChat raw data.

## Required Before Stage 3 Data Work

Before Stage 3 can use message-level data, WDA needs:
- A safe, authorized readable artifact path.
- An explicit import schema.
- Stop conditions and rollback.
- Validation that does not use decryption, key extraction, protected-store bypass, or third-party WeChat export/decrypt tools.
- A decision record that upgrades Raw Gate from `Conditional Investigation`.

Current conclusion: Stage 3 data-dependent implementation is blocked.
