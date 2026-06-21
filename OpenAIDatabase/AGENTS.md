# OpenAIDatabase Agent Rules

Default user-facing language: Chinese. Keep code identifiers, API names, model
names, errors, and source titles in English when that is clearer.

## Startup

1. Read this `AGENTS.md`.
2. Route the task with `scripts/route_agent_resources.py --intent <intent>`.
3. For default startup, read only the route's required `read_order`.
4. Load `data/derived/profile/CORE_PROFILE.md`, full agent context packs, or
   architecture docs only when the route lists them as conditional resources
   and the current task gives a concrete reason.
5. For ChatGPT/Project personalization tasks, read
   `data/derived/personalization/chatgpt_personalization.md`.

Use route-specific files before broad repository search.

## Canonical Contracts

- Three-layer context source: `config/context_sources/three_layer_context.json`
- Resource routing: `config/context_sources/resource_routes.json`
- Codex runtime config: `.codex/config.toml`
- Personalization manifests, not runtime config:
  `config/codex/config.template.toml` and `config/codex/project.config.toml`
- Evaluation harness: `config/evaluation/personalization_harness.json`
- Task-run evidence schema: `config/evaluation/task_run.schema.json`
- Detailed user requirements: `docs/USER_REQUIREMENTS.md`
- Model and parameter documentation: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Delivery record: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`

## Sync Requirement

Any future agent that updates or syncs profile, preference, taste, history, or
pattern information must:

1. Update the mapped source files in the three-layer context.
2. Regenerate `data/derived/agent_context/*`.
3. Regenerate `data/derived/personalization/*`.
4. Run `scripts/evaluate_personalization_context.py`.
5. Append a redacted task-run evidence row under one of:
   - `data/run_logs/sync_runs/`
   - `data/run_logs/export_runs/`
   - `data/run_logs/evaluation_runs/`
   - `data/run_logs/agent_runs/`
   Each row must include `context_used`, `tools_used`, `tests_run`, and
   `failure_recovery`.
6. Commit and push the redacted derived updates to GitHub.

If the update target is unclear, log it as `UNKNOWN` with a follow-up task.
Do not silently drop memory-affecting changes.

## Hard Boundaries

- Do not commit raw OpenAI exports, full transcripts, cookies, browser state,
  `.local_keys/`, `.env`, plaintext secrets, private keys, or local absolute
  paths.
- Do not automate ChatGPT login, UI scraping, export download, or saved-memory
  writes.
- Generated memory candidates remain pending until reviewed.
- Memory Atlas may consume only redacted derived visualization data from
  `data/derived/visualization/memory_atlas.json`.
- Frontend writeback must remain proposal-only; do not directly mutate
  `data/memory/active/active_memory.jsonl` from the UI.
- Local `node_modules`, `dist`, app bundles, temporary work, and caches are not
  delivery artifacts and must not be committed.

## Minimum Validation

Run the narrowest useful checks for the change. For personalization/context
changes, use:

```bash
python3 scripts/build_personalization_exports.py --database-dir .
python3 scripts/route_agent_resources.py --database-dir . --intent startup
python3 scripts/evaluate_personalization_context.py --database-dir .
python3 -m unittest tests.test_personalization_architecture -q
```

For broader OpenAIDatabase changes, add:

```bash
python3 -m py_compile scripts/build_agent_context_pack.py scripts/sync_codex_memory_data.py
python3 -m unittest discover -s tests -p "test_*.py" -q
```
