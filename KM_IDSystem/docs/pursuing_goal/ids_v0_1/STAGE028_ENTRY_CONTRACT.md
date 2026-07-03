# IDS v0.1 STAGE-028 Entry Contract

## Identity
- Stage: `STAGE-028 · 压缩包对抗测试`
- Task: `IDS-V0_1-STAGE028-P1`
- Acceptance: `ACC-STAGE-028`
- Local code: `D05-S005`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-028_压缩包对抗测试.md`
- Taskpack SHA-256: `a3fb4b9bcfe0772fe3860ddfa01f342fc42d05380802d555f21e7c73e6d60d6e`

## Pursuing Goal
用路径穿越、压缩炸弹、嵌套包、乱码文件名和超大文件数量样本验证防护。

STAGE-028 does not replace the earlier archive boundaries. It binds:
- `STAGE-024` archive threat model.
- `STAGE-025` safe extraction engine.
- `STAGE-026` archive manifest.
- `STAGE-027` extracted-file re-ingest.

## Phase 1 Scope
Phase 1 defines the archive adversarial testing boundary only. It records:
- 压缩包安全边界.
- 解压 staging 区.
- 文件数量限制.
- 体积限制.
- 嵌套限制.
- 自动解压不覆盖原始压缩包.
- 自动解压不写出指定 staging 区.
- `archive_manifest` and safe extraction evidence requirements.
- 解压后重新进入 `hash`、`manifest`、`dedup`、`parser` 的规则.
- 自动清理必须使用 cleanup allowlist and must not delete original archives, fact sources, evidence ledgers, audit logs, or delivered reports.

## Required Adversarial Scenario Families
- `path_traversal`: 路径穿越.
- `absolute_path`: 绝对路径.
- `archive_bomb`: 压缩炸弹.
- `nested_archive`: 嵌套包.
- `garbled_filename`: 乱码文件名.
- `too_many_files`: 超大文件数量.

## Non-Goals
- 不执行压缩包对抗测试 runner.
- 不实现安全解压、路径过滤、风险标记、隔离或 cleanup allowlist runtime behavior.
- 不读取真实压缩包内容.
- 不自动解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不移动、删除、覆盖原始文件.
- 不写 archive_adversarial runtime output.
- 不写 archive_manifest runtime output.
- 不创建 staging runtime directory.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- 不进入 Phase 2.

## Raw Data Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得提交真实原始资料、secrets、API key、数据库密码或云端凭证.
- 不得移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.

## Stop Gate
- Current gate: `IDS-STAGE028-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement adversarial sample generation, extraction, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, archive_manifest writes, or post-extract pipeline execution.
