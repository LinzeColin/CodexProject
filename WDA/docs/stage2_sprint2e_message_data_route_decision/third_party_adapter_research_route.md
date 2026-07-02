# Third-Party Adapter Research Route

Generated: 2026-07-03T09:43:38+10:00

Decision: research-only backup, not execution.

What may be allowed in a later research sprint:
- Identify candidate tools or formats at a high level.
- Review licenses, privacy posture, local-only behavior, and whether tools require decryption or key extraction.
- Reject tools that require protected-store bypass, key extraction, SQLCipher key attempts, or raw upload.

What is not allowed in Sprint 2E:
- Running third-party WeChat export/decrypt tools.
- Installing or testing adapters.
- Pointing tools at real WDA data.
- Parsing message content.

Current stance: this route remains lower priority than the official/user-readable artifact route because it is more likely to violate the safety boundary or introduce toolchain trust risk.
