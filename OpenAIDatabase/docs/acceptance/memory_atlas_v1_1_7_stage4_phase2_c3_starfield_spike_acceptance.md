# Memory Atlas v1.1.7 Stage 4 Phase 4.2 C3 Starfield Spike Acceptance

- Spike version: `memory_starfield_c3_spike.v1_1_7_stage4_phase2`
- Task ID: `MA-V117-S4P02`
- Acceptance ID: `ACC-MA-V117-S4P02`
- Status: `phase_4_2_c3_starfield_spike_completed_pending_stage4_review`
- Static validator: `validate:v1.1.7-stage4-phase2`
- Browser validator: `validate:memory-starfield-spike-browser`

## Required Checks

Stage 4 Phase 4.2 passes only when:

1. The isolated experiment remains under
   `apps/memory-atlas/src/experiments/memory-starfield-spike/`.
2. The default browser path renders `>=10k particles`.
3. Browser metrics report `>=30 FPS` on the local desktop validation run.
4. Flow Field / Curl Noise reports `curl_noise_shader`.
5. The scene exposes at least `256` particle trails.
6. Cluster Gravity exposes at least six gravity sources with damping and a
   minimum-distance clamp.
7. Hover Cards B2 shows topic, redacted summary, importance and priority.
8. Browser validation captures a screenshot.
9. Production `src/App.tsx`, `src/main.tsx`, production components, production
   styles, app bundle, raw/private data and deploy files are not changed.
10. Records and package scripts register both validators.

## Non-Goals

- No production Galaxy replacement.
- No production route or navigation change.
- No feature flag default switch.
- No Stage 4 review.
- No production build as acceptance for this phase.
- No local app install.
- No Cloudflare deploy.
- No raw/private/cookie/session/secret data read.
- No direct active-memory writeback.
- No agent apply.
- No GitHub main upload before the whole Stage 0-10 project is complete.

## Validation

Static validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage4-phase2
```

Browser validator, with a local Vite server already running:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:memory-starfield-spike-browser -- --url http://127.0.0.1:5194/src/experiments/memory-starfield-spike/index.html --output-dir /tmp/memory-starfield-stage4-phase2
```

The browser validator must verify particle count, FPS, `curl_noise_shader`,
particle trails, gravity sources, Hover Cards B2, screenshot bytes and console
errors.
