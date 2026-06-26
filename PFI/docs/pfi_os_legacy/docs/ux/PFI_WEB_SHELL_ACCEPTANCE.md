# PFI Web Shell 验收契约

Version: PFI-004 / v0.1.1 repair

PFI Web Shell 是 PFI OS 的默认用户入口。交付标准是中文优先、面向真实使用、六个一级入口可切换完整功能板块，而不是只替换标题或展示旧系统壳。

## 用户可见范围

- 一级入口固定为：首页、市场、研究、持仓、策略实验室、数据与系统。
- 每个入口必须同步切换：标题、副标题、结论、状态卡、功能卡、决策表格、任务中心、证据抽屉和图表。
- 策略实验室必须保留策略回测、参数扫描、模拟实验和盘感训练。
- 持仓入口只生成人工复核材料和订单意图草案，不连接券商、不自动提交订单。
- 数据与系统入口必须展示来源、任务、隐私边界、备份和诊断状态。
- 首屏、按钮、错误、缓存兜底、任务状态和证据抽屉必须使用中文用户文案；技术标识、schema、文件名和证券代码可保留英文。

## 交互契约

- 工作区切换在本地完成，不刷新整页，不跳回旧页面。
- 功能卡必须有明确的 `打开功能` 动作；所有可见功能卡都必须先打开同屏中文操作面板，而不是只切换工作区、跳到旧 Streamlit 详情页或只打开证据说明。
- 功能面板必须使用中文用户语义解释检查项、证据边界和下一步；技术字段名、schema 名和英文状态码不得作为默认用户文案暴露。
- 全局上下文保存到本地状态，覆盖市场、标的、组合、日期、币种、新鲜度、研究任务、证据集和模拟场景。
- 命令面板、任务中心、证据抽屉、表格筛选、排序、导出、缓存刷新和缓存兜底按钮必须可触发。
- 超过 300ms 的反馈显示骨架态；超过 1s 显示步骤；超过 10s 显示后台任务编号。
- Streamlit 嵌入入口必须隐藏无关工具栏噪音，让用户默认看到 PFI 工作台。
- Streamlit 必须用 `components.html` 渲染内联 PFI Web Shell，不允许把完整 HTML 传给 iframe URL API，避免出现 raw HTML、英文技术噪音或乱码页。
- 浏览器本地状态 key 为 `pfi-context-v2`；旧缓存状态不得继续控制新 PFI Shell 的默认打开位置。

## 非目标

- 本轮不重写回测内核。
- 本轮不接入本地模型。
- 本轮不新增 Docker、独立 Web API 或 Worker。
- 本轮不迁移旧业务页面目录。
- 本轮不创建任何实盘自动下单、支付、投注或无人值守执行路径。

## Gate 2 验收

- 合同测试覆盖六入口、中文证据抽屉、全局上下文、功能开关、隐私边界和无退休品牌文本。
- 静态 E2E 测试覆盖本地状态保存、六入口完整重渲染、任务中心、证据抽屉、命令面板、表格控件和缓存兜底。
- 浏览器验证必须实际点击六个入口，并确认页面内容随入口切换且无退休品牌或旧价值账本用户可见内容。
- `scripts/pfiGate2ShellAcceptance.sh` 是 Gate 2 的正式用户导向验收入口，必须生成 `PFIGate2ShellAcceptanceV1` JSON。
- Gate 2 必须覆盖八条命名 UAT：`JOURNEY_HOME_TO_BACKTEST`、`JOURNEY_STRATEGY_MARKET_FEEL`、`JOURNEY_STRATEGY_PARAMETER_SCAN`、`JOURNEY_STRATEGY_SIMULATION`、`JOURNEY_MARKET_HOTSPOTS`、`JOURNEY_RESEARCH_REPORT_POLICY`、`JOURNEY_PORTFOLIO_HOLDINGS_REVIEW`、`JOURNEY_DATA_SYSTEM_DIAGNOSTICS`。
- Gate 2 必须遍历六个入口下全部可见功能卡，逐个点击并确认同壳中文功能面板、操作区、安全边界、无新页面、无 legacy query。
- 核心功能入口必须先打开同壳中文功能面板和操作区；兼容详情页只能通过显式 `pfi_legacy=1` 路径访问，不属于默认用户交付路径，当前 PFI Web Shell 不得被替换成旧导航。
- Gate 2 必须同时记录 WCAG 结构证明、交互性能预算、截图证据和失败闭合原因。
