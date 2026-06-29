# PFI v0.2.3 Stage 0 基线报告

## 目标

建立 v0.2.3 的机器可读和人类可读合同，废弃历史 9 入口等冲突约束，记录后续开发证据基线。

## 输入资料

- `/Users/linzezhang/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt`
- `/Users/linzezhang/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip`

## 当前入口基线

只读审计结果：

- `PFI/web/index.html` 已存在 `data-primary-workspaces="10"`。
- `PFI/web/index.html` 当前一级入口包含 `市场与研究`。
- `PFI/web/app/shell.js` 当前 workspace 文案包含 `市场与研究`。
- `PFI/web/app/shell.js` 当前搜索关键词包含 `策略实验室`。

Stage 0 只记录这些事实，不修改 UI。

## v0.2.3 合同基线

正式一级入口固定为：

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

## 废弃历史冲突

以下历史约束不得进入后续 v0.2.3 run：

- `9 个一级入口`
- `市场与研究不得作为一级入口`
- 暗色 AI 控制台风格
- 演示数据可用于财务验收
- README/docs 写完成即可 closeout

## 后续 Stage 入口

- Stage 1 才处理 app/localhost/frontend bundle 一致性。
- Stage 2 及以后才处理真实页面、路由、产品体验、数据状态机和报告能力。
- Stage 0 完成后必须等待用户验收确认，不得自动进入 Stage 1。
