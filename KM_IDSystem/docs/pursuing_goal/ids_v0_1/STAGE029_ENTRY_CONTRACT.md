# IDS v0.1 STAGE-029 Entry Contract

## Identity
- Stage: `STAGE-029 · 压缩包清理白名单`
- Task: `IDS-V0_1-STAGE029-P1`
- Acceptance: `ACC-STAGE-029`
- Local code: `D05-S006`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-029_压缩包清理白名单.md`
- Taskpack SHA-256: `b17be7330d9a4ce1f5a9ead4c0620d733693ccd10d6eeff7c8a1298c11889ac2`

## Pursuing Goal
只清理允许清理的解压临时文件，禁止清理原始资料、manifest、evidence、audit 和报告。

STAGE-029 does not replace earlier archive contracts. It binds:

- `STAGE-024` archive threat model.
- `STAGE-025` safe extraction engine.
- `STAGE-026` archive manifest.
- `STAGE-027` extracted-file re-ingest.
- `STAGE-028` archive adversarial testing.

## Phase 1 Scope
Phase 1 defines the archive cleanup allowlist boundary only. It records:

- 压缩包安全边界.
- 解压 staging 区.
- 文件数量限制.
- 体积限制.
- 嵌套限制.
- 自动解压不覆盖原始压缩包.
- 自动解压不写出指定 staging 区.
- `archive_manifest` and safe extraction evidence requirements.
- 解压后重新进入 `hash`、`manifest`、`dedup`、`parser` 的规则.
- Cleanup allowlist 只能包含 explicit staging temp files.
- Cleanup allowlist must not include original archives, original materials,
  archive_manifest, evidence ledger, audit log, delivered reports, database,
  index, parser output, or raw metadata.

## Protected Materials
- `PROTECTED_ORIGINAL_ARCHIVE`: 原始压缩包.
- `PROTECTED_ORIGINAL_MATERIAL`: 原始资料.
- `PROTECTED_ARCHIVE_MANIFEST`: manifest and archive_manifest evidence.
- `PROTECTED_EVIDENCE_LEDGER`: evidence ledger and evidence products.
- `PROTECTED_AUDIT_LOG`: audit log.
- `PROTECTED_DELIVERED_REPORT`: delivered reports, PDFs, and report evidence.
- `PROTECTED_RAW_METADATA_ROOT`: `/Users/linzezhang/Downloads/IDS_MetaData`.

## Non-Goals
- 不执行 cleanup runner.
- 不自动清理.
- 不删除原始资料.
- 不删除原始压缩包.
- 不删除 manifest.
- 不删除 evidence.
- 不删除 audit.
- 不删除报告.
- 不读取真实压缩包内容.
- 不自动解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不移动、删除、覆盖原始文件.
- 不写 archive_cleanup runtime output.
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
- Current gate: `IDS-STAGE029-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement cleanup runner, safe extraction,
  path filtering, risk marking, quarantine, cleanup runtime behavior,
  archive_manifest writes, deletion, or post-extract pipeline execution.
