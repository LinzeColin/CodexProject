# Validation Task Execution

## 功能定位

`Validation Task Execution` 用于执行一个研究验证任务，并生成可追溯的执行记录。当前优先支持 `CrossSourceValidation`，也就是对同一标的、同一时间区间、同一周期的收盘价做多源交叉校验。

它解决的问题是：验证任务不能只停留在待办列表里，必须记录“执行了什么、用了哪些数据源、结果是否通过、为什么没通过、下一步是什么”。

## 安全边界

该功能只做研究验证。

它不会连接实盘交易。

它不会提交真实订单。

它不会修改持仓。

它不会修改旧报告。

它不会自动把策略升级为可用结论。

它默认不修改 `ValidationTasks.json` 的任务状态，而是生成独立执行记录。

## 输入

| 输入 | 默认值 | 说明 |
| --- | --- | --- |
| 任务 | 最高优先级 `CrossSourceValidation` | 来自 `ValidationTaskPriorityPlan_latest.json` 或实时计划 |
| 标的 | 任务中的 `symbol` | 例如 `AAPL` |
| 市场 | 任务中的 `market` | 例如 `US` |
| 周期 | `1d` | 当前优先日线 |
| 开始日期 | `2024-01-01` | 可通过命令覆盖 |
| 结束日期 | `2024-01-31` | 可通过命令覆盖 |
| 容忍差异 | `1.00%` | 收盘价最大差异超过则进入复核 |

## 输出

输出目录：

```text
data/validationQueue/
```

文件：

| 文件 | 用途 |
| --- | --- |
| `ValidationTaskExecution_DDMMYYYY_<id>.json` | 机器可读执行记录 |
| `ValidationTaskExecution_DDMMYYYY_<id>.csv` | 表格摘要 |
| `ValidationTaskExecution_DDMMYYYY_<id>.md` | 人工阅读摘要 |
| `ValidationTaskExecution_DDMMYYYY_<id>.pdf` | 正式执行摘要 |
| `ValidationTaskExecution_latest.*` | 最新执行指针 |
| `CrossValidation_*.json` | 底层多源交叉校验详情，只有实际运行校验时生成 |

## 执行状态

| 状态 | 含义 | 是否关闭证据缺口 |
| --- | --- | --- |
| `Pass` | 多源数据有重叠，差异在容忍范围内 | 可以作为该时间窗口的证据 |
| `Review` | 已运行，但差异过大、无重叠或数据不足 | 不能关闭，需要复核 |
| `Blocked` | 缺代码、市场或至少两个真实数据源 | 不能关闭，需要先补输入或数据源 |
| `Error` | 运行中出错 | 不能关闭，需要修复后重跑 |

## 页面使用

1. 打开 `PFI_OS`。
2. 进入 `报告中心`。
3. 打开 `验证任务`。
4. 先点击 `生成验证优先级计划`。
5. 再点击 `执行最高优先级验证任务`。
6. 查看状态、阻塞项和执行记录路径。

## 命令使用

执行最高优先级任务：

```bash
scripts/runValidationTask.sh --output-dir data/validationQueue
```

指定任务：

```bash
scripts/runValidationTask.sh --task-id reportGapTask_e075e54ff090b224301e --output-dir data/validationQueue
```

指定数据源：

```bash
scripts/runValidationTask.sh --provider "Yahoo Finance" --provider "Polygon" --symbol AAPL --market US --output-dir data/validationQueue
```

指定时间区间：

```bash
scripts/runValidationTask.sh --start 2024-01-01 --end 2024-01-31 --output-dir data/validationQueue
```

## 结果判读

如果状态是 `Pass`，说明本次标的、区间、周期、数据源组合下，多源收盘价差异在容忍范围内。

如果状态是 `Blocked`，通常是因为当前只有一个真实数据源可用，或者 Moomoo OpenD / Alpha Vantage / Polygon / TuShare 未配置。此时不能把报告升级为证据充分。

如果状态是 `Review`，需要打开底层 `CrossValidation_*.json`，检查重叠行数、最大差异、均值差异和各数据源价格。

## 验收标准

1. 命令能生成 JSON、CSV、Markdown 和 PDF。
2. 原始 `ValidationTasks.json` 不被修改。
3. 数据源不足时输出 `Blocked`，而不是伪造通过。
4. 执行成功时保存底层 `CrossValidation_*.json`。
6. `scripts/verifyPFIOS.sh` 和 `scripts/finalAcceptanceCheck.sh` 均通过。

## 已知限制

当前执行器优先支持 `CrossSourceValidation`。参数稳定性、样本外验证和 walk-forward 的执行器应后续逐项新增，不能混在同一轮里一次性堆完。
