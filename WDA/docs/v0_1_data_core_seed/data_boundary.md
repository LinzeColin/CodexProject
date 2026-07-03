# Data Boundary

## Local Sensitive Boundary

Full-sensitive message text and contact values are stored only in the local
SQLite database:

`/Users/linzezhang/Downloads/WDA_MetaData/v0_1/data_core_seed/wda_v0_1_seed.sqlite`

## Git Boundary

Git may contain only repo-safe reports with counts, schema, checksums, and
validation results. Git must not contain:

- raw messages
- raw contacts
- Raw Import Pack files
- transfer bundles
- SQLite databases or sidecars
- keys or decrypted DBs

## Still Blocked

- full export
- media paths
- RAG
- Web
- Matrix
- ChatGPT Pack using raw messages

Raw Gate remains `First-Batch Subject Coverage Proven`, not full Go.
