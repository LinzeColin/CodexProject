# IDS v0.1 STAGE-025 Entry Contract

## Identity
- Stage: `STAGE-025 · 安全解压引擎`
- Task: `IDS-V0_1-STAGE025-P1`
- Acceptance: `ACC-STAGE-025`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-025_安全解压引擎.md`
- Taskpack SHA-256: `ab244ea554dc30616115d6db8baaef53d339b21d53a6d5c51013660ea30e6807`

## Pursuing Goal
自动解压到 staging 区，阻止路径穿越、绝对路径、覆盖原文件和误执行。

## Phase 1 Scope
Phase 1 defines the safe extraction engine boundary only. It records:
- 压缩包安全边界.
- 解压 `staging` 区.
- 文件数量限制.
- 体积限制.
- 嵌套限制.
- 自动解压不覆盖原始压缩包.
- 自动解压不写出指定 staging 区.
- 防止路径穿越、绝对路径、覆盖原文件和误执行.
- `archive_manifest` 合同.
- 解压后重新进入 `hash`、`manifest`、`dedup`、`parser` 的规则.

## Relationship To STAGE-024
STAGE-024 defined and validated the archive threat model. STAGE-025 turns that
threat model into the future safe extraction engine contract, but this Phase 1
does not implement or run the engine.

## Non-Goals
- 不执行解压引擎.
- 不实现安全解压、路径过滤、风险标记、隔离、cleanup allowlist runtime 行为或 post-extract pipeline execution.
- 不读取真实压缩包内容.
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
- Current gate: `IDS-STAGE025-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement extraction, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, or post-extract pipeline execution.
