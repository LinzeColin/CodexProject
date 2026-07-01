# KM_IDSystem S4PCT01 中文结构验收报告

- 任务：`S4PCT01`
- 验收：`ACC-S4PCT01`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

KM_IDSystem 的 S4PCT01 把历史备份和原型工作从主动源码层分离出去。`backend/**`、`frontend/**`、`app_bundle/**`、`samples/**`、运行数据和报告路径保持原有职责，不改变 API、UI、模型、启动器或交付构建行为。

## 中文验收标准

- Owner 不读英文技术表也能知道主动源码、历史归档、demo 输入和运行输出的边界。
- 三个中文入口继续是人类主视图，archive 只是历史恢复资料。
- 本任务不得把治理迁移说明写成产品功能承诺。

## 停止条件与结果

- delivery package 与 runtime source 职责未分离：`未触发`
- backend/frontend runtime 行为被改变：`未触发`
- startup command 改动但 README 未同步：`未触发`
- app bundle 构建源码被移动：`未触发`
- sample/demo 输入被移动：`未触发`

## 回滚

优先用 git revert 回退 S4PCT01 任务提交。若必须手工恢复，从 `governance/archive/other8_wave1_pending/KM_IDSystem/` 按 OLD_TO_NEW_MAP 还原，并复核 S4PAT02 checksum 与 S4PCT01 run manifest。

## 下一步

后续开发只在主动源码层做业务变更；历史备份和原型资料不得重新进入默认开发循环。

---

## 原技术记录

# KM_IDSystem S4PCT01 结构报告

任务：`S4PCT01`
验收：`ACC-S4PCT01`
日期：2026-06-25

## 范围

本报告记录 KM_IDSystem 在 Other8 S4PC 中的结构瘦身：主动运行源码与历史备份、原型工作分离；backend、frontend、app launcher、API、UI 和模型行为均未改变。

## 主动结构

| 用途 | 主动路径 | 状态 |
|---|---|---|
| Backend 运行源码 | `KM_IDSystem/backend/**` | 未改变 |
| Frontend 运行源码 | `KM_IDSystem/frontend/**` | 未改变 |
| 交付 app 构建源码 | `KM_IDSystem/app_bundle/**` | 未改变 |
| 运行数据和生成状态 | `KM_IDSystem/data/**`, `KM_IDSystem/reports/**` | 未改变；仍是运行输出或忽略层 |
| demo 上传样例 | `KM_IDSystem/samples/**` | 未改变；仍是主动 demo 输入 |
| 历史备份 | `governance/archive/other8_wave1_pending/KM_IDSystem/backups/generated-artifacts/**` | 已归档 |
| 原型工作 | `governance/archive/other8_wave1_pending/KM_IDSystem/work/original/**` | 已归档 |

`app_bundle/native_launcher.c` 和 `app_bundle/assets/OpMeIcon.*` 仍是主动构建输入，因为 `scripts/build_app_bundle.sh`、`scripts/install_app_entries.sh` 和 `scripts/generate_app_icon.py` 使用这些路径。生成的 `.app` bundle 和 iconset 继续忽略。

## 旧到新路径映射（OLD_TO_NEW_MAP）

| 旧路径 | 新路径 | 状态 |
|---|---|---|
| `KM_IDSystem/backups/generated-artifacts/**` | `governance/archive/other8_wave1_pending/KM_IDSystem/backups/generated-artifacts/**` | 已归档 |
| `KM_IDSystem/work/original/**` | `governance/archive/other8_wave1_pending/KM_IDSystem/work/original/**` | 已归档 |

精确的 18 个移动路径绑定在 `governance/run_manifests/GOV-OTHER8-S4PCT01-OPME-STRUCTURE-SIMPLIFICATION-20260625.json`，并可追溯到 `governance/stage_gates/s4pa/wave1_archive_manifest.json`。

## 保持不变的路径

- `KM_IDSystem/backend/**` 和 `KM_IDSystem/frontend/**` 未改变。
- `KM_IDSystem/app_bundle/**` 仍是主动交付构建源码。
- `KM_IDSystem/samples/**` 仍是主动 demo 输入，因为 README 暴露它为上传路径，runtime 也可能重建 `samples/`。
- `KM_IDSystem/data/**`、生成运行报告和本地依赖缓存继续由既有 ignore/runtime 规则管理。

## 停止条件保持情况

- delivery package 与 runtime source 职责已分离：已满足。
- backend/frontend runtime 行为被改变：未触发。
- startup command 改动但 README 未同步：未触发。
- app bundle 构建源码被移动：未触发。
- sample/demo 输入被移动：未触发。

## 回滚方式

回滚优先使用 git revert 回退 S4PCT01 任务提交。若手工回滚，则按 `OLD_TO_NEW_MAP` 把每个归档路径从 `governance/archive/other8_wave1_pending/KM_IDSystem/` 还原到旧 `KM_IDSystem/` 路径，然后复核 S4PAT02 checksum 和 S4PCT01 run manifest。
