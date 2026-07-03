# Data Boundary

## Local Full-Sensitive Outputs

Full-sensitive outputs are stored only under:

`/Users/linzezhang/Downloads/WDA_MetaData/v0_1/analysis_layer/`

These include message timelines, keyword hit rows, candidate rows, and one
full-sensitive markdown report per subject.

## Repo-Safe Outputs

Git contains only aggregate counts, signal category summaries, query shapes, and
validation status. Git must not contain raw messages, SQLite databases,
full-sensitive reports, Raw Import Packs, transfer bundles, keys, or decrypted
DBs.

## Still Blocked

- RAG
- Web
- Matrix
- full export
- media handling
- ChatGPT Pack using raw messages
- OpenAI API calls with raw message content
