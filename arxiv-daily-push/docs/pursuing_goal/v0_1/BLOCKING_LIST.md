# BLOCKING_LIST · S0-P02 阻断清单

> 任务 `ADP-S0-P02-T007` 交付物。列出 P0 未知/漂移及其**明确归属**。
> 规则：P0 未知项必须分配到明确任务/门；未解决前，**依赖该未知的下游需求不得开工**。

## A. 阻断项（P0，须 Owner 在 S0 Exit 处理）

| # | 阻断 | 影响 | 归属 | 是否阻断进入 S1 |
|---|---|---|---|---|
| BLOCK-A1 | FACT-013 Cloudflare 套餐/账单未知 | 无法量化 S8 Value-Cost 硬 Gate；成本决策缺真实账单 | **S0 Exit · Owner 后台确认套餐/账单** | 否（仅阻断 S8 与任何成本承诺；S1–S7 可先行，成本项标 UNKNOWN 不记 0） |
| BLOCK-A2 | FACT-015 私有分支/未提交代码未知 | 可能存在未纳入公开仓库的真身，影响「单一事实源」 | **S0 Exit · Owner/仓库只读盘点** | 否（S1 可先行；若 Owner 盘点发现私有实现，须回到权威顺序裁决） |

两项均**不阻断 S1 起步**，但 **阻断 S0 Exit 的 Owner 签署**：Owner 必须确认「私有事实快照无关键遗漏」，即对 FACT-013/FACT-015 给出确认或补充。

## B. 须排期的漂移（非阻断 S1，但必须在具名任务修复）

| # | 漂移 | 归属任务 | 备注 |
|---|---|---|---|
| BLOCK-B1 | DRIFT-FACT-006 来源真相（board3 config ↔ worker 硬编码） | 后续来源真相任务（S1/S2） | 与 DIR-002（A0-A2）一并处理；worker 为真身，boards 对齐或重写 |
| BLOCK-B2 | DRIFT-FACT-007 状态文档矛盾（STATUS.yaml J5↔R6） | 后续治理一致性任务 | 将 R6 标 superseded，收敛单一状态源 |
| BLOCK-B3 | DRIFT-FACT-011 D1 遗留 mirror 表（6 张） | 后续 D1 清理任务（须 migration+rollback） | 与 DRIFT-FACT-007 同源；清理前须确认无读依赖 |

## C. 不阻断（已核实 / 已受控）

- FACT-011（D1 schema/大小/计数）、FACT-012（R2 NOT_ENABLED）已 VERIFIED；R2 未启用不阻断当前（数据 1.05MB 无需对象存储），仅当后续需存原文/历史时再由 **Owner 决定是否开 R2**。
- FACT-014 build↔域名 = PARTIAL（live 455afd98 + 相似 0.9973）；后续 S1 以部署纪律补齐严格逐 host 校验。

## D. 硬约束复述

- **任何需求不得由 UNKNOWN 直接推导**：引用事实前先查 `FACT_LEDGER.csv` 的 classification/verification_status。
- **UNKNOWN ≠ 0**：成本/容量项在 FACT-013 解决前一律标 UNKNOWN，不得记 0 或臆造 ROI。
