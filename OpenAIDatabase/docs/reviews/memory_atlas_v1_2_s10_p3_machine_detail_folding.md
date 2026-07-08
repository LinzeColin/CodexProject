# Memory Atlas v1.2 S10 P3 Machine Detail Folding Review

状态：`phase_s10_p3_machine_detail_folding_completed_pending_s10_review`。

任务 ID：`MA-V12-S10P3`。

验收 ID：`ACC-MA-V12-S10P3`。

Validator：`validate:v1.2-s10-p3`。

## Scope

S10 P3 完成机器字段默认折叠和高级详情入口的最小高置信切口。默认首页、搜索、
复盘、总结闭环和 Inspector 先显示中文人类可读解释；`query`、`matched_reason`、
`evidence_refs`、`proposal_candidate`、schema version、proposal id、Agent 字段和
no-apply 布尔边界进入“高级详情”折叠层。

Runtime contract 为 `machine_detail_folding.v1_2_s10_p3`。本 phase 不修改 raw，
不执行 proposal apply，不上传 GitHub main，不进入 S10 Review。

## Acceptance

- App shell 暴露 `data-s10-p3-machine-detail-folding`。
- `window.__memoryAtlasS10Phase3()` 返回 `machineFieldsDefaultCollapsed=true`、
  `advancedDetailsEntryVisible=true` 和 `defaultHumanReadableFirst=true`。
- 首页 arrival briefing、搜索会话、搜索结果、复盘会话、总结闭环和 Inspector 的机器
  字段默认折叠。
- 默认可见层不再直接展示 `search_session_summary`、`Review session output`、
  `change_comparison`、`stale_conflict_signals`、`proposal_candidates`、
  `jump_to_starfield`、`open_inspector` 等机器字段标签。
- `scripts/atlasctl.py audit --check chinese-ux` 返回 `MA-V12-S10P3` /
  `ACC-MA-V12-S10P3`，并确认 S10 P1、S10 P2 和 S10 P3 合同仍同时成立。

## Evidence

- `OpenAIDatabase/apps/memory-atlas/src/App.tsx`
- `OpenAIDatabase/apps/memory-atlas/src/i18n/zh-CN.ts`
- `OpenAIDatabase/apps/memory-atlas/src/styles.css`
- `OpenAIDatabase/scripts/atlasctl.py`
- `OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs`
- `OpenAIDatabase/人类可读/26_机器字段高级详情说明.md`

## Boundaries

- No GitHub main upload in this phase。
- No remote push in this phase。
- No raw mutation。
- No proposal apply execution。
- No S10 Review work。
- No S11 work。
- No app reinstall。

## Next

下一步为 pending S10 Review：复审 S10 P1 首页 arrival briefing、S10 P2 全局中文和
S10 P3 机器字段默认折叠是否共同满足 S10 stage gate。

Machine-readable boundary summary: Memory Atlas v1.2 S10 P3; MA-V12-S10P3; ACC-MA-V12-S10P3; phase_s10_p3_machine_detail_folding_completed_pending_s10_review; validate:v1.2-s10-p3; machine_detail_folding.v1_2_s10_p3; 机器字段默认折叠; 高级详情入口; pending S10 Review; No GitHub main upload in this phase; No raw mutation; No proposal apply execution.
