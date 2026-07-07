# Memory Atlas v1.1.7 Stage 5 Phase 5.2 C3 River Spike Acceptance

- Task ID: `MA-V117-S5P02`
- Acceptance ID: `ACC-MA-V117-S5P02`
- Status: `phase_5_2_c3_river_spike_completed_pending_stage5_review`
- Spike version: `memory_river_c3_spike.v1_1_7_stage5_phase2`
- Static validator: `validate:v1.1.7-stage5-phase2`
- Browser validator: `validate:memory-river-spike-browser`

## Scope

This phase upgrades the isolated C3 Memory River spike only. It does not replace
the production Timeline, add a production route, change navigation, set a
feature flag default, deploy, upload to GitHub main, read raw/private data or
write active memory.

## Required Checks

Stage 5 Phase 5.2 passes only when:

1. Stage 5 Phase 5.1 continuity is preserved through
   `validate:v1.1.7-stage5-phase1`.
2. `memory-river-spike` exposes year, month, week and day time scale levels.
3. Browser zoom changes the Memory River zoom scale and preserves date
   positioning.
4. A selected range brush produces selected range themes and selected range
   events.
5. Theme lanes show `rising`, `declining`, `stable` and `conflict` trends.
6. Black Hole and Proto-Star signals can be positioned on the time scale and
   included in selected range output.
7. Reduced motion disables continuous animation while keeping interactions
   available.
8. The browser validator captures screenshot evidence.
9. Redacted fixture safety flags remain false:
   `rawPrivateDataIncluded`, `plaintextSecretsIncluded`,
   `localAbsolutePathsIncluded` and `writebackAllowed`.
10. Records include `MA-V117-S5P02`, `ACC-MA-V117-S5P02`,
    `phase_5_2_c3_river_spike_completed_pending_stage5_review`,
    `validate:v1.1.7-stage5-phase2`, `validate:memory-river-spike-browser`,
    `memory_river_c3_spike.v1_1_7_stage5_phase2`, `No production Timeline
    replacement` and `No GitHub main upload`.

## Validation

Required local validation:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage5-phase2
python /Users/linzezhang/.codex/skills/webapp-testing/scripts/with_server.py --server "pnpm --dir OpenAIDatabase/apps/memory-atlas exec vite --host 127.0.0.1 --port 5196" --port 5196 -- node OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs --url http://127.0.0.1:5196/src/experiments/memory-river-spike/index.html?smoke=1 --output-dir /tmp/memory-river-stage5-phase2
```

## Failure Conditions

Fail this phase if:

- the spike becomes a date list, static scatter or ordinary chart without river
  interaction;
- the time scale does not support year, month, week and day;
- selected range output omits selected range themes or selected range events;
- Black Hole or Proto-Star signals cannot be located by date;
- reduced motion disables required interactions;
- production code imports or references `memory-river-spike`;
- raw/private/cookie/session/secret data is read;
- active memory, proposals, deployment, PRs, branches or GitHub main upload are
  created.

## Boundary

- No production Timeline replacement.
- No production route or navigation change.
- No feature flag default switch.
- No raw/private/cookie/session/secret data read.
- No direct active-memory writeback.
- No proposal write.
- No agent apply.
- No Stage 5.3.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Stage 5 Phase 5.2 C3 River Spike;
MA-V117-S5P02; ACC-MA-V117-S5P02;
phase_5_2_c3_river_spike_completed_pending_stage5_review;
validate:v1.1.7-stage5-phase2; validate:memory-river-spike-browser;
memory_river_c3_spike.v1_1_7_stage5_phase2; year; month; week; day; selected
range; rising; declining; stable; conflict; Black Hole; Proto-Star; No
production Timeline replacement; No GitHub main upload.
