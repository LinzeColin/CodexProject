# OpenAIDatabase Personal Context Architecture

This document is the canonical architecture entry for future agents that need
profile, preference, taste, history, pattern, project context, or
personalization data from `LinzeColin/CodexProject/OpenAIDatabase`.

## Scope

OpenAIDatabase is a private, structured, local-first memory source. GitHub
stores redacted derived memory, machine-readable contracts, generated
personalization exports, and audit logs. Raw exports, cookies, browser state,
full transcripts, plaintext secrets, and private keys stay outside GitHub.

## Three-Layer Context Source

The machine contract is `config/context_sources/three_layer_context.json`.

### L1_CORE_PROFILE

- Purpose: durable core profile, stable answer style, collaboration standards,
  preference, taste, long-term plans, and hard safety boundaries.
- Canonical files:
  - `data/memory/records/manifest.json`
  - `data/derived/profile/CORE_PROFILE.md`
- Required update targets: `profile`, `preference`, `taste`.

### L2_PROJECT_MEMORY

- Purpose: accepted active memory, project index, decision log, reusable
  workflows, medium/long-term constraints, and durable project context.
- Canonical files:
  - `data/memory/records/manifest.json`
  - `data/derived/project_index/PROJECT_INDEX.md`
  - `data/derived/decision_log/DECISION_LOG.md`
- Required update targets: `history`, `pattern`, `project_context`.

### L3_BEHAVIOR_HISTORY

- Purpose: redacted Codex behavior history, activity snapshots, recurring
  execution patterns, timeline, weekly/monthly packs, candidates, and temporary
  sensitive references.
- Canonical files:
  - `data/processed/codex/codex_activity_snapshot.json`
  - `data/processed/codex/codex_daily_activity.jsonl`
  - `data/processed/codex/codex_session_manifest.jsonl`
  - `data/derived/codex/codex_agent_recommendations.json`
  - `data/derived/timeline/TIMELINE.md`
  - `data/derived/weekly/*.weekly_memory_pack.md`
  - `data/derived/monthly/*.monthly_memory_pack.md`
- Required update targets: `history`, `pattern`.

Canonical candidate, active, disputed, and retired states share the V2 schema
under `data/memory/records/`. The former `active/`, `candidates/`, `curation/`,
and `secret_refs/` trees are read-only migration evidence, not update targets.

## Generated Personalization Exports

Generated outputs live in `data/derived/personalization/`:

- `chatgpt_personalization.md`: compact ChatGPT/Project personalization export.
- `codex_personalization.md`: Codex startup and AGENTS-oriented export.
- `personalization_export.json`: machine-readable export with source refs,
  update targets, and route hints.

Regenerate them with:

```bash
python3 scripts/build_agent_context_pack.py --database-dir .
python3 scripts/build_personalization_exports.py --database-dir .
```

`scripts/sync_codex_memory_data.py --build-atlas` also rebuilds the
personalization exports after refreshing Codex-derived data.

## Codex Config

- Runtime project config: `.codex/config.toml`
- User personalization manifest: `config/codex/config.template.toml`
- Project personalization manifest: `config/codex/project.config.toml`

Only `.codex/config.toml` is the Codex project runtime config. It uses the
official Codex config shape and keeps the project-level settings intentionally
small: `project_doc_max_bytes`, `features.memories`, and
`sandbox_workspace_write.network_access`.

The two files under `config/codex/` are OpenAIDatabase personalization
manifests. They are valid TOML, but they are not loaded automatically by Codex
and must not be copied verbatim into `~/.codex/config.toml`.

## On-Demand Resource Routing

Machine route definitions live in `config/context_sources/resource_routes.json`.

Use:

```bash
python3 scripts/route_agent_resources.py --database-dir . --intent startup
python3 scripts/route_agent_resources.py --database-dir . --intent taste_profile
```

Agents must start with the smallest route that matches the task instead of
loading the entire repository. Broad search is allowed only after the route is
insufficient.

The startup route is intentionally minimal:

- Required `read_order`: `AGENTS.md`,
  `data/derived/personalization/codex_personalization.md`.
- Conditional resource:
  `data/derived/profile/CORE_PROFILE.md`, only when the task needs stable user
  profile or taste detail beyond the startup summary.

`docs/PERSONAL_CONTEXT_ARCHITECTURE.md`, full `AGENT_CONTEXT.md`,
`agent_context_pack.json`, and full Memory Atlas data are not default startup
resources. They are loaded for architecture maintenance, profile analysis, or
memory audit tasks with an explicit reason.

## Evaluation Harness

Machine rules live in `config/evaluation/personalization_harness.json`.

Run:

```bash
python3 scripts/evaluate_personalization_context.py --database-dir .
```

The harness checks required architecture files, generated exports, required
sections, update targets, log categories, JSONL syntax, task-run evidence
schema, test exit-code evidence, and basic forbidden plaintext patterns.

## Per-Task Evidence And Run Log Categories

Run logs live under `data/run_logs/` and are designed for GitHub backup:

- `sync_runs`: Codex/ChatGPT/source sync operations.
- `export_runs`: generated personalization export operations.
- `evaluation_runs`: evaluation harness results.
- `agent_runs`: meaningful future-agent runs that update or consume
  personalization context.

Logs are JSONL and must be redacted. Each task row must include the four
evidence fields required by `config/evaluation/task_run.schema.json`:

- `context_used`
- `tools_used`
- `tests_run`
- `failure_recovery`

`PASS` tests must include `exit_code = 0` and an evidence path that exists.
`NOT_RUN` tests must include `not_run_reason`. Planned commands are not
recorded as executed tests. Do not write raw transcript text, plaintext
secrets, cookies, browser state, or local absolute paths.

## Future-Agent Sync Rule

Any future agent that changes user profile, preference, taste, history, or
pattern information must update the corresponding canonical source files and
then regenerate the derived exports.

Minimum required sequence:

1. Update the relevant source layer file.
2. Rebuild `data/derived/agent_context/*`.
3. Rebuild `data/derived/personalization/*`.
4. Run the evaluation harness.
5. Append the matching run log category.
6. Commit and push the redacted derived files to GitHub.

If the agent cannot determine which target changed, it must mark the item as
`UNKNOWN` in the run log and create a follow-up task rather than silently
dropping the update.
