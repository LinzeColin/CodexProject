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

Each task-run log row must be single-line JSON and include at least:

- `timestamp`
- `category`
- `status`
- `task_id`
- `run_type`
- `context_used`
- `tools_used`
- `tests_run`
- `failure_recovery`
- `base_commit`
- `result_commit`
- `residual_risks`

Evidence rules:

- `PASS` tests must include `exit_code = 0`.
- `NOT_RUN` tests must include `not_run_reason`.
- `tests_run` records only commands that actually ran, or explicit `NOT_RUN`
  entries with a reason.
- Evidence paths must exist.
- Final records must not keep `git_commit`, `base_commit`, or `result_commit`
  as `PENDING`.
- `updated_targets`
- `source_files`
- `output_files`
- `tests`
- `risks`
- `git_commit`
