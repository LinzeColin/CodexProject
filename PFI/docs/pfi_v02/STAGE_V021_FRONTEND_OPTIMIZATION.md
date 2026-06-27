# PFI v0.2.1 前端优化

更新时间：2026-06-27 Australia/Sydney

## Stage 0 目标

本轮是 `v0.2.1 前端优化` 的准备轮，任务 ID 为 `V021-P0-S0-T01`。目标是读取并锁定 roadmap，把后续前端优化拆成可逐 stage 验收的合同，不提前实现后续 stage。

权威输入：

- `/Users/linzezhang/Downloads/pfi_v0.2.1_frontend_optimization_task_pack_roadmap.md`
- `/Users/linzezhang/Downloads/pfi_os_delivery_stage1_clicksafe.html`
- 当前 GitHub / 本机产品根：`LinzeColin/CodexProject/PFI`
- 当前正式前端目标：`PFI/web/index.html` + `PFI/web/app/shell.js`

## 本轮范围

本轮只做准备和合同化：

- 锁定版本名：`v0.2.1 前端优化`。
- 锁定后续交付范围：PFI 前端、交互、图表、上传命名、设置页、持仓编辑持久化。
- 锁定正式 UI 目标：HTML Web Shell，不再把交付目标放在演示 HTML 或 Streamlit 侧栏。
- 锁定 CNY 作为系统基准货币。
- 锁定所有页面顶部右上角常态显示 CNY/AUD 汇率。
- 锁定 UIUX 多模态反馈归属：只在设置页管理，不常驻干扰业务页面。

## 明确不做

- 不重构 QBVS。
- 不把 QBVS 重新放回 PFI。
- 不新增 Alpha、Ralpha、System、Development 产品一级入口。
- 不声明真实账户生产联通。
- 不执行实盘下单、支付提交或券商提交。
- 不在 stage0 提前实现导航、图表、上传、设置页、持仓持久化等后续 stage 功能。

## CNY 基准与 CNY/AUD 汇率契约

PFI v0.2.1 之后整体系统以 CNY 元为基准。所有页面顶部右上角必须常态化展示汇率徽标：

```text
CNY/AUD=4.70（YYYYMMDD--HH:MM）
```

合同解释：

- `base_currency = CNY`。
- `quote_pair = CNY/AUD`。
- 展示语义：1 AUD 折算多少 CNY，用于用户读数和跨币种视图统一。
- 展示位置：所有页面顶部右上角。
- 数据时间：读取当日 06:00 Australia/Sydney 本地时间的汇率快照。
- 时间格式：`YYYYMMDD--HH:MM`。
- 示例：`CNY/AUD=4.70（20260627--06:00）`。
- 数据缺失时必须显示中文空状态：`汇率数据待更新`，不得伪造汇率。

Stage 1 之后的实现验收必须检查 HTML 顶栏、路由切换后保留、桌面和手机视口均可见。

## 统一导航目标

v0.2.1 最终一级入口按以下顺序显示，不展示新旧分组标题。旧入口作为别名或深链，不创建第二套页面。

| 顺序 | 可见入口 | 路由 | 页面归属 |
| --- | --- | --- | --- |
| 1 | 首页总览 | `/home` | 首页总览 |
| 2 | 账户与资产 | `/accounts` | 账户与资产 |
| 3 | 账本流水 | `/ledger` | 账本流水 |
| 4 | 投资管理 | `/investment` | 投资管理 |
| 5 | 消费管理 | `/consumption` | 消费管理 |
| 6 | 数据源与上传 | `/sources-upload` | 数据源与上传 |
| 7 | 建议与复盘 | `/review` | 建议与复盘 |
| 8 | 报告与洞察 | `/reports` | 报告与洞察 |
| 9 | 首页 | `/home` | 首页总览 |
| 10 | 市场 | `/investment?tab=market` | 投资管理 |
| 11 | 研究 | `/investment?tab=research` | 投资管理 |
| 12 | 持仓 | `/investment?tab=holdings` | 投资管理 |
| 13 | 策略实验室 | `/investment/strategy-lab` | 投资管理 |
| 14 | 数据与系统 | `/settings?tab=data-system` | 设置 |
| 15 | 设置 | `/settings` | 设置 |

禁用用户可见分组或模块名：

- `PFI 2.0 当前入口`
- `PFI 1.0 兼容入口`
- `V0.2 当前入口`
- `V0.1 兼容入口`
- `运行边界`
- `Boundary`
- `Non-execution boundary`

## HTML 与多模态反馈目标

正式交付目标是 `PFI/web` HTML Web Shell。`pfi_os_delivery_stage1_clicksafe.html` 只作为交互参考，不作为替代产品页面。

多模态反馈必须进入设置页：

- 运行反馈控制台
- 多模态反馈
- 触感反馈强度
- 声音反馈
- 视觉反馈
- 通知反馈
- 反馈测试
- 无障碍反馈

业务页面默认不常驻反馈控制台。手机浏览器支持震动时才调用 `navigator.vibrate`，不支持时静默降级。

## Roadmap 拆分

| Phase | Stage | Task ID | Task | Done 标准 |
| --- | --- | --- | --- | --- |
| P0 | S0 基线 | V021-P0-S0-T01 | 建立 v0.2.1 任务记录 | 文档、版本、范围明确。 |
| P1 | S1 导航合并 | V021-P1-S1-T01 | 删除新旧入口分组标题 | 入口统一显示，无分组字样。 |
| P1 | S1 导航合并 | V021-P1-S1-T02 | 数据源与同步改为数据源与上传 | 全站展示新名称。 |
| P1 | S1 导航合并 | V021-P1-S1-T03 | 低操作导入中心改为导入中心 | 全站展示导入中心。 |
| P1 | S1 导航合并 | V021-P1-S1-T04 | 合并策略实验室 | 只有一个策略实验室路由和状态源。 |
| P2 | S2 文案清理 | V021-P2-S2-T01 | 全局中文化 | 禁用英文扫描通过。 |
| P2 | S2 文案清理 | V021-P2-S2-T02 | 删除运行边界 UI 板块 | 用户界面不出现运行边界模块。 |
| P2 | S2 文案清理 | V021-P2-S2-T03 | 删除桌面手机预览框 | 桌面无手机演示框，手机真实响应式可用。 |
| P3 | S3 设置页 | V021-P3-S3-T01 | 设置页独立路由 | 默认不显示右侧设置。 |
| P3 | S3 设置页 | V021-P3-S3-T02 | 运行反馈控制台移入设置 | 设置页可配置反馈。 |
| P4 | S4 趋势模型 | V021-P4-S4-T01 | 新增统一趋势数据结构 | 三类页面可读同一趋势合同。 |
| P4 | S4 趋势模型 | V021-P4-S4-T02 | 账户与资产折线图 | 现金 / 净资产趋势显示。 |
| P4 | S4 趋势模型 | V021-P4-S4-T03 | 投资管理折线图 | 市值 / 总收益 / 现金仓位显示。 |
| P4 | S4 趋势模型 | V021-P4-S4-T04 | 消费管理折线图 | 支出 / 预算 / 现金流显示。 |
| P5 | S5 上传中心 | V021-P5-S5-T01 | 上传中心 | 上传、拖拽、状态、失败反馈可用。 |
| P5 | S5 上传中心 | V021-P5-S5-T02 | 导入中心 | 批次、摘要、复核入口可用。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T01 | 持仓编辑数据模型 | adjustment 和 snapshot 可写入数据库。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T02 | 持仓编辑服务 | 新增、修改、软删除、读取测试通过。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T03 | 持仓编辑前端 | 刷新 / 重启后修改仍存在。 |
| P7 | S7 流畅度 | V021-P7-S7-T01 | 所有入口和按钮可点击 | 自动遍历无死按钮。 |
| P7 | S7 流畅度 | V021-P7-S7-T02 | 页面反馈统一 | 成功、失败、进行中都有反馈。 |
| P8 | S8 验收 | V021-P8-S8-T01 | 前端合同测试 | 新增测试通过。 |
| P8 | S8 验收 | V021-P8-S8-T02 | 浏览器验收 | 桌面 / 手机关键路径通过。 |
| P8 | S8 验收 | V021-P8-S8-T03 | 命令验收 | 单测、JS 检查、治理、diff 检查通过。 |

## Stage 0 验收标准

- `PFI/VERSION` 写明 `v0.2.1 前端优化`。
- 本文件存在，并写明 v0.2.1 是前端优化，不是 V0.2 重构。
- 三基文件已更新：`开发记录.md`、`功能清单.md`、`模型参数文件.md`。
- 新增 `src/pfi_v02/stage_v021_frontend_contract.py`。
- 新增 `tests/test_v021_stage0_frontend_contract.py`。
- 合同测试覆盖 CNY 基准、CNY/AUD 顶栏、HTML 目标、多模态反馈设置页归属、15 个统一入口、P0-P8 任务清单。
- 不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口。

## Stage 0 停止条件

满足以下条件即停止，不继续实现后续 stage：

- Stage 0 文档、版本、三基、合同测试完成。
- `tests.test_v021_stage0_frontend_contract` 通过。
- 既有 PFI Stage 1 IA 合同仍通过，证明没有提前破坏 V0.2 基线。
- `node --check web/app/shell.js` 通过。
- `python3 ../scripts/validate_project_governance.py --project PFI` 通过。
- `git diff --check -- PFI` 通过。

## 下一轮执行顺序

下一轮 pursuing goal 应从 P1/S1 开始，优先完成导航合并、数据源与上传命名、导入中心命名和策略实验室单一路由。不得跳到持仓持久化或图表实现，除非用户明确改变阶段顺序。
