# Read-only Retrieval

The retrieval layer is read-only.

Supported surfaces:

- CLI `search`
- CLI `fetch`
- local JSON-RPC/MCP-like `serve-mcp`

Allowed data sources:

- `data/memory/active/active_memory.jsonl`
- `data/memory/candidates/*.memory_candidates.jsonl`
- `data/processed/indexes/memory_index.sqlite`

Disallowed behavior:

- write/update/delete tools
- shell execution
- reading raw export ZIPs
- returning `secret` sensitivity records

`search` should return compact records. `fetch` may return one full redacted memory record by ID with evidence summaries only.
