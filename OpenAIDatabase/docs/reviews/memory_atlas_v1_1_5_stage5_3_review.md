# Memory Atlas v1.1.5 Stage 5.3 Review

- Review date: 2026-07-01
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 5.3 Evidence Layers
- Runtime status: `时间轴` defaults to `memory-river`; `legacy` remains the
  rollback renderer.

## Review Result

Stage 5.3 is review-passed.

The implementation satisfies the phase acceptance target: Memory River now
renders black-hole lifecycle bands, proto-star lifecycle growth paths, and
stale/deprecated cooling fade layers. All three layers are derived from the
existing redacted timeline/node snapshot and use the same black-hole /
proto-star candidate semantics already used by Home Overview.

This review does not complete Stage 5. The Stage 5 whole-stage review, any
findings from that review, and GitHub main upload remain separate.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 5.3.1 Black Hole Lifecycle | `black-hole-lifecycle` renders a band, strength path and points for stale / needs-review / deprecated / temporary low-weight signals. The mapping reuses `isBlackHoleCandidate`, keeping Timeline aligned with Home Overview risk-loop counts. | PASS |
| 5.3.2 Proto-Star Lifecycle | `proto-star-lifecycle` renders a growth path and opportunity markers for recent decision, project-context, high-importance and high-leverage signals. | PASS |
| 5.3.3 Stale / Deprecated Layer | `stale-deprecated` renders cooling fade segments for stale, deprecated and temporary signals without exposing raw transcript content. | PASS |
| Model Parameters | `config/visualization/model_parameters.memory_river.yaml` now records Stage 5.3 evidence-layer inputs, render shapes, caps and rollback options. | PASS |

## Validation Evidence

Commands run from the CodexProject worktree root unless noted:

```bash
git diff --check

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-river-rendering

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-river-interaction

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-river-evidence

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase

cd OpenAIDatabase
python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
```

Observed results:

1. `validate:memory-river-rendering`: PASS, 5/5 checks.
2. `validate:memory-river-interaction`: PASS, 5/5 checks.
3. `validate:memory-river-evidence`: PASS, 5/5 checks.
4. `pnpm lint`: PASS.
5. `pnpm build`: PASS, with the existing Vite warning that `GalaxyScene` is
   larger than 500 kB after minification.
6. Visual acceptance audit: PASS, 32/32 checks, including
   `timeline_stage5_3_evidence_layers_ready`.
7. Release audit: PASS, 6 publish files audited.
8. Overall acceptance audit: PASS, including `memory_atlas_visual_acceptance`
   32 checks passed.
9. Chrome CDP evidence: screenshot
   `/tmp/memory-atlas-stage5-3-evidence-layers.png`, sha256
   `d289286a823f940b2323ec4fdd5d6ac9c7cad7dd3453774b04d8baaa4b7292b4`;
   renderer `memory-river`; `data-evidence-layers` contains
   `black-hole-lifecycle proto-star-lifecycle stale-deprecated`.
10. Chrome CDP layer counts: black-hole band `1`, black-hole points `6`,
    proto-star path `1`, proto-star points `10`, stale fade segments `18`,
    redacted evidence titles `3`.
11. Preview cleanup: `lsof -nP -iTCP:4177 -sTCP:LISTEN` and
    `lsof -nP -iTCP:9227 -sTCP:LISTEN` returned no listeners after shutdown.

## Boundary Review

Stage 5.3 did not:

1. Run Stage 5 whole-stage review.
2. Push or merge to GitHub main.
3. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
4. Add ingestion or direct writeback.
5. Upload to Cloudflare or change Access policy.

## Residual Risks

1. Evidence-layer thresholds are heuristic and based on existing derived
   candidate semantics, not calibrated from user feedback.
2. Dense late-window signals can visually cluster near the right edge of the
   river; the layer remains readable but may need future collision avoidance.
3. The existing GalaxyScene chunk-size warning remains unrelated to this phase.

## Next Gate

Run the Stage 5 whole-stage review across Stage 5.1, 5.2 and 5.3. Fix any
findings, then upload the reviewed Stage 5 state to GitHub main.
