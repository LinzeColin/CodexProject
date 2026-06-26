# PFI_OS 快速使用说明

这份文档是日常使用主入口。`PFI_OS` 是总系统入口，应用显示为 `PFI_OS`；PFIOS 是其中的量化研究与回测主入口。目标是让你不用记很多命令，也能完成启动、更新持仓、运行回测、阅读报告、同步行研系统和触发独立验证。

系统只做研究、回测、验证、复盘和报告。禁止接入实盘交易，禁止真实下单，禁止保存券商账户密码。

## 1. 每天怎么用

最常用流程是五步：

| 步骤 | 做什么 | 正常结果 |
| --- | --- | --- |
| 1 | 双击 `PFI_OS.app` | 浏览器打开 PFI_OS / PFIOS 工作台 |
| 2 | 看 `总控驾驶舱` | 显示总控状态、行动队列、证据来源、风控闸门和最新报告 |
| 3 | 更新或确认持仓 | 正式持仓写入持仓簿，截图/视频先进入候选复核 |
| 4 | 跑单标的回测或参数扫描 | 页面显示图表、核心指标、风险诊断 |
| 5 | 生成并阅读 Word 报告 | 报告进入 `~/Downloads/量化回测分析` |

日常使用优先从页面操作，不需要先打开终端。终端命令主要用于检查、同步、自动化和排查问题。

## 2. 启动和停止

最快启动方式：双击任意一个入口。

```text
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

`.app` 启动不会弹出 Terminal。关闭浏览器页面后，后台服务会在心跳超时后自动停止并释放内存。

如果页面显示 `No connection`、`Connection lost` 或一直打不开，先运行状态检查：

```bash
$PFI_OS_HOME/scripts/statusPFIOS.sh
```

如果只是日常开发、交接给 agent，或想确认 macOS 状态，优先运行统一验收入口；它默认只做轻量聚合，不触发完整 SmokeTest：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh
```

不要把完整 SmokeTest 当作日常检查。`finalAcceptanceCheck.sh` 和 `ciSmoke.sh` 默认需要 `PFI_OS_ALLOW_HEAVY_SMOKE=1`，只给明确 release gate 使用。

常用高级模式：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode app-entry --summary-json
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode lifecycle --summary-json
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode app-runtime --summary-json
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode ui --summary-json
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode public-summary --summary-json
```

底层脚本仍然保留给调试和追溯，例如：

```bash
$PFI_OS_HOME/scripts/devReadyCheck.sh --summary-json
$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh --summary-json
$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --summary-json
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --summary-json
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --output-dir data/systemAudit
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI_OS.app --summary-json
$PFI_OS_HOME/scripts/uiVisualAcceptance.sh --summary-json
$PFI_OS_HOME/scripts/macosPublicAcceptanceSummary.sh
```

需要强制停止时运行：

```bash
$PFI_OS_HOME/scripts/stopPFIOS.sh
```

备用双击停止入口：

```text
$PFI_OS_HOME/StopPFIOS.command
```

## 3. 工作台功能区怎么选

建议按这个顺序使用：

| 功能区 | 什么时候用 | 重点看什么 |
| --- | --- | --- |
| 总控驾驶舱 | 每次打开系统、生成报告前、使用结论前 | 总控状态、行动队列、证据来源、风控闸门 |
| 单标的回测 | 验证一个股票、ETF、基金或指数的策略表现 | 走势、策略收益、买入持有、相对收益、回撤、费用 |
| 报告中心 | 查找历史报告、复盘记录、验证任务和证据索引 | 报告验证工作台、Word 报告、数据质量、补证据任务、实验记录、错误画像 |
| 参数扫描 | 比较不同指标参数组合 | 热力图、稳定性、样本外验证、Walk-Forward |
| 组合轮动 | 多标的组合和轮动研究 | 组合收益、集中度、市场/货币/主题暴露 |
| 数据中心 | 检查数据源、搜索标的、做多源校验 | 数据质量、多源差异、A 股代码格式 |
| 情绪分析 | 看大盘、自选对象和持仓对象短期情绪 | 情绪分、RSI、波动、回撤、市场状态 |
| 热点分析 | 看大盘、行业、风格和避险资产强弱扩散 | 热点时间轴、热力图、气泡图、时间切片、热点热度 |
| 盘感训练 | 用技术指标练习读图和判断市场结构 | MA、RSI、MACD、Bollinger、ATR、量价确认 |
| 持仓 | 查看、导入、同步和复核持仓 | 正式持仓、待确认订单、候选更新 |
| 行研报告 | 按日期访问行研报告并生成验证任务 | 来源段落、研究主题、待验证问题 |
| 个人画像 | 汇总行为习惯、风险和改进方向 | 仓位纪律、交易冲动、风险暴露 |
| 大数据模拟 | 触发独立验证系统做大规模测试 | 行数、分片、checksum、运行状态 |
| 研究总线 | 查看跨系统输入、输出、心跳和错误 | Pending、Failed、候选持仓、系统状态 |
| 策略库 | 新增、编辑、排序和维护策略 | 策略逻辑、参数、收益来源、失效环境 |
| 左侧功能导航和使用指导 | 边切换功能区，边查看步骤、检查点和术语 | 手把手说明、风险、产出位置、悬停解释 |

## 4. 单标的回测怎么跑

进入 `单标的回测` 后按四步执行：

1. 选择市场、数据源、标的、周期和日期。
2. 选择策略和参数。
3. 设置成本假设，包括手续费、滑点和冲击成本。
4. 点击运行，先看页面结果，再打开 Word 报告。

第一次测试建议用默认样例：

| 项目 | 建议值 |
| --- | --- |
| 数据源 | Sample |
| 市场 | US |
| 标的 | AAPL |
| 周期 | 1d |
| 策略 | MA Crossover |

真实数据优先顺序：

| 市场 | 优先数据源 | 备注 |
| --- | --- | --- |
| A 股 | Moomoo、AKShare、TuShare | Moomoo 需要本机 OpenD |
| 美股 | Moomoo、Yahoo Finance、Alpha Vantage、Polygon | API key 缺失时会降级或提示 |
| 港股 | Moomoo、Yahoo Finance、AKShare | 以可用性和校验结果为准 |

如果标的搜索没有结果，不要强行回测。先检查市场选择、代码格式和数据源状态。

## 5. 结果先看什么

阅读结果时按这个顺序，不要先看总收益：

| 顺序 | 检查项 | 判断目的 |
| --- | --- | --- |
| 1 | 数据质量摘要 | 数据是否为空、缺字段、重复时间戳或异常 |
| 2 | 多源交叉校验 | 不同数据源是否互相支持 |
| 3 | 目标走势和策略收益图 | 策略是否只是跟随上涨 |
| 4 | 核心指标对比表 | 策略、买入持有、相对收益的收益/回撤/夏普 |
| 5 | 交易表和费用 | 交易次数、买入卖出次数、手续费、滑点、冲击成本 |
| 6 | 策略诊断 | 收益来源、失效环境、成本压力、鲁棒性 |
| 7 | 风险闸门和决策质量 | 是否只能继续研究、观察或暂停使用 |

如果报告状态是 `NeedsMoreEvidence` 或 `DoNotUse`，先不要把结论用于真实决策。优先进入 `报告中心 -> 证据索引` 看 `报告验证工作台`，它会只读合并报告证据、补证据候选和验证优先级，不写文件、不入队、不执行验证。

命令方式：

```bash
$PFI_OS_HOME/scripts/reportValidation.sh
```

确认要把候选任务写入队列时，再进入 `验证任务` 页的高级动作，或运行：

```bash
$PFI_OS_HOME/scripts/reportGapTasks.sh --output-dir data/reportDecision
```

如果验证任务很多，再点击高级动作里的 `生成验证优先级计划`。系统会把任务分为 `RunFirst`、`PrepareInputs`、`BatchValidate`、`ManualReview` 等处理桶，并指出每个任务缺什么输入、怎么验证、跳过有什么风险。

命令方式：

```bash
$PFI_OS_HOME/scripts/validationPriorityPlan.sh --output-dir data/validationQueue
```

如果最高优先级任务是可执行的 `CrossSourceValidation`，点击 `执行最高优先级验证任务` 或运行下面命令。执行结果可能是 `Pass`、`Review`、`Blocked` 或 `Error`；只有 `Pass` 才表示本次多源交叉校验证据可用。

```bash
$PFI_OS_HOME/scripts/runValidationTask.sh --output-dir data/validationQueue
```

关键概念：

| 名称 | 含义 |
| --- | --- |
| 买入持有 | 一开始买入目标对象并一直持有到结束 |
| 相对收益 | 策略收益率减去目标对象买入持有收益率 |
| 最大回撤 | 资金曲线从历史高点跌到后续低点的最大跌幅 |
| 滑点 | 假设成交价相对理想价格的不利偏移 |
| 冲击成本 | 订单本身影响成交价格造成的额外成本 |
| 胜率 | 已完成交易回合中盈利回合的比例，不等于策略一定赚钱 |

## 6. 持仓怎么更新

正式持仓文件：

```text
$PFI_OS_HOME/data/holdings/HoldingsBook.json
```

推荐导入结构化文件，准确率最高：

| 格式 | 推荐用途 |
| --- | --- |
| CSV | 日常持仓表、交易流水 |
| XLSX | 从表格软件导出的持仓 |
| JSON | 从其他系统直接同步 |
| 图片/视频 | 先进入候选复核；当前机器缺 OCR 依赖时不会自动写正式持仓 |

推荐字段：

```csv
symbol,name,market,position_value,quantity,updated_at
600000.SH,浦发银行,CN,12000,1000,2026-06-05
```

通过研究总线提交结构化持仓附件：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat \
  --text "这是今天的持仓文件，请进入候选复核" \
  --source-system ExternalChat \
  --attachment-path "/path/to/holding.csv" \
  --json
```

处理待办请求：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

确认结构化候选后才会写入正式持仓：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh confirm-holding-candidate \
  --candidate-id "holdingCandidate_xxx" \
  --json
```

截图或视频如果没有被解析成结构化持仓，会停在候选队列，不会覆盖正式持仓。这是故意的安全设计。

当前持仓表默认隐藏来源文件 path，只显示来源系统、代码、名称、市场、数量、成本/成本价、持仓金额、持有收益、持有收益率、权重和更新时间。

持有收益率口径：`持有收益率 = 持有收益 / (持仓金额 - 持有收益)`。如果分母不可用，系统显示为 `0.00%`，不自动编造收益率。

如果支付宝截图或视频只识别出基金名称、没有识别出代码，持仓页仍会保存金额和收益。情绪分析会先尝试使用本地“持仓名称 -> 行情代理代码”规则，把明显的黄金、半导体、人工智能、银行、恒生科技、纳斯达克、标普500等基金映射到 ETF、指数或行业代理；没有命中的对象会提示补代码。

代理代码只用于研究观察，不代表基金本身，不用于实盘交易指令。自定义映射可放在：

```text
$PFI_OS_HOME/data/holdings/HoldingSymbolMap.json
```

## 7. 情绪分析怎么用

进入 `情绪分析` 后按三步执行：

1. 选择数据源和市场。
2. 在 `对象来源` 勾选 `大盘对象`、`我的持仓` 或 `自选代码`。
3. 确认右侧 `已选择对象` 后，点击 `生成情绪观察`。

常用选择：

| 场景 | 建议选择 |
| --- | --- |
| 快速看市场温度 | 勾选 `大盘对象` |
| 看自己组合相关对象 | 勾选 `我的持仓`；系统会优先用真实代码，缺代码时用本地代理规则 |
| 看某几个具体对象 | 勾选 `自选代码` 并输入代码 |
| 组合观察 | 同时勾选 `大盘对象`、`我的持仓` 和 `自选代码` |

如果 `我的持仓` 没有可勾选对象，但页面显示了持仓名称，说明当前正式持仓缺少可拉行情的代码，且没有命中本地代理规则。系统会展示持仓列表并提示补代码，不会把这种情况误报成程序故障。

窗口口径：页面里的 `展示开始日期` 只控制显示和查看范围。系统会自动向前多取预热数据计算 RSI、波动率、回撤和情绪分。因此在数据源、目标对象和结束日期相同的情况下，改变展示开始日期不应让同一目标日期的情绪分发生大幅跳变。

如果使用 `Sample` 数据源，它现在按代码和时间戳稳定生成演示行情；同一个目标日期不会因为你改变展示开始日期而换一套底层价格。真实研究仍应优先使用 Moomoo、Yahoo Finance、AKShare 等可验证数据源。

## 8. 热点分析怎么用

进入 `热点分析` 后按六步执行：

1. 选择数据源、市场和时间粒度。`60min` 用于小时级观察，`1d` 用于日线观察。
2. 在 `分析范围` 勾选 `大盘热点`、`我的持仓` 或 `自选代码`。
3. 设置日期区间。小时级建议至少保留 30 个交易日。
4. 保持 `每小时自动刷新当前页` 开启，或关闭后手动点击生成。
5. 点击 `生成热点分析`，先看 `热点证据闸门`。如果出现 Review 或 Block，只能作为观察线索，需要先修正数据源、代码、时间粒度或样本区间。
6. 再看 `热点时间轴`，拖动 `时间切片` 或输入自定义时间查看不同小时或日期的变化。
7. 最后看热力图、气泡图、优先复核对象和热点明细。

读图顺序：

| 图表 | 怎么看 | 注意 |
| --- | --- | --- |
| 热力图 | 红色偏强，绿色偏弱，白色接近中性 | 颜色代表短期热度，不代表操作建议 |
| 气泡图 | 右上角表示近1期和近5期同步偏强，左下角同步偏弱 | 气泡越大，波动或异动越明显；象限标签只辅助读图 |
| 热点时间轴 | 看平均热度、偏强对象和偏弱对象如何随时间变化 | 图表底部可拖动时间轴，适合检查热点是否持续 |
| 时间切片 | 拖动查看热点是否持续扩散或快速消退 | 单小时异动需要结合新闻、成交和数据质量复核 |
| 热点证据闸门 | 检查数据覆盖率、失败率、样本长度、切片数量、刷新粒度和集中度 | 不通过时不要把热点图作为交易前参考 |

热点热度综合近 1 期、近 5 期、近 20 期涨跌、RSI、波动和回撤。VIX 等波动率对象会反向处理，因为波动上升通常代表风险温度上升。页面默认使用 `平滑热度`，它由多个时间切片的 `即时热度` 平滑而来；即时热度用于发现异动，平滑热度用于判断是否持续。该板块只用于研究观察，不输出实盘买卖或仓位建议。

窗口口径：`展示开始日期` 不再直接作为指标计算起点。系统会向前扩展预热窗口，再只把展示区间内的时间切片显示出来。这样同一个对象、同一个时间切片在不同展示区间下应保持相同即时热度、平滑热度和热度变化，除非数据源本身返回的数据发生变化。

`Sample` 数据源只用于功能演示和测试，但它也必须满足重叠区间稳定性：同一个代码、同一个时间切片在不同请求起点下应使用同一底层行情。

时间切片口径：热点图是横向比较，不应因为某个对象的行情时间戳差几分钟或半小时就把它排除。系统会用你选择的时间切片作为统一观察点，对每个对象取该时间点之前最新可用行情；明细表里的 `实际行情时间` 用来说明该对象实际使用的是哪一根行情。

## 9. 盘感训练怎么用

进入 `盘感训练` 后按六步执行：

1. 选择数据源和市场。
2. 在 `对象来源` 勾选 `大盘对象`、`我的持仓` 或 `自选代码`。
3. 设置日期区间，至少保留 60 个交易日，日常建议一年以上。
4. 选择训练难度：`入门` 只判断方向，`中等` 判断方向和收益区间，`专家` 判断方向、收益区间和更精确涨跌幅。
5. 选择判断周期和限时秒数。
6. 点击 `生成盘感训练`，先看隐藏答案区间的图表，点击开始后页面会自动倒计时；限时作答后再查看答案和复盘。

读图顺序：

| 顺序 | 看什么 | 目的 |
| --- | --- | --- |
| 1 | 价格、MA20、MA60 | 判断短期和中期趋势是否一致 |
| 2 | Bollinger | 判断是否接近上轨拥挤或下轨风险释放 |
| 3 | RSI14 | 判断动能是偏强、偏弱、拥挤还是低迷 |
| 4 | MACD | 判断动能是否改善或转弱 |
| 5 | 20日支撑/压力 | 判断价格离近期需求区和供给区有多远 |
| 6 | ATR、波动、回撤、成交量比 | 判断风险是否升温，以及量能是否确认价格方向 |

页面会输出 `事前技术分析`、`实际方向`、`实际收益区间`、`一致性` 和 `多维复盘`。事前技术分析只使用答案揭示前的数据。如果技术面倾向和实际走势不一致，复盘会提示补查事实面、基本面、价值面和交易面证据，而不是根据结果倒推分析过程。这些内容只用于读图训练和研究观察，不是涨跌预测，也不是实盘买卖或仓位建议。

## 9. 行研系统、消费行为系统、FIFA、政策系统和独立验证怎么同步

一次性同步所有系统：

```bash
$PFI_OS_HOME/scripts/syncResearchSystemsOnce.sh
```

只同步 PFIOS 研究总线：

```bash
$PFI_OS_HOME/scripts/syncResearchBus.sh --json
```

行研系统写入同一条研究总线：

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-submit --text "请把这条研究问题同步到 PFIOS" --json
```

共享数据库：

```text
$PFI_OS_HOME/data/researchBus/ResearchBus.sqlite
```

共享 schema：

```text
$PFI_OS_HOME/docs/ResearchBusSchema.json
```

查看母子系统注册表：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh status --json
```

登记并同步 FIFA/TAB、政府文件/政策系统、行研系统和独立验证系统的产物索引：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh register --json
$PFI_OS_HOME/scripts/orchestrateSystems.sh sync-artifacts --json
```

母系统 dry-run 调度子系统，不实际运行：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh run --system FIFA-Research-System --action health --json
```

子系统仍可独立运行。例如 FIFA：

```bash
cd $PFI_SYSTEMS_ROOT/fifa_research
scripts/run_tab_fifa_daily_automation.sh --verify-only
```

政府文件/政策系统：

```bash
cd $PFI_GOVERNMENT_POLICY_ROOT
python3 -m source_registry --db data/source_registry.sqlite status --json
```

## 10. 大数据模拟怎么用

页面方式：进入首页或 `大数据模拟` 功能区，选择行数、分片大小和模式后运行。

命令方式，百亿行 dry-run：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run \
  --synthetic-rows 10000000000 \
  --rows-per-shard 100000000 \
  --json
```

命令方式，checksum 分片校验：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run \
  --synthetic-rows 10000000 \
  --rows-per-shard 1000000 \
  --mode checksum \
  --json
```

命令方式，百亿行本机 worker pool checksum：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run \
  --synthetic-rows 10000000000 \
  --rows-per-shard 1000000000 \
  --mode checksum \
  --worker-count 4 \
  --json
```

自然语言入口也支持：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat \
  --text "请运行千万行独立验证 checksum 校验，每片100万行" \
  --source-system ExternalChat \
  --json
```

## 11. 报告在哪里

报告主目录：

```text
~/Downloads/量化回测分析
```

报告命名规则：

```text
报告名称_DDMMYYYY.docx
```

每份正式回测报告应优先阅读：

| 报告位置 | 内容 |
| --- | --- |
| 执行摘要 | 策略与买入持有对比、核心结论 |
| 数据质量摘要 | 数据是否可用、是否有缺口 |
| 多源交叉校验摘要 | 不同数据源是否一致 |
| 核心指标表 | 策略、买入持有、相对表现 |
| 图表区 | 走势、收益、回撤、买卖点、费用 |
| 策略诊断 | 收益来源、失效环境、成本压力 |
| 元数据说明 | 本次运行的参数、代码化记录和追溯信息 |

## 12. 常见问题

| 问题 | 处理方式 |
| --- | --- |
| 页面显示 No connection | 运行 `statusPFIOS.sh`；必要时运行 `stopPFIOS.sh` 后重新双击 app |
| 双击 app 没反应 | 查看 `data/cache/pfi_os_macos_app.log`，再运行 `scripts/startPFIOS.sh` 做终端诊断 |
| Moomoo 不可用 | 确认 Moomoo OpenD 已启动并监听 `11111` 端口 |
| AKShare 或 Yahoo 临时失败 | 这是外部数据源问题；换数据源或稍后重试，并看多源校验结果 |
| 截图/视频没有自动入库 | 当前机器缺 OCR/ffmpeg 依赖时会 fail-closed，需要提供 CSV/XLSX/JSON |
| 情绪分析的我的持仓为空 | 当前持仓可能只有名称且未命中代理规则；先补代码，或在 `HoldingSymbolMap.json` 里增加映射 |
| 热点分析失败对象较多 | 先切换 Sample 验证页面，再检查真实数据源权限、代码格式和 60min 粒度是否支持 |
| 盘感训练提示样本不足 | 把开始日期提前，至少保留 60 个交易日 |
| 后台同步权限失败 | 当前工程在 `Documents` 下，macOS TCC 可能拦截 LaunchAgent；优先手动运行 `syncResearchSystemsOnce.sh` |
| 不确定策略能不能用 | 到策略库确认当前版本、数据质量、成本压力、样本外验证、Walk-Forward 和风险闸门 |

## 13. 后续新增功能时怎么维护说明

每次新增或修改功能后，至少同步更新：

| 文件 | 更新内容 |
| --- | --- |
| `docs/QuickStart.md` | 日常用户怎么使用 |
| `docs/FeatureSpecification.md` | 功能说明书和增删修补记录 |
| `docs/Handbook.md` | 深入解释、公式和专业概念 |
| `docs/ResearchBus.md` | 跨系统输入、输出、数据表或命令变化 |
| `HANDOFF.md` | 关键决策、验证结果、未解决问题 |

如果功能涉及金额、收益、成本、持仓、回撤或比例，必须写清公式、假设、数据来源和验证方式。
