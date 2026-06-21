# OpenAIDatabase Agent Rules

Default user-facing language: Chinese. Keep code identifiers, API names, model
names, errors, and source titles in English when that is clearer.

## Startup

1. Read `docs/PERSONAL_CONTEXT_ARCHITECTURE.md`.
2. Route the task with `scripts/route_agent_resources.py --intent <intent>`.
3. For fast personalization, read `data/derived/profile/CORE_PROFILE.md`.
4. For Codex startup context, read `data/derived/personalization/codex_personalization.md`.
5. For ChatGPT/Project personalization, read `data/derived/personalization/chatgpt_personalization.md`.

Use route-specific files before broad repository search.

## Canonical Contracts

- Three-layer context source: `config/context_sources/three_layer_context.json`
- Resource routing: `config/context_sources/resource_routes.json`
- Codex config template: `config/codex/config.template.toml`
- Project config: `config/codex/project.config.toml`
- Evaluation harness: `config/evaluation/personalization_harness.json`
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
5. Append a redacted run log under one of:
   - `data/run_logs/sync_runs/`
   - `data/run_logs/export_runs/`
   - `data/run_logs/evaluation_runs/`
   - `data/run_logs/agent_runs/`
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
