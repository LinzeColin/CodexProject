# IDS v0.1 STAGE-024 Entry Contract

## Identity
- Stage: `STAGE-024 · 压缩包威胁模型`
- Task: `IDS-V0_1-STAGE024-P1`
- Acceptance: `ACC-STAGE-024`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-024_压缩包威胁模型.md`
- Taskpack SHA-256: `add98ee0f7852ed4cd1b1aa9ef1266094ab6cbc26d88696c14f2553e1ef60745`

## Pursuing Goal
定义 ZIP/RAR/7Z/TAR 等压缩包的安全边界和风险模型。

Supported archive families for this contract:
- `ZIP`
- `RAR`
- `7Z`
- `TAR`

## Phase 1 Scope
Phase 1 defines the archive safety contract only. It records:
- 压缩包安全边界.
- 解压 staging 区.
- 文件数量限制.
- 体积限制.
- 嵌套限制.
- 自动解压不覆盖原始压缩包.
- 自动解压不写出指定 staging 区.
- `archive_manifest` 合同.
- 解压后重新进入 `hash`、`manifest`、`dedup`、`parser` 的规则.

## Non-Goals
- 不实现安全解压引擎.
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
- Current gate: `IDS-STAGE024-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement extraction, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, or post-extract pipeline execution.
