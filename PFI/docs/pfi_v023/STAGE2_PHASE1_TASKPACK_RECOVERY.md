# PFI v0.2.3 Stage 2 Phase 1 任务包恢复与防幻觉门

## 目标

本轮是 Stage 2，但每次 run work 最多只解决一个 phase。Phase 1 的目标是先恢复并验证 v0.2.3 Stage 2 的真实任务包边界，防止在缺少官方 Stage 2 Roadmap/TaskPack 时凭历史版本或旧页面经验编造页面、路由、数据或报告需求。

## 当前事实

当前 GitHub `main` 只包含 v0.2.3 Stage 0 和 Stage 1 交付物：

- `PFI/docs/pfi_v023/README.md`
- `PFI/docs/pfi_v023/STAGE0_BASELINE.md`
- `PFI/docs/pfi_v023/STAGE1_APP_ENTRY_BUNDLE_CONSISTENCY.md`
- `PFI/reports/pfi_v023/stage_1/evidence.json`

Stage 0 文档记录的原始输入路径如下，但当前新电脑检查未找到这些文件：

- `~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt`
- `~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip`

因此本 phase 不得把 v0.2.1.1 的 `S2 页面骨架与去 AI 化`、v0.2.2 的 `Stage 2 CNY/Fx` 或更早 `PFI V0.2 Stage 2` 当作 v0.2.3 Stage 2 任务包。

## 本轮范围

- 建立 `build_stage2_phase1_contract()` 机器合同。
- 记录已检查的任务包路径和当前缺失状态。
- 生成 Stage 2 Phase 1 evidence pack。
- 保持 Stage 0/1 基线：10 个一级入口、`市场与研究` 正式一级入口、禁止假财务数据、每轮只做一个 phase。

## 明确不做

- 不做 Stage 2 页面重建。
- 不改一级入口数量、路由归属或 Web Shell UI。
- 不改数据计算、read model、报告生成或财务结论。
- 不重装 `PFI.app`。
- 不上传 GitHub main；中间 phase 完成不上传。
- 不使用 mock、sample、synthetic、fixture、demo、fake 财务数据。

## 下一步进入条件

进入 Stage 2 Phase 2 前必须满足至少一项：

1. 用户重新提供 v0.2.3 Human Product Experience Recovery Roadmap 和 TaskPack。
2. GitHub main 中新增可审计的 v0.2.3 Stage 2 phase/task 定义。
3. 用户明确确认以当前仓内某个具体 v0.2.3 文档作为 Stage 2 任务包替代源。

未满足前，只能继续报告缺失和准备恢复，不能开发后续功能。
