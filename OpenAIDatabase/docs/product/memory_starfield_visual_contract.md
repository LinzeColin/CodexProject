# Memory Starfield Visual Contract

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.2.2 记忆星系 Visual Contract
- Status: visual contract only; no production UI implementation
- Last updated: 2026-06-30

## Purpose

“记忆星系”是现有 Galaxy 板块的目标替代形态。它必须把长期记忆、项目、兴趣、行为模式、机会、风险和决策关系表现为深空星云、Flow Field、星系引力盘、Black Hole、Proto-Star 和 Memory Terrain，而不是普通点线图。

This contract freezes the visual direction and interaction boundaries before any spike or production integration.

## Hard Visual Boundary

记忆星系不得退回以下形态：

1. 普通 node-link graph。
2. 静态 scatter plot。
3. 小光点随机漂浮。
4. 只有线和点、没有空间结构和语义层的图。
5. 纯装饰粒子背景，无法解释 Universe State。

The starfield must remain data-driven. It may be visually immersive, but every primary visual signal must map back to redacted derived memory data or Universe State.

## Visual Layers

### 1. Deep-Space Nebula

Nebula is the atmospheric layer for topic density and semantic proximity.

Required mapping:

| Visual signal | Meaning |
|---|---|
| Nebula density | local memory/activity density |
| Nebula color family | theme/category/source mixture |
| Nebula opacity | confidence or evidence coverage |
| Nebula spread | topic dispersion |

Nebula must not be hard-coded decoration. If data is sparse, it should become subtle instead of inventing structure.

### 2. Flow Field

Flow Field shows movement of attention, behavior or project momentum across the memory universe.

Required mapping:

1. Direction: movement between related themes or phases.
2. Speed/intensity: recent activity or rising score.
3. Turbulence: conflict, fragmentation or repeated switching.
4. Calm zones: stable mature themes.

Flow Field must be optional or simplified under reduced motion.

### 3. Gravitational Disk

The gravitational disk organizes high-importance clusters into a galaxy-like structure.

Required mapping:

| Disk concept | Memory meaning |
|---|---|
| Core | dominant high-leverage memory clusters |
| Spiral arms | related project/theme paths |
| Orbit distance | semantic/behavioral distance from core |
| Orbit stability | recurrence and consistency |
| Edge objects | weak, new, or drifting topics |

The disk must support focus/zoom without collapsing into a flat list.

### 4. Black Hole

Black Hole visualizes low-value loops, repeated mistakes, conflict zones, or attention sinks.

Required traits:

1. Strong local distortion or absorption visual.
2. Distinct from normal dense clusters.
3. Evidence-linked in Analysis Mode.
4. Click opens Inspector with cause, evidence, confidence and reduction proposal.

Black Hole is a risk signal, not a moral judgment and not a deletion command.

### 5. Proto-Star

Proto-Star visualizes early opportunities, emerging themes, possible projects, or new capability growth.

Required traits:

1. Small but visually alive signal.
2. May sit near weak clusters or rising trajectories.
3. Must show why it is early and uncertain.
4. Click opens validation path and evidence.

Proto-Star must not be promoted to dominant cluster until Universe State supports it.

### 6. Memory Terrain

Memory Terrain is a semantic terrain layer inside the starfield, not an external knowledge-source import feature.

Required terrain concepts:

| Terrain | Meaning |
|---|---|
| Ridge | persistent high-ROI theme |
| Valley | underdeveloped or inactive area |
| Basin | repeated low-value loop |
| Fault line | contradiction or conflict zone |
| Shoreline | boundary between mature and emerging topics |

Memory Terrain must be subtle in Presentation Mode and explainable in Analysis Mode.

## Presentation / Analysis Modes

### Presentation Mode

Presentation Mode is the default. It should feel like an immersive, readable memory universe.

Required behavior:

1. Minimal labels.
2. Clean visual hierarchy.
3. Hover reveals only human-readable summaries.
4. Black Hole and Proto-Star remain visible but not over-explained.
5. Motion is elegant and bounded.

### Analysis Mode

Analysis Mode exposes the reasoning layer.

Required behavior:

1. Show formulas, parameters and confidence where available.
2. Show legend for visual encodings.
3. Show evidence counts and source scope.
4. Enable Inspector details.
5. Show debug-lite states without exposing raw/private data.

Analysis Mode must explain, not overwhelm. It must still preserve spatial context.

## Interaction Boundary

Required interactions for future implementation:

1. Hover object: show human summary, type, confidence and evidence count.
2. Click object: sync Inspector focus.
3. Focus cluster: zoom or pan into local neighborhood.
4. Toggle edges/flow/terrain: reduce visual noise.
5. Select source/filter/time range: recompute visible starfield from shared state.
6. Switch Presentation / Analysis mode without losing camera or selection.

Non-goals for this contract phase:

1. No WebGL spike implementation.
2. No production Galaxy replacement.
3. No feature flag creation.
4. No new ingestion or writeback.
5. No raw/private/session/cookie/secret data access.

## Data Boundary

The visual layer may use only:

1. Redacted derived memory records.
2. `Universe State Snapshot`.
3. Existing visualization snapshot data.
4. Aggregated scores, counts, labels and relationship summaries.

It must not use raw transcript text, hidden session files, tokens, cookies, browser state, plaintext secrets or private full-message exports.

## Acceptance Criteria

Phase 0.2.2 is accepted when this document:

1. Defines the starfield as deep-space nebula plus Flow Field plus gravitational disk.
2. Includes Black Hole, Proto-Star and Memory Terrain.
3. Explicitly forbids regression to ordinary point-line graph, static scatter, or random small light dots.
4. Defines Presentation Mode and Analysis Mode.
5. Defines visual-to-data mappings and interaction boundaries.
6. States privacy and non-implementation limits.

## Rollback

Delete this document or revert it before spike work begins. No production code rollback is required because this contract phase does not change runtime behavior.
