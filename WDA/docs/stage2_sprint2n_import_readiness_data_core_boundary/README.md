# WDA Stage 2 Sprint 2N Import Readiness Data Core Boundary

Sprint 2N is a readiness and boundary sprint. It validates that the Sprint
2M-B bounded Raw Import Pack can support a minimal local Data Core seed sprint,
but it does not create a database.

## Decision

Sprint 2O can start with strict limits.

- Raw Gate: `First-Batch Subject Coverage Proven`
- Full Raw Gate Go: not proven
- Local Raw Import Pack rows: `500` messages, `5` conversations, `23` contacts
- Media rows: `0`; media remains disabled
- Sprint 2N database creation: not performed
- RAG/Web/Matrix: blocked

Sprint 2O must ingest only the bounded Sprint 2M-B 500-row Raw Import Pack and
store any database under WDA_MetaData, not GitHub.

