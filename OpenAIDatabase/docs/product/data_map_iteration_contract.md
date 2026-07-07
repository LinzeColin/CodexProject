# Memory Atlas v1.1.7 Stage 6 Phase 6.1 Data Map Structure Model Contract

Task ID: `MA-V117-S6P01`.

Acceptance ID: `ACC-MA-V117-S6P01`.

Status: `phase_6_1_data_map_structure_model_completed_pending_stage6_review`.

Structure model version: `data_map_structure_model.v1_1_7_stage6_phase1`.

Relation explanation version: `data_map_relation_explanation.v1_1_7_stage6_phase1`.

## Scope

Stage 6 Phase 6.1 implements 四层结构重定义 and Relation Explanation for the production Data Guide. It does not enter Phase 6.2 details, editing, proposal editing, raw/private data access, direct active-memory writeback, deploy, or GitHub main upload.

## Four Layers

| layer id | label | node types | fields | interaction | detail entry |
|---|---|---|---|---|---|
| `source_layer` | 来源层 | `theme`, `tier`, `category` | `data_source`, `source_label`, `category`, `date` | `select_source_or_topic_node` | `open_source_or_topic_detail` |
| `profile_layer` | 画像层 | `memory:preference`, `memory:answering_rule`, `memory:security_boundary` | `memory_tier`, `category`, `importance`, `confidence` | `select_profile_node` | `open_profile_detail` |
| `project_decision_layer` | 项目决策层 | `project`, `decision`, `memory:project_context`, `memory:workflow` | `project`, `decision`, `validity`, `importance` | `select_project_decision_node` | `open_project_decision_detail` |
| `action_opportunity_layer` | 行动机会层 | `memory:temporary`, `memory:recommended_action`, `memory:roi_opportunity` | `recommended_action`, `leverage_score`, `staleness_status`, `date` | `select_action_opportunity_node` | `open_action_opportunity_detail` |

Every layer has node types, fields, interaction, and detail entry. Runtime frames are default collapsed so the map stays readable when graph density rises.

## Relation Explanation

Each visible cross-layer relation must be clickable. Clicking edge / relation shows:

- source: frame, source label or data source, and edge kind.
- strength: derived from edge weight as `高`, `中`, or `低`.
- evidence: edge id, edge kind, edge weight, and the two node ids.
- time: latest public `date` field from the two nodes, or `time unavailable`.

The UI labels the panel as `关系解释` and explains why nodes connect. If evidence fields are insufficient, the fallback still shows available explanation and keeps the relation panel default collapsed until a relation is selected.

## Runtime Hooks

- Production Data Guide root exposes `data-data-map-structure-model="data_map_structure_model.v1_1_7_stage6_phase1"`.
- Relation hitboxes expose `data-data-map-relation-explanation="data_map_relation_explanation.v1_1_7_stage6_phase1"`.
- Layer frames expose `source_layer`, `profile_layer`, `project_decision_layer`, `action_opportunity_layer`.
- Browser debug hook: `window.__memoryAtlasStage6Phase1()`.

## Validation

- Static validator: `validate:v1.1.7-stage6-phase1`.
- Browser validator: `validate:data-map-structure-browser`.
- Required browser proof: four layers rendered, clicking edge opens relation explanation with source / strength / evidence / time, debug signal reports safe flags, screenshot and console safety pass.

## Boundaries

- No Phase 6.2.
- No proposal editing.
- No direct active-memory writeback.
- No raw/private/cookie/session/secret data access.
- No agent apply.
- No deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Phase 6.1; Structure Model; Relation Explanation; MA-V117-S6P01; ACC-MA-V117-S6P01; phase_6_1_data_map_structure_model_completed_pending_stage6_review; validate:v1.1.7-stage6-phase1; validate:data-map-structure-browser; data_map_structure_model.v1_1_7_stage6_phase1; data_map_relation_explanation.v1_1_7_stage6_phase1; source_layer; profile_layer; project_decision_layer; action_opportunity_layer; default collapsed; No Phase 6.2; No proposal editing; No direct active-memory writeback; No GitHub main upload.
