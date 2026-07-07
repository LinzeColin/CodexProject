# Memory Atlas v1.1.7 Stage 6 Phase 6.2 Data Map Detail Proposal Acceptance

Task ID: `MA-V117-S6P02`.

Acceptance ID: `ACC-MA-V117-S6P02`.

Status: `phase_6_2_data_map_detail_proposal_completed_pending_stage6_review`.

Static validator: `validate:v1.1.7-stage6-phase2`.

Browser validator: `validate:data-map-detail-proposal-browser`.

Detail panel version: `data_map_detail_panel.v1_1_7_stage6_phase2`.

Proposal entry version: `data_map_proposal_entry.v1_1_7_stage6_phase2`.

## Acceptance

The production Data Guide exposes a `数据导图详情面板` after clicking a node. The panel must show:

- `资产`
- `主题`
- `建议动作`
- `重要性`
- `优先级`

The production Data Guide exposes a `数据导图 proposal 入口` that uses the existing ProposalEditor flow. The entry must:

- 只生成 proposal.
- 导出 proposal JSON.
- Mark the payload source as `data_guide_detail_panel`.
- Keep `proposal-only`.
- Keep `No direct active-memory writeback`.

## Browser Proof

`validate:data-map-detail-proposal-browser` clicks a Data Guide memory node, reads the detail fields, changes importance / priority proposal inputs, exports a proposal JSON file, checks `window.__memoryAtlasStage6Phase2()`, records screenshot evidence and fails on unsafe console errors.

## Boundaries

- No direct active-memory writeback.
- No Stage 6 review.
- No GitHub main upload before whole Stage 0-10 completion.
- No raw/private/cookie/session/secret data access.
- No agent apply.
- No deploy.

Machine-readable boundary summary: Phase 6.2; Details & Editing; MA-V117-S6P02; ACC-MA-V117-S6P02; phase_6_2_data_map_detail_proposal_completed_pending_stage6_review; validate:v1.1.7-stage6-phase2; validate:data-map-detail-proposal-browser; data_map_detail_panel.v1_1_7_stage6_phase2; data_map_proposal_entry.v1_1_7_stage6_phase2; 数据导图详情面板; 数据导图 proposal 入口; 资产; 主题; 建议动作; 重要性; 优先级; 只生成 proposal; 导出 proposal; proposal-only; No direct active-memory writeback; No Stage 6 review; No GitHub main upload.
