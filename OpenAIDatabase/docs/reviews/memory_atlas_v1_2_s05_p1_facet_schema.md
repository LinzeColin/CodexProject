# Memory Atlas v1.2 S05 P1 Facet Schema Review

## Identity

- Task ID: `MA-V12-S05P1`
- Acceptance ID: `ACC-MA-V12-S05P1`
- Status: `phase_s05_p1_facet_schema_completed_pending_s05_p2`
- Validator: `validate:v1.2-s05-p1`

## Result

S05 P1 defines the canonical facet schema for later behavior-intelligence events:

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`
- `人类可读/12_Facet字段与事件语义说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs`

The schema covers `source`, `topic`, `intent`, `task_type`, `project`,
`output_type`, `language`, `tool`, `turn_count`, `friction`, `value_signal`
and `future_agent_source`.

## Acceptance

- Field names are English.
- Human-facing explanations are in Chinese.
- Source coverage includes ChatGPT, Codex and future agent.
- S05 P1 does not implement an extractor.
- S05 P1 does not generate `data/derived/behavior_intelligence/events.json`.
- S05 P1 does not modify raw data or first-screen UI.

## Boundary

- No GitHub main upload in this phase.
- No remote push in this phase.
- No app reinstall in this phase.
- No extractor in this phase.
- No fake events in this phase.
- No raw mutation in this phase.

## Next Gate

The next allowed phase is S05 P2 extractor.

Machine-readable boundary summary: Memory Atlas v1.2 S05 P1 Facet Schema; MA-V12-S05P1; ACC-MA-V12-S05P1; phase_s05_p1_facet_schema_completed_pending_s05_p2; validate:v1.2-s05-p1; facet_event_schema.v1_2_s05_p1.json; 12_Facet字段与事件语义说明.md; memory_atlas_v1_2_s05_p1_facet_schema.md; S05 P1; pending S05 P2; No GitHub main upload in this phase; No remote push in this phase; No extractor in this phase; No fake events in this phase; No raw mutation in this phase.
