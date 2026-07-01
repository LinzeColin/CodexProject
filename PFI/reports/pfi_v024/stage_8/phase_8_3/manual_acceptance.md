# PFI v0.2.4 Stage 8 Phase 8.3 Manual Acceptance

Status: 待用户确认

本文件是 `Stage 8 Phase 8.3 - 人工验收` 的人工验收清单。它只把 Phase 8.1 自动验收和 Phase 8.2 截图验收结果整理成用户可确认的检查项；不代替用户确认，不进入 Stage 8 whole-stage review，不得进入 Stage 9。

## 验收前提

- Phase 8.1 自动验收已 candidate pass。
- Phase 8.2 截图验收已 candidate pass。
- 本 phase 不重装 app bundle，不修改 launcher，不写入、清理、删除、补造或改写真实财务数据。
- 当前 `/Applications/PFI.app` 缺失；`~/Downloads/PFI.app` 存在并在 Phase 8.2 验证为指向当前 checkout。人工验收时优先打开现有 `~/Downloads/PFI.app`，或按用户后续指令处理 `/Applications/PFI.app`。

## 人工验收清单

| Check | 操作 | 期望 |
| --- | --- | --- |
| A8.3-01 | 打开 PFI.app。 | app 能进入当前 checkout 对应的 PFI 页面，入口版本与 v0.2.4 / v0.2.3-repair 一致。 |
| A8.3-02 | 打开 localhost。 | localhost 页面与 app 入口视觉和 bundle hash 一致。 |
| A8.3-03 | 逐项点击 10 个一级入口。 | `首页总览`、`账户与资产`、`账本流水`、`投资管理`、`消费管理`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`市场与研究`、`设置` 均可访问。 |
| A8.3-04 | 打开核心二级页面。 | 每个核心二级页面能展示业务内容、状态和可行动入口，不退回旧 9 入口约束。 |
| A8.3-05 | 使用浏览器后退/前进。 | 浏览器后退/前进能回到相邻页面，URL 和选中导航同步。 |
| A8.3-06 | 查看首页、账户、投资、消费、报告核心指标。 | 核心指标无假零；缺失真实输入时显示阻断/缺口状态，不显示伪造财务结论。 |
| A8.3-07 | 打开报告中心。 | 报告中心可见 6 类报告、公式、参数、样本量、数据范围、置信度、缺口和复核入口。 |
| A8.3-08 | 检查亮色 UI。 | 默认亮色 UI 可读，页面背景、卡片、表格和图表槽不退回暗色控制台风格。 |
| A8.3-09 | 用移动端宽度查看。 | 移动端响应式可用，无水平溢出。 |
| A8.3-10 | 检查执行边界。 | 用户确认前不得进入 Stage 9，不上传 GitHub main，不声明整阶段完成。 |

## 判定方式

- 用户确认后，下一轮才能进入 Stage 8 whole-stage review。
- 如果用户发现体验问题，记录到 `defects.md`，优先在 Stage 8 whole-stage review 或修复轮处理。
- 如果用户明确不接受，本 phase 保持 `ready_for_user_acceptance`，不得推进 Stage 9。
