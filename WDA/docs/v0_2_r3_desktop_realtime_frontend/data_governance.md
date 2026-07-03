# Data Governance

## Local-only Sources

- Data Core: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace/data_core/wda_v0_2_r2.sqlite`
- R3 runtime: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime`
- Local reports: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace/reports`

## Never Commit

- raw messages
- SQLite DB, WAL, SHM
- Raw Import Pack
- transfer bundles
- keys
- decrypted DBs
- private report contents
- local venv
- runtime logs/state

## R3 Service Boundary

The local service:

- opens SQLite read-only;
- uses the new computer only;
- does not access `/Volumes/My Passport`;
- does not access `/Volumes/WDA_WECHAT_APFS`;
- does not run WeChat exporter tools;
- does not upload data;
- does not call OpenAI API with raw content.

## Repo-safe Docs

Repo docs may include architecture, commands, counts, sanitized examples, file paths, and validation evidence. They must not include private message text or sensitive report excerpts.
