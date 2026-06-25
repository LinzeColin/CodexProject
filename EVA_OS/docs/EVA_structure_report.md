# EVA_OS S4PBT02 中文结构验收报告

- 任务：`S4PBT02`
- 验收：`ACC-S4PBT02`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

EVA_OS 的 S4PBT02 只清理主动项目表面的历史交接文档、`handoff_packs/`、`cleanup/` 和生成版功能 PDF。源码、共享模块、系统目录、测试、运行数据路径和私密 owner 复核数据没有移动。Owner 判断当前入口时，应从 `EVA_OS/README.md`、`EVA_OS/docs/Index.md`、三个中文入口和 `docs/governance/` 读取事实。

## 中文验收标准

- 第一屏必须说明改了什么、没改什么、风险在哪里。
- 中文说明必须覆盖 active source、archive、private data、rollback。
- 技术路径保留英文原样，但不能让英文段落成为唯一可读解释。

## 停止条件与结果

- EVA system/shared module import 路径被改变：`未触发`
- runtime 或 live-trading 行为被改变：`未触发`
- PRIVATE data 被移动或归档：`未触发`
- 根 README 无分层地膨胀：`未触发`

## 回滚

优先用 git revert 回退 S4PBT02 任务提交。若必须手工恢复，从 `governance/archive/other8_wave1_pending/EVA_OS/` 按 OLD_TO_NEW_MAP 还原，并复核 S4PAT02 checksum 与 S4PBT02 run manifest。

## 下一步

后续 Agent 只能把 archive 视为历史资料，不得把归档文件重新作为默认运行或 import 入口。

---

## 原技术记录

# EVA_OS S4PBT02 结构报告

任务：`S4PBT02`
验收：`ACC-S4PBT02`
日期：2026-06-25

## 范围

本报告记录 EVA_OS 在 S4PB 中的独立结构瘦身：历史根目录交接文档、`handoff_packs/`、`cleanup/` 和生成版功能 PDF 从主动项目表面移出；源码、共享模块、测试、运行数据路径和 PRIVATE owner 复核数据保持不变。

## 架构导航

当前 owner 与 Agent 的主动导航使用以下路径：

| 用途 | 主动路径 |
|---|---|
| Owner 总览 | `EVA_OS/README.md` |
| 文档索引 | `EVA_OS/docs/Index.md` |
| 架构总览 | `EVA_OS/docs/EVA_OS.md` |
| Lean v2 项目事实 | `EVA_OS/docs/governance/project.yaml` |
| Roadmap 事实 | `EVA_OS/docs/governance/roadmap.yaml` |
| 事件事实 | `EVA_OS/docs/governance/events.jsonl` |
| 结构迁移证据 | `EVA_OS/docs/EVA_structure_report.md` |

历史资料仍可在 `governance/archive/other8_wave1_pending/EVA_OS/` 读取，但它们不是主动 runtime 或 import 入口。

## 旧到新路径映射（OLD_TO_NEW_MAP）

| 旧路径 | 新路径 | 状态 |
|---|---|---|
| `EVA_OS/15_OPEN_QUESTIONS.md` | `governance/archive/other8_wave1_pending/EVA_OS/15_OPEN_QUESTIONS.md` | 已归档 |
| `EVA_OS/AGENT_CONTINUITY.md` | `governance/archive/other8_wave1_pending/EVA_OS/AGENT_CONTINUITY.md` | 已归档 |
| `EVA_OS/CODEX_PROMPTS.md` | `governance/archive/other8_wave1_pending/EVA_OS/CODEX_PROMPTS.md` | 已归档 |
| `EVA_OS/CODEX_TASK_PACK.md` | `governance/archive/other8_wave1_pending/EVA_OS/CODEX_TASK_PACK.md` | 已归档 |
| `EVA_OS/HANDOFF.md` | `governance/archive/other8_wave1_pending/EVA_OS/HANDOFF.md` | 已归档 |
| `EVA_OS/PLANS.md` | `governance/archive/other8_wave1_pending/EVA_OS/PLANS.md` | 已归档 |
| `EVA_OS/UPLOAD_MANIFEST.md` | `governance/archive/other8_wave1_pending/EVA_OS/UPLOAD_MANIFEST.md` | 已归档 |
| `EVA_OS/cleanup/**` | `governance/archive/other8_wave1_pending/EVA_OS/cleanup/**` | 已归档 |
| `EVA_OS/handoff_packs/**` | `governance/archive/other8_wave1_pending/EVA_OS/handoff_packs/**` | 已归档 |
| `EVA_OS/docs/FeatureSpecification.pdf` | `governance/archive/other8_wave1_pending/EVA_OS/docs/FeatureSpecification.pdf` | 已归档生成 PDF |

精确的 40 个移动路径绑定在 `governance/run_manifests/GOV-OTHER8-S4PBT02-EVA-STRUCTURE-SIMPLIFICATION-20260625.json`，并可追溯到 `governance/stage_gates/s4pa/wave1_archive_manifest.json`。

## 保持不变的路径

- `EVA_OS/src/**`、`EVA_OS/shared/**`、`EVA_OS/systems/**` 和 `EVA_OS/tests/**` 均未改变。
- `EVA_OS/data/**` PRIVATE owner 复核候选仍保留原位。
- `EVA_OS/assets/**` 和 `EVA_OS/macos/**` 生成 app 资产仍保留原位；它们不属于 S4PBT02 范围。
- `EVA_OS/docs/FeatureSpecification.md` 仍为主动文档；只有生成 PDF 副本移入归档。

## 停止条件保持情况

- EVA system/shared module import 路径被改变：未触发。
- runtime 或 live-trading 行为被改变：未触发。
- PRIVATE data 被移动或归档：未触发。
- 根 README 无分层地膨胀：未触发。

## 回滚方式

回滚优先使用 git revert 回退 S4PBT02 任务提交。若手工回滚，则按 `OLD_TO_NEW_MAP` 把每个归档路径从 `governance/archive/other8_wave1_pending/EVA_OS/` 还原到旧 `EVA_OS/` 路径，然后复核 S4PAT02 checksum 和 S4PBT02 run manifest。
