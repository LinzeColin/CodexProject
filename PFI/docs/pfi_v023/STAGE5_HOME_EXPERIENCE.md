# PFI v0.2.3 Stage 5 - 首页人类任务流重建

## Phase 5.1 范围

本轮只执行 `V023-S5-P5.1 首页信息架构`，不进入 Phase 5.2、Phase 5.3、Stage 6 或后续 Stage。

Phase 5.1 只解决首页先回答四个问题：

1. 我现在有多少钱。
2. 钱在哪里。
3. 哪些数据有问题。
4. 最近发生了什么。

## 交付内容

- 新增 `PFI/web/app/pages/home.js`，定义 Stage 5 首页信息架构 view model。
- 首页 view model 使用 Stage 2 数据状态字段：`status`、`source`、`as_of`、`evidence_hash`、`message_zh`。
- 未加载、路径错误、解析失败、权限失败、过期、筛选为空、计算失败、待复核等状态只显示中文状态，不显示财务数值。
- `ready` 和 `confirmed_zero` 只有带完整来源、时间和证据 hash 时才显示数值。
- `PFI/web/app/shell.js` 只做最小接入：动态加载 `home.js`，并把 view model 映射到现有首页卡片、说明卡、行和任务区。

## 任务包边界

Stage 5 allowed files 原本列出 `PFI/web/app/pages/home.js`，但当前 v0.2.3 前端首页渲染仍在 `shell.js` monolith 中。如果不在 `shell.js` 加载并应用 `home.js`，用户真实打开 app 时不会看到 Phase 5.1 首页信息架构。因此本轮对 `shell.js` 的改动仅限 loader 与 home view model 应用，不改变 Stage 3/4 路由合同，不实现 Phase 5.2 动作生成。

## 明确未完成

- Phase 5.2 下一步动作生成。
- Phase 5.3 首页残留术语全量清理。
- Stage 5 whole-stage review。
- Stage 6 核心财务指标 read model 接入。
- 中间 phase GitHub main 上传。

## 验收方式

- `PFI/tests/test_v023_stage5_home_experience.py`
- `PFI/web/app/pages/home.js` syntax check
- `PFI/web/app/shell.js` syntax check
- v0.2.3 回归测试
- 禁用财务数据词扫描
