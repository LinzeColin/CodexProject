# Risk Register

| id | risk | mitigation | status |
|---|---|---|---|
| OAF-APP-001 | Missing active fill record could be mistaken for source-map closure | Application status and Go/No-Go remain blocked | blocked |
| OAF-APP-002 | Codex could mutate or derive from raw sources during application | Raw boundary flags and validator keep this phase raw-inbox-free | controlled |
| OAF-APP-003 | Later processed outputs may diverge from raw source truth | Final goal requires cross-validation and a difference report if repeated checks still diverge | controlled |
