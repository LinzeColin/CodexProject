# PFI v0.2.1.1 Product UI Recovery Roadmap Lock

更新时间：2026-06-29

## 执行口径

用户最新要求优先：roadmap 中 Phase、Stage、Task 的母子关系不作为执行层级。v0.2.1.1 后续执行以 **Stage** 为 pursuing goal 的顶层 run gate，Phase 和 Task 只是 Stage 内部的子项。

硬规则：

- 一共有 6 个执行 Stage：`S0` 到 `S5`。
- 每次 run work 最多完成 1 个 Stage。
- `S0 准备轮` 已完成并推送 GitHub main。
- `S1 产品壳与路由` 已完成并推送 GitHub main。
- `S2 页面骨架与去 AI 化` 已完成并推送 GitHub main。
- `S3 真实操作流` 已完成并推送 GitHub main。
- `S4 持久化与同步` 已完成并推送 GitHub main。
- 本轮完成 `S5 真实图表与最终验收`，并按用户口径执行 `Stage 6 项目级复审验收` closeout。
- Stage 0 不修改正式 UI。
- `S5` 完成并通过项目级复审、GitHub main 同步、本机 PFI.app 入口刷新和非必要缓存清理后，才允许声明 v0.2.1.1 本轮完成。

## 6 个执行 Stage

| 执行 Stage | 名称 | 吸收的来源 Phase/Stage | 本 Stage 只做什么 | 不做什么 |
| --- | --- | --- | --- | --- |
| S0 | 准备轮：失败冻结与执行锁 | Phase 0、Stage 0.1、资料读取、路线纠偏 | 标记旧前端失败；锁定 6-stage 执行模型；建立来源清单、合同和测试；记录冲突默认处理 | 不改 Web Shell，不重建导航，不做图表、上传、持仓、报告 |
| S1 | 产品壳与路由 | 原 P0 + P1 | 重建正式主导航、一级页面状态、旧入口别名、浏览器前进后退 | 不做图表、上传闭环、持仓编辑、报告 |
| S2 | 页面骨架与去 AI 化 | 原 P2 + P3 | 清理开发者词和演示污染；建立首页、账户、投资、消费、数据源、建议、报告、设置骨架 | 不做数据库 migration，不伪造趋势数据 |
| S3 | 真实操作流 | 原 P4 | 上传、账本复核、持仓编辑表单、设置保存 | 不用 toast 代替操作，不用浏览器缓存做生产保存 |
| S4 | 持久化与同步 | 原 P6 | 持仓写 SQLite；刷新和重启后读取；首页、投资、报告同步 | 不跳过 SQLite 查询，不声明真实账户生产联通 |
| S5 | 真实图表与最终验收 | 原 P5 + P7 | 账户、投资、消费真实图表或中文空状态；全入口点击、数据、视觉验收 | 不用 demo/sample/mock/fake 数据，不用关键词测试替代行为测试 |

## Stage 1 默认产品决策

Stage 0 读取到两个来源的导航差异。默认采用 RTF 最新纠偏稿：

1. 正式主导航为 10 个入口：首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置。
2. 旧入口不作为主导航展示，只作为路由别名、搜索别名或二级入口。
3. 策略实验室只有一个真实页面，默认归到 `市场与研究 > 策略实验室`。
4. 如用户下一轮明确改回 9 个入口，则先更新本路线锁和合同，再做 Stage 1。

## Stage 0 进入/退出条件

Stage 0 进入条件：

- 已读取 `/Users/linzezhang/Downloads/v0.2.1.1.rtf`。
- 已读取 `/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md`。
- 已读取 PFI 当前 `AGENTS.md`、`HANDOFF.md`、三基文件和现有 v0.2.1/v0.2.2 记录。

Stage 0 退出条件：

- `docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md` 存在。
- `docs/pfi_v0211/ROADMAP_LOCK.md` 存在。
- `docs/pfi_v0211/STAGE0_PREPARATION.md` 存在。
- `src/pfi_v02/stage_v0211_ui_recovery.py` 存在。
- `tests/test_v0211_stage0_preparation_contract.py` 通过。
- 三基文件记录当前 v0.2.1.1 准备轮和下一轮 Stage 1 边界。

## Stage 1 退出条件

Stage 1 退出条件：

- `web/index.html` 正式一级入口为 10 个。
- 旧入口只作为 route alias、搜索别名或命令别名，不再污染侧边一级导航。
- 策略实验室 canonical route 为 `/market-research/strategy-lab`。
- `#/strategy-lab` 和 `#/investment/strategy-lab` 兼容跳转到同一个策略实验室。
- 浏览器前进后退可用。
- `tests/test_v0211_stage1_product_shell_contract.py` 通过。
- `node --check web/app/shell.js` 通过。

## Stage 2 退出条件

Stage 2 退出条件：

- `web/index.html` 默认首屏使用中文用户任务语言，不出现运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据或任务中心等正式 UI 污染。
- 10 个正式一级入口都有页面骨架和二级入口：`首页总览`、`账户与资产`、`账本流水`、`投资管理`、`消费管理`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`市场与研究`、`设置`。
- `数据源与上传` 二级入口固定包含 `上传中心` 与 `导入中心`。
- `设置` 页是反馈、主题、语言、备份等设置内容的唯一正式入口；业务页默认不展示反馈控制台。
- 无真实数据时显示中文真实空状态；不伪造趋势、收益、持仓或消费数值。
- 不做数据库 migration、持仓 SQLite 闭环、真实图表数据接入或上传入库闭环。
- `tests/test_v0211_stage2_page_skeleton_contract.py` 通过。
- `node --check web/app/shell.js` 通过。
- 真实浏览器点击 10 个一级入口和关键二级入口可切换页面状态。

## Stage 3 退出条件

Stage 3 退出条件：

- `数据源与上传` 显示上传中心、解析预览、字段映射、确认入库和待复核队列路径。
- `账本流水` 显示账本筛选、分类选择、保存复核和导出流水路径。
- `投资管理 > 持仓` 显示持仓编辑表单、未提交草稿标识、保存修改入口和恢复默认入口。
- `设置` 页显示保存设置、恢复默认和保存状态；业务页默认不展示设置反馈控制台。
- 点击上传确认、账本复核保存、账本导出、持仓保存、设置保存时，页面状态、摘要、表格或状态条必须变化，不能只弹 toast。
- 持仓生产保存不得调用 `localStorage`、`sessionStorage` 或 `IndexedDB`；浏览器缓存只允许保存明确标注的未提交草稿。
- 无真实数据时显示中文空状态，不新增测试数据、样例流水、模拟持仓或虚构财务事实。
- `tests/test_v0211_stage3_real_operation_flow_contract.py` 通过。
- `node --check web/app/shell.js` 通过。
- 真实浏览器点击上传、账本、持仓和设置主要按钮可获得中文反馈。

## Stage 4 退出条件

Stage 4 退出条件：

- `投资管理 > 持仓` 的保存路径为 Web Shell -> `/api/holdings` -> `V021HoldingsPersistenceService` -> SQLite operational DB。
- 持仓字段至少包含标的、名称、数量、成本、价格、币种、账户、更新时间和备注。
- SQLite 中能查询到保存后的 `v021_holding_snapshots` 和 `v021_position_adjustments`。
- 页面刷新后能通过 `/api/holdings` 读回保存结果。
- 重启本机服务后仍能从同一 SQLite 文件读回保存结果。
- `/api/read-model` 同步首页、投资管理和报告与洞察所需的持仓读模型。
- `/api/reports/holdings` 读取同一 SQLite 数据源；正式库无持仓时显示中文空状态，不生成模拟收益。
- `tests/test_v0211_stage4_persistence_sync_contract.py` 通过。
- `node --check web/app/shell.js` 通过。
- 真实 8501 浏览器验收覆盖投资持仓、保存入口、首页、投资页和报告页。

## Stage 5 退出条件

Stage 5 退出条件：

- 账户与资产、投资管理、消费管理趋势图统一读取 `/api/trends`，不得继续使用硬编码 chart array。
- 账户与资产趋势从 SQLite operational DB / 读模型派生现金总额、净资产、总资产、总负债；数据不足时显示中文空状态。
- 投资管理趋势从 SQLite 持仓快照派生投资市值、总收益、未实现盈亏、现金仓位；无真实持仓时不伪造收益。
- 消费管理趋势从 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` 派生本月支出、预算剩余、固定支出、弹性支出、现金流预测；缺数据时显示中文空状态。
- 正式 Web Shell 不暴露合成验收、测试样例、fixture、demo、mock、fake 或硬编码趋势路径。
- 所有一级入口、关键二级入口、主要按钮、全局搜索、策略实验室同路由、设置隔离和图表空状态必须用真实浏览器验收。
- `tests/test_v0211_stage5_6_final_acceptance_contract.py` 通过。
- `node --check web/app/shell.js` 通过。

## Stage 6 项目级复审验收退出条件

用户口径的 Stage 6 是 Stage 5 之后的第二阶段 closeout，不是路线锁之外再新增一个可跳过的机器 Stage。

- 复审首页、账户、账本、投资、消费、数据源、建议、报告、市场与研究和设置。
- 修复复审暴露的问题后再同步 GitHub main。
- 刷新本机 `PFI.app` 入口并确认 8501 health。
- 清理本轮临时 worktree、pytest cache、`__pycache__`、临时 SQLite 和临时截图/日志，不清理用户原始数据、`MetaDatabase`、正式 operational DB 或其它项目。

## 后续停止条件

任意 Stage 触发以下条件时，不允许声明通过：

- 继续写“v0.2.1 前端优化已完成”而不说明其正式 UI 失败。
- 把所有模块堆在一个长页面里，用锚点滚动冒充页面跳转。
- 正式 UI 出现运行边界、默认反馈控制台、右侧设置栏、Task Pack、Demo、Prototype、runtime、Boundary 等开发者词污染。
- 按字符串/marker/function name 测试替代真实浏览器点击、保存、刷新、重启、SQLite 查询和截图验收。
- 使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为正式产品数据源。
