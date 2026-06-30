# Agent Loop Review Checklist

Codex review and optional Architect Review must check:

- Scope drift.
- Unrelated refactor.
- Missing tests.
- Missing validation evidence.
- Security or privacy risk.
- Performance regression.
- Governance mismatch.
- Forbidden path changes.
- Release or rollback risk.
- Acceptance criteria mismatch.
- Secrets, tokens, credentials, `.env`, or local runtime data.
- Production deploy attempt.
- Dependency changes without explicit authorization.

Severity:

| Severity | Meaning | Merge impact |
|---|---|---|
| P0 | Critical correctness/security/governance issue | Blocks merge |
| P1 | High-risk issue or failed acceptance | Blocks merge |
| P2 | Important but fixable follow-up | Does not block if accepted by policy |
| P3 | Minor note | Does not block |
