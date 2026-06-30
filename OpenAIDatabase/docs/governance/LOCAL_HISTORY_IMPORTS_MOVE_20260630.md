# Local Codex History Imports Move - 2026-06-30

## Summary

- action_time_utc: `2026-06-30T11:22:54Z`
- action_time_local: `2026-06-30T21:22:54+1000`
- operator: `Codex side-conversation assistant`
- status: `completed`
- action_type: `local_move_only`

The local old-Mac Codex history import source directory was moved out of
`~/.codex` into the Codex workspace backup area after GitHub backup presence was
confirmed.

## Paths

- old_path: `/Users/linzezhang/.codex/history_imports`
- new_path: `/Users/linzezhang/Documents/Codex/backups/codex-history-imports/history_imports`
- moved_size_observed: `5.9G`

## GitHub Backup Evidence

Before the local move, `origin/main` was checked for the OpenAIDatabase backup
paths:

- `OpenAIDatabase/session_history/old-mac-20260630/`
- `OpenAIDatabase/session_history/current-mac-20260630/`
- `OpenAIDatabase/token_usage/old-mac-20260630/`

The check was performed against remote `main` commit
`b8fcc7784bd4281140473d5ee7e85842efe5ac62`.

## Live Data Boundary

The move did not touch these live/runtime paths:

- `/Users/linzezhang/.codex/sessions`
- `/Users/linzezhang/.codex/archived_sessions/old-mac-token-usage-20260630-synthetic`
- `/Users/linzezhang/Library/Caches/CodexBar/cost-usage/codex-v8.json`
- `/Users/linzezhang/Library/Application Support/com.steipete.codexbar/`

Do not copy the moved backup back over live Codex state. If future work needs to
rebuild analysis inputs, read from `new_path` as a cold source and write derived
outputs to the appropriate OpenAIDatabase or local analysis directory.

## Future Agent Rules

1. Treat `new_path` as the local cold backup for old-Mac import source material.
2. Do not expect `/Users/linzezhang/.codex/history_imports` to exist.
3. Do not recreate `/Users/linzezhang/.codex/history_imports` unless the user explicitly asks.
4. Do not move, overwrite, or merge raw import source into `/Users/linzezhang/.codex/sessions`.
5. For GitHub-backed facts, prefer `OpenAIDatabase/session_history/` and `OpenAIDatabase/token_usage/`.
6. For CodexBar local token/cost display, the current synthetic archive is under `/Users/linzezhang/.codex/archived_sessions/old-mac-token-usage-20260630-synthetic`.

