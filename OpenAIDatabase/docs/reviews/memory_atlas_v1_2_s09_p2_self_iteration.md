# Memory Atlas v1.2 S09 P2 Self Iteration

## Scope

- task_id: `MA-V12-S09P2`
- acceptance_id: `ACC-MA-V12-S09P2`
- status: `phase_s09_p2_self_iteration_completed_pending_s09_p3`
- validator: `validate:v1.2-s09-p2`
- config: `机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json`
- builder: `scripts/build_memory_atlas_self_iteration.py`
- output: `data/derived/behavior_intelligence/self_iteration_suggestions.json`

S09 P2 only generates proposal-only self-iteration suggestions. It does not
apply proposals, edit memory/config/AGENTS/style/personalization target files,
create a decision debt ledger, mutate raw data, push a remote branch, or upload
GitHub main.

## Acceptance

Each suggestion contains:

- `target_type`
- `target_files`
- `rationale_zh`
- `expected_change_zh`
- `evidence_refs`
- `action_half_life_days`
- `proposal.expires_at`
- `proposal.validation_commands`
- `proposal.rollback_plan_zh`

Current output:

| Suggestion | Target | Half-Life | Expires At | Source |
|---|---|---:|---|---|
| `self_iter_memory_a39afeb2bc01` | memory | 45 days | `2026-08-07T08:18:30Z` | `reusable_asset_candidate` |
| `self_iter_config_452697c82264` | config | 30 days | `2026-08-07T08:18:30Z` | `workflow_reuse_candidate` |
| `self_iter_agents_5ac6261d70fe` | AGENTS | 21 days | `2026-08-07T08:18:30Z` | `scope_boundary_candidate` |
| `self_iter_style_bacfc2ea0ab5` | style | 14 days | `2026-08-07T08:18:30Z` | `quality_ceiling_candidate` |
| `self_iter_personalization_0ffe0fc24ec9` | personalization | 21 days | `2026-08-07T08:18:30Z` | `artifact_closure_candidate` |

Proposal expiry policy:

- warn after 7 days
- stale after 30 days
- archive after 90 days
- permanent pending is not allowed

## Safety

- Every proposal starts at `pending_human_review`.
- `apply_execution_allowed=false` for every proposal.
- `raw_apply_target_allowed=false` for every proposal.
- `not_permanent_pending=true` for every proposal.
- Decision debt ledger is deferred to S09 P3.
- The output stays a candidate list, not a pressure list.

## Validation

- `python -B -m unittest OpenAIDatabase.tests.test_s09p2_self_iteration -q`
- `python OpenAIDatabase/scripts/atlasctl.py analyze --stage self-iteration --dry-run`
- `python OpenAIDatabase/scripts/atlasctl.py audit --check self-iteration-safety`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s09-p2`

## Boundary

Machine-readable boundary summary: Memory Atlas v1.2 S09 P2 Self Iteration; MA-V12-S09P2; ACC-MA-V12-S09P2; phase_s09_p2_self_iteration_completed_pending_s09_p3; validate:v1.2-s09-p2; self_iteration_suggestions.json; proposal expiry; action half-life; memory; config; AGENTS; style; personalization; pending S09 P3; No GitHub main upload in this phase; No remote push in this phase; No raw mutation; No proposal apply execution; No decision debt ledger; No permanent pending proposal.
