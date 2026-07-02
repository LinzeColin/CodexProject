# Readable Artifact Search Scope

Generated: 2026-07-03T09:34:23+10:00

Searched source roots:
- LOCAL_METADATA_ROOT: root `/Users/linzezhang/Downloads/WDA_MetaData`, total files seen 16, readable-extension files 15, candidate rows before cap 12, rejected non-readable files 0, walk errors 0
- APFS_RAW_COPY_ROOT: root `/Volumes/WDA_WECHAT_APFS/.../raw/Data_Documents`, total files seen 2670, readable-extension files 152, candidate rows before cap 0, rejected non-readable files 86, walk errors 0

Included readable extensions:
- `.json`
- `.jsonl`
- `.csv`
- `.txt`
- `.md`
- `.html`
- `.xml`

Candidate signals:
- Exact Sprint 2C contract filenames: `import_manifest.json`, `messages.jsonl`, `conversations.jsonl`, `contacts.jsonl`, `media_index.csv`.
- Message/chat/conversation/contact/export/history-like filename or folder signals.
- Existing generated reports that may document structured export routes.

Explicitly rejected or pruned as non-readable artifacts:
- Protected DBs and DB sidecars.
- `key_info`, login, MMKV, KVDB, and key-value store paths.
- Raw media/cache paths such as `msg/file`, `msg/attach`, and `msg/video`.
- Sparseimage package internals and copied candidate DB bundle raw files.
- Any source requiring decryption, key extraction, protected-store bypass, or third-party export/decrypt tools.

Privacy rule: reports store redacted paths and path fingerprints only. They do not include raw message content, contact values, or full private source paths.
