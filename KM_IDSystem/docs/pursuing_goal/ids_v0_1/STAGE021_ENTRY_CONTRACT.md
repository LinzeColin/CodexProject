# IDS v0.1 STAGE-021 Entry Contract

## Taskpack Identity
- Stage: `STAGE-021 · 预检确认 UI`
- Task: `IDS-V0_1-STAGE021-P1`
- Acceptance: `ACC-STAGE-021`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Pursuing goal: `在人类产品入口显示预检结果，让 owner 决定继续、暂停、分批或排除。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-021_预检确认UI.md`
- P0 stage file SHA-256:
  `2428711c7a935317de9bed7d50bbd02b7954ec7cdc5e1bfb832149a0c30103e8`

## Preconditions
- `STAGE-011..020` are uploaded to GitHub main and app entries have been reinstalled.
- `STAGE-021` starts the next ten-stage batch lock: `BATCH021_030_UPLOAD_LOCK.yaml`.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE021-P1` defines the preflight confirmation UI boundary for later implementation. It records the input snapshots, owner-facing output summary, risk items, cost items, confirmation states, and no-processing rules required before the UI can let an owner continue, pause, split a batch, or exclude items.

Phase 1 is a contract-only phase:
- It defines accepted metadata-only inputs and owner-visible outputs for the human product entrance and IDS operations entrance.
- It binds risk and cost summaries from prior preflight/risk/cost estimator stages without re-reading raw source content.
- It confirms owner confirmation is mandatory: owner 确认后才进入批量处理.
- It preserves the raw data boundary: 只读取元信息, 不解析正文, 不修改原始文件.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement the UI component, route, backend endpoint, state reducer, persistence, screenshot, or runnable preflight confirmation workflow.
- Do not start OCR, Embedding, index building, import, report generation, external API calls, service start, dependency install, GitHub upload, PR, merge, or app reinstall.
- Do not create runtime data, reports, outputs, manifests, evidence ledgers, audit logs, document/chunk/job/index/import rows, screenshots, PDFs, JSON output files, or production preflight reports.
- Do not use fake IDS business data, fake database rows, fake source documents, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage021_preflight_confirmation_ui.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
