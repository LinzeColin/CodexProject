# Memory Atlas 记忆时间河 C3 隔离原型合同

- Version: v1.1.6 Stage 9 Phase 2
- Contract ID: `memory_river_c3_spike_contract`
- Task ID: `MA-V116-S9P02`
- Status: `phase_9_2_memory_river_c3_spike_ready_pending_stage_review`

## Goal

Stage 9 Phase 2 fixes the Memory River spike as the second runnable C3
isolated prototype evidence for Roadmap v2. It verifies that the existing
`memory-river-spike` remains inspectable, redacted, deterministic and isolated
from production before any future Timeline replacement or integration work.

This phase validates and documents the isolated prototype. It does not replace
the production Timeline, import the experiment directory into the app shell,
run a production build, start browser screenshot acceptance, deploy Cloudflare,
modify Access policy, read raw/private data, write proposals or write active
memory.

## Prototype Surface

The C3 Memory River spike surface is:

- `apps/memory-atlas/src/experiments/memory-river-spike/README.md`
- `apps/memory-atlas/src/experiments/memory-river-spike/index.html`
- `apps/memory-atlas/src/experiments/memory-river-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-river-spike/fixture.ts`

The prototype must stay reachable as a standalone Vite experiment path and
must not become a production route, navigation item, feature flag default,
Timeline renderer import or shared runtime dependency in this phase.

## Required Prototype Features

The spike must continue to expose:

1. `d3_time_scale`: D3 UTC time scale for accurate event positioning.
2. `zoom_pan`: horizontal D3 zoom and pan behavior.
3. `brush_selection`: D3 brush range selection with readable dates.
4. `theme_lanes`: macro, meso and micro theme lanes.
5. `black_hole_band`: visible low-value loop / risk interval band.
6. `proto_star_marker`: visible opportunity marker with confidence.
7. `event_pulses`: date-specific pulses with kind, intensity and evidence.
8. `hover_card`: redacted hover summary for lanes, events, bands and markers.
9. `reduced_motion`: reduced-motion mode that keeps interactions usable.
10. `smoke_status_hook`: hidden automation hook for future browser checks.

## Required Fixture Contract

`fixture.ts` may contain only deterministic redacted derived fixture data. It
must include:

- `schemaVersion`
- `source`
- `rawPrivateDataIncluded: false`
- `plaintextSecretsIncluded: false`
- `localAbsolutePathsIncluded: false`
- `writebackAllowed: false`
- theme lanes with stable IDs, labels, levels and evidence counts
- redacted timeline events with date, kind, confidence and evidence counts
- Black Hole bands with start and end dates
- Proto-Star markers with confidence and evidence counts

Forbidden fixture payload:

- raw transcripts
- cookies, sessions, browser state or tokens
- plaintext secrets or private keys
- local absolute paths
- writeback permission or direct active-memory mutation

## Isolation Rules

Fail this phase if:

- production `src/App.tsx`, `src/main.tsx` or production components import or
  reference `memory-river-spike`;
- a navigation item, route, feature flag default or production Timeline points
  to this experiment;
- the spike reads raw/private/cookie/session/secret payloads;
- the spike writes active memory or proposals;
- the spike removes D3 UTC scale, zoom, brush, theme lanes, Black Hole band,
  Proto-Star marker, event pulses, hover card, reduced motion or smoke status
  evidence;
- the spike becomes a date list, static scatter or ordinary chart with no
  river interaction layer.

## Safety Boundary

- No production runtime integration.
- No production route or navigation change.
- No feature flag default switch.
- No production build in this phase.
- No browser screenshot run in this phase.
- No local app install or rebuild.
- No Cloudflare live deploy.
- No Access policy change.
- No raw/private/cookie/session/secret data read.
- No raw/private data read.
- No direct writeback.
- No proposal write.
- No agent apply.
- No Stage 9 review, Stage 10 work or GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Acceptance Hook

Future implementation phases may run browser smoke checks against:

```text
/src/experiments/memory-river-spike/index.html?smoke=1
```

This phase only validates the static contract, fixture safety, production
isolation and governance records.
