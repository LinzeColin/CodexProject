# Risk Register

| id | risk | mitigation | status |
|---|---|---|---|
| RAW-OWNER-001 | Owner decision could be confused with raw alignment completion | Keep NO_GO until a later application phase validates an active public-safe decision | open |
| RAW-OWNER-002 | Raw names or hashes could be pasted into public decision records | Validator rejects forbidden keys, local source tokens and hash-like values | controlled |
| RAW-OWNER-003 | GitHub upload or app reinstall could proceed before source identity is resolved | Go/No-Go blocks upload and app reinstall | blocked |
