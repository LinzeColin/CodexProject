# Read-only Retrieval

The retrieval layer is read-only.

Supported surfaces:

- CLI `search`
- CLI `fetch`
- local JSON-RPC/MCP-like `serve-mcp`

Source and cache:

- Canonical source: `data/memory/records/manifest.json` plus its declared
  `records-NNNN.jsonl` shards.
- Local cache: `data/processed/indexes/memory_index.sqlite`; it is ignored and
  automatically rebuilt from the canonical dataset when absent.
- Default query status: `active`. Candidate, disputed, and retired records are
  not returned by default.

Disallowed behavior:

- write/update/delete tools or canonical mutations
- shell execution
- reading raw export ZIPs or retired legacy memory directories
- returning credential material or an unredacted sensitive source

`search` returns compact redacted records. `fetch` may return one canonical
record by ID, subject to the same sensitivity boundary.
