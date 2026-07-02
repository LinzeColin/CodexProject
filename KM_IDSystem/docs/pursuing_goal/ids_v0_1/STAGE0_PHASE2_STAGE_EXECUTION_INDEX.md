# IDS v0.1 Stage 0 Phase 2 Stage Execution Index

## Run Contract

- Stage: `STAGE-0`
- Phase: `STAGE0-P2`
- Status: `completed_local_evidence`
- Acceptance: `STAGE-001..168` can be selected from a durable local index without reading unrelated projects, and `STAGE-001` has a bridge contract for the next run.
- Non-goals: no implementation of `STAGE-001`, no runtime code changes, no dependency install, no `IDS_DATA_ROOT`, no generated data/report outputs.

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `V0_1_STAGE_EXECUTION_INDEX.csv` | Local CSV mirror of the P0 taskpack machine index. |
| `V0_1_STAGE_EXECUTION_INDEX.json` | JSON execution index with provenance, domain summary, rules, and all 168 Stage records. |
| `STAGE001_ENTRY_CONTRACT.md` | Minimal bridge for entering `STAGE-001 / ACC-STAGE-001` in the next run. |

## Provenance

- P0 taskpack: `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip`
- P0 taskpack SHA-256: `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- Source machine index: `IDS_v0_1_Final_Chinese_Revised/machine_readable/v0_1_stage_index.csv`
- Source machine index SHA-256: `f767fa0ccf751b96d18d91602f8d8118637eff545d879d05800d9b5e44784b03`
- Local CSV SHA-256: `2e0088153cd1e13a09d9aebd09a1bd0c8c7162acd0788360d45f5c7320af1e9a`
- Local JSON SHA-256: `d9e2f12ea3148be984c029f12e0f6ddff187486fad4dc54c72f56c5168619678`
- STAGE-001 taskpack file SHA-256: `db3f6828b413d9f537a006058603ac8d1f306470ca8a51395c5815c20d36ebf4`

## Index Checks

- Stage count: `168`
- Stage range: `STAGE-001..STAGE-168`
- Missing stage numbers: none
- Parallel counts: `是=100`, `否=68`
- First stage: `STAGE-001 / ACC-STAGE-001 / IDS 产品命名合同`
- Final v0.1 stage: `STAGE-168 / ACC-STAGE-168 / v0.1 最终验收门禁`

## Domain Summary

| Domain | Stages | Count | Name |
|---|---:|---:|---|
| D01 | STAGE-001..STAGE-005 | 5 | 一次性仓库治理与产品命名 |
| D02 | STAGE-006..STAGE-011 | 6 | 本地运行环境与存储根目录 |
| D03 | STAGE-012..STAGE-017 | 6 | 原始资料保护与文件身份 |
| D04 | STAGE-018..STAGE-023 | 6 | 导入预检与数据优先级 |
| D05 | STAGE-024..STAGE-029 | 6 | 自动解压与压缩包安全 |
| D06 | STAGE-030..STAGE-036 | 7 | PostgreSQL 控制面 |
| D07 | STAGE-037..STAGE-044 | 8 | 任务编排与机器控制 |
| D08 | STAGE-045..STAGE-050 | 6 | 解析器路由 |
| D09 | STAGE-051..STAGE-056 | 6 | OCR 管线 |
| D10 | STAGE-057..STAGE-062 | 6 | 结构化数据与表格事实库 |
| D11 | STAGE-063..STAGE-068 | 6 | Chunking 与语义资产 |
| D12 | STAGE-069..STAGE-075 | 7 | Embedding 与外部 API 策略 |
| D13 | STAGE-076..STAGE-082 | 7 | 索引版本与检索不中断 |
| D14 | STAGE-083..STAGE-088 | 6 | 混合检索 |
| D15 | STAGE-089..STAGE-096 | 8 | 证据账本与可信等级 |
| D16 | STAGE-097..STAGE-104 | 8 | RAG 回答层与安全 |
| D17 | STAGE-105..STAGE-112 | 8 | 报告交付 |
| D18 | STAGE-113..STAGE-118 | 6 | 人工复核队列 |
| D19 | STAGE-119..STAGE-123 | 5 | 数据质量门禁 |
| D20 | STAGE-124..STAGE-126 | 3 | 血缘与溯源 |
| D21 | STAGE-127..STAGE-135 | 9 | 人类产品入口 UI/UX |
| D22 | STAGE-136..STAGE-142 | 7 | IDS 系统运营入口 |
| D23 | STAGE-143..STAGE-147 | 5 | 备份恢复 |
| D24 | STAGE-148..STAGE-151 | 4 | 安全与审计 |
| D25 | STAGE-152..STAGE-161 | 10 | 测试、压测与发布验证 |
| D26 | STAGE-162..STAGE-168 | 7 | Codex 执行治理与 v0.1 验收 |

## Next Run Bridge

The next implementation run should start at `STAGE-001 / ACC-STAGE-001`, but still follow the one-phase rule. The expected first STAGE-001 run is Phase 1: scope, inputs/outputs, affected files, and legacy-name boundary confirmation.

## Stop Gates Carried Forward

- Do not execute `STAGE-001` during Stage 0.
- Do not use full/v2 files as higher priority than the three P0 v0.1-only files.
- Do not expand sparse checkout just to satisfy unrelated governance validation.
- Do not touch real raw data, secrets, `00_ORIGINAL_RAW_DATA`, runtime data, reports, or dependency folders.
