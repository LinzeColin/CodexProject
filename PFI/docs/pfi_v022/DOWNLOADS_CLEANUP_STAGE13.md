# Stage 13 Downloads 清理记录

本轮只复审解决 Stage 13。适用阶段：Stage 13 - 后置触发型复核。适用任务：`S13-P1-T1`、`S13-P1-T2`、`S13-P1-T3`。触发条件为 `交付前人工指定`，本文件服务本地 Codex Review Ticket。

整体项目复审解决不在本轮实现。GitHub 同步不在本轮执行。app 入口重装不在本轮执行。本轮禁止全仓无差别扫描，不联网，不调用外部 LLM，仅对异常区域进行复核。

## 清理原则

- 只处理 PFI 预同步临时目录。
- 不删除 `PFI.app`。
- 不删除用户提供的 taskpack、roadmap、zip、md 源文件。
- 清理前先归档，避免未归档就删除。
- 清理动作只服务本轮 `交付前人工指定` 的 Codex Review Ticket，禁止全仓无差别扫描。
- 仅对异常区域进行复核：本文件只记录 Downloads 污染文件夹的归档、迁移和保留项，不扫描或修改 EEI、ADP、Alpha、Serenity、QBVS 等非 PFI 目录。

## 归档

- 归档文件：`PFI/docs/pfi_v022/downloads_cleanup/PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz`
- SHA-256：`c636b7afbd40923946af77c4987bb5dc1342e924b89e2b3da5bd2128795b6274`
- 原目录已移出 Downloads 到 macOS Trash 下的恢复目录：`~/.Trash/PFI_V022_STAGE13_DOWNLOADS_CLEANUP_20260628/`

## Downloads 污染文件夹白名单

| 原 Downloads 目录 | 动作 | 状态 |
| --- | --- | --- |
| `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` | 归档后移出 Downloads | 已处理 |
| `PFI_V022_STAGE0_REDO_PRE_CANONICAL_SYNC_20260628T091046` | 归档后移出 Downloads | 已处理 |
| `PFI_V022_STAGE0_REDO_PRE_CANONICAL_SYNC_20260628T105440` | 归档后移出 Downloads | 已处理 |
| `PFI_V022_STAGE1_PRE_CANONICAL_SYNC_20260628T095205` | 归档后移出 Downloads | 已处理 |
| `PFI_V022_STAGE2_PRE_CANONICAL_SYNC_20260628T102911` | 归档后移出 Downloads | 已处理 |
| `PFI_V022_STAGE3_PRE_CANONICAL_SYNC_20260628T111109` | 归档后移出 Downloads | 已处理 |

## 保留来源

- `PFI.app`：当前仍在 Downloads，作为本机 PFI app 入口。
- `PFI_v0.2.2_Codex_Task_Pack_zh.md`：本轮不删除，来源名保留在 manifest。
- `PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md`：本轮不删除，来源名保留在 manifest。
- `PFI_v0.2.2_E2E_logic_optimization_package.zip` 和同名复制包：本轮不删除，来源名保留在 manifest。

## 复核结论

本轮记录了问题、修复、验证、剩余风险：Downloads 污染文件夹已清理出 Downloads，`PFI.app` 仍存在，用户源文件名留在记录中，阻塞项数量：`0`。
