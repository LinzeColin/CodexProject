# Run Logs

OpenAIDatabase keeps four redacted run-log categories for GitHub-backed
continuity. Logs are JSONL and must never contain raw transcripts, cookies,
browser state, local absolute paths, plaintext secrets, or private keys.

Categories:

- `sync_runs`: source sync and data refresh operations.
- `export_runs`: generated personalization export operations.
- `evaluation_runs`: evaluation harness checks.
- `agent_runs`: future-agent runs that update or consume personalization
  context.

Each log row should include at least:

- `timestamp`
- `category`
- `status`
- `task`
- `updated_targets`
- `source_files`
- `output_files`
- `tests`
- `risks`
- `git_commit`
