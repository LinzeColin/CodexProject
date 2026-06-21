# Private Structured Context Source

This directory documents the private three-layer context model used by
OpenAIDatabase. It intentionally contains structure and routing contracts, not
raw private exports.

Canonical machine configuration:

- `config/context_sources/three_layer_context.json`
- `config/context_sources/resource_routes.json`

Layer directories:

- `l1_core_profile`: stable profile, preference, taste, answer style, plans.
- `l2_project_memory`: projects, decisions, active memory, workflows.
- `l3_behavior_history`: timeline, Codex behavior, recurring patterns, weekly
  and monthly review context.

Do not place plaintext secrets, raw ChatGPT/Codex transcripts, cookies, browser
profiles, or unredacted exports here.
