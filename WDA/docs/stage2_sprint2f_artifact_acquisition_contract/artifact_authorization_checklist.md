# Artifact Authorization Checklist

Generated: 2026-07-03T09:51:08+10:00

Before Sprint 2G validates a readable artifact, the user must provide or approve:

| Check | Required |
|---|---:|
| Artifact is intentionally provided for WDA local validation | Yes |
| Owner or authorized user is identified | Yes |
| Source route is described | Yes |
| Time range is stated or explicitly unknown | Yes |
| Account/device scope is stated or explicitly unknown | Yes |
| Contact/subject scope is stated or explicitly unknown | Yes |
| Privacy level is declared | Yes |
| Original vs redacted content is declared | Yes |
| Checksums are available or can be generated locally | Yes |
| Import manifest is present or approved to be created locally | Yes |

Authorization statement template:

```text
I authorize WDA to perform local-only validation of this readable artifact package.
I understand this does not authorize upload, decryption, key extraction, protected-store bypass, or RAG/Web/Matrix import.
```

If authorization is missing, Sprint 2G must stop.
