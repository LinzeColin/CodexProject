# EVA_OS S4PBT02 中文结构验收报告

- 任务：`S4PBT02`
- 验收：`ACC-S4PBT02`
- 结论：中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。

## 用户可读结论

EVA_OS 的 S4PBT02 只清理主动项目表面的历史交接文档、`handoff_packs/`、`cleanup/` 和生成版功能 PDF。源码、共享模块、系统目录、测试、运行数据路径和私密 owner 复核数据没有移动。Owner 判断当前入口时，应从 `EVA_OS/README.md`、`EVA_OS/docs/Index.md`、三个中文入口和 `docs/governance/` 读取事实。

## 中文验收标准

- 第一屏必须说明改了什么、没改什么、风险在哪里。
- 中文说明必须覆盖 active source、archive、private data、rollback。
- 技术路径保留英文原样，但不能让英文段落成为唯一可读解释。

## 停止条件与结果

- EVA system/shared module import 路径被改变：`false`
- runtime 或 live-trading 行为被改变：`false`
- PRIVATE data 被移动或归档：`false`
- 根 README 无分层地膨胀：`false`

## 回滚

优先用 git revert 回退 S4PBT02 任务提交。若必须手工恢复，从 `governance/archive/other8_wave1_pending/EVA_OS/` 按 OLD_TO_NEW_MAP 还原，并复核 S4PAT02 checksum 与 S4PBT02 run manifest。

## 下一步

后续 Agent 只能把 archive 视为历史资料，不得把归档文件重新作为默认运行或 import 入口。

---

## 原技术记录

# EVA_OS S4PBT02 Structure Report

Task: `S4PBT02`
Acceptance: `ACC-S4PBT02`
Date: 2026-06-25

## Scope

This report records the independent EVA_OS structure simplification for S4PB.
It moves historical root handoff documents, `handoff_packs/`, `cleanup/`, and
the generated feature PDF out of the active EVA_OS project surface while keeping
source code, shared modules, tests, runtime data paths, and PRIVATE owner-review
data unchanged.

## Architecture Navigation

Active owner and agent navigation now uses:

| Purpose | Active path |
|---|---|
| Owner overview | `EVA_OS/README.md` |
| Documentation index | `EVA_OS/docs/Index.md` |
| Architecture overview | `EVA_OS/docs/EVA_OS.md` |
| Lean v2 project truth | `EVA_OS/docs/governance/project.yaml` |
| Roadmap truth | `EVA_OS/docs/governance/roadmap.yaml` |
| Event truth | `EVA_OS/docs/governance/events.jsonl` |
| Structure migration evidence | `EVA_OS/docs/EVA_structure_report.md` |

Historical references remain readable in
`governance/archive/other8_wave1_pending/EVA_OS/`, but they are not active
runtime or import entry points.

## OLD_TO_NEW_MAP

| Old path | New path | Status |
|---|---|---|
| `EVA_OS/15_OPEN_QUESTIONS.md` | `governance/archive/other8_wave1_pending/EVA_OS/15_OPEN_QUESTIONS.md` | archived |
| `EVA_OS/AGENT_CONTINUITY.md` | `governance/archive/other8_wave1_pending/EVA_OS/AGENT_CONTINUITY.md` | archived |
| `EVA_OS/CODEX_PROMPTS.md` | `governance/archive/other8_wave1_pending/EVA_OS/CODEX_PROMPTS.md` | archived |
| `EVA_OS/CODEX_TASK_PACK.md` | `governance/archive/other8_wave1_pending/EVA_OS/CODEX_TASK_PACK.md` | archived |
| `EVA_OS/HANDOFF.md` | `governance/archive/other8_wave1_pending/EVA_OS/HANDOFF.md` | archived |
| `EVA_OS/PLANS.md` | `governance/archive/other8_wave1_pending/EVA_OS/PLANS.md` | archived |
| `EVA_OS/UPLOAD_MANIFEST.md` | `governance/archive/other8_wave1_pending/EVA_OS/UPLOAD_MANIFEST.md` | archived |
| `EVA_OS/cleanup/**` | `governance/archive/other8_wave1_pending/EVA_OS/cleanup/**` | archived |
| `EVA_OS/handoff_packs/**` | `governance/archive/other8_wave1_pending/EVA_OS/handoff_packs/**` | archived |
| `EVA_OS/docs/FeatureSpecification.pdf` | `governance/archive/other8_wave1_pending/EVA_OS/docs/FeatureSpecification.pdf` | archived generated PDF |

The exact 40 moved paths are bound in
`governance/run_manifests/GOV-OTHER8-S4PBT02-EVA-STRUCTURE-SIMPLIFICATION-20260625.json`
and trace back to `governance/stage_gates/s4pa/wave1_archive_manifest.json`.

## Preserved Paths

- `EVA_OS/src/**`, `EVA_OS/shared/**`, `EVA_OS/systems/**`, and `EVA_OS/tests/**`
  are unchanged.
- `EVA_OS/data/**` PRIVATE owner-review candidates remain in place.
- `EVA_OS/assets/**` and `EVA_OS/macos/**` generated app assets remain in place;
  they are outside S4PBT02.
- `EVA_OS/docs/FeatureSpecification.md` remains active; only the generated PDF
  copy moved to archive.

## Stop Conditions Preserved

- EVA system/shared module import path changed: no.
- Runtime or live-trading behavior changed: no.
- PRIVATE data moved or archived: no.
- Root README expanded without layering: no.

## Rollback

Rollback is a git revert of the S4PBT02 task commit. Manual rollback restores
each archived path from `governance/archive/other8_wave1_pending/EVA_OS/` to the
old `EVA_OS/` path according to `OLD_TO_NEW_MAP`, then verifies the S4PAT02
checksums and the S4PBT02 run manifest.
