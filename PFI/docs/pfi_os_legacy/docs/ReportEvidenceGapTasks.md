# Report Evidence Gap Tasks

## 功能定位

`Report Evidence Gap Tasks` 是报告中心的补证据任务生成器。它读取 `Report Decision Support Index` 中被降级为 `NeedsMoreEvidence` 或 `DoNotUse` 的报告，把缺失证据拆成验证任务，并追加到验证任务队列。

它解决的问题是：报告已经指出证据不足，但下一步到底该补数据质量、多源交叉校验、参数稳定性、样本外验证还是 walk-forward 验证，需要自动结构化，避免人工漏项。

## 安全边界

该功能只生成研究验证任务。

它不会联网刷新行情。

它不会运行回测或验证。

它不会修改旧报告。

它不会修改持仓。

它不会连接券商、不会下单、不会输出实盘交易指令。

## 输入

主要输入来自：

| 输入 | 位置 | 用途 |
| --- | --- | --- |
| Report Decision Support Index | `data/reportDecision/ReportDecisionSupportIndex_latest.json` 或实时扫描报告目录 | 找出证据不足的报告 |
| RunMetadata | `~/Downloads/量化回测分析/YYYY-MM-DD/RunMetadata_*.json` | 读取策略、标的、市场、风险闸门和缺失证据 |
| Word 报告 | `~/Downloads/量化回测分析/YYYY-MM-DD/*.docx` | 关联正式报告路径 |
| 验证任务队列 | `data/validationQueue/ValidationTasks.json` | 追加新任务并去重 |

## 输出

正式输出保存在：

```text
data/reportDecision/
```

每次运行会生成：

| 文件 | 用途 |
| --- | --- |
| `ReportEvidenceGapTasks_DDMMYYYY.json` | 机器可读任务清单 |
| `ReportEvidenceGapTasks_DDMMYYYY.csv` | 表格查看和筛选 |
| `ReportEvidenceGapTasks_DDMMYYYY.md` | 人工阅读摘要 |
| `ReportEvidenceGapTasks_DDMMYYYY.pdf` | 正式交付摘要 |
| `ReportEvidenceGapTasks_latest.*` | 最新指针 |

新任务会追加到：

```text
data/validationQueue/ValidationTasks.json
```

## 任务分类

系统会把缺失证据自动归类为：

| 类别 | 说明 | 下一步 |
| --- | --- | --- |
| `ReportEvidence` | 报告缺少 `PFIOSReportEvidenceV1` | 重新生成带证据层的报告 |
| `DataQuality` | 缺少数据质量检查 | 补跑数据质量审计 |
| `CrossSourceValidation` | 缺少多源交叉校验 | 比较至少两个可用真实数据源 |
| `RiskGate` | 缺少研究风险闸门 | 补收益、回撤、成本、稳定性和停用条件 |
| `DecisionQuality` | 缺少决策质量信息 | 补 Thesis、证据、风险、反方观点和退出条件 |
| `ParameterStability` | 缺少参数稳定性验证 | 补参数扫描和稳定性检查 |
| `TrainTestValidation` | 缺少样本内/样本外验证 | 补训练集和测试集表现对比 |
| `WalkForwardValidation` | 缺少滚动验证 | 补 walk-forward 验证 |
| `WordReport` | 缺少可追溯正式报告 | 重新导出 Word 报告 |
| `EvidenceReview` | 未识别的证据缺口 | 人工复核 |

## 页面使用

1. 打开 `PFI_OS`。
2. 进入 `报告中心`。
3. 打开验证任务队列区域。
4. 点击 `从报告缺失证据生成任务`。
5. 查看新增数量、跳过重复数量和输出文件路径。
6. 后续再按验证任务逐项补数据、补报告或补实验。

## 命令使用

预览任务，不写入队列：

```bash
scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision
```

追加任务到正式验证队列：

```bash
scripts/reportGapTasks.sh --output-dir data/reportDecision
```

只看候选数量，不写文件、不写队列：

```bash
scripts/reportGapTasks.sh --json-only
```

## 去重规则

系统使用稳定去重键，核心字段包括：

| 字段 | 作用 |
| --- | --- |
| `source_report` | 来源报告 |
| `metadata_path` | 来源 RunMetadata |
| `run` | 运行编号 |
| `evidence_gap` | 缺失证据类别 |
| `symbol` | 标的 |
| `market` | 市场 |
| `signal_to_validate` | 待验证信号 |

重复运行同一个命令不会重复追加同一任务。

## 验收标准

合格状态：

1. `scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision` 可以生成 JSON、CSV、Markdown 和 PDF。
2. `scripts/reportGapTasks.sh --output-dir data/reportDecision` 会追加新任务到验证队列。
3. 第二次运行同一命令时，`appended=0`，重复任务被跳过。
4. 原有验证任务仍然保留。
5. 旧报告和持仓不会被修改。
6. `scripts/verifyPFIOS.sh` 和 `scripts/finalAcceptanceCheck.sh` 均通过。

## 已知限制

任务生成器只负责把缺失证据变成待办任务。它不会判断补完证据后的策略是否有效，也不会自动把报告升级为 `ContinueResearch`。

报告是否升级，需要后续真实运行数据质量检查、多源校验、参数扫描、样本外验证和 walk-forward 验证后，由 `Report Decision Support Index` 重新评估。
