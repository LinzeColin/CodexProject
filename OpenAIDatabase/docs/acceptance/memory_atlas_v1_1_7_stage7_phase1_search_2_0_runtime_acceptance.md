# Memory Atlas v1.1.7 Stage 7 Phase 7.1 Search 2.0 Runtime Acceptance

Task ID: `MA-V117-S7P01`

Acceptance ID: `ACC-MA-V117-S7P01`

Status: `phase_7_1_search_2_0_runtime_completed_pending_stage7_review`

Runtime version: `search_2_0_runtime.v1_1_7_stage7_phase1`

Session summary version: `search_2_0_session_summary.v1_1_7_stage7_phase1`

Static validator: `validate:v1.1.7-stage7-phase1`

Browser validator: `validate:search-2-0-browser`

## Scope

This phase implements Search 2.0 runtime integration only. It must provide a
usable query/filter/result workflow over the existing public redacted derived
Memory Atlas snapshot, and it must connect results to the already implemented
Starfield, Memory River and Inspector surfaces.

This phase does not implement Review / Summary / Iteration runtime, Stage 7
review, Stage 8 summary iteration closure, direct database writeback, agent
apply, deployment or GitHub main upload.

## Runtime Acceptance

The Search 2.0 runtime must expose:

| Surface | Required behavior |
|---|---|
| `query_input` | User can enter natural language query inside the Search view. |
| `filter_state` | UI shows active query, tier, topic, recency, importance and evidence-only filters with result count. |
| `result_list` | Each result shows title, summary, source, tier, topic, recency, importance, `matched_reason`, `evidence_refs` and `proposal_candidate`. |
| `result_action_bar` | Each result exposes `jump_to_starfield`, `jump_to_river` and `open_inspector`. |
| `search_session_summary` | Summary shows query, result_count, dominant_topics, high_importance_hits, stale_or_black_hole_hits, missing_evidence, next_step and proposal_candidate. |
| `zero_result_recovery` | Empty searches show broaden query, remove filter, related topic, stale/archive and later review hint actions. |

## Browser Acceptance

`validate:search-2-0-browser` must prove:

1. The Search view renders `search_2_0_runtime.v1_1_7_stage7_phase1`.
2. A query such as `Codex` yields at least one result with `matched_reason` and
   `evidence_refs`.
3. The debug hook `window.__memoryAtlasStage7Phase1()` reports result coverage,
   jump actions and safety flags.
4. A zero-result query renders `zero_result_recovery`.
5. `jump_to_starfield` switches to Starfield and preserves the selected node.
6. `jump_to_river` switches to Memory River and preserves the selected node.
7. `open_inspector` keeps Search 2.0 open and selects the Inspector node.
8. A screenshot is captured and there are no actionable browser console errors
   or failed responses.

## Safety Acceptance

The phase passes only when all of the following remain true:

1. No Review / Summary / Iteration runtime.
2. No raw/private/cookie/session/secret data access.
3. No direct active-memory writeback.
4. No proposal queue write from Search 2.0.
5. No agent apply.
6. No deploy.
7. No GitHub main upload before the whole Stage 0-10 project is complete.

## Validation

Required validation:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage7-phase1
python /Users/linzezhang/.codex/skills/webapp-testing/scripts/with_server.py --server "pnpm --dir OpenAIDatabase/apps/memory-atlas exec vite --host 127.0.0.1 --port 5201" --port 5201 -- node OpenAIDatabase/apps/memory-atlas/scripts/validate_search_2_0_browser.cjs --url http://127.0.0.1:5201/ --output-dir /tmp/search-2-0-stage7-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
pnpm --dir OpenAIDatabase/apps/memory-atlas run build
git diff --check -- OpenAIDatabase
```

## Rollback

Revert the Stage 7 Phase 7.1 commit. This removes the Search 2.0 runtime
surface, scoped CSS, validators, acceptance and records. No raw/private source
data, active memory database, proposal queue or GitHub main tree is mutated by
this phase.
