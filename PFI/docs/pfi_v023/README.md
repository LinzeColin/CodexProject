# PFI v0.2.3 人类产品体验恢复版

## 版本定位

PFI v0.2.3 是一次产品体验恢复，不是 UI 换皮、文案整理或演示页开发。本版本目标是把 PFI 恢复为一个正常人类会长期使用的个人经济/财务分析系统，重点解决三类阻塞：

1. 入口不一致：用户点击 `PFI.app` 后必须进入同一个最新 UI，而不是旧页面、旧缓存或历史 shell。
2. 数据不可信：真实数据未加载、路径错误、过期、解析失败、筛选为空和真实为 0 必须可区分，不允许用假 0 掩盖问题。
3. 体验机械化：一级/二级页面、操作流、反馈、报告和分析结论必须像真实软件，而不是 AI 模板堆叠。

## Stage 0 范围

本轮只完成 Stage 0：需求锁定、历史约束废弃、证据基线建立。

本轮明确不做：

- 不改正式 UI。
- 不改路由实现。
- 不改数据计算或 read model。
- 不重装 app。
- 不新增报告生成能力。
- 不声明 v0.2.3 整体完成。

## 固定 10 个一级入口

v0.2.3 正式一级入口固定为 10 个，顺序固定：

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察
9. 市场与研究
10. 设置

`市场与研究` 是正式一级入口。历史 9 入口约束和历史 `市场与研究` 禁令均作废。

## v0.1 兼容规则

v0.1 习惯入口不得再作为同层一级入口堆叠，只能作为兼容路由、二级入口、重定向或搜索命令存在。

| v0.1 习惯入口 | v0.2.3 归属 |
|---|---|
| 首页 | 首页总览 |
| 市场 | 市场与研究 |
| 研究 | 市场与研究 |
| 持仓 | 投资管理 |
| 策略实验室 | 市场与研究 / 投资管理共享同一状态 |
| 数据与系统 | 设置 |

## 真实数据铁律

正式 UI、验收、报告、首页摘要、图表和建议不得使用 mock、sample、synthetic、fixture、demo、fake 或自动生成的财务数据。真实数据不足时只能显示中文真实状态，例如“未加载真实数据”“路径错误”“解析失败”“需要复核”，不得显示财务假 0。

## 后续 Stage 进入条件

Stage 0 候选通过后，仍需用户确认本合同。未确认前不得进入 Stage 1。Stage 1 才处理 app/localhost/frontend bundle 一致性。

## Stage 1-3 Group Review 状态

当前本机 Downloads 中已存在 v0.2.3 roadmap 和 taskpack：

- `/Users/linzezhang/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt`
- `/Users/linzezhang/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip`
- `/Users/linzezhang/Downloads/pfi_v023_phase1_human_product_experience_preview.html`

第二阶段第一组整体复审对标 `pfi_v023_phase1_human_product_experience_preview.html`，
覆盖 Stage 1、Stage 2、Stage 3：

- Stage 1：当前 localhost app 入口加载当前 checkout 的 PFI shell，并暴露 Stage 1 metadata。
- Stage 2：缺少账户、现金、持仓真实 read model 时，首页不显示 `CNY 0.00`；只显示真实缺失状态。
- Stage 3：正式一级入口为 10 个，包含 `市场与研究`，旧入口只保留兼容 route/命令入口。

记录文件：`STAGE1_3_GROUP_REVIEW.md`。
