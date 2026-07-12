# Public Raw Archive

Task ID: `MA-V12-S03P1`.

Acceptance ID: `ACC-MA-V12-S03P1`.

Status: `phase_s03_p1_public_raw_path_defined_pending_s03_p2`.

This directory is the public plaintext raw archive root for Memory Atlas v1.2.

Defined raw paths:

- `data/public_raw/chatgpt`
- `data/public_raw/codex`
- `data/public_raw/agents/{agent_id}`

Rules:

- Raw transcript files may be appended here after the later sync phases create them.
- Existing raw files are append-only: do not modify, delete, overwrite or rewrite them.
- A later raw manifest/hash ledger must make hash drift fail when an existing raw file changes.
- Raw files are not proposal apply targets.
- `credentials_not_transcript`: credentials are not memory and must not be stored here.

No transcript ingestion in S03 P1. This phase only defines the public path, manifest/hash contract,
append-only rule and hash drift fail rule.
