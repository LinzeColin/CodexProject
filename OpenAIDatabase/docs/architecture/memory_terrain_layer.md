# Memory Terrain Layer

- Contract version: `memory_terrain_layer.v1_1_7_stage4_phase1`
- Linked visual contract: `memory_starfield_visual_contract.v1_1_7_stage4_phase1`
- Task ID: `MA-V117-S4P01`
- Acceptance ID: `ACC-MA-V117-S4P01`
- Status: `phase_4_1_visual_contract_update_completed_pending_stage4_review`
- Validator: `validate:v1.1.7-stage4-phase1`

Stage 4 Phase 4.1 defines the terrain layer as an analysis-mode semantic
surface inside Memory Starfield. It is not a separate knowledge map and not a
source importer. The terrain semantic registry below converts long-lived memory
patterns into visual geography that future starfield rendering can test.

## terrain semantic registry

| Terrain class | Chinese term | Visual definition | Data-derived signal | Inspector handoff |
|---|---|---|---|---|
| `long_term_theme` | 长期主题 | Ridge or highland area that persists across multiple review windows. | Stable theme frequency, high confidence, repeated useful decisions. | Show theme age, evidence count, linked assets and next useful action. |
| `growth_band` | 成长带 | Bright rising band or slope around skills, projects or opportunities gaining traction. | Positive trend, rising action count, new evidence and improved ROI. | Show growth driver, uncertainty and validation proposal. |
| `migration_flow` | 迁移流 | River-like path across terrain where focus moved from one theme to another. | Source theme, target theme, time window and transition reason. | Show before/after summary and reversible proposal path. |
| `relic` | 遗迹 | Dim preserved structure that still explains current behavior but is no longer active. | Old high-confidence evidence with low recent activity. | Show why it remains retained and whether review is needed. |
| `black_hole` | 黑洞 | Depression, distortion or collapse basin for loops, stale risk and low-value pull. | Repetition, low ROI, conflict, stale orbit or attention sink score. | Show cause, evidence count, mitigation and proposal-only boundary. |
| `opportunity` | 机会 | Proto-star terrain pocket or fertile edge where new value may emerge. | Weak but rising signal, cross-theme relation and uncertainty score. | Show validation path, confidence and next observation. |

## Rendering Rules

1. `memory_terrain_layer` is required in Analysis Mode and optional but hinted in
   Presentation Mode.
2. Terrain must explain the same memory universe as `nebula_field`,
   `flow_field`, `particle_trails`, `gravity_sources`, `black_hole_core` and
   `proto_star_cloud`; it must not introduce unrelated data.
3. Terrain colors and elevation may be simplified under reduced motion or
   low-quality fallback, but the semantic class must remain inspectable.
4. Terrain must be generated only from redacted derived state, aggregated
   counts, labels and scores. No raw/private/cookie/session/secret payload is
   allowed.

## Overload Control

The full terrain registry has six classes. If a future implementation becomes
visually overloaded, the Top 4 fallback is:

1. `long_term_theme`
2. `growth_band`
3. `black_hole`
4. `opportunity`

`migration_flow` and `relic` may move into hover/Inspector detail in that
fallback, but they must remain defined in the contract and available for future
Analysis Mode expansion.

## Boundary

This phase creates the terrain contract only. No Phase 4.2, No runtime renderer
replacement, No C3 Starfield Spike implementation, No browser screenshot, No
production build, No direct active-memory writeback, No agent apply and No
GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary tokens: No Phase 4.2; No runtime renderer replacement; No GitHub main upload before the whole Stage 0-10 project is complete.
