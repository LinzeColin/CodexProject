# Artifact Privacy And Redaction Policy

Generated: 2026-07-03T09:51:08+10:00

Privacy levels:

| Level | Meaning | Sprint 2G handling |
|---|---|---|
| `sample_redacted` | Small redacted sample | Shape validation only. |
| `sample_original` | Small original sample | Validate only after explicit user approval. |
| `full_redacted` | Larger redacted export | Manifest/checksum first; row validation only if approved. |
| `full_original` | Larger original export | Requires a later explicit import/privacy gate. |

Required declarations:
- Whether content is original or redacted.
- Whether contacts are original, redacted, or omitted.
- Whether media is included, redacted, omitted, or referenced only.
- Whether the package contains third-party/private data.

Default Sprint 2G policy:
- Validate manifest and schema shape first.
- Do not print message text or contact values in reports.
- Do not include raw content in git.
- Stop before RAG/Web/Matrix ingestion.

Raw Gate remains `Conditional Investigation` until a later approved validation result supports a gate change.
