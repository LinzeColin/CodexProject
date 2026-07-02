# Downgrade To File Evidence System

Generated: 2026-07-03T09:43:38+10:00

Fallback route: build WDA around non-message evidence and file-level metadata if message-level import remains unavailable.

Allowed scope:
- File inventories.
- Metadata summaries.
- Governance and decision records.
- User-authored notes.
- Evidence references that do not include private message content.

Not allowed:
- Claiming message readability.
- Building message RAG/Web/Matrix features.
- Treating file metadata as chat content.

Tradeoff:
- This route allows WDA to progress as a governance/evidence workspace.
- It does not satisfy the original message-level data goal.
- Raw Gate remains `Conditional Investigation`.

Decision: keep as fallback only if the official/user-readable artifact route cannot be obtained.
