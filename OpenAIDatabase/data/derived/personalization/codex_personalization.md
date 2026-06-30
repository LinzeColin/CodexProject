# Codex Personalization Export

- generated_at: 2026-06-30T07:08:17Z
- source: OpenAIDatabase redacted derived context
- raw_private_data_included: false
- plaintext_secrets_included: false

## Startup Read Order

- `AGENTS.md`
- `data/derived/personalization/codex_personalization.md`

## Codex Route

- `AGENTS.md`
- `data/derived/personalization/codex_personalization.md`

## Required Sync Targets

- `profile`
- `preference`
- `taste`
- `history`
- `pattern`

## Four Run Log Categories

- `data/run_logs/sync_runs/`
- `data/run_logs/export_runs/`
- `data/run_logs/evaluation_runs/`
- `data/run_logs/agent_runs/`

## Agent Rules

- Default to Chinese for user-facing replies unless technical terms require English.
- Prefer route-specific context before broad repository search.
- Treat GitHub as the durable backup surface for redacted derived memory and generated personalization exports.
- If a memory-affecting run cannot update the relevant source file, log `UNKNOWN` with a follow-up task.
- Never commit raw exports, full transcripts, cookies, browser profiles, local absolute paths, or plaintext secrets.
