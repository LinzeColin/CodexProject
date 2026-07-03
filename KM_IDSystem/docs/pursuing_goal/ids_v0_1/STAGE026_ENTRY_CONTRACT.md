# IDS v0.1 STAGE-026 Entry Contract

## Identity
- Stage: `STAGE-026 · 压缩包 Manifest`
- Task: `IDS-V0_1-STAGE026-P1`
- Acceptance: `ACC-STAGE-026`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-026_压缩包Manifest.md`
- Taskpack SHA-256: `71f966c9a669563073a502e3beef5bc85a50d9cdb077b996687653ca48c3da70`

## Pursuing Goal
记录压缩包 hash、解压文件列表、解压体积、嵌套层级、失败项和风险项。

## Phase 1 Scope
Phase 1 defines the archive manifest boundary only. It records:
- 压缩包 Manifest 的稳定身份、schema 与字段边界.
- 压缩包 hash 观察的未来字段，不读取真实压缩包内容.
- 解压文件列表的未来字段，不枚举真实压缩包条目.
- 解压体积、单文件体积、文件数量和嵌套层级限制.
- 失败项和风险项的人工复核状态.
- 解压 staging 区的路径合同.
- 自动解压不覆盖原始压缩包.
- 自动解压不写出指定 staging 区.
- 解压后重新进入 `hash`、`manifest`、`dedup`、`parser` 的规则.

## Relationship To STAGE-024 And STAGE-025
STAGE-024 defined archive threat-model rules, and STAGE-025 wrapped those
rules in a safe extraction engine. STAGE-026 defines the archive_manifest
contract that future safe extraction results must use before any extracted
file can re-enter the import pipeline.

## Non-Goals
- 不执行解压.
- 不实现安全解压、路径过滤、风险标记、隔离、cleanup allowlist runtime 行为或 post-extract pipeline execution.
- 不读取真实压缩包内容.
- 不枚举真实压缩包条目.
- 不计算真实压缩包 hash.
- 不生成 `archive_manifest` runtime output.
- 不创建 staging runtime directory.
- 不写出解压产物.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- 不进入 Phase 2.

## Raw Data Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得提交真实原始资料、secrets、API key、数据库密码或云端凭证.
- 不得移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.

## Stop Gate
- Current gate: `IDS-STAGE026-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement extraction, archive_manifest runtime output, manifest persistence, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, or post-extract pipeline execution.
