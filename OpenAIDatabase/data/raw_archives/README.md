# Raw Archives

Canonical GitHub URL:

`https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase/data/raw_archives`

This is the complete-source archive root for ChatGPT, Codex, future-agent,
other-agent, and LLM exports that the user asks to preserve in GitHub. It exists
so any future agent or LLM can recover original data without relying on a
temporary local computer.

## Mandatory Rule

If an agent/LLM source export must be preserved, store a GitHub-recoverable copy
under:

```text
OpenAIDatabase/data/raw_archives/{source_id}/{archive_date_or_run_id}/
```

Do not leave the only complete copy in `~/Downloads`, `/tmp`, a local app cache,
or another machine-local path.

## Required Files

Each archive directory must contain:

- `manifest.json`: source id, original filename, byte size, SHA256, archive
  timestamp, repository path, visibility/user-authorization note, and ordered
  part metadata when split.
- `README.md`: short human restore instructions and expected SHA256.
- `restore.sh` or equivalent deterministic restore instructions when archive
  reconstruction is needed.
- `parts/`: split files when the original file is too large for normal GitHub
  file limits.

## Restore Contract

A future agent must be able to restore and verify with:

```bash
cd OpenAIDatabase/data/raw_archives/{source_id}/{archive_date_or_run_id}
./restore.sh
```

The restored file's SHA256 must equal the value in `manifest.json`.

## Boundary

`data/public_raw/`, `data/derived/`, and `data/run_logs/` are processing,
derived, and evidence layers. They are useful, but they do not replace this
complete raw archive root.

Credentials, cookies, browser state, private keys, session tokens, API keys,
OAuth tokens, and plaintext secrets are not agent memory. Exclude or encrypt
them unless the user explicitly authorizes a specific public raw archive action.
