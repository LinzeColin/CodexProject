# Memory Atlas v1.1.7 Stage 6 Phase 6.1 Data Map Structure Acceptance

Task ID: `MA-V117-S6P01`.

Acceptance ID: `ACC-MA-V117-S6P01`.

Status: `phase_6_1_data_map_structure_model_completed_pending_stage6_review`.

Contract version: `data_map_structure_model.v1_1_7_stage6_phase1`.

Relation version: `data_map_relation_explanation.v1_1_7_stage6_phase1`.

## Acceptance Criteria

1. `source_layer` / 来源层 exists and declares node types, fields, interaction, and detail entry.
2. `profile_layer` / 画像层 exists and declares node types, fields, interaction, and detail entry.
3. `project_decision_layer` / 项目决策层 exists and declares node types, fields, interaction, and detail entry.
4. `action_opportunity_layer` / 行动机会层 exists and declares node types, fields, interaction, and detail entry.
5. Clicking edge / relation in the production Data Guide shows source, strength, evidence, and time.
6. Relation explanation panel is default collapsed before selection and uses available explanation when evidence is partial.
7. Runtime exposes `window.__memoryAtlasStage6Phase1()` with `proposalWrite=false`, `directActiveMemoryWriteback=false`, and `rawPrivateDataIncluded=false`.

## Required Validation

- `validate:v1.1.7-stage6-phase1`
- `validate:data-map-structure-browser`
- `ACC-MA-V117-S6P01`

The browser validator must cover four layers, relation click explanation, debug signal, screenshot, and console safety.

## Stop Conditions

- Stop after Phase 6.1.
- No Phase 6.2.
- No proposal editing.
- No direct active-memory writeback.
- No raw/private/cookie/session/secret data access.
- No deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Phase 6.1; Structure Model; Relation Explanation; MA-V117-S6P01; ACC-MA-V117-S6P01; phase_6_1_data_map_structure_model_completed_pending_stage6_review; validate:v1.1.7-stage6-phase1; validate:data-map-structure-browser; data_map_structure_model.v1_1_7_stage6_phase1; data_map_relation_explanation.v1_1_7_stage6_phase1; source_layer; 来源层; profile_layer; 画像层; project_decision_layer; 项目决策层; action_opportunity_layer; 行动机会层; clicking edge; source; strength; evidence; time; default collapsed; No Phase 6.2; No GitHub main upload.
