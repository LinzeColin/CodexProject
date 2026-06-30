# Codex Session History Imports

This directory stores imported Codex session history snapshots for future RAG,
behavior analysis, data analysis, and Memory Atlas updates.

These files are historical snapshots only. They must not be copied over a live
`~/.codex/sessions` directory.

## Imports

- `old-mac-20260630/`: old Mac Codex session history snapshot from
  `codex-token-history-migration-pack-20260630.tar.gz`.
- `current-mac-20260630/`: current Mac Codex session history snapshot captured
  on 2026-06-30.

## Old Mac Archive Reassembly

The old Mac session archive is split to keep every Git blob below GitHub's
ordinary file-size limit.

```sh
cd OpenAIDatabase/session_history/old-mac-20260630
cat archive_parts/old-mac-session-history-20260630.tar.gz.part-* > old-mac-session-history-20260630.tar.gz
shasum -a 256 old-mac-session-history-20260630.tar.gz
```

Expected full archive SHA-256:

```text
bb8489bc3705f9f23d735608b14baf4844ceb6c7d9c4a85d6774c74680ea31f9  old-mac-session-history-20260630.tar.gz
```

The archive contains:

- `session_index.jsonl`
- `transcription-history.jsonl`
- `sessions/`
- `archived_sessions/`

It intentionally excludes old Mac SQLite state backups and other live runtime
state. Those remain only in the local import staging directory.
