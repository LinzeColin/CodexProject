# Old Mac Session History 2026-06-30

Source archive on this machine:

`/Users/linzezhang/.codex/history_imports/old-mac-20260630/codex-token-history-migration-pack-20260630.tar.gz`

Local extracted staging directory:

`/Users/linzezhang/.codex/history_imports/old-mac-20260630/codex-token-history-migration-pack-20260630/`

GitHub payload:

- `archive_parts/`: split parts of `old-mac-session-history-20260630.tar.gz`
- `SHA256SUMS`: SHA-256 checksums for the split parts

Source counts:

- active session JSONL files: 241
- archived session JSONL files: 167
- total session JSONL files: 408

The split archive can be reassembled with:

```sh
cat archive_parts/old-mac-session-history-20260630.tar.gz.part-* > old-mac-session-history-20260630.tar.gz
```

Expected full archive SHA-256:

```text
bb8489bc3705f9f23d735608b14baf4844ceb6c7d9c4a85d6774c74680ea31f9  old-mac-session-history-20260630.tar.gz
```
