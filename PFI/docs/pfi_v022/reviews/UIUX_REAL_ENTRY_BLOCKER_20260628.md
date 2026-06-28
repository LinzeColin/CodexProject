# PFI 真实入口 UIUX 阻断复现与分工记录

日期：2026-06-28 Australia/Sydney

本记录用于纠偏：当前不能再只用合同测试、字符串测试或静态 HTML 宣称 PFI 正式交付通过。真实入口必须以 `PFI.app` / `http://127.0.0.1:8501` 为准。

## 线程分工

side thread 已暂停直接改仓库，并准备只处理以下 PFI 前端重叠范围：

- 把底部 Streamlit 上传补丁移入“数据源与上传”正式入口。
- 删除正式业务页中的“交互反馈 / 多模态交互反馈 / 视觉状态轨道 / 触感强度 / 声音反馈 / 反馈日志”等污染板块。
- 交互反馈只保留在“设置”页。
- 数字搜索按真实入口编号、日期、记录数、金额等索引，不造测试数据。

主线程当前不修改这些文件，避免覆盖 side thread：

- `PFI/web/index.html`
- `PFI/web/app/shell.js`
- `PFI/src/pfi_os/app/streamlit_app.py`
- 相关前端验收测试

## 真实入口复现

入口：`http://127.0.0.1:8501`

证据路径：

- `/tmp/pfi_uiux_repro_stage5/uiux_single_page_matrix.json`
- `/tmp/pfi_uiux_repro_stage5/desktop_single_single_before.png`
- `/tmp/pfi_uiux_repro_stage5/mobile_single_single_before.png`
- `/tmp/pfi_uiux_repro_stage5/desktop_matrix.json`
- `/tmp/pfi_uiux_repro_stage5/desktop_matrix.png`

## 可用性矩阵

| 视口 | 真实结果 | 结论 |
| --- | --- | --- |
| 桌面 1440x1000 | 15 个一级入口可见；抽样点击 `首页总览`、`账户与资产`、`账本流水`、`投资管理`、`消费管理`、`数据源与上传`、`策略实验室`、`设置` 均能切换；顶部 `搜索`、`任务`、`证据`、`设置` 抽样点击无 console/page error。 | 桌面主入口不是全断，但仍存在 iframe/Streamlit 混合层级与多滚动容器问题。 |
| 移动 390x844 | 一级入口列表全部不可见；`首页总览`、`账户与资产`、`账本流水`、`投资管理`、`消费管理`、`数据源与上传`、`策略实验室`、`设置` 点击结果均为 `not_visible`。 | 移动端正式入口阻断，不能通过交付验收。 |
| 桌面父页面 | 父页面存在 Streamlit 原生上传文字和工作台 iframe；检测到多个 iframe / scrollable container。 | 正式入口仍是 Web Shell 与 Streamlit 原生上传区混合。 |
| 正式可见禁词 | 抽样未命中 `运行边界`、`使用限制`、`隐私边界`、`不做实盘自动下单`、`demo`、`sample`、`synthetic`、`fixture`、`mock`、`fake`、`测试样例`、`低操作导入中心`、`数据源与同步`。 | 当前抽样没有发现禁词污染，但仍需 side thread 修复入口结构和设置隔离。 |

## 复验更新

复验时间：2026-06-28 Australia/Sydney

复验证据：

- `/tmp/pfi_uiux_recheck_stage5/summary.json`
- `/tmp/pfi_uiux_recheck_stage5/desktop.png`
- `/tmp/pfi_uiux_recheck_stage5/mobile.png`

已改善：

- 真实 8501 父页面不再显示底部 Streamlit 上传补丁：`hasNativeUploadPatch=false`。
- 父页面 iframe 从 2 个降为 1 个，父页面 scrollable container 降为 1 个。
- 桌面端 15 个一级入口可见。
- 桌面端点击 `数据源与上传` 后，真实支付宝数据进入正式入口；搜索 `8815` / `406` 能命中 `真实支付宝流水` 和 `待复核流水`。
- 业务页抽样不显示多模态反馈；设置页显示多模态反馈。
- 禁止可见词抽样 0 命中，console/page error 为 0。

仍未关闭：

- 移动端 `[data-primary-entry=true]` 15 个一级入口仍全部不可见。
- 移动端只显示 5 个 `[data-mobile-workspace]`：首页、账户、流水、上传、更多。
- `更多` 按钮真实点击失败：元素存在并显示，但 Playwright 判定 `element is outside of the viewport`，疑似底部导航、iframe 或 viewport 裁切问题。
- 因此移动端入口覆盖仍不能声明完成，正式 UIUX 交付仍阻断。

## 最终复验更新

复验时间：2026-06-28 Australia/Sydney

复验证据：

- `/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json`
- `/tmp/pfi_uiux_recheck_stage5_fixed2/desktop.png`
- `/tmp/pfi_uiux_recheck_stage5_fixed2/mobile.png`

复验结论：

| 视口 | 真实结果 | 结论 |
| --- | --- | --- |
| 桌面 1440x1000 | iframe=1；父页面无底部 Streamlit 上传补丁；15/15 一级入口可见且可点击；搜索 `8815` / `406` 命中真实支付宝流水和待复核流水；搜索结果一次 Escape 后关闭；`数据源与上传` 显示上传中心、导入中心、真实支付宝流水、`8815`、`406`；业务页未显示多模态反馈污染；设置页显示反馈控制；禁用可见词 0 命中；console/page error 为 0。 | 通过 |
| 移动 390x844 | iframe=1；父页面无底部 Streamlit 上传补丁；15/15 一级入口可见且可点击；移动端一级入口高度稳定为 42px；搜索 `8815` / `406` 命中真实支付宝流水和待复核流水；搜索结果一次 Escape 后关闭；上传中心、导入中心、真实支付宝流水、`8815`、`406` 可见；业务页未显示多模态反馈污染；设置页显示反馈控制；禁用可见词 0 命中；console/page error 为 0。 | 通过 |

附加修复：

- side thread 已完成正式入口上传/导入归位、业务页反馈污染清理、设置页反馈隔离、真实数字搜索索引、功能卡片小字和阶段标签清理。
- 主线程补充了全局搜索关闭兜底：`input type=search` 首次 Escape 会触发浏览器原生清空行为，导致结果面板继续拦截导航点击；现在 keyup Escape 和 blur 都会关闭搜索结果面板。

## 当前阻断状态

- 真实 8501 UIUX 入口阻断：已关闭。
- 移动端一级入口不可见：已关闭。
- 搜索结果拦截导航点击：已关闭。
- 正式页面可见测试/样例/模拟数据污染：本次真实浏览器抽样 0 命中。
- PFI 仓库 legacy 测试/样例/模拟数据审计：仍是全局后续风险，见 `TEST_DATA_AUDIT_STAGE5_20260628.md`；它不能用完整 pytest 直接替代产品验收。

## 后续验收要求

- 后续 Stage 复审必须继续从 `PFI.app` / 8501 验证桌面和移动端。
- 验收矩阵必须覆盖一级入口、二级入口、主要按钮、设置隔离、上传/导入、搜索、报告、图表、空状态、console error 和滚动手感；不能退回 marker/string-only 测试。
- 正式页面无真实数据时只显示中文真实空状态，不显示模拟值。
