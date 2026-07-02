# Artifact Source Options

Generated: 2026-07-03T09:12:39+10:00

| Source option | Acceptable for future validation? | Conditions | Notes |
|---|---:|---|---|
| Owner-provided readable JSONL package | Yes | Must include manifest, checksums, authorization, and local-only allowed use. | Preferred route. |
| Official/user-controlled export | Yes | Must be produced without WDA decrypting or bypassing protected stores. | Acceptable if owner approves. |
| Manual redacted sample | Yes | Must be owner-authored or owner-approved and clearly labeled. | Good for validating import shape. |
| Synthetic fixture | Yes | Must be clearly synthetic and not derived from raw WeChat data. | Useful for UI/schema tests, not Raw Gate Go. |
| Existing protected DB bundle | No | Sprint 2B-B safe SQLite route failed 91/91; further attempts risk forbidden methods. | Not the next route. |
| `key_info`, login, MMKV, KVDB, key-value stores | No | Forbidden. | Do not open. |
| Third-party WeChat export/decrypt tool output | No | Forbidden by current run contract. | Do not use. |
| Full old WeChat cache copy | No | Too broad and not necessary for the safe route. | Not recommended. |

Decision: prefer an owner-provided readable JSONL package or an official/user-controlled export that already meets the contract.
