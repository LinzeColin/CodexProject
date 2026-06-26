# Validation Priority Plan

## 功能定位

`Validation Priority Plan` 是验证任务队列的执行顺序规划器。它读取 `data/validationQueue/ValidationTasks.json`，按证据缺口类型、任务状态、是否来自正式报告、是否具备标的代码和市场、是否需要先补输入等因素，为待验证任务生成优先级计划。

这个功能解决的问题是：验证任务数量可能很多，如果没有排序，很容易先处理低价值任务，反而让关键报告长期停留在 `NeedsMoreEvidence`。

## 安全边界

该功能只排序和生成计划。

它不会联网刷新行情。

它不会运行回测。

它不会运行多源校验。

它不会修改验证任务状态。

它不会修改持仓或旧报告。

它不会连接实盘、不会下单、不会输出交易指令。

## 输入

| 输入 | 位置 | 用途 |
| --- | --- | --- |
| 验证任务队列 | `data/validationQueue/ValidationTasks.json` | 待排序任务来源 |
| 补证据任务扩展字段 | `evidence_gap`、`dedupe_key`、`metadata_path` | 判断缺失证据类型和来源 |
| 任务状态 | `待验证`、`验证中`、`已完成`、`暂停` | 判断是否纳入本轮计划 |

默认不纳入 `已完成` 任务。

## 输出

输出目录：

```text
data/validationQueue/
```

文件：

| 文件 | 用途 |
| --- | --- |
| `ValidationTaskPriorityPlan_DDMMYYYY.json` | 机器可读优先级计划 |
| `ValidationTaskPriorityPlan_DDMMYYYY.csv` | 表格筛选 |
| `ValidationTaskPriorityPlan_DDMMYYYY.md` | 人工阅读摘要 |
| `ValidationTaskPriorityPlan_DDMMYYYY.pdf` | 正式摘要 |
| `ValidationTaskPriorityPlan_latest.*` | 最新指针 |

## 优先级逻辑

排序优先级遵循一个核心原则：先补会影响所有后续结论的基础证据。

| 证据缺口 | 优先级理由 |
| --- | --- |
| `DataQuality` | 数据本身不可信时，所有收益、回撤和指标都不可信 |
| `CrossSourceValidation` | 单一数据源错误可能被误当成策略证据 |
| `ReportEvidence` | 没有报告证据层时，报告无法追溯 |
| `RiskGate` | 防止只看收益、不看回撤、成本和停用条件 |
| `WalkForwardValidation` | 检查规律是否跨时间窗口稳定 |
| `TrainTestValidation` | 检查是否只在样本内有效 |
| `ParameterStability` | 检查结论是否依赖单一参数 |
| `DecisionQuality` | 补 Thesis、反方观点、风险和退出条件 |

## 处理桶

| 处理桶 | 含义 | 下一步 |
| --- | --- | --- |
| `RunFirst` | 基础证据完整，优先补跑 | 下一轮优先执行 |
| `PrepareInputs` | 缺代码、市场、来源报告等输入 | 先补输入，不要直接跑验证 |
| `BatchValidate` | 可批量验证 | 适合后续批处理 |
| `ManualReview` | 需要人工复核或研究判断 | 先补文字证据和假设 |
| `Paused` | 已暂停 | 暂不处理 |
| `Completed` | 已完成 | 默认不纳入计划 |

## 页面使用

1. 打开 `PFI_OS`。
2. 进入 `报告中心`。
3. 打开 `验证任务`。
4. 点击 `生成验证优先级计划`。
5. 先看顶部 20 条任务。
6. 若出现 `PrepareInputs`，先补代码、市场或来源报告。
7. 后续按 `RunFirst -> BatchValidate -> ManualReview` 顺序推进。

## 命令使用

生成正式计划：

```bash
scripts/validationPriorityPlan.sh --output-dir data/validationQueue
```

只看统计，不写文件：

```bash
scripts/validationPriorityPlan.sh --json-only
```

增加输出任务数量：

```bash
scripts/validationPriorityPlan.sh --max-tasks 300 --output-dir data/validationQueue
```

## 验收标准

合格状态：

1. 命令可以生成 JSON、CSV、Markdown 和 PDF。
2. 原始 `ValidationTasks.json` 不被修改。
3. `DataQuality`、`CrossSourceValidation`、`ReportEvidence` 等基础证据任务优先。
4. 缺少代码或市场的数据依赖任务进入 `PrepareInputs`。
5. 输出明确写明所需输入、验证方式、跳过风险和阻塞项。
6. `scripts/verifyPFIOS.sh` 与 `scripts/finalAcceptanceCheck.sh` 均通过。

## 已知限制

优先级分数是执行计划启发式，不是策略有效性的证据。

真正把报告从 `NeedsMoreEvidence` 升级，需要后续实际补跑数据质量、多源校验、参数稳定性、样本外验证或 walk-forward 验证。
